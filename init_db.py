import os
import sys
from datetime import datetime, timedelta

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from business_logic.models.db_models import db, User, Role, Permission, PasswordPolicy, init_db


def initialize_database():
    with app.app_context():
        print('正在初始化数据库...')
        init_db()
        print('数据库表结构创建完成！')
        
        admin_role = Role.query.filter_by(name='admin').first()
        
        if not User.query.filter_by(username='admin').first():
            admin_user = User(
                username='admin',
                email='admin@example.com',
                is_active=True,
                is_verified=True
            )
            admin_user.set_password('admin123')
            admin_user.roles.append(admin_role)
            db.session.add(admin_user)
            db.session.commit()
            print('默认管理员账户创建成功！')
            print('用户名: admin')
            print('密码: admin123')
            print('请登录后立即修改密码！')
        
        print('\n初始化完成！')


if __name__ == '__main__':
    initialize_database()
