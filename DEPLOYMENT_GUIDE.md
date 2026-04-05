# 校园众筹网站云服务器部署指南

本指南详细介绍了如何将校园众筹网站部署到云服务器，使用 Nginx 作为反向代理。

## 一、本地代码准备

### 1. 代码适配（已完成）

- ✅ 修改了 `app.py` 中的启动配置：
  - 使用 `production` 环境
  - 设置 `host='0.0.0.0'` 允许公网访问
  - 设置 `port=8000` 作为应用端口
  - 关闭 `debug` 模式，提高安全性

- ✅ 更新了 `.env` 文件：
  - 设置了更安全的密钥
  - 添加了数据库连接配置
  - 设置 `FLASK_ENV=production`

- ✅ 检查了代码中的路径处理：
  - 所有路径使用 `os.path` 处理，兼容 Linux 系统
  - 无硬编码的 Windows 路径分隔符

### 2. 清理不需要的文件

在部署前，建议清理以下文件，减少部署包大小：

```bash
# 删除虚拟环境
rm -rf .venv venv

# 删除 IDE 配置文件
rm -rf .idea

# 删除编译缓存
rm -rf __pycache__

# 删除 SQLite 数据库文件（如果使用 MySQL）
rm -f database.db

# 删除迁移脚本和检查脚本（可选）
rm -rf db_migrations
rm -f *.pyc
rm -f add_indexes.py check_all_admin_routes.py check_db_fields.py check_known_issues.py check_reply_counts.py enhance_sensitive_data_encryption.py find_missing_fields.py fix_bom.py fix_csrf_tokens.py fix_models_bom.py init_sample_data.py migrate_add_admin_post_field.py migrate_add_count_fields.py migrate_db_structure.py
```

### 3. 生成依赖清单（已完成）

项目已包含 `requirements.txt` 文件，包含所有必要的依赖项。

## 二、云服务器准备

### 1. 服务器配置

- **操作系统**：Ubuntu 20.04 LTS 或 CentOS 7+
- **内存**：至少 2GB
- **CPU**：至少 1 核
- **存储空间**：至少 20GB

### 2. 安装必要的软件

#### Ubuntu/Debian

```bash
# 更新系统
apt update && apt upgrade -y

# 安装必要的软件
apt install -y nginx mysql-server python3 python3-pip python3-venv git

# 启动服务
systemctl start nginx
systemctl start mysql
systemctl enable nginx
systemctl enable mysql
```

#### CentOS/RHEL

```bash
# 更新系统
yum update -y

# 安装必要的软件
yum install -y nginx mariadb-server python3 python3-pip git

# 启动服务
systemctl start nginx
systemctl start mariadb
systemctl enable nginx
systemctl enable mariadb
```

### 3. 配置 MySQL 数据库

```bash
# 登录 MySQL
mysql -u root -p

# 创建数据库和用户
CREATE DATABASE campus_crowdfunding CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'campus_user'@'localhost' IDENTIFIED BY 'your_password';
GRANT ALL PRIVILEGES ON campus_crowdfunding.* TO 'campus_user'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

## 三、部署代码

### 1. 上传代码

使用 SCP 或 FTP 工具将代码上传到服务器：

```bash
# 本地执行
scp -r campus_crowdfunding.zip root@your_server_ip:/opt/

# 服务器执行
unzip /opt/campus_crowdfunding.zip -d /opt/
cd /opt/campus_crowdfunding
```

### 2. 创建虚拟环境并安装依赖

```bash
# 创建虚拟环境
python3 -m venv venv

# 激活虚拟环境
source venv/bin/activate

# 安装依赖
pip install -i https://mirrors.aliyun.com/pypi/simple/ -r requirements.txt
```

### 3. 更新环境变量

在服务器上创建 `.env` 文件，填写正确的数据库连接信息：

```bash
# 编辑 .env 文件
nano .env

# 填写以下内容
FLASK_APP=app.py
FLASK_ENV=production
SECRET_KEY=campus_crowdfunding_2026_secure_secret_key
ENCRYPTION_KEY=campus_crowdfunding_2026_secure_encryption_key
DEV_DATABASE_URL=mysql+pymysql://campus_user:your_password@localhost/campus_crowdfunding
DATABASE_URL=mysql+pymysql://campus_user:your_password@localhost/campus_crowdfunding
```

### 4. 初始化数据库

```bash
# 激活虚拟环境（如果未激活）
source venv/bin/activate

# 运行应用，自动创建数据库表
python app.py

# 按 Ctrl+C 停止应用
```

## 四、配置 Nginx

### 1. 创建 Nginx 配置文件

```bash
# 创建配置文件
nano /etc/nginx/sites-available/campus_crowdfunding

# 填写以下内容
server {
    listen 80;
    server_name your_domain.com;

    location / {
        proxy_pass http://localhost:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    # 静态文件配置
    location /static {
        alias /opt/campus_crowdfunding/static;
        expires 30d;
    }
}
```

### 2. 启用配置文件

```bash
# 创建符号链接
ln -s /etc/nginx/sites-available/campus_crowdfunding /etc/nginx/sites-enabled/

# 测试配置
nginx -t

# 重启 Nginx
systemctl restart nginx
```

## 五、启动应用

### 1. 使用 Gunicorn 启动（推荐）

```bash
# 安装 Gunicorn
pip install gunicorn

# 启动应用
cd /opt/campus_crowdfunding
source venv/bin/activate
gunicorn -w 4 -b 0.0.0.0:8000 app:create_app('production')
```

### 2. 使用 systemd 管理服务

```bash
# 创建服务文件
nano /etc/systemd/system/campus_crowdfunding.service

# 填写以下内容
[Unit]
Description=Campus Crowdfunding Application
After=network.target

[Service]
User=root
WorkingDirectory=/opt/campus_crowdfunding
Environment="PATH=/opt/campus_crowdfunding/venv/bin"
ExecStart=/opt/campus_crowdfunding/venv/bin/gunicorn -w 4 -b 0.0.0.0:8000 app:create_app('production')
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
# 启用并启动服务
systemctl daemon-reload
systemctl enable campus_crowdfunding
systemctl start campus_crowdfunding

# 查看服务状态
systemctl status campus_crowdfunding
```

## 六、安全配置

### 1. 配置防火墙

```bash
# 查看当前防火墙状态
iptables -L

# 允许 80 端口（HTTP）
iptables -A INPUT -p tcp --dport 80 -j ACCEPT

# 允许 443 端口（HTTPS，如果使用 SSL）
iptables -A INPUT -p tcp --dport 443 -j ACCEPT

# 保存防火墙规则
# Ubuntu/Debian
iptables-save > /etc/iptables/rules.v4

# CentOS/RHEL
iptables-save > /etc/sysconfig/iptables
```

### 2. 配置 SSL（可选）

使用 Let's Encrypt 获取免费的 SSL 证书：

```bash
# 安装 Certbot
apt install -y certbot python3-certbot-nginx

# 获取证书
certbot --nginx -d your_domain.com

# 自动续期
certbot renew --dry-run
```

## 七、常见问题排查

### 1. 应用无法启动

```bash
# 查看应用日志
systemctl status campus_crowdfunding

# 或查看 Gunicorn 日志
tail -f /var/log/campus_crowdfunding.log
```

### 2. 数据库连接错误

- 检查 `.env` 文件中的数据库连接字符串是否正确
- 检查 MySQL 服务是否正在运行
- 检查数据库用户是否有正确的权限

### 3. Nginx 502 Bad Gateway

- 检查 Flask 应用是否正在运行
- 检查 Flask 应用的端口是否正确
- 检查 Nginx 配置文件中的 `proxy_pass` 是否正确

### 4. 静态文件无法访问

- 检查 Nginx 配置文件中的 `static` 路径是否正确
- 检查静态文件是否存在于指定路径

## 八、部署完成后的检查

部署完成后，建议检查以下功能：

1. **网站访问**：使用浏览器访问网站，检查是否可以正常加载
2. **用户登录**：测试用户登录功能，确保可以正常登录
3. **管理员功能**：测试管理员登录和管理功能
4. **数据库操作**：测试数据的增删改查功能
5. **文件上传**：测试文件上传功能（如果有）

## 总结

本指南详细介绍了将校园众筹网站部署到云服务器的完整流程，包括代码准备、服务器配置、依赖安装、数据库配置、Nginx 配置和启动服务等步骤。按照本指南操作，应该可以顺利完成网站部署。

如果在部署过程中遇到任何问题，可以参考常见问题排查部分，或联系技术支持。