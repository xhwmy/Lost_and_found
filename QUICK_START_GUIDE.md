# 校园失物招领平台 - 快速启动指南

## 项目概述

这是一个校园失物招领平台，支持用户发布失物信息、招领信息，管理员审核内容，以及论坛功能。

## 系统要求

- Python 3.8+
- MySQL（可选，当前使用内存数据库）

## 快速启动

### 1. 安装依赖
```bash
pip install -r requirements.txt
```

### 2. 启动应用
```bash
python app.py
```

或者使用启动脚本：
```bash
./start.bat  # Windows
```

### 3. 访问应用
- 应用将在 `http://127.0.0.1:5000` 启动
- 默认管理员账号：`admin`
- 默认管理员密码：`admin123`

## 功能说明

### 用户功能
- 注册/登录
- 发布失物信息
- 发布招领信息
- 搜索失物/招领信息
- 认领失物
- 收藏功能
- 论坛发帖

### 管理员功能
- 用户管理
- 物品审核
- 认领审核
- 论坛管理
- 系统公告

## 数据库迁移说明

由于数据库结构与模型定义不匹配，已创建SQL迁移脚本：

- 位置：`db_migrations/` 目录
- 详细说明见：`DB_MIGRATION_INSTRUCTIONS.md`

## 当前状态

- 所有模型结构不匹配问题已修复
- 临时解决方案已实施
- 长期解决方案（数据库迁移）已提供
- 应用可正常启动和运行

## 常见问题

### Q: 无法登录管理员账户？
A: 请确认使用默认账户 `admin` / `admin123`

### Q: 论坛功能无法使用？
A: 检查 ForumPost 模型是否包含所需字段

### Q: 数据库连接错误？
A: 当前使用内存数据库，重启后数据会丢失

## 开发说明

### 模型修复
- Admin 模型：添加了 role, email, real_name 等字段
- ForumPost 模型：添加了 user_id, is_pinned, pin_order 等字段
- 移除了临时不需要的字段（如 author_name）

### 数据库迁移
- 所有必要的字段迁移脚本已创建
- 请参考 `DB_MIGRATION_INSTRUCTIONS.md` 进行数据库结构更新

## 联系支持

如有问题，请检查：
1. `FINAL_COMPLETE_DB_FIX_SUMMARY.md` - 完整修复总结
2. `DB_MIGRATION_INSTRUCTIONS.md` - 数据库迁移说明
3. `README.md` - 项目说明文档