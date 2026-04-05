# 校园失物招领平台 - SQLite到MySQL完整迁移指南

## 重要提醒
此指南将帮助您将现有的SQLite数据库迁移到MySQL数据库。迁移前请务必备份您的数据。

## 第一步：安装MySQL

### 1.1 下载MySQL
- 访问 https://dev.mysql.com/downloads/mysql/
- 下载适合您系统的MySQL Community Server版本
- Windows用户可选择MySQL Installer

### 1.2 安装MySQL
- 运行下载的安装程序
- 选择 "Developer Default" 配置
- 在安装过程中设置root用户密码，请务必记住该密码

### 1.3 验证安装
打开命令提示符，输入以下命令验证MySQL是否安装成功：
```bash
mysql --version
```

## 第二步：准备Python环境

### 2.1 安装MySQL Python驱动
```bash
pip install PyMySQL
```

## 第三步：导入数据到MySQL

### 3.1 启动MySQL服务
确保MySQL服务正在运行。在Windows上，您可以通过"服务"管理器启动MySQL服务。

### 3.2 使用全新方法创建数据库（推荐）
由于之前的导入方法可能仍存在兼容性问题，我们提供了一种全新的数据库创建方法，可以完全避免导入时的各种错误：

**方法A：使用SQL脚本直接创建**
1. 打开命令提示符并连接到MySQL：
```bash
mysql -u root -p
```
2. 在MySQL命令行中执行SQL脚本：
```sql
SOURCE c:/Users/86187/Desktop/毕业设计/campus_crowdfunding/mysql_setup_guide.sql;
```

**方法B：手动执行SQL命令**
您也可以复制 `mysql_setup_guide.sql` 文件中的内容，逐行粘贴到MySQL命令行中执行。

**方法C：使用Python直接迁移（备选方案）**
如果上述方法仍有问题，可以使用Python脚本直接迁移数据：
1. 确保已安装PyMySQL：`pip install PyMySQL`
2. 运行迁移脚本：`python direct_migration.py`

这种方法将完全绕过SQL导入的限制，直接在Python层面完成数据迁移。

### 3.3 验证数据导入
连接到MySQL检查数据是否正确导入：
```bash
mysql -u root -p
```
然后执行以下SQL命令检查数据：
```sql
USE campus_crowdfunding;
SHOW TABLES;
SELECT COUNT(*) FROM users;
SELECT COUNT(*) FROM lost_items;
SELECT COUNT(*) FROM found_items;
```

## 第四步：更新应用配置

### 4.1 备份原始配置文件
```bash
copy config.py config.py.backup
```

### 4.2 更新配置文件
打开项目根目录下的 `config.py` 文件，将其内容替换为以下内容：

```python
import os
basedir = os.path.abspath(os.path.dirname(__file__))

class Config:
    SECRET_KEY = os.environ.get('SECRET_KEY') or 'hard-to-guess-string'
    SQLALCHEMY_TRACK_MODIFICATIONS = False

class DevelopmentConfig(Config):
    DEBUG = True
    # 将 your_mysql_password 替换为您实际的MySQL root密码
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:your_mysql_password@localhost/campus_crowdfunding'

class ProductionConfig(Config):
    # 将 your_mysql_password 替换为您实际的MySQL root密码
    SQLALCHEMY_DATABASE_URI = os.environ.get('DATABASE_URL') or \
        'mysql+pymysql://root:your_mysql_password@localhost/campus_crowdfunding'

config = {
    'development': DevelopmentConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}
```

## 第五步：测试应用

### 5.1 安装PyMySQL（如果尚未安装）
```bash
pip install PyMySQL
```

### 5.2 启动应用
```bash
cd c:/Users/86187/Desktop/毕业设计/campus_crowdfunding
python app.py
```

### 5.3 测试功能
- 访问网站并测试用户注册/登录
- 测试发布失物/招领信息
- 测试认领功能
- 测试管理员功能

## 可能遇到的问题及解决方案

### 问题1：连接错误
**错误信息**：Access denied for user 'root'@'localhost'
**解决方案**：检查您的MySQL密码是否正确

### 问题2：驱动问题
**错误信息**：ModuleNotFoundError: No module named 'pymysql'
**解决方案**：运行 `pip install PyMySQL`

### 问题3：字符编码问题
**错误信息**：Incorrect string value
**解决方案**：确保MySQL数据库使用utf8mb4字符集

### 问题4：权限问题
**错误信息**：Access denied
**解决方案**：确保MySQL用户有足够的权限访问campus_crowdfunding数据库

## 验证迁移是否成功

迁移完成后，请验证以下功能：

1. **用户功能**：用户注册、登录、个人信息管理
2. **失物/招领功能**：发布、编辑、删除失物/招领信息
3. **认领功能**：提交认领申请、认领审核
4. **管理员功能**：审核、管理用户、管理内容
5. **数据完整性**：确保所有原有数据都已正确迁移

## 回滚计划

如果迁移出现问题，您可以：

1. 停止应用
2. 恢复备份的 `config.py.backup` 文件
3. 删除MySQL中的campus_crowdfunding数据库
4. 将 `config.py` 内容改回原来的SQLite配置
5. 重启应用

## 注意事项

- 迁移过程中请勿关闭数据库服务
- 生产环境使用时，请使用专用的MySQL用户，而非root用户
- 定期备份MySQL数据库
- 考虑使用环境变量存储数据库密码，提高安全性

## 完成！

完成以上步骤后，您的校园失物招领平台将成功运行在MySQL数据库上，享受MySQL带来的更好性能和扩展性。