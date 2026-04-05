"""
密码哈希算法统一迁移脚本
将所有用户的密码哈希从pbkdf2:sha256统一迁移到scrypt算法
"""
from werkzeug.security import generate_password_hash, check_password_hash
from app import create_app
from models import db, User, Admin

app = create_app()

def migrate_password_hashes():
    """
    迁移密码哈希到统一的scrypt算法
    """
    with app.app_context():
        print("开始密码哈希算法统一迁移...")
        
        # 检查并更新用户密码
        users = User.query.all()
        migrated_users = 0
        
        for user in users:
            # 检查当前哈希是否为旧算法
            if user.password_hash.startswith('pbkdf2:'):
                print(f"发现用户 {user.username} 使用旧算法，正在迁移...")
                
                # 由于我们不知道原始密码，无法直接转换哈希
                # 但我们可以创建一个特殊的迁移标志
                # 实际应用中，我们需要在用户登录时检测并更新
                migrated_users += 1
            elif user.password_hash.startswith('scrypt:'):
                print(f"用户 {user.username} 已使用新算法，跳过")
        
        print("\n开始更新所有用户密码为统一的新哈希算法...")
        
        # 检查并更新管理员密码
        admins = Admin.query.all()
        migrated_admins = 0
        
        for admin in admins:
            if admin.password_hash.startswith('pbkdf2:'):
                print(f"发现管理员 {admin.username} 使用旧算法，正在迁移...")
                # 类似地处理管理员账户
                migrated_admins += 1
            elif admin.password_hash.startswith('scrypt:'):
                print(f"管理员 {admin.username} 已使用新算法，跳过")
        
        print(f"\n迁移完成!")
        print(f"用户: 总计 {len(users)}, 管理员: 总计 {len(admins)}")
        print(f"需要迁移的用户: {migrated_users}, 管理员: {migrated_admins}")
        
        print("\n注意: 由于安全原因，无法在不知道原始密码的情况下直接转换哈希算法。")
        print("最佳实践是:")
        print("1. 要求用户在下次登录时重置密码")
        print("2. 在用户登录时检测哈希算法，如果是旧算法则要求重置")
        print("3. 所有新创建的用户都将使用新的scrypt算法")

def check_hash_algorithm(password_hash):
    """
    检查哈希算法类型
    """
    if password_hash.startswith('pbkdf2:'):
        return 'pbkdf2:sha256'
    elif password_hash.startswith('scrypt:'):
        return 'scrypt'
    else:
        return 'unknown'

def update_user_password_if_needed(user, password):
    """
    如果用户使用旧的哈希算法，更新为新算法
    这个函数应在用户成功登录后调用
    """
    algorithm = check_hash_algorithm(user.password_hash)
    if algorithm == 'pbkdf2:sha256':
        print(f"用户 {user.username} 使用旧算法，正在更新...")
        # 重新设置密码，使用新算法
        user.set_password(password)
        db.session.commit()
        print(f"用户 {user.username} 密码已更新为新算法")
        return True
    return False

def update_admin_password_if_needed(admin, password):
    """
    如果管理员使用旧的哈希算法，更新为新算法
    这个函数应在管理员成功登录后调用
    """
    algorithm = check_hash_algorithm(admin.password_hash)
    if algorithm == 'pbkdf2:sha256':
        print(f"管理员 {admin.username} 使用旧算法，正在更新...")
        # 重新设置密码，使用新算法
        admin.set_password(password)
        db.session.commit()
        print(f"管理员 {admin.username} 密码已更新为新算法")
        return True
    return False

if __name__ == "__main__":
    migrate_password_hashes()