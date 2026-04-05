数据库字段更新说明
==================

问题：
- announcements表缺少is_published字段
- user_views.py中使用了不存在的is_published字段进行查询
- 导致InvalidRequestError: Entity namespace for "announcements" has no property "is_published"

解决方案：
1. 已修改user_views.py中的查询，移除对is_published字段的依赖
2. 已在models.py的Announcement模型中添加is_published字段定义
3. 创建了SQL迁移脚本来更新数据库结构（见db_migrations/add_is_published_to_announcements.sql）

临时修复：
- 修改了两处查询：
  - 第1处：获取首页公告的查询（原第187行左右）
  - 第2处：获取最新公告的查询（原第197行左右）
- 查询不再使用filter_by(is_published=True)，而是直接查询所有公告

永久解决方案：
运行SQL脚本 db_migrations/add_is_published_to_announcements.sql 来更新数据库结构
完成后，可选择性地启用is_published字段的过滤功能

当前状态：
- 应用可以正常启动和运行
- 公告功能正常工作（显示所有公告，不限制is_published状态）
- 系统稳定性已恢复
