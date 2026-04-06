from flask import Flask, render_template, redirect, url_for
from config import config
from models import db
import os
import sys
import logging
from logging.handlers import RotatingFileHandler
from flask_wtf.csrf import CSRFProtect
import secrets


def create_app(config_name='default'):
    """应用工厂函数"""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 配置日志
    BASE_DIR = os.path.dirname(os.path.abspath(__file__))
    LOG_DIR = os.path.join(BASE_DIR, 'logs')
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
    
    # 配置日志处理器
    handler = RotatingFileHandler(
        os.path.join(LOG_DIR, 'app.log'),
        maxBytes=10*1024*1024,  # 10MB
        backupCount=5
    )
    handler.setFormatter(logging.Formatter('%(asctime)s - %(levelname)s - %(filename)s:%(lineno)d - %(message)s'))
    app.logger.addHandler(handler)
    app.logger.setLevel(logging.INFO)
    
    app.logger.info(f'Creating app with config: {config_name}')
    app.logger.info(f'Database URL: {app.config.get("SQLALCHEMY_DATABASE_URI")}')
    app.logger.info(f'Host: {os.environ.get("HOST", "127.0.0.1")}')
    app.logger.info(f'Port: {os.environ.get("PORT", "5000")}')
    
    # 确保加密密钥有效
    from models import EncryptedField
    try:
        _ = EncryptedField.get_cipher()  # 初始化密钥
    except:
        pass  # 如果初始化失败，忽略错误，让后续请求时再处理
    
    # 初始化扩展
    db.init_app(app)
    
    # 初始化CSRF保护
    csrf = CSRFProtect(app)
    
    # 注册 Jinja2 自定义过滤器
    from utils import mask_email, mask_phone
    app.jinja_env.filters['mask_email'] = mask_email
    app.jinja_env.filters['mask_phone'] = mask_phone
    
    # 注册蓝图
    from admin_views import admin_bp
    from user_views import user_bp
    
    app.register_blueprint(admin_bp)
    app.register_blueprint(user_bp)
    
    # 首页路由
    @app.route('/')
    def index():
        return redirect(url_for('user.index'))
    
    # 错误处理
    @app.errorhandler(404)
    def not_found(error):
        return render_template('404.html'), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return render_template('500.html'), 500
    
    # 创建数据库表
    with app.app_context():
        db.create_all()
        
        # 检查并添加缺失的列
        from sqlalchemy import text
        try:
            # 检查数据库类型
            dialect = db.engine.dialect.name
            
            # 检查users表的列
            if dialect == 'mysql':
                # MySQL语法
                result = db.session.execute(text("SHOW COLUMNS FROM users"))
                columns = [row[0] for row in result]
            else:
                # SQLite语法
                result = db.session.execute(text("PRAGMA table_info(users)"))
                columns = [row[1] for row in result]
            
            if 'login_attempts' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0"))
                print("Added login_attempts column to users table")
            
            if 'last_failed_login' not in columns:
                db.session.execute(text("ALTER TABLE users ADD COLUMN last_failed_login DATETIME"))
                print("Added last_failed_login column to users table")
            
            # 检查security_rules表的列
            if dialect == 'mysql':
                # MySQL语法
                result = db.session.execute(text("SHOW COLUMNS FROM security_rules"))
                columns = [row[0] for row in result]
            else:
                # SQLite语法
                result = db.session.execute(text("PRAGMA table_info(security_rules)"))
                columns = [row[1] for row in result]
            
            if 'name' not in columns:
                db.session.execute(text("ALTER TABLE security_rules ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT 'unnamed'"))
                print("Added name column to security_rules table")
            
            if 'is_active' not in columns:
                db.session.execute(text("ALTER TABLE security_rules ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                print("Added is_active column to security_rules table")
            
            db.session.commit()
        except Exception as e:
            print(f'Warning: Could not add missing columns: {e}')
            db.session.rollback()
        
        # 创建默认管理员账号（如果不存在）
        from models import Admin
        # Use raw SQL to check if admin exists to avoid field mismatch issues
        existing_admin = None
        try:
            existing_admin = Admin.query.filter_by(username='admin').first()
            app.logger.info(f'Checked for existing admin: {existing_admin}')
        except Exception as e:
            # If there's a field mismatch error, try to create a new admin anyway
            app.logger.warning(f'Could not check for existing admin due to database field mismatch: {e}')
            existing_admin = None
            
        if not existing_admin:
            # 默认管理员密码：生产环境务必避免写死密码
            default_password = os.environ.get('ADMIN_DEFAULT_PASSWORD')
            app.logger.info(f'ADMIN_DEFAULT_PASSWORD from env: {default_password}')
            
            if not default_password:
                # 本地/开发环境保持兼容；生产环境则生成一次性强密码
                if config_name in ('development', 'default') and app.config.get('DEBUG', False):
                    default_password = 'admin123'
                    app.logger.info('Using default password for development environment')
                else:
                    default_password = secrets.token_urlsafe(16)
                    app.logger.warning(f'生成随机管理员密码：admin / {default_password}')
            else:
                app.logger.info('Using ADMIN_DEFAULT_PASSWORD from environment')

            admin = Admin(
                username='admin',
                password_hash=''  # Will be set by set_password
            )
            admin.set_password(default_password)
            # Only set basic fields that are guaranteed to exist in the database
            # Other fields will be set to defaults by the model definition
            try:
                db.session.add(admin)
                db.session.commit()
                app.logger.info(f'默认管理员账号已创建: admin / {default_password}')
                print(f'默认管理员账号已创建: admin / {default_password}')
            except Exception as e:
                app.logger.error(f'Could not create default admin: {e}')
                print(f'Warning: Could not create default admin: {e}')
                db.session.rollback()
    
    return app


# 创建应用实例供Gunicorn使用
config_name = os.environ.get('APP_CONFIG', 'default')
app = create_app(config_name)

if __name__ == '__main__':
    print('Starting application...')
    print('Python version:', sys.version)
    print('Current directory:', os.getcwd())
    try:
        print('Application created successfully!')
        print('Running app...')
        host = os.environ.get('HOST', '127.0.0.1')
        port = int(os.environ.get('PORT', '5000'))
        app.run(host=host, port=port, debug=app.config.get('DEBUG', False))
    except Exception as e:
        print(f'Error starting application: {e}')
        import traceback
        traceback.print_exc()
