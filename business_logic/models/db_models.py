from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash

db = SQLAlchemy()


class User(db.Model):
    __tablename__ = 'users'
    
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=True)
    user_type = db.Column(db.String(20), default='user')
    is_active = db.Column(db.Boolean, default=True)
    is_verified = db.Column(db.Boolean, default=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    roles = db.relationship('Role', secondary='user_roles', back_populates='users')
    attributes = db.relationship('UserAttribute', backref='user', uselist=False, lazy=True)
    file_permission = db.relationship('FilePermission', backref='user', uselist=False, lazy=True)
    
    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        if not self.password_hash:
            return False
        return check_password_hash(self.password_hash, password)
    
    def has_permission(self, permission_name):
        if self.user_type == 'admin':
            return True
        for role in self.roles:
            for perm in role.permissions:
                if perm.name == permission_name or perm.name == 'admin':
                    return True
        return False
    
    def has_role(self, role_name):
        return any(role.name == role_name for role in self.roles)
    
    def is_admin(self):
        return self.user_type == 'admin' or self.has_role('admin')
    
    def is_guest(self):
        return self.user_type == 'guest' or (not self.is_active and not self.password_hash)
    
    def to_dict(self):
        return {
            'id': self.id,
            'username': self.username,
            'email': self.email,
            'user_type': self.user_type,
            'is_active': self.is_active,
            'is_verified': self.is_verified,
            'created_at': self.created_at.isoformat(),
            'roles': [role.name for role in self.roles],
            'attributes': self.attributes.to_dict() if self.attributes else None,
            'file_permission': self.file_permission.to_dict() if self.file_permission else None
        }


class UserAttribute(db.Model):
    __tablename__ = 'user_attributes'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    storage_quota = db.Column(db.BigInteger, default=1073741824)
    storage_used = db.Column(db.BigInteger, default=0)
    upload_speed_limit = db.Column(db.Integer, default=0)
    max_file_size = db.Column(db.BigInteger, default=104857600)
    max_files_per_day = db.Column(db.Integer, default=100)
    files_uploaded_today = db.Column(db.Integer, default=0)
    last_upload_date = db.Column(db.Date)
    can_share = db.Column(db.Boolean, default=True)
    can_download = db.Column(db.Boolean, default=True)
    can_preview = db.Column(db.Boolean, default=True)
    custom_settings = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'storage_quota': self.storage_quota,
            'storage_used': self.storage_used,
            'storage_quota_formatted': format_size(self.storage_quota),
            'storage_used_formatted': format_size(self.storage_used),
            'storage_usage_percent': round((self.storage_used / self.storage_quota) * 100, 2) if self.storage_quota > 0 else 0,
            'upload_speed_limit': self.upload_speed_limit,
            'max_file_size': self.max_file_size,
            'max_file_size_formatted': format_size(self.max_file_size),
            'max_files_per_day': self.max_files_per_day,
            'files_uploaded_today': self.files_uploaded_today,
            'can_share': self.can_share,
            'can_download': self.can_download,
            'can_preview': self.can_preview
        }


class FilePermission(db.Model):
    __tablename__ = 'file_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False, unique=True)
    allowed_types = db.Column(db.Text, default='jpg,jpeg,png,gif,pdf,doc,docx,xls,xlsx,zip,rar,mp4,mp3')
    blocked_types = db.Column(db.Text, default='exe,bat,cmd,sh,ps1')
    max_file_size = db.Column(db.BigInteger, default=104857600)
    allowed_paths = db.Column(db.Text, default='/')
    blocked_paths = db.Column(db.Text, default='')
    visible_paths = db.Column(db.Text, default='/')
    restrict_to_visible = db.Column(db.Boolean, default=False)
    require_approval = db.Column(db.Boolean, default=False)
    auto_approve_types = db.Column(db.Text, default='jpg,jpeg,png,gif,pdf')
    max_concurrent_uploads = db.Column(db.Integer, default=3)
    max_directory_depth = db.Column(db.Integer, default=0)
    show_hidden_files = db.Column(db.Boolean, default=False)
    allow_create_folder = db.Column(db.Boolean, default=True)
    allow_delete_folder = db.Column(db.Boolean, default=True)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'allowed_types': self.allowed_types.split(',') if self.allowed_types else [],
            'blocked_types': self.blocked_types.split(',') if self.blocked_types else [],
            'max_file_size': self.max_file_size,
            'max_file_size_formatted': format_size(self.max_file_size),
            'allowed_paths': self.allowed_paths.split(',') if self.allowed_paths else [],
            'blocked_paths': self.blocked_paths.split(',') if self.blocked_paths else [],
            'visible_paths': self.visible_paths.split(',') if self.visible_paths else ['/'],
            'restrict_to_visible': self.restrict_to_visible,
            'require_approval': self.require_approval,
            'auto_approve_types': self.auto_approve_types.split(',') if self.auto_approve_types else [],
            'max_concurrent_uploads': self.max_concurrent_uploads,
            'max_directory_depth': self.max_directory_depth,
            'show_hidden_files': self.show_hidden_files,
            'allow_create_folder': self.allow_create_folder,
            'allow_delete_folder': self.allow_delete_folder
        }
    
    def is_type_allowed(self, file_extension):
        ext = file_extension.lower().replace('.', '')
        if self.blocked_types and ext in self.blocked_types.split(','):
            return False
        if self.allowed_types:
            return ext in self.allowed_types.split(',')
        return True
    
    def is_path_allowed(self, path):
        if self.blocked_paths:
            for blocked in self.blocked_paths.split(','):
                if blocked.strip() and path.startswith(blocked.strip()):
                    return False
        if self.allowed_paths:
            for allowed in self.allowed_paths.split(','):
                if allowed.strip() == '/' or path.startswith(allowed.strip()):
                    return True
            return False
        return True
    
    def is_path_visible(self, path):
        if not self.restrict_to_visible:
            return True
        if not self.visible_paths:
            return True
        visible_list = [p.strip() for p in self.visible_paths.split(',') if p.strip()]
        if not visible_list:
            return True
        for visible in visible_list:
            if visible == '/':
                return True
            if path == visible or path.startswith(visible.rstrip('/') + '/'):
                return True
        return False
    
    def get_visible_root(self):
        if not self.restrict_to_visible:
            return '/'
        if not self.visible_paths:
            return '/'
        visible_list = [p.strip() for p in self.visible_paths.split(',') if p.strip()]
        if not visible_list:
            return '/'
        return visible_list[0]
    
    def get_visible_paths_list(self):
        if not self.restrict_to_visible:
            return ['/']
        if not self.visible_paths:
            return ['/']
        visible_list = [p.strip() for p in self.visible_paths.split(',') if p.strip()]
        return visible_list if visible_list else ['/']
    
    def virtual_to_real_path(self, virtual_path):
        if not self.restrict_to_visible:
            return virtual_path
        
        visible_list = self.get_visible_paths_list()
        if not visible_list or visible_list[0] == '/':
            return virtual_path
        
        real_root = visible_list[0].rstrip('/')
        virtual_path = virtual_path.strip('/')
        
        if not virtual_path:
            return real_root if real_root else '/'
        
        return f"{real_root}/{virtual_path}"
    
    def real_to_virtual_path(self, real_path):
        if not self.restrict_to_visible:
            return real_path
        
        visible_list = self.get_visible_paths_list()
        if not visible_list or visible_list[0] == '/':
            return real_path
        
        real_root = visible_list[0].rstrip('/')
        real_path = real_path.rstrip('/')
        
        if real_path == real_root:
            return '/'
        
        if real_path.startswith(real_root + '/'):
            return '/' + real_path[len(real_root) + 1:]
        
        return real_path
    
    def is_depth_allowed(self, path):
        if self.max_directory_depth <= 0:
            return True
        depth = path.strip('/').count('/') + 1 if path.strip('/') else 0
        return depth <= self.max_directory_depth


class PathPermission(db.Model):
    __tablename__ = 'path_permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    role_id = db.Column(db.Integer, db.ForeignKey('roles.id'), nullable=True)
    path = db.Column(db.String(512), nullable=False)
    permission_type = db.Column(db.String(20), nullable=False, default='read')
    is_allowed = db.Column(db.Boolean, default=True)
    priority = db.Column(db.Integer, default=0)
    inherit = db.Column(db.Boolean, default=True)
    conditions = db.Column(db.Text, default='{}')
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    user = db.relationship('User', backref=db.backref('path_permissions', lazy='dynamic'))
    role = db.relationship('Role', backref=db.backref('path_permissions', lazy='dynamic'))
    
    PERMISSION_TYPES = ['read', 'write', 'delete', 'share', 'download', 'admin']
    
    def to_dict(self):
        import json
        return {
            'id': self.id,
            'user_id': self.user_id,
            'role_id': self.role_id,
            'path': self.path,
            'permission_type': self.permission_type,
            'is_allowed': self.is_allowed,
            'priority': self.priority,
            'inherit': self.inherit,
            'conditions': json.loads(self.conditions) if self.conditions else {},
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
    
    def matches_path(self, target_path):
        if self.path == '/':
            return True
        if self.inherit:
            return target_path.startswith(self.path)
        return target_path == self.path
    
    @staticmethod
    def check_permission(user, path, permission_type='read'):
        if user.is_admin():
            return True
        
        permissions = PathPermission.query.filter(
            db.or_(
                PathPermission.user_id == user.id,
                PathPermission.role_id.in_([role.id for role in user.roles])
            ),
            PathPermission.permission_type == permission_type
        ).order_by(PathPermission.priority.desc()).all()
        
        for perm in permissions:
            if perm.matches_path(path):
                return perm.is_allowed
        
        return True


def format_size(size):
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size < 1024:
            return f"{size:.2f} {unit}"
        size /= 1024
    return f"{size:.2f} PB"


class Role(db.Model):
    __tablename__ = 'roles'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    users = db.relationship('User', secondary='user_roles', back_populates='roles')
    permissions = db.relationship('Permission', secondary='role_permissions', back_populates='roles')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'permissions': [perm.name for perm in self.permissions]
        }


class Permission(db.Model):
    __tablename__ = 'permissions'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), unique=True, nullable=False)
    description = db.Column(db.String(255))
    module = db.Column(db.String(50))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    roles = db.relationship('Role', secondary='role_permissions', back_populates='permissions')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'module': self.module
        }


user_roles = db.Table('user_roles',
    db.Column('user_id', db.Integer, db.ForeignKey('users.id'), primary_key=True),
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True)
)


role_permissions = db.Table('role_permissions',
    db.Column('role_id', db.Integer, db.ForeignKey('roles.id'), primary_key=True),
    db.Column('permission_id', db.Integer, db.ForeignKey('permissions.id'), primary_key=True)
)


class VerificationToken(db.Model):
    __tablename__ = 'verification_tokens'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    token = db.Column(db.String(256), unique=True, nullable=False)
    token_type = db.Column(db.String(20), nullable=False)
    expires_at = db.Column(db.DateTime, nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    used = db.Column(db.Boolean, default=False)
    
    user = db.relationship('User', backref=db.backref('tokens', lazy=True))


class PasswordPolicy(db.Model):
    __tablename__ = 'password_policy'
    
    id = db.Column(db.Integer, primary_key=True)
    min_length = db.Column(db.Integer, default=8)
    require_uppercase = db.Column(db.Boolean, default=True)
    require_lowercase = db.Column(db.Boolean, default=True)
    require_digit = db.Column(db.Boolean, default=True)
    require_special = db.Column(db.Boolean, default=True)
    special_chars = db.Column(db.String(50), default='!@#$%^&*()_+-=[]{}|;:,.<>?')
    max_age_days = db.Column(db.Integer, default=90)
    history_count = db.Column(db.Integer, default=5)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def to_dict(self):
        return {
            'min_length': self.min_length,
            'require_uppercase': self.require_uppercase,
            'require_lowercase': self.require_lowercase,
            'require_digit': self.require_digit,
            'require_special': self.require_special,
            'special_chars': self.special_chars,
            'max_age_days': self.max_age_days,
            'history_count': self.history_count
        }


GUEST_USER = None


def get_guest_user():
    global GUEST_USER
    
    try:
        db_guest = User.query.filter_by(user_type='guest', is_active=True).first()
        if db_guest:
            return db_guest
    except:
        pass
    
    if GUEST_USER is None:
        guest = User(
            id=0,
            username='guest',
            email='guest@system.local',
            user_type='guest',
            is_active=True,
            is_verified=False
        )
        try:
            guest_role = Role.query.filter_by(name='guest').first()
            if guest_role:
                guest.roles = [guest_role]
        except:
            pass
        GUEST_USER = guest
    return GUEST_USER


def invalidate_guest_cache():
    global GUEST_USER
    GUEST_USER = None


def init_db():
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
        guest_role = Role(name='guest', description='游客')
        
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
