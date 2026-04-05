"""
增强敏感数据加密保护脚本
对用户的真实姓名、电话、学号等敏感信息进行加密存储
"""
from cryptography.fernet import Fernet
import os
import base64
from app import create_app
from models import db, User
import json

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

def decrypt_data(value):
    """解密字符串值"""
    if value is None:
        return None
    cipher = get_cipher()
    try:
        return cipher.decrypt(value.encode()).decode()
    except:
        return value  # 解密失败时返回原文

def enhance_user_data_encryption():
    """
    增强用户敏感数据的加密保护
    """
    with app.app_context():
        print("开始增强用户敏感数据加密保护...")
        
        users = User.query.all()
        print(f"发现 {len(users)} 个用户")
        
        for user in users:
            print(f"处理用户: {user.username}")
            
            # 检查并加密真实姓名
            if user.real_name and not user.real_name.startswith('gAAAAA'):
                encrypted_real_name = encrypt_data(user.real_name)
                print(f"  - 真实姓名已加密: {user.real_name} -> {encrypted_real_name[:20]}...")
                user.real_name = encrypted_real_name
            
            # 检查并加密电话号码
            if user.phone and not user.phone.startswith('gAAAAA'):
                encrypted_phone = encrypt_data(user.phone)
                print(f"  - 电话号码已加密: {user.phone} -> {encrypted_phone[:20]}...")
                user.phone = encrypted_phone
            
            # 检查并加密学号
            if user.student_id and not user.student_id.startswith('gAAAAA'):
                encrypted_student_id = encrypt_data(user.student_id)
                print(f"  - 学号已加密: {user.student_id} -> {encrypted_student_id[:20]}...")
                user.student_id = encrypted_student_id
        
        # 提交所有更改
        db.session.commit()
        print("\n敏感数据加密增强完成！")

def test_encryption():
    """
    测试加密功能
    """
    print("\n=== 加密功能测试 ===")
    
    original_data = {
        'real_name': '张三',
        'phone': '13812345678',
        'student_id': '2021001001'
    }
    
    print(f"原始数据: {original_data}")
    
    encrypted_data = {}
    for key, value in original_data.items():
        encrypted_value = encrypt_data(value)
        encrypted_data[key] = encrypted_value
        print(f"{key}: {value} -> {encrypted_value[:30]}...")
    
    decrypted_data = {}
    for key, value in encrypted_data.items():
        decrypted_value = decrypt_data(value)
        decrypted_data[key] = decrypted_value
        print(f"解密 {key}: {encrypted_value[:30]}... -> {decrypted_value}")
    
    print(f"解密成功验证: {original_data == decrypted_data}")

def update_model_class():
    """
    提供更新模型类的建议代码
    """
    print("\n=== 模型类更新建议 ===")
    print("为了更好地保护敏感数据，建议更新User模型类：")
    print("""
# 在models.py中更新User类的敏感字段定义：

class User(UserMixin, db.Model):
    # ... 其他字段 ...

    # 个人信息字段 - 加密存储
    _real_name = db.Column('real_name', db.String(100))  # 私有字段存储加密数据
    _phone = db.Column('phone', db.String(50))           # 私有字段存储加密数据
    _student_id = db.Column('student_id', db.String(50)) # 私有字段存储加密数据
    school = db.Column(db.String(100))                   # 非敏感信息可明文存储
    
    # 提供属性访问器进行自动加密/解密
    @property
    def real_name(self):
        return decrypt_data(self._real_name)
    
    @real_name.setter
    def real_name(self, value):
        self._real_name = encrypt_data(value)
    
    @property
    def phone(self):
        return decrypt_data(self._phone)
    
    @phone.setter
    def phone(self, value):
        self._phone = encrypt_data(value)
    
    @property
    def student_id(self):
        return decrypt_data(self._student_id)
    
    @student_id.setter
    def student_id(self, value):
        self._student_id = encrypt_data(value)
    """)

if __name__ == "__main__":
    print("增强敏感数据加密保护工具")
    print("="*50)
    
    # 运行测试
    test_encryption()
    
    # 显示模型更新建议
    update_model_class()
    
    print("\n注意：运行增强加密功能前，请确保备份数据库！")
    print("执行增强功能：enhance_user_data_encryption()")
    
    # 如果用户确认，可以取消下面的注释来执行实际的加密
    # enhance_user_data_encryption()