# MySQL配置说明

## 重要：修改数据库密码

在启动应用之前，您需要将配置文件中的密码替换为您实际的MySQL密码。

### 1. 编辑配置文件
打开 `config.py` 文件，将 `your_actual_password` 替换为您的MySQL root密码：

```python
class DevelopmentConfig(Config):
    DEBUG = True
    # MySQL数据库连接字符串 - 请将your_actual_password替换为实际的MySQL密码
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:your_actual_password@localhost/campus_crowdfunding'
```

修改为（假设您的密码是 "mypassword"）：

```python
class DevelopmentConfig(Config):
    DEBUG = True
    # MySQL数据库连接字符串 - 已设置为实际密码
    SQLALCHEMY_DATABASE_URI = os.environ.get('DEV_DATABASE_URL') or \
        'mysql+pymysql://root:mypassword@localhost/campus_crowdfunding'
```

同样修改 ProductionConfig 部分。

### 2. 确认数据库已创建
确保您已经使用以下命令创建了数据库：

```sql
SOURCE c:/Users/86187/Desktop/毕业设计/campus_crowdfunding/mysql_setup_guide.sql;
```

### 3. 启动应用
完成上述配置后，运行：

```bash
python app.py
```

## 故障排除

如果遇到连接错误：

1. **检查MySQL服务**：确保MySQL服务正在运行
2. **检查密码**：确认密码设置正确
3. **检查数据库**：确认 campus_crowdfunding 数据库存在
4. **检查端口**：确认MySQL在默认端口3306上运行

## 访问应用
启动成功后，您可以通过以下地址访问：
- 本地访问：http://127.0.0.1:5000
- 局域网访问：http://[您的IP]:5000