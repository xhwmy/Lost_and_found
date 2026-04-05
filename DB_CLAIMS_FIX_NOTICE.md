数据库结构修复说明
================

问题：
- claims表缺少reviewed_at, reviewer_id, review_note字段
- 模型中定义了这些字段，但数据库中不存在
- 导致'Unknown column 'claims.reviewed_at' in 'field list''错误

根本原因：
- 数据库结构与模型定义不匹配
- claims表缺少审核相关的字段

解决方案：
1.  已从模型中临时移除审核相关字段
2.  已创建SQL迁移脚本来永久修复数据库结构
3.  应用可以立即正常运行

临时修复：
- 从Claim模型中移除了reviewed_at字段
- 从Claim模型中移除了reviewer_id字段
- 从Claim模型中移除了review_note字段
- 从Claim模型中移除了reviewer关系
- 这使得应用可以在数据库结构修复前正常运行

永久解决方案：
运行SQL脚本 db_migrations/add_review_fields_to_claims.sql 来更新数据库结构
完成后，可以选择性地将审核相关字段和关系加回到模型中

当前状态：
-  应用可以正常启动和运行
-  认领功能正常工作（但缺少审核功能）
-  系统稳定性已恢复

后续步骤（可选）：
1. 运行数据库迁移脚本以永久修复结构
2. 将审核相关字段和关系重新添加到Claim模型中
3. 更新相关查询逻辑以利用审核功能
