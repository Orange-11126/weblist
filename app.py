import json
import os
import hashlib
import re
from datetime import datetime, timedelta, timezone
from functools import wraps
from flask import Flask, request, jsonify, render_template, send_from_directory, url_for, redirect
from flask_cors import CORS
import jwt

CONFIG_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'config', 'config.json')
BACKUP_DIR = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'static', 'config', 'backups')

DEFAULT_CONFIG = {
    "site": {
        "title": "个人网盘",
        "description": "基于123网盘的个人文件管理系统"
    },
    "theme": {
        "primary_color": "#4F46E5",
        "background_color": "#f5f3ff",
        "font_family": ""
    },
    "layout": {
        "header_html": "<header class='site-header'><h1>个人网盘</h1></header>",
        "footer_html": "<footer class='site-footer'><p>&copy; 2024 个人网盘</p></footer>",
        "custom_css": "/* 自定义样式 */",
        "show_footer": True,
        "show_breadcrumb": True,
        "max_width": "1200px"
    },
    "upload": {
        "max_file_size": 2147483648,
        "max_concurrent": 3,
        "allowed_types": "jpg,jpeg,png,gif,pdf,zip,rar,doc,docx,xls,xlsx,mp4,mp3"
    },
    "features": {
        "enable_search": True,
        "enable_share": True,
        "enable_preview": True,
        "enable_drag_drop": True
    },
    "email": {
        "smtp_server": "smtp.example.com",
        "smtp_port": 587,
        "smtp_use_tls": True,
        "smtp_username": "",
        "smtp_password": "",
        "from_email": "noreply@example.com",
        "from_name": "个人网盘"
    },
    "auth": {
        "jwt_secret": "your-secret-key-change-in-production",
        "token_expire_hours": 24
    },
    "setup_completed": False
}


def ensure_config_exists():
    if not os.path.exists(CONFIG_PATH):
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(DEFAULT_CONFIG, f, ensure_ascii=False, indent=2)
        print('配置文件已创建: ' + CONFIG_PATH)
        return DEFAULT_CONFIG
    return None


def load_config():
    try:
        default_created = ensure_config_exists()
        if default_created:
            return default_created
        with open(CONFIG_PATH, 'r', encoding='utf-8') as f:
            config = json.load(f)
            changed = False
            for key, value in DEFAULT_CONFIG.items():
                if key not in config:
                    config[key] = value
                    changed = True
            if changed:
                save_config(config)
            return config
    except Exception as e:
        return {"error": str(e)}


def save_config(config):
    try:
        os.makedirs(os.path.dirname(CONFIG_PATH), exist_ok=True)
        with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return True
    except Exception as e:
        print(f"Save config error: {e}")
        return False


app = Flask(__name__, template_folder='templates', static_folder='static')
CORS(app)

config = load_config()
app.config['SECRET_KEY'] = config.get('auth', {}).get('jwt_secret', 'your-secret-key-change-in-production')
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///users.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

email_config = config.get('email', {})
app.config['MAIL_SERVER'] = email_config.get('smtp_server', 'smtp.example.com')
app.config['MAIL_PORT'] = email_config.get('smtp_port', 587)
app.config['MAIL_USE_TLS'] = email_config.get('smtp_use_tls', True)
app.config['MAIL_USERNAME'] = email_config.get('smtp_username', '')
app.config['MAIL_PASSWORD'] = email_config.get('smtp_password', '')
app.config['MAIL_DEFAULT_SENDER'] = email_config.get('from_email', 'noreply@example.com')

from business_logic.models.db_models import db, User, Role, Permission, PasswordPolicy, UserAttribute, FilePermission, PathPermission, get_guest_user, invalidate_guest_cache
from business_logic.services.user_service import PasswordValidator

db.init_app(app)


def validate_color(color):
    hex_pattern = r'^#([A-Fa-f0-9]{6}|[A-Fa-f0-9]{3})$'
    rgb_pattern = r'^rgb\(\s*\d{1,3}\s*,\s*\d{1,3}\s*,\s*\d{1,3}\s*\)$'
    hsl_pattern = r'^hsl\(\s*\d{1,3}\s*,\s*\d{1,3}%?\s*,\s*\d{1,3}%?\s*\)$'
    return bool(re.match(hex_pattern, color) or re.match(rgb_pattern, color) or re.match(hsl_pattern, color))


def sanitize_html(html_content):
    dangerous_tags = ['<script', '</script>', 'javascript:', 'onerror=', 'onclick=', 'onload=']
    sanitized = html_content
    for tag in dangerous_tags:
        sanitized = sanitized.replace(tag, '')
    return sanitized


def create_backup():
    try:
        os.makedirs(BACKUP_DIR, exist_ok=True)
        config = load_config()
        if "error" in config:
            return None
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_path = os.path.join(BACKUP_DIR, f'config_backup_{timestamp}.json')
        with open(backup_path, 'w', encoding='utf-8') as f:
            json.dump(config, f, ensure_ascii=False, indent=2)
        return timestamp
    except Exception as e:
        print(f"Backup error: {e}")
        return None


def get_token_from_request():
    auth_header = request.headers.get('Authorization', '')
    if auth_header.startswith('Bearer '):
        return auth_header[7:]
    return None


def generate_token(username):
    config = load_config()
    secret = config.get('auth', {}).get('jwt_secret', 'default-secret')
    expire_hours = config.get('auth', {}).get('token_expire_hours', 24)
    payload = {
        'username': username,
        'exp': datetime.now(timezone.utc) + timedelta(hours=expire_hours),
        'iat': datetime.now(timezone.utc)
    }
    return jwt.encode(payload, secret, algorithm='HS256')


