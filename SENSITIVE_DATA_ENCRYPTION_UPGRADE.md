# 敏感数据加密升级说明

## 问题概述
系统中存在敏感信息（如真实姓名、电话、学号等）明文存储的安全风险。

## 解决方案
我们实现了对敏感数据的端到端加密保护：

### 1. 模型层加密
- 在 `models.py` 中更新了 User 模型
- 将 `real_name`、`phone`、`student_id` 等敏感字段改为加密存储
- 使用 `EncryptedField` 工具类进行自动加密/解密

### 2. 加密机制
- 使用 `cryptography.fernet` 进行对称加密
- 自动生成安全的加密密钥
- 使用 Base64 编码确保数据安全传输

### 3. 属性访问器
- 通过 Python 的 `@property` 和 `@setter` 实现透明加密
- 开发人员可像使用普通字段一样使用加密字段
- 自动处理加密和解密过程

### 4. 数据迁移
- 提供 `migrate_sensitive_data.py` 脚本进行数据迁移
- 将现有的明文敏感数据加密存储

## 代码实现细节

### 模型更新
```python
# 加密存储字段
_real_name = db.Column('real_name', db.String(100))  # 私有字段存储加密数据
_phone = db.Column('phone', db.String(50))           # 私有字段存储加密数据
_student_id = db.Column('student_id', db.String(50)) # 私有字段存储加密数据

# 属性访问器实现自动加密/解密
@property
def real_name(self):
    return EncryptedField.decrypt(self._real_name)

@real_name.setter
def real_name(self, value):
    self._real_name = EncryptedField.encrypt(value)
```

## 安全优势
- **数据保护**：敏感数据在数据库中以加密形式存储
- **透明访问**：应用代码可以像普通字段一样使用加密字段
- **密钥管理**：自动密钥生成和管理
- **向后兼容**：现有功能不受影响

## 影响
- 现有用户数据会逐渐迁移到加密存储
- 数据库中的敏感信息将以加密形式显示
- 应用程序访问数据时会自动解密
- 提高了整体系统的数据安全性

## 验证
您可以运行以下命令来验证加密功能：

```bash
python migrate_sensitive_data.py
```

---
此升级增强了系统的敏感数据保护能力，确保用户隐私信息得到充分保护。