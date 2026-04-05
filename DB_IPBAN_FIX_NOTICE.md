数据库结构修复说明 - IPBan表
================

问题：
- ip_bans表缺少is_active字段
- admin_views.py中查询IPBan时使用了不存在的is_active字段
- 导致'Entity namespace for 'ip_bans' has no property 'is_active''错误

根本原因：
- 数据库结构与代码查询不匹配
- IPBan表缺少is_active字段

解决方案：
1.  已修改admin_views.py中的查询逻辑，移除对is_active字段的依赖
2.  已在IPBan模型中添加is_banned()方法，基于现有字段判断封禁状态
3.  已创建SQL迁移脚本来永久修复数据库结构

临时修复：
- 修改admin_views.py中的IP查询，移除is_active条件
- 使用IPBan模型中的is_banned()方法来判断IP是否被封禁
- 这使得应用可以在数据库结构修复前正常运行

永久解决方案：
运行SQL脚本 db_migrations/add_is_active_to_ip_bans.sql 来更新数据库结构
完成后，可以优化is_banned()方法逻辑以利用is_active字段

当前状态：
-  应用可以正常启动和运行
-  IP封禁功能正常工作
-  系统稳定性已恢复

后续步骤（可选）：
1. 运行数据库迁移脚本以永久修复结构
2. 优化IPBan模型中的is_banned()方法以利用is_active字段
3. 更新相关查询逻辑以利用新字段
