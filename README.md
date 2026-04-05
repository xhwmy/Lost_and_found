# 校园失物招领平台

一个功能完整的校园失物招领平台系统，包含管理员模块和用户模块，支持容器化部署和生产级运维。

## 功能特性

### 管理员模块
1. **登录注册** - 管理员专属账号注册、登录及密码找回
2. **用户管理** - 查询、冻结、解冻用户
3. **项目管理** - 管理失物招领项目
4. **数据统计** - 查看平台运营数据
5. **交流论坛** - 查看帖子并删除不良帖子
6. **系统公告** - 发布、删除、修改系统公告
7. **安全管理** - IP白名单设置、风险规则配置、操作日志审计、敏感数据加密

### 用户模块
1. **登录注册** - 支持注册、登录及找回密码
2. **失物招领** - 发布失物、认领物品、搜索项目
3. **个人中心** - 完善个人信息、修改个人信息、修改密码
4. **消息通知** - 查看系统公告、接收项目进度提醒
5. **交流论坛** - 发帖、回帖、删除帖子、浏览帖子、收藏帖子

## 技术栈

- **后端框架**: Flask 3.1.2
- **数据库**: MySQL 8.0
- **容器化**: Docker + Docker Compose
- **应用服务器**: Gunicorn 21.2.0
- **Web服务器**: Nginx
- **ORM**: SQLAlchemy
- **认证**: Flask-Login
- **前端**: Bootstrap
- **加密**: Cryptography
- **监控**: Prometheus + Grafana (可选)

## 部署方式

### 1. 容器化部署（推荐）

#### 环境要求
- Docker 20.10+
- Docker Compose 1.29+

#### 部署步骤

1. **克隆项目**
   ```bash
   git clone <repository-url>
   cd campus_crowdfunding
   ```

2. **配置环境变量**
   编辑 `.env` 文件：
   ```
   SECRET_KEY=your-secure-secret-key
   FIELD_ENCRYPTION_KEY=your-secure-encryption-key
   ADMIN_DEFAULT_PASSWORD=your-admin-password
   ```

3. **启动服务**
   ```bash
   docker compose up -d --build
   ```

4. **访问应用**
   - 应用地址: http://localhost:8000
   - 管理员登录: http://localhost:8000/admin/login

### 2. 生产环境部署

#### 配置Nginx反向代理

创建 `/etc/nginx/conf.d/campus_crowdfunding.conf`：

```nginx
upstream campus_app {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;

    location /static/ {
        alias /opt/campus_project/campus_crowdfunding/static/;
        expires 30d;
    }

    location / {
        proxy_pass http://campus_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

#### 配置systemd服务

1. **复制服务文件**
   ```bash
   sudo cp campus_crowdfunding.service /etc/systemd/system/
   ```

2. **启用服务**
   ```bash
   sudo systemctl daemon-reload
   sudo systemctl enable campus_crowdfunding
   sudo systemctl start campus_crowdfunding
   ```

3. **查看服务状态**
   ```bash
   sudo systemctl status campus_crowdfunding
   ```

### 3. 一键部署脚本

使用 `deploy.sh` 脚本进行快速部署：

```bash
sudo ./deploy.sh
```

## 默认账号

### 管理员账号
- 用户名: `admin`
- 密码: 首次启动时自动生成（查看容器日志获取）

## 项目结构

```
campus_crowdfunding/
├── app.py                 # 应用入口
├── config.py             # 配置文件
├── models.py             # 数据库模型
├── admin_views.py        # 管理员视图
├── user_views.py         # 用户视图
├── utils.py              # 工具函数
├── requirements.txt      # 依赖列表
├── .env                  # 环境变量
├── Dockerfile            # Docker构建文件
├── docker-compose.yml    # Docker Compose配置
├── campus_crowdfunding.service  # systemd服务文件
├── deploy.sh             # 一键部署脚本
├── templates/            # 模板文件
│   ├── base.html
│   ├── admin/           # 管理员模板
│   └── user/            # 用户模板
└── static/              # 静态文件
    └── uploads/         # 上传文件目录
```

## 监控配置

### Prometheus + Grafana监控

1. **添加监控服务到docker-compose.yml**
   ```yaml
   prometheus:
     image: prom/prometheus:latest
     ports:
       - "9090:9090"
     volumes:
       - prometheus_data:/prometheus
       - ./prometheus.yml:/etc/prometheus/prometheus.yml

   grafana:
     image: grafana/grafana:latest
     ports:
       - "3000:3000"
     volumes:
       - grafana_data:/var/lib/grafana
   ```

2. **创建prometheus.yml配置文件**
   ```yaml
global:
  scrape_interval: 15s

scrape_configs:
  - job_name: 'flask_app'
    static_configs:
      - targets: ['campus_app:8000']
  - job_name: 'node'
    static_configs:
      - targets: ['node-exporter:9100']
   ```

## 注意事项

1. **生产环境安全**
   - 务必修改 `.env` 文件中的所有密钥
   - 使用强密码和密钥
   - 配置防火墙，只开放必要端口

2. **性能优化**
   - 根据服务器配置调整Gunicorn worker数量
   - 启用Nginx静态文件缓存
   - 定期清理日志文件

3. **数据备份**
   - 定期备份MySQL数据
   - 备份上传文件目录

## 技术亮点

1. **容器化部署** - 使用Docker Compose实现服务编排
2. **生产级配置** - Gunicorn + Nginx + systemd
3. **安全措施** - CSRF保护、密码加密、登录限制
4. **自动数据库迁移** - 自动检测和添加缺失字段
5. **监控系统** - 支持Prometheus + Grafana监控

## 许可证

MIT License

## 联系方式

如有问题，请提交Issue。
