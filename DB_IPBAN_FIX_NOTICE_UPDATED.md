数据库结构修复说明 - IPBan表（更新版）
================

问题：
- ip_bans表缺少banned_at字段
- models.py中的IPBan模型定义了banned_at字段，但数据库中不存在
- 导致'Unknown column 'ip_bans.banned_at' in 'field list''错误

根本原因：
- 数据库结构与模型定义不匹配
- IPBan表缺少banned_at字段

解决方案：
1.  已从IPBan模型中临时移除banned_at字段定义
2.  已创建SQL迁移脚本来永久修复数据库结构
3.  应用可以立即正常运行

临时修复：
- 从IPBan模型中移除banned_at字段定义
- 保留is_banned()方法，仅基于expires_at字段判断封禁状态
- 这使得应用可以在数据库结构修复前正常运行

永久解决方案：
运行SQL脚本 db_migrations/add_banned_at_to_ip_bans.sql 来更新数据库结构
完成后，可以将banned_at字段重新添加到IPBan模型中

当前状态：
-  应用可以正常启动和运行
-  IP封禁功能正常工作
-  系统稳定性已恢复

后续步骤（可选）：
1. 运行数据库迁移脚本以永久修复结构
2. 将banned_at字段重新添加到IPBan模型中
3. 更新is_banned()方法逻辑以利用banned_at字段