def verify_token(token):
    try:
        config = load_config()
        secret = config.get('auth', {}).get('jwt_secret', 'default-secret')
        payload = jwt.decode(token, secret, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def require_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if not token:
            return jsonify({'code': 401, 'message': '未提供认证令牌', 'data': None}), 401
        payload = verify_token(token)
        if not payload:
            return jsonify({'code': 401, 'message': '令牌无效或已过期', 'data': None}), 401
        user = User.query.filter_by(username=payload['username']).first()
        if not user or not user.is_active:
            return jsonify({'code': 401, 'message': '用户不存在或已被禁用', 'data': None}), 401
        request.current_user = user
        return f(*args, **kwargs)
    return decorated


def optional_auth(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = get_token_from_request()
        if token:
            payload = verify_token(token)
            if payload:
                user = User.query.filter_by(username=payload['username']).first()
                if user and user.is_active:
                    request.current_user = user
                else:
                    request.current_user = get_guest_user()
            else:
                request.current_user = get_guest_user()
        else:
            request.current_user = get_guest_user()
        return f(*args, **kwargs)
    return decorated


def get_current_user_or_guest():
    token = get_token_from_request()
    if token:
        payload = verify_token(token)
        if payload:
            user = User.query.filter_by(username=payload['username']).first()
            if user and user.is_active:
                return user, None, None
    return get_guest_user(), None, None


def require_permission(permission_name):
    def decorator(f):
        @wraps(f)
        def decorated(*args, **kwargs):
            if not hasattr(request, 'current_user'):
                return jsonify({'code': 401, 'message': '未认证', 'data': None}), 401
            if not request.current_user.has_permission(permission_name):
                return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
            return f(*args, **kwargs)
        return decorated
    return decorator


@app.route('/')
def index():
    config = load_config()
    if not config.get('setup_completed', False):
        return redirect('/setup')
    return render_template('index.html')


@app.route('/setup')
def setup_page():
    config = load_config()
    if config.get('setup_completed', False):
        return redirect('/')
    return render_template('setup.html')


@app.route('/settings')
def settings():
    return render_template('settings.html')


@app.route('/test-ui')
def test_ui():
    return render_template('test_ui.html')


@app.route('/login')
def login_page():
    return render_template('index.html')


@app.route('/user-management')
def user_management_page():
    return render_template('user_management.html')


@app.route('/permission-management')
def permission_management_page():
    return render_template('permission_management.html')


@app.route('/api/setup/status', methods=['GET'])
def get_setup_status():
    config = load_config()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'setup_completed': config.get('setup_completed', False),
            'has_admin': User.query.filter_by(user_type='admin').first() is not None
        }
    })


