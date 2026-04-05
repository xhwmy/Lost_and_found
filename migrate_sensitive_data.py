"""
敏感数据加密迁移脚本
将现有数据库中的明文敏感数据加密存储
"""
from app import create_app
from models import db, User
from cryptography.fernet import Fernet
import os
import base64

app = create_app()

def get_cipher():
    """获取加密/解密器"""
    key = os.environ.get('ENCRYPTION_KEY')
    if not key:
        # 生成32字节随机密钥并进行Base64编码
        key_bytes = os.urandom(32)
        key = base64.urlsafe_b64encode(key_bytes).decode()
        os.environ['ENCRYPTION_KEY'] = key
    return Fernet(key.encode())

def encrypt_data(value):
    """加密字符串值"""
    if value is None:
        return None
    cipher = get_cipher()
    return cipher.encrypt(value.encode()).decode()

def migrate_sensitive_data():
    """
    迁移现有敏感数据到加密存储
    """
    with app.app_context():
        print("开始迁移敏感数据到加密存储...")
        
        users = User.query.all()
        migrated_count = 0
        
        for user in users:
            print(f"处理用户: {user.username}")
            
            # 迁移真实姓名（如果尚未加密）
            if user._real_name and not user._real_name.startswith('gAAAAA'):
                encrypted_real_name = encrypt_data(user._real_name)
                user._real_name = encrypted_real_name
                print(f"  - 真实姓名已加密")
                migrated_count += 1
            
            # 迁移电话号码（如果尚未加密）
            if user._phone and not user._phone.startswith('gAAAAA'):
                encrypted_phone = encrypt_data(user._phone)
                user._phone = encrypted_phone
                print(f"  - 电话号码已加密")
                migrated_count += 1
            
            # 迁移学号（如果尚未加密）
            if user._student_id and not user._student_id.startswith('gAAAAA'):
                encrypted_student_id = encrypt_data(user._student_id)
                user._student_id = encrypted_student_id
                print(f"  - 学号已加密")
                migrated_count += 1
        
        # 提交所有更改
        db.session.commit()
        print(f"\n敏感数据加密迁移完成！共处理 {migrated_count} 个字段")

def test_encryption():
    """
    测试加密功能
    """
    print("\n=== 加密迁移测试 ===")
    
    with app.app_context():
        users = User.query.limit(1).all()
        if users:
            user = users[0]
            print(f"测试用户: {user.username}")
            
            # 测试属性访问器
            if user.real_name:
                print(f"真实姓名（解密后）: {user.real_name}")
            if user.phone:
                print(f"电话（解密后）: {user.phone}")
            if user.student_id:
                print(f"学号（解密后）: {user.student_id}")
            if user.id_card_number:
                print(f"身份证号（解密后）: {user.id_card_number}")

if __name__ == "__main__":
    print("敏感数据加密迁移工具")
    print("="*40)
    
    # 运行测试
    test_encryption()
    
    # 提示用户执行迁移
    print("\n注意：执行迁移前请确保备份数据库！")
    print("执行迁移: migrate_sensitive_data()")
    
    # 取消下面的注释来执行实际的迁移（谨慎操作）
    # migrate_sensitive_data()