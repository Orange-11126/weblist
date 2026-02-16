from functools import wraps
from flask import request, jsonify, g
from datetime import datetime, timedelta
import threading
import json

_path_permission_cache = {}
_cache_lock = threading.Lock()
_cache_ttl = 300

def get_cached_permissions(user_id, role_ids):
    cache_key = f"user_{user_id}_roles_{'_'.join(map(str, sorted(role_ids)))}"
    with _cache_lock:
        cached = _path_permission_cache.get(cache_key)
        if cached and cached['expires_at'] > datetime.utcnow():
            return cached['permissions']
    return None

def set_cached_permissions(user_id, role_ids, permissions):
    cache_key = f"user_{user_id}_roles_{'_'.join(map(str, sorted(role_ids)))}"
    with _cache_lock:
        _path_permission_cache[cache_key] = {
            'permissions': permissions,
            'expires_at': datetime.utcnow() + timedelta(seconds=_cache_ttl)
        }

def invalidate_permission_cache(user_id=None, role_id=None):
    with _cache_lock:
        if user_id:
            keys_to_remove = [k for k in _path_permission_cache.keys() if f"user_{user_id}_" in k]
            for key in keys_to_remove:
                del _path_permission_cache[key]
        elif role_id:
            keys_to_remove = [k for k in _path_permission_cache.keys() if f"_roles_" in k and str(role_id) in k]
            for key in keys_to_remove:
                del _path_permission_cache[key]
        else:
            _path_permission_cache.clear()

def check_path_permission(user, path, permission_type='read'):
    from business_logic.models.db_models import PathPermission, db
    
    if user.is_admin():
        return True, None
    
    role_ids = [role.id for role in user.roles]
    cached_perms = get_cached_permissions(user.id, role_ids)
    
    if cached_perms is not None:
        permissions = cached_perms
    else:
        permissions = PathPermission.query.filter(
            db.or_(
                PathPermission.user_id == user.id,
                PathPermission.role_id.in_(role_ids)
            )
        ).order_by(PathPermission.priority.desc()).all()
        
        permissions_data = [{
            'path': p.path,
            'permission_type': p.permission_type,
            'is_allowed': p.is_allowed,
            'inherit': p.inherit
        } for p in permissions]
        
        set_cached_permissions(user.id, role_ids, permissions_data)
        permissions = permissions_data
    
    for perm in permissions:
        if perm['permission_type'] != permission_type:
            continue
            
        perm_path = perm['path']
        inherit = perm['inherit']
        
        if perm_path == '/':
            return perm['is_allowed'], None if perm['is_allowed'] else "无权访问此路径"
        
        if inherit:
            if path.startswith(perm_path):
                return perm['is_allowed'], None if perm['is_allowed'] else "无权访问此路径"
        else:
            if path == perm_path:
                return perm['is_allowed'], None if perm['is_allowed'] else "无权访问此路径"
    
    return True, None

def require_path_permission(permission_type='read'):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from business_logic.models.db_models import User, get_guest_user, db
            
            token = request.headers.get('Authorization', '').replace('Bearer ', '')
            if not token:
                token = request.cookies.get('token')
            
            user = None
            if token:
                from flask import current_app
                try:
                    import jwt
                    payload = jwt.decode(
                        token, 
                        current_app.config['SECRET_KEY'], 
                        algorithms=['HS256']
                    )
                    user = User.query.get(payload.get('user_id'))
                except:
                    pass
            
            if not user:
                user = get_guest_user()
            
            path = request.args.get('path', '/')
            if request.method == 'POST' and request.is_json:
                data = request.get_json()
                if 'path' in data:
                    path = data['path']
                elif 'parentPath' in data:
                    path = data['parentPath']
            
            has_permission, error_msg = check_path_permission(user, path, permission_type)
            
            if not has_permission:
                return jsonify({
                    'code': 403,
                    'message': error_msg or '无权访问此路径',
                    'data': None
                }), 403
            
            g.current_user = user
            g.current_path = path
            
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def get_user_accessible_paths(user):
    from business_logic.models.db_models import PathPermission, db
    
    if user.is_admin():
        return [{'path': '/', 'permission': 'admin', 'is_allowed': True}]
    
    role_ids = [role.id for role in user.roles]
    
    permissions = PathPermission.query.filter(
        db.or_(
            PathPermission.user_id == user.id,
            PathPermission.role_id.in_(role_ids)
        )
    ).order_by(PathPermission.priority.desc(), PathPermission.path).all()
    
    accessible = []
    for perm in permissions:
        accessible.append({
            'path': perm.path,
            'permission': perm.permission_type,
            'is_allowed': perm.is_allowed,
            'inherit': perm.inherit
        })
    
    return accessible

def filter_files_by_permission(user, files, path, permission_type='read'):
    from business_logic.models.db_models import PathPermission, db
    
    if user.is_admin():
        return files
    
    role_ids = [role.id for role in user.roles]
    
    permissions = PathPermission.query.filter(
        db.or_(
            PathPermission.user_id == user.id,
            PathPermission.role_id.in_(role_ids)
        ),
        PathPermission.permission_type == permission_type
    ).order_by(PathPermission.priority.desc()).all()
    
    allowed_paths = set()
    blocked_paths = set()
    
    for perm in permissions:
        full_path = perm.path if perm.path.endswith('/') else perm.path + '/'
        if perm.is_allowed:
            allowed_paths.add(full_path)
        else:
            blocked_paths.add(full_path)
    
    def is_path_blocked(file_path):
        for blocked in blocked_paths:
            if file_path.startswith(blocked):
                return True
        return False
    
    def is_path_allowed(file_path):
        if not allowed_paths:
            return True
        for allowed in allowed_paths:
            if file_path.startswith(allowed) or allowed == '/':
                return True
        return False
    
    filtered_files = []
    for file in files:
        file_path = path + '/' + file.get('name', '') if path != '/' else '/' + file.get('name', '')
        
        if is_path_blocked(file_path):
            continue
        
        if is_path_allowed(file_path):
            filtered_files.append(file)
    
    return filtered_files