@app.route('/api/setup/complete', methods=['POST'])
def complete_setup():
    try:
        data = request.get_json()
        
        pan_username = data.get('pan_username', '').strip()
        pan_password = data.get('pan_password', '').strip()
        admin_username = data.get('admin_username', '').strip()
        admin_password = data.get('admin_password', '').strip()
        theme_color = data.get('theme_color', '#4F46E5')
        add_guest = data.get('add_guest', False)
        guest_paths = data.get('guest_paths', '/')
        
        if not pan_username or not pan_password:
            return jsonify({'code': 400, 'message': '请填写123网盘API配置', 'data': None}), 400
        
        if not admin_username or not admin_password:
            return jsonify({'code': 400, 'message': '请填写管理员账户信息', 'data': None}), 400
        
        if len(admin_password) < 8:
            return jsonify({'code': 400, 'message': '密码长度至少8位', 'data': None}), 400
        
        has_upper = any(c.isupper() for c in admin_password)
        has_lower = any(c.islower() for c in admin_password)
        has_digit = any(c.isdigit() for c in admin_password)
        has_special = any(c in '!@#$%^&*()_+-=[]{}|;:,.<>?' for c in admin_password)
        
        if not (has_upper and has_lower and has_digit and has_special):
            return jsonify({'code': 400, 'message': '密码必须包含大小写字母、数字和特殊符号', 'data': None}), 400
        
        settings = {'username': pan_username, 'password': pan_password}
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        import api as pan_api
        login_result = pan_api.login(pan_username, pan_password)
        if 'error' in login_result:
            return jsonify({'code': 400, 'message': f'123网盘登录失败: {login_result["error"]}', 'data': None}), 400
        
        if User.query.filter_by(username=admin_username).first():
            return jsonify({'code': 400, 'message': '管理员用户名已存在', 'data': None}), 400
        
        admin_user = User(username=admin_username, email=f'{admin_username}@admin.local', user_type='admin')
        admin_user.set_password(admin_password)
        admin_user.is_verified = True
        
        admin_role = Role.query.filter_by(name='admin').first()
        if admin_role:
            admin_user.roles.append(admin_role)
        
        db.session.add(admin_user)
        
        if add_guest:
            existing_guest = User.query.filter_by(user_type='guest').first()
            if not existing_guest:
                guest_user = User(username='guest', email='guest@system.local', user_type='guest', is_active=True)
                guest_role = Role.query.filter_by(name='guest').first()
                if guest_role:
                    guest_user.roles.append(guest_role)
                db.session.add(guest_user)
                db.session.flush()
                
                file_perm = FilePermission(user_id=guest_user.id, visible_paths=guest_paths, restrict_to_visible=True)
                db.session.add(file_perm)
        
        config = load_config()
        config['setup_completed'] = True
        config['theme']['primary_color'] = theme_color
        save_config(config)
        
        db.session.commit()
        
        return jsonify({'code': 200, 'message': '系统配置完成', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/setup/validate-path', methods=['POST'])
def validate_guest_path():
    try:
        data = request.get_json()
        path = data.get('path', '').strip()
        
        if not path:
            return jsonify({'code': 400, 'message': '路径不能为空', 'data': None}), 400
        
        if not path.startswith('/'):
            return jsonify({'code': 400, 'message': '路径必须以 / 开头', 'data': None}), 400
        
        return jsonify({'code': 200, 'message': '路径格式有效', 'data': {'valid': True}})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/auth/login', methods=['POST'])
def login():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '')
        
        if not username or not password:
            return jsonify({'code': 400, 'message': '用户名和密码不能为空', 'data': None}), 400
        
        user = User.query.filter(
            db.or_(User.username == username, User.email == username)
        ).first()
        
        if not user:
            return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None}), 401
        
        if not user.check_password(password):
            return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None}), 401
        
        if not user.is_active:
            return jsonify({'code': 403, 'message': '账户已被禁用', 'data': None}), 403
        
        token = generate_token(user.username)
        user.last_login = datetime.utcnow()
        db.session.commit()
        
        return jsonify({
            'code': 200,
            'message': '登录成功',
            'data': {
                'token': token,
                'user': user.to_dict()
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/auth/logout', methods=['POST'])
def logout():
    return jsonify({'code': 200, 'message': '退出成功', 'data': None})


@app.route('/api/users/change-password', methods=['PUT'])
@require_auth
def change_password():
    try:
        data = request.get_json()
        old_password = data.get('old_password', '')
        new_password = data.get('new_password', '')
        
        if not old_password or not new_password:
            return jsonify({'code': 400, 'message': '旧密码和新密码不能为空', 'data': None}), 400
        
        if not request.current_user.check_password(old_password):
            return jsonify({'code': 400, 'message': '旧密码错误', 'data': None}), 400
        
        policy = PasswordPolicy.query.first()
        validator = PasswordValidator(policy.to_dict() if policy else None)
        validation = validator.validate(new_password)
        
        if not validation['valid']:
            return jsonify({'code': 400, 'message': '新密码不符合要求', 'data': {'errors': validation['errors']}}), 400
        
        request.current_user.set_password(new_password)
        db.session.commit()
        
        return jsonify({'code': 200, 'message': '密码修改成功', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/password-policy', methods=['GET'])
def get_password_policy():
    try:
        policy = PasswordPolicy.query.first()
        if not policy:
            policy = PasswordPolicy()
            db.session.add(policy)
            db.session.commit()
        
        return jsonify({'code': 200, 'message': 'success', 'data': policy.to_dict()})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/password-policy', methods=['PUT'])
@require_auth
@require_permission('admin')
def update_password_policy():
    try:
        data = request.get_json()
        policy = PasswordPolicy.query.first()
        if not policy:
            policy = PasswordPolicy()
            db.session.add(policy)
        
        if 'min_length' in data:
            policy.min_length = data['min_length']
        if 'require_uppercase' in data:
            policy.require_uppercase = data['require_uppercase']
        if 'require_lowercase' in data:
            policy.require_lowercase = data['require_lowercase']
        if 'require_digit' in data:
            policy.require_digit = data['require_digit']
        if 'require_special' in data:
            policy.require_special = data['require_special']
        if 'special_chars' in data:
            policy.special_chars = data['special_chars']
        if 'max_age_days' in data:
            policy.max_age_days = data['max_age_days']
        if 'history_count' in data:
            policy.history_count = data['history_count']
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '密码策略更新成功', 'data': policy.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/validate-password', methods=['POST'])
def validate_password():
    try:
        data = request.get_json()
        password = data.get('password', '')
        
        policy = PasswordPolicy.query.first()
        validator = PasswordValidator(policy.to_dict() if policy else None)
        validation = validator.validate(password)
        
        return jsonify({'code': 200, 'message': 'success', 'data': validation})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users', methods=['GET'])
@require_auth
@require_permission('user_manage')
def list_users():
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        
        query = User.query
        total = query.count()
        users = query.offset((page - 1) * page_size).limit(page_size).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'users': [user.to_dict() for user in users],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>', methods=['GET'])
@require_auth
def get_user(user_id):
    try:
        if request.current_user.id != user_id and not request.current_user.has_permission('user_manage'):
            return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        return jsonify({'code': 200, 'message': 'success', 'data': user.to_dict()})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users', methods=['POST'])
@require_auth
@require_permission('user_manage')
def create_user():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        email = data.get('email', '').strip()
        password = data.get('password', '')
        user_type = data.get('user_type', 'user')
        roles = data.get('roles', [])
        
        is_guest = user_type == 'guest'
        
        if is_guest:
            existing_guest = User.query.filter_by(user_type='guest').first()
            if existing_guest:
                return jsonify({'code': 400, 'message': '系统中已存在游客账户，不能重复创建', 'data': None}), 400
            
            if not username:
                username = 'guest'
            
            if User.query.filter_by(username=username).first():
                return jsonify({'code': 400, 'message': '用户名已存在', 'data': None}), 400
            
            if not email:
                email = f'guest_{username}@system.local'
            elif User.query.filter_by(email=email).first():
                return jsonify({'code': 400, 'message': '邮箱已被使用', 'data': None}), 400
            
            user = User(username=username, email=email, user_type='guest', is_active=True, is_verified=False)
        else:
            if not username or not email or not password:
                return jsonify({'code': 400, 'message': '用户名、邮箱和密码不能为空', 'data': None}), 400
            
            if User.query.filter_by(username=username).first():
                return jsonify({'code': 400, 'message': '用户名已存在', 'data': None}), 400
            
            if User.query.filter_by(email=email).first():
                return jsonify({'code': 400, 'message': '邮箱已被注册', 'data': None}), 400
            
            user = User(username=username, email=email, user_type=user_type)
            user.set_password(password)
        
        for role_id in roles:
            role = Role.query.get(role_id)
            if role:
                user.roles.append(role)
        
        db.session.add(user)
        db.session.commit()
        
        if is_guest:
            invalidate_guest_cache()
        
        return jsonify({
            'code': 200,
            'message': '用户创建成功',
            'data': user.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>', methods=['PUT'])
@require_auth
def update_user(user_id):
    try:
        if request.current_user.id != user_id and not request.current_user.has_permission('user_manage'):
            return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        data = request.get_json()
        
        if 'username' in data and request.current_user.has_permission('user_manage'):
            if User.query.filter(User.username == data['username'], User.id != user_id).first():
                return jsonify({'code': 400, 'message': '用户名已存在', 'data': None}), 400
            user.username = data['username']
        
        if 'email' in data:
            if User.query.filter(User.email == data['email'], User.id != user_id).first():
                return jsonify({'code': 400, 'message': '邮箱已被使用', 'data': None}), 400
            user.email = data['email']
        
        if 'is_active' in data and request.current_user.has_permission('user_manage'):
            user.is_active = data['is_active']
        
        if 'roles' in data and request.current_user.has_permission('user_manage'):
            roles = Role.query.filter(Role.name.in_(data['roles'])).all()
            user.roles = roles
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '用户更新成功', 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>', methods=['DELETE'])
@require_auth
@require_permission('user_manage')
def delete_user(user_id):
    try:
        if user_id == request.current_user.id:
            return jsonify({'code': 400, 'message': '不能删除自己', 'data': None}), 400
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        db.session.delete(user)
        db.session.commit()
        return jsonify({'code': 200, 'message': '用户删除成功', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/type', methods=['PUT'])
@require_auth
@require_permission('user_manage')
def update_user_type(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        data = request.get_json()
        user_type = data.get('user_type', 'user')
        
        if user_type not in ['admin', 'user', 'guest']:
            return jsonify({'code': 400, 'message': '无效的用户类型', 'data': None}), 400
        
        user.user_type = user_type
        
        if user_type == 'admin':
            admin_role = Role.query.filter_by(name='admin').first()
            if admin_role and admin_role not in user.roles:
                user.roles.append(admin_role)
        elif user_type == 'guest':
            guest_role = Role.query.filter_by(name='guest').first()
            if guest_role:
                user.roles = [guest_role]
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '用户类型更新成功', 'data': user.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/attributes', methods=['GET'])
@require_auth
def get_user_attributes(user_id):
    try:
        if request.current_user.id != user_id and not request.current_user.has_permission('user_manage'):
            return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        if not user.attributes:
            attributes = UserAttribute(user_id=user.id)
            db.session.add(attributes)
            db.session.commit()
        
        return jsonify({'code': 200, 'message': 'success', 'data': user.attributes.to_dict()})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/attributes', methods=['PUT'])
@require_auth
@require_permission('user_manage')
def update_user_attributes(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        if not user.attributes:
            user.attributes = UserAttribute(user_id=user.id)
        
        data = request.get_json()
        attrs = user.attributes
        
        if 'storage_quota' in data:
            attrs.storage_quota = data['storage_quota']
        if 'upload_speed_limit' in data:
            attrs.upload_speed_limit = data['upload_speed_limit']
        if 'max_file_size' in data:
            attrs.max_file_size = data['max_file_size']
        if 'max_files_per_day' in data:
            attrs.max_files_per_day = data['max_files_per_day']
        if 'can_share' in data:
            attrs.can_share = data['can_share']
        if 'can_download' in data:
            attrs.can_download = data['can_download']
        if 'can_preview' in data:
            attrs.can_preview = data['can_preview']
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '用户属性更新成功', 'data': attrs.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/file-permission', methods=['GET'])
@require_auth
def get_user_file_permission(user_id):
    try:
        if request.current_user.id != user_id and not request.current_user.has_permission('user_manage'):
            return jsonify({'code': 403, 'message': '权限不足', 'data': None}), 403
        
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        if not user.file_permission:
            fp = FilePermission(user_id=user.id)
            db.session.add(fp)
            db.session.commit()
        
        return jsonify({'code': 200, 'message': 'success', 'data': user.file_permission.to_dict()})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/file-permission', methods=['PUT'])
@require_auth
@require_permission('user_manage')
def update_user_file_permission(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        if not user.file_permission:
            user.file_permission = FilePermission(user_id=user.id)
        
        data = request.get_json()
        fp = user.file_permission
        
        if 'allowed_types' in data:
            fp.allowed_types = ','.join(data['allowed_types']) if isinstance(data['allowed_types'], list) else data['allowed_types']
        if 'blocked_types' in data:
            fp.blocked_types = ','.join(data['blocked_types']) if isinstance(data['blocked_types'], list) else data['blocked_types']
        if 'max_file_size' in data:
            fp.max_file_size = data['max_file_size']
        if 'max_directory_depth' in data:
            fp.max_directory_depth = data['max_directory_depth']
        if 'show_hidden_files' in data:
            fp.show_hidden_files = data['show_hidden_files']
        if 'allow_create_folder' in data:
            fp.allow_create_folder = data['allow_create_folder']
        if 'allow_delete_folder' in data:
            fp.allow_delete_folder = data['allow_delete_folder']
        if 'allowed_paths' in data:
            fp.allowed_paths = ','.join(data['allowed_paths']) if isinstance(data['allowed_paths'], list) else data['allowed_paths']
        if 'blocked_paths' in data:
            fp.blocked_paths = ','.join(data['blocked_paths']) if isinstance(data['blocked_paths'], list) else data['blocked_paths']
        if 'visible_paths' in data:
            fp.visible_paths = ','.join(data['visible_paths']) if isinstance(data['visible_paths'], list) else data['visible_paths']
        if 'restrict_to_visible' in data:
            fp.restrict_to_visible = data['restrict_to_visible']
        if 'require_approval' in data:
            fp.require_approval = data['require_approval']
        if 'auto_approve_types' in data:
            fp.auto_approve_types = ','.join(data['auto_approve_types']) if isinstance(data['auto_approve_types'], list) else data['auto_approve_types']
        if 'max_concurrent_uploads' in data:
            fp.max_concurrent_uploads = data['max_concurrent_uploads']
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '文件权限更新成功', 'data': fp.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/batch-attributes', methods=['POST'])
@require_auth
@require_permission('user_manage')
def batch_update_user_attributes():
    try:
        data = request.get_json()
        user_ids = data.get('user_ids', [])
        attributes = data.get('attributes', {})
        
        if not user_ids:
            return jsonify({'code': 400, 'message': '用户ID列表不能为空', 'data': None}), 400
        
        updated_count = 0
        for user_id in user_ids:
            user = User.query.get(user_id)
            if user:
                if not user.attributes:
                    user.attributes = UserAttribute(user_id=user.id)
                
                for key, value in attributes.items():
                    if hasattr(user.attributes, key):
                        setattr(user.attributes, key, value)
                updated_count += 1
        
        db.session.commit()
        return jsonify({'code': 200, 'message': f'成功更新 {updated_count} 个用户属性', 'data': {'updated_count': updated_count}})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/path-permissions', methods=['GET'])
@require_auth
@require_permission('user_manage')
def get_path_permissions():
    try:
        user_id = request.args.get('user_id', type=int)
        role_id = request.args.get('role_id', type=int)
        path = request.args.get('path')
        
        query = PathPermission.query
        
        if user_id:
            query = query.filter(PathPermission.user_id == user_id)
        if role_id:
            query = query.filter(PathPermission.role_id == role_id)
        if path:
            query = query.filter(PathPermission.path.startswith(path))
        
        permissions = query.order_by(PathPermission.priority.desc(), PathPermission.path).all()
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'permissions': [p.to_dict() for p in permissions]
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/path-permissions', methods=['POST'])
@require_auth
@require_permission('user_manage')
def create_path_permission():
    try:
        data = request.get_json()
        
        path = data.get('path')
        permission_type = data.get('permission_type', 'read')
        
        if not path:
            return jsonify({'code': 400, 'message': '路径不能为空', 'data': None}), 400
        
        if permission_type not in PathPermission.PERMISSION_TYPES:
            return jsonify({'code': 400, 'message': f'无效的权限类型，可选: {PathPermission.PERMISSION_TYPES}', 'data': None}), 400
        
        user_id = data.get('user_id')
        role_id = data.get('role_id')
        
        if not user_id and not role_id:
            return jsonify({'code': 400, 'message': '必须指定用户ID或角色ID', 'data': None}), 400
        
        existing = PathPermission.query.filter(
            PathPermission.path == path,
            PathPermission.permission_type == permission_type,
            db.or_(
                db.and_(PathPermission.user_id == user_id, PathPermission.user_id != None),
                db.and_(PathPermission.role_id == role_id, PathPermission.role_id != None)
            )
        ).first()
        
        if existing:
            return jsonify({'code': 400, 'message': '该路径权限已存在', 'data': None}), 400
        
        import json as json_module
        permission = PathPermission(
            user_id=user_id,
            role_id=role_id,
            path=path,
            permission_type=permission_type,
            is_allowed=data.get('is_allowed', True),
            priority=data.get('priority', 0),
            inherit=data.get('inherit', True),
            conditions=json_module.dumps(data.get('conditions', {}))
        )
        
        db.session.add(permission)
        db.session.commit()
        
        from business_logic.middleware.path_permission import invalidate_permission_cache
        if user_id:
            invalidate_permission_cache(user_id=user_id)
        if role_id:
            invalidate_permission_cache(role_id=role_id)
        
        return jsonify({
            'code': 200,
            'message': '路径权限创建成功',
            'data': permission.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/path-permissions/<int:permission_id>', methods=['PUT'])
@require_auth
@require_permission('user_manage')
def update_path_permission(permission_id):
    try:
        permission = PathPermission.query.get(permission_id)
        if not permission:
            return jsonify({'code': 404, 'message': '权限不存在', 'data': None}), 404
        
        data = request.get_json()
        
        if 'path' in data:
            permission.path = data['path']
        if 'permission_type' in data:
            if data['permission_type'] not in PathPermission.PERMISSION_TYPES:
                return jsonify({'code': 400, 'message': f'无效的权限类型', 'data': None}), 400
            permission.permission_type = data['permission_type']
        if 'is_allowed' in data:
            permission.is_allowed = data['is_allowed']
        if 'priority' in data:
            permission.priority = data['priority']
        if 'inherit' in data:
            permission.inherit = data['inherit']
        if 'conditions' in data:
            import json as json_module
            permission.conditions = json_module.dumps(data['conditions'])
        
        db.session.commit()
        
        from business_logic.middleware.path_permission import invalidate_permission_cache
        if permission.user_id:
            invalidate_permission_cache(user_id=permission.user_id)
        if permission.role_id:
            invalidate_permission_cache(role_id=permission.role_id)
        
        return jsonify({
            'code': 200,
            'message': '路径权限更新成功',
            'data': permission.to_dict()
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/path-permissions/<int:permission_id>', methods=['DELETE'])
@require_auth
@require_permission('user_manage')
def delete_path_permission(permission_id):
    try:
        permission = PathPermission.query.get(permission_id)
        if not permission:
            return jsonify({'code': 404, 'message': '权限不存在', 'data': None}), 404
        
        user_id = permission.user_id
        role_id = permission.role_id
        
        db.session.delete(permission)
        db.session.commit()
        
        from business_logic.middleware.path_permission import invalidate_permission_cache
        if user_id:
            invalidate_permission_cache(user_id=user_id)
        if role_id:
            invalidate_permission_cache(role_id=role_id)
        
        return jsonify({
            'code': 200,
            'message': '路径权限删除成功',
            'data': None
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/path-permissions/batch', methods=['POST'])
@require_auth
@require_permission('user_manage')
def batch_create_path_permissions():
    try:
        data = request.get_json()
        permissions_data = data.get('permissions', [])
        
        if not permissions_data:
            return jsonify({'code': 400, 'message': '权限列表不能为空', 'data': None}), 400
        
        import json as json_module
        created_permissions = []
        
        for perm_data in permissions_data:
            path = perm_data.get('path')
            permission_type = perm_data.get('permission_type', 'read')
            
            if not path:
                continue
            
            permission = PathPermission(
                user_id=perm_data.get('user_id'),
                role_id=perm_data.get('role_id'),
                path=path,
                permission_type=permission_type,
                is_allowed=perm_data.get('is_allowed', True),
                priority=perm_data.get('priority', 0),
                inherit=perm_data.get('inherit', True),
                conditions=json_module.dumps(perm_data.get('conditions', {}))
            )
            
            db.session.add(permission)
            created_permissions.append(permission)
        
        db.session.commit()
        
        from business_logic.middleware.path_permission import invalidate_permission_cache
        invalidate_permission_cache()
        
        return jsonify({
            'code': 200,
            'message': f'成功创建 {len(created_permissions)} 条路径权限',
            'data': {
                'permissions': [p.to_dict() for p in created_permissions]
            }
        })
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/users/<int:user_id>/accessible-paths', methods=['GET'])
@require_auth
def get_user_accessible_paths(user_id):
    try:
        user = User.query.get(user_id)
        if not user:
            return jsonify({'code': 404, 'message': '用户不存在', 'data': None}), 404
        
        from business_logic.middleware.path_permission import get_user_accessible_paths
        paths = get_user_accessible_paths(user)
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'accessible_paths': paths
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/guest/info', methods=['GET'])
def get_guest_info():
    guest = get_guest_user()
    return jsonify({
        'code': 200,
        'message': 'success',
        'data': {
            'user_type': 'guest',
            'username': 'guest',
            'is_guest': True,
            'permissions': ['read']
        }
    })


@app.route('/api/roles', methods=['GET'])
@require_auth
def list_roles():
    try:
        roles = Role.query.all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'roles': [role.to_dict() for role in roles]}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/roles', methods=['POST'])
@require_auth
@require_permission('role_manage')
def create_role():
    try:
        data = request.get_json()
        name = data.get('name', '').strip()
        description = data.get('description', '')
        
        if not name:
            return jsonify({'code': 400, 'message': '角色名称不能为空', 'data': None}), 400
        
        if Role.query.filter_by(name=name).first():
            return jsonify({'code': 400, 'message': '角色已存在', 'data': None}), 400
        
        role = Role(name=name, description=description)
        
        if 'permissions' in data:
            permissions = Permission.query.filter(Permission.name.in_(data['permissions'])).all()
            role.permissions = permissions
        
        db.session.add(role)
        db.session.commit()
        
        return jsonify({'code': 200, 'message': '角色创建成功', 'data': role.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/roles/<int:role_id>', methods=['PUT'])
@require_auth
@require_permission('role_manage')
def update_role(role_id):
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404
        
        data = request.get_json()
        
        if 'name' in data:
            if Role.query.filter(Role.name == data['name'], Role.id != role_id).first():
                return jsonify({'code': 400, 'message': '角色名称已存在', 'data': None}), 400
            role.name = data['name']
        
        if 'description' in data:
            role.description = data['description']
        
        if 'permissions' in data:
            permissions = Permission.query.filter(Permission.name.in_(data['permissions'])).all()
            role.permissions = permissions
        
        db.session.commit()
        return jsonify({'code': 200, 'message': '角色更新成功', 'data': role.to_dict()})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/roles/<int:role_id>', methods=['DELETE'])
@require_auth
@require_permission('role_manage')
def delete_role(role_id):
    try:
        role = Role.query.get(role_id)
        if not role:
            return jsonify({'code': 404, 'message': '角色不存在', 'data': None}), 404
        
        if role.name in ['admin', 'user', 'guest']:
            return jsonify({'code': 400, 'message': '不能删除系统默认角色', 'data': None}), 400
        
        db.session.delete(role)
        db.session.commit()
        return jsonify({'code': 200, 'message': '角色删除成功', 'data': None})
    except Exception as e:
        db.session.rollback()
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/permissions', methods=['GET'])
@require_auth
def list_permissions():
    try:
        permissions = Permission.query.all()
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {'permissions': [perm.to_dict() for perm in permissions]}
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/auth/login', methods=['POST'])
def auth_login():
    try:
        data = request.get_json()
        username = data.get('username', '')
        password = data.get('password', '')
        
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password) and user.is_active:
            token = generate_token(username)
            return jsonify({
                'code': 200,
                'message': '登录成功',
                'data': {'token': token, 'user': user.to_dict()}
            })
        
        return jsonify({'code': 401, 'message': '用户名或密码错误', 'data': None}), 401
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/auth/check', methods=['GET'])
@require_auth
def check_auth():
    return jsonify({
        'code': 200,
        'message': '已认证',
        'data': request.current_user.to_dict()
    })


@app.route('/api/config', methods=['GET'])
def get_config():
    config = load_config()
    if "error" in config:
        return jsonify({'code': 500, 'message': config['error'], 'data': None}), 500
    safe_config = config.copy()
    if 'auth' in safe_config:
        del safe_config['auth']
    return jsonify({'code': 200, 'message': 'success', 'data': safe_config})


@app.route('/api/config/<section>', methods=['GET'])
def get_config_section(section):
    config = load_config()
    if "error" in config:
        return jsonify({'code': 500, 'message': config['error'], 'data': None}), 500
    if section not in config:
        return jsonify({'code': 404, 'message': f'配置段 {section} 不存在', 'data': None}), 404
    return jsonify({'code': 200, 'message': 'success', 'data': config[section]})


@app.route('/api/config', methods=['PUT'])
@require_auth
def update_config():
    try:
        new_config = request.get_json()
        if not new_config:
            return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None}), 400
        create_backup()
        current_config = load_config()
        if "error" in current_config:
            return jsonify({'code': 500, 'message': current_config['error'], 'data': None}), 500
        updated_fields = []
        for key, value in new_config.items():
            if key == 'auth':
                continue
            if key == 'theme' and isinstance(value, dict):
                for color_key in ['primary_color', 'secondary_color', 'background_color', 'text_color', 'border_color', 'hover_color']:
                    if color_key in value and not validate_color(value[color_key]):
                        return jsonify({'code': 400, 'message': f'颜色值 {color_key} 格式不正确', 'data': None}), 400
            if key == 'layout' and isinstance(value, dict):
                for html_key in ['header_html', 'footer_html']:
                    if html_key in value:
                        value[html_key] = sanitize_html(value[html_key])
            current_config[key] = value
            updated_fields.append(key)
        if save_config(current_config):
            return jsonify({'code': 200, 'message': '配置更新成功', 'data': {'updated_fields': updated_fields}})
        return jsonify({'code': 500, 'message': '保存配置失败', 'data': None}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/<section>', methods=['PATCH'])
@require_auth
def update_config_section(section):
    try:
        new_section = request.get_json()
        if not new_section:
            return jsonify({'code': 400, 'message': '请求体不能为空', 'data': None}), 400
        create_backup()
        current_config = load_config()
        if "error" in current_config:
            return jsonify({'code': 500, 'message': current_config['error'], 'data': None}), 500
        if section not in current_config:
            return jsonify({'code': 404, 'message': f'配置段 {section} 不存在', 'data': None}), 404
        if section == 'theme':
            for color_key in ['primary_color', 'secondary_color', 'background_color', 'text_color', 'border_color', 'hover_color']:
                if color_key in new_section and not validate_color(new_section[color_key]):
                    return jsonify({'code': 400, 'message': f'颜色值 {color_key} 格式不正确', 'data': None}), 400
        if section == 'layout':
            for html_key in ['header_html', 'footer_html']:
                if html_key in new_section:
                    new_section[html_key] = sanitize_html(new_section[html_key])
        current_config[section].update(new_section)
        if save_config(current_config):
            return jsonify({'code': 200, 'message': f'{section} 配置更新成功', 'data': current_config[section]})
        return jsonify({'code': 500, 'message': '保存配置失败', 'data': None}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/validate', methods=['POST'])
def validate_config():
    try:
        config_data = request.get_json()
        errors = []
        if 'theme' in config_data:
            for color_key in ['primary_color', 'secondary_color', 'background_color', 'text_color', 'border_color', 'hover_color']:
                if color_key in config_data['theme']:
                    if not validate_color(config_data['theme'][color_key]):
                        errors.append(f'颜色值 {color_key} 格式不正确')
        if 'upload' in config_data:
            if 'max_file_size' in config_data['upload']:
                if not isinstance(config_data['upload']['max_file_size'], int) or config_data['upload']['max_file_size'] <= 0:
                    errors.append('max_file_size 必须是正整数')
        return jsonify({'code': 200, 'message': '验证完成', 'data': {'valid': len(errors) == 0, 'errors': errors}})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


SETTINGS_PATH = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'settings.json')


@app.route('/api/config/123pan', methods=['GET'])
@require_auth
@require_permission('system_manage')
def get_123pan_config():
    try:
        if os.path.exists(SETTINGS_PATH):
            with open(SETTINGS_PATH, 'r', encoding='utf-8') as f:
                settings = json.load(f)
            return jsonify({
                'code': 200,
                'message': 'success',
                'data': {
                    'username': settings.get('username', ''),
                    'password': '****' if settings.get('password') else ''
                }
            })
        return jsonify({'code': 200, 'message': 'success', 'data': {'username': '', 'password': ''}})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/123pan', methods=['PUT'])
@require_auth
@require_permission('system_manage')
def update_123pan_config():
    try:
        data = request.get_json()
        username = data.get('username', '').strip()
        password = data.get('password', '').strip()
        
        if not username:
            return jsonify({'code': 400, 'message': '用户名不能为空', 'data': None}), 400
        
        if not password:
            return jsonify({'code': 400, 'message': '密码不能为空', 'data': None}), 400
        
        settings = {'username': username, 'password': password}
        
        os.makedirs(os.path.dirname(SETTINGS_PATH), exist_ok=True)
        with open(SETTINGS_PATH, 'w', encoding='utf-8') as f:
            json.dump(settings, f, ensure_ascii=False, indent=2)
        
        return jsonify({'code': 200, 'message': '123网盘API配置已保存', 'data': None})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/backup', methods=['POST'])
@require_auth
def backup_config():
    timestamp = create_backup()
    if timestamp:
        return jsonify({'code': 200, 'message': '备份创建成功', 'data': {'backup_id': timestamp}})
    return jsonify({'code': 500, 'message': '备份创建失败', 'data': None}), 500


@app.route('/api/config/backups', methods=['GET'])
@require_auth
def list_backups():
    try:
        if not os.path.exists(BACKUP_DIR):
            return jsonify({'code': 200, 'message': 'success', 'data': {'backups': []}})
        backups = []
        for filename in os.listdir(BACKUP_DIR):
            if filename.startswith('config_backup_') and filename.endswith('.json'):
                backup_id = filename.replace('config_backup_', '').replace('.json', '')
                filepath = os.path.join(BACKUP_DIR, filename)
                stat = os.stat(filepath)
                backups.append({
                    'backup_id': backup_id,
                    'created_at': datetime.fromtimestamp(stat.st_mtime).isoformat(),
                    'size': stat.st_size
                })
        backups.sort(key=lambda x: x['created_at'], reverse=True)
        return jsonify({'code': 200, 'message': 'success', 'data': {'backups': backups}})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/restore/<backup_id>', methods=['POST'])
@require_auth
def restore_backup(backup_id):
    try:
        backup_path = os.path.join(BACKUP_DIR, f'config_backup_{backup_id}.json')
        if not os.path.exists(backup_path):
            return jsonify({'code': 404, 'message': '备份文件不存在', 'data': None}), 404
        with open(backup_path, 'r', encoding='utf-8') as f:
            backup_config = json.load(f)
        if save_config(backup_config):
            return jsonify({'code': 200, 'message': '配置恢复成功', 'data': None})
        return jsonify({'code': 500, 'message': '恢复配置失败', 'data': None}), 500
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/config/theme', methods=['GET'])
def get_theme():
    config = load_config()
    if "error" in config:
        return jsonify({'code': 500, 'message': config['error'], 'data': None}), 500
    return jsonify({'code': 200, 'message': 'success', 'data': config.get('theme', {})})


@app.route('/api/config/theme', methods=['PUT'])
@require_auth
def update_theme():
    return update_config_section('theme')


import sys
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), '123pan'))
import api as pan_api


@app.route('/api/files', methods=['GET'])
def list_files():
    try:
        virtual_path = request.args.get('path', '/')
        limit = request.args.get('limit', 100, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        user, error_response, status_code = get_current_user_or_guest()
        if error_response:
            return error_response, status_code
        
        file_perm = user.file_permission if user.file_permission else None
        
        real_path = virtual_path
        if file_perm and file_perm.restrict_to_visible:
            real_path = file_perm.virtual_to_real_path(virtual_path)
        
        if file_perm:
            if not file_perm.is_path_allowed(real_path):
                return jsonify({'code': 403, 'message': '无权访问此路径', 'data': None}), 403
            if not file_perm.is_depth_allowed(virtual_path):
                return jsonify({'code': 403, 'message': '已达到最大目录深度限制', 'data': None}), 403
        
        result = pan_api.list_folder(real_path) if real_path != '/' else pan_api.list()
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        folders = result.get('folder', [])
        files = result.get('file', [])
        
        if file_perm and not file_perm.show_hidden_files:
            folders = [f for f in folders if not f.get('name', '').startswith('.')]
            files = [f for f in files if not f.get('name', '').startswith('.')]
        
        total_folders = len(folders)
        total_files = len(files)
        
        if limit > 0:
            all_items = folders + files
            paginated = all_items[offset:offset + limit]
            folders = [i for i in paginated if i.get('type') == 'folder' or 'size' not in i]
            files = [i for i in paginated if i.get('type') == 'file' or 'size' in i]
        
        return jsonify({
            'code': 200, 
            'message': 'success', 
            'data': {
                'folder': folders,
                'file': files,
                'total_folders': total_folders,
                'total_files': total_files,
                'current_path': virtual_path,
                'current_depth': virtual_path.strip('/').count('/') + 1 if virtual_path.strip('/') else 0,
                'max_depth': file_perm.max_directory_depth if file_perm else 0,
                'restricted': file_perm.restrict_to_visible if file_perm else False
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/list', methods=['GET'])
def list_files_paginated():
    try:
        path = request.args.get('path', '/')
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 50))
        keyword = request.args.get('keyword', '')
        file_type = request.args.get('file_type', '')
        
        user, error_response, status_code = get_current_user_or_guest()
        if error_response:
            return error_response, status_code
        
        file_perm = user.file_permission if user.file_permission else None
        if file_perm:
            if not file_perm.is_path_allowed(path):
                return jsonify({'code': 403, 'message': '无权访问此路径', 'data': None}), 403
            if not file_perm.is_depth_allowed(path):
                return jsonify({'code': 403, 'message': '已达到最大目录深度限制', 'data': None}), 403
        
        result = pan_api.list_folder(path) if path != '/' else pan_api.list()
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        folders = result.get('folder', [])
        files = result.get('file', [])
        
        if file_perm and not file_perm.show_hidden_files:
            folders = [f for f in folders if not f.get('name', '').startswith('.')]
            files = [f for f in files if not f.get('name', '').startswith('.')]
        
        if keyword:
            folders = [f for f in folders if keyword.lower() in f.get('name', '').lower()]
            files = [f for f in files if keyword.lower() in f.get('name', '').lower()]
        
        if file_type:
            files = [f for f in files if f.get('name', '').lower().endswith(f'.{file_type.lower()}')]
        
        total_folders = len(folders)
        total_files = len(files)
        all_items = folders + files
        total = len(all_items)
        start = (page - 1) * page_size
        end = start + page_size
        paginated = all_items[start:end]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total': total,
                'total_folders': total_folders,
                'total_files': total_files,
                'page': page,
                'page_size': page_size,
                'folders': folders[start:end],
                'files': files[start:end] if start < len(files) else [],
                'current_path': path,
                'current_depth': path.strip('/').count('/') + 1 if path.strip('/') else 0,
                'max_depth': file_perm.max_directory_depth if file_perm else 0
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/download', methods=['GET'])
def download_file():
    try:
        virtual_path = request.args.get('path', '')
        if not virtual_path:
            return jsonify({'code': 400, 'message': '路径不能为空', 'data': None}), 400
        
        user, error_response, status_code = get_current_user_or_guest()
        if error_response:
            return error_response, status_code
        
        file_perm = user.file_permission if user.file_permission else None
        
        real_path = virtual_path
        if file_perm and file_perm.restrict_to_visible:
            real_path = file_perm.virtual_to_real_path(virtual_path)
            if not file_perm.is_path_allowed(real_path):
                return jsonify({'code': 403, 'message': '无权访问此文件', 'data': None}), 403
        
        result = pan_api.parsing(real_path)
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        return jsonify({'code': 200, 'message': 'success', 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/upload', methods=['POST'])
@require_auth
def upload_file():
    try:
        if 'file' not in request.files:
            return jsonify({'code': 400, 'message': '没有上传文件', 'data': None}), 400
        
        file = request.files['file']
        virtual_path = request.form.get('path', '/')
        
        if file.filename == '':
            return jsonify({'code': 400, 'message': '文件名为空', 'data': None}), 400
        
        file_perm = request.current_user.file_permission if request.current_user.file_permission else None
        
        real_path = virtual_path
        if file_perm and file_perm.restrict_to_visible:
            real_path = file_perm.virtual_to_real_path(virtual_path)
            if not file_perm.is_path_allowed(real_path):
                return jsonify({'code': 403, 'message': '无权上传到此路径', 'data': None}), 403
        
        import tempfile
        with tempfile.NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as tmp:
            file.save(tmp.name)
            tmp_path = tmp.name
        
        try:
            result = pan_api.upload(tmp_path, real_path)
        finally:
            os.unlink(tmp_path)
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        return jsonify({'code': 200, 'message': '上传成功', 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/folder', methods=['POST'])
@require_auth
def create_folder():
    try:
        data = request.get_json()
        virtual_parent_path = data.get('parentPath', '/')
        folder_name = data.get('name', '')
        
        if not folder_name:
            return jsonify({'code': 400, 'message': '文件夹名称不能为空', 'data': None}), 400
        
        file_perm = request.current_user.file_permission if request.current_user.file_permission else None
        
        real_parent_path = virtual_parent_path
        if file_perm and file_perm.restrict_to_visible:
            real_parent_path = file_perm.virtual_to_real_path(virtual_parent_path)
            if not file_perm.is_path_allowed(real_parent_path):
                return jsonify({'code': 403, 'message': '无权在此路径创建文件夹', 'data': None}), 403
        
        result = pan_api.create_folder(real_parent_path, folder_name)
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        return jsonify({'code': 200, 'message': '创建成功', 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/files', methods=['DELETE'])
@require_auth
def delete_file():
    try:
        virtual_path = request.args.get('path', '')
        if not virtual_path:
            return jsonify({'code': 400, 'message': '路径不能为空', 'data': None}), 400
        
        file_perm = request.current_user.file_permission if request.current_user.file_permission else None
        
        real_path = virtual_path
        if file_perm and file_perm.restrict_to_visible:
            real_path = file_perm.virtual_to_real_path(virtual_path)
            if not file_perm.is_path_allowed(real_path):
                return jsonify({'code': 403, 'message': '无权删除此文件', 'data': None}), 403
        
        result = pan_api.delete(real_path)
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        return jsonify({'code': 200, 'message': '删除成功', 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/share', methods=['POST'])
@require_auth
def share_file():
    try:
        data = request.get_json()
        path = data.get('path', '')
        
        if not path:
            return jsonify({'code': 400, 'message': '路径不能为空', 'data': None}), 400
        
        result = pan_api.share(path)
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        return jsonify({'code': 200, 'message': '分享成功', 'data': result})
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/search', methods=['GET'])
def search_files():
    try:
        keyword = request.args.get('keyword', '')
        virtual_path = request.args.get('path', '/')
        
        if not keyword:
            return jsonify({'code': 400, 'message': '搜索关键词不能为空', 'data': None}), 400
        
        user, error_response, status_code = get_current_user_or_guest()
        if error_response:
            return error_response, status_code
        
        file_perm = user.file_permission if user.file_permission else None
        
        real_path = virtual_path
        if file_perm and file_perm.restrict_to_visible:
            real_path = file_perm.virtual_to_real_path(virtual_path)
            if not file_perm.is_path_allowed(real_path):
                return jsonify({'code': 403, 'message': '无权搜索此路径', 'data': None}), 403
        
        result = pan_api.list_folder(real_path) if real_path != '/' else pan_api.list()
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        folders = [f for f in result.get('folder', []) if keyword.lower() in f.get('name', '').lower()]
        files = [f for f in result.get('file', []) if keyword.lower() in f.get('name', '').lower()]
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'folders': folders,
                'files': files,
                'total': len(folders) + len(files)
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


LOG_FILE = 'audit.log'


@app.route('/api/logs', methods=['GET'])
@require_auth
@require_permission('log_view')
def get_logs():
    try:
        page = int(request.args.get('page', 1))
        page_size = int(request.args.get('page_size', 20))
        start_time = request.args.get('start_time', '')
        end_time = request.args.get('end_time', '')
        
        if not os.path.exists(LOG_FILE):
            return jsonify({'code': 200, 'message': 'success', 'data': {'logs': [], 'total': 0}})
        
        logs = []
        with open(LOG_FILE, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    parts = line.split(' - ', 3)
                    if len(parts) >= 4:
                        log_data = json.loads(parts[3])
                        logs.append({
                            'timestamp': parts[0],
                            'level': parts[2],
                            **log_data
                        })
                except:
                    continue
        
        if start_time:
            logs = [l for l in logs if l.get('timestamp', '') >= start_time]
        if end_time:
            logs = [l for l in logs if l.get('timestamp', '') <= end_time]
        
        logs.sort(key=lambda x: x.get('timestamp', ''), reverse=True)
        
        total = len(logs)
        start = (page - 1) * page_size
        end = start + page_size
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'logs': logs[start:end],
                'total': total,
                'page': page,
                'page_size': page_size
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


@app.route('/api/business/stats', methods=['GET'])
@require_auth
def get_stats():
    try:
        result = pan_api.list()
        
        if 'error' in result:
            return jsonify({'code': 400, 'message': result['error'], 'data': None}), 400
        
        total_files = len(result.get('file', []))
        total_folders = len(result.get('folder', []))
        
        return jsonify({
            'code': 200,
            'message': 'success',
            'data': {
                'total_files': total_files,
                'total_folders': total_folders
            }
        })
    except Exception as e:
        return jsonify({'code': 500, 'message': str(e), 'data': None}), 500


if __name__ == '__main__':
    with app.app_context():
        db.create_all()
        
        if not Permission.query.first():
            permissions = [
                Permission(name='read', description='读取权限', module='files'),
                Permission(name='write', description='写入权限', module='files'),
                Permission(name='delete', description='删除权限', module='files'),
                Permission(name='share', description='分享权限', module='files'),
                Permission(name='upload', description='上传权限', module='files'),
                Permission(name='user_manage', description='用户管理权限', module='users'),
                Permission(name='role_manage', description='角色管理权限', module='roles'),
                Permission(name='config_manage', description='配置管理权限', module='config'),
                Permission(name='log_view', description='日志查看权限', module='logs'),
                Permission(name='admin', description='超级管理员权限', module='system'),
                Permission(name='system_manage', description='系统管理权限', module='system')
            ]
            db.session.add_all(permissions)
            db.session.commit()
        
        if not Role.query.first():
            admin_role = Role(name='admin', description='超级管理员')
            user_role = Role(name='user', description='普通用户')
            guest_role = Role(name='guest', description='访客')
            
            all_perms = Permission.query.all()
            admin_role.permissions = all_perms
            
            user_perms = Permission.query.filter(
                Permission.name.in_(['read', 'write', 'delete', 'share', 'upload'])
            ).all()
            user_role.permissions = user_perms
            
            guest_perms = Permission.query.filter(Permission.name == 'read').all()
            guest_role.permissions = guest_perms
            
            db.session.add_all([admin_role, user_role, guest_role])
            db.session.commit()
        
        if not PasswordPolicy.query.first():
            policy = PasswordPolicy()
            db.session.add(policy)
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=8000)
