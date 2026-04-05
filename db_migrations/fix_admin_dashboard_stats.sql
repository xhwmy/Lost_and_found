-- 修复管理员仪表盘模板中stats变量未定义的问题
-- 此脚本不需要对数据库进行任何更改，仅用于记录修复

-- 修复内容：
-- 1. 在admin_views.py的dashboard函数中创建stats字典
-- 2. 将所有统计数据放入stats字典中传递给模板
-- 3. 模板现在可以通过stats.total_users等方式访问数据

-- 这是一个逻辑修复，不需要数据库结构更改
SELECT 'Admin dashboard stats fix applied' AS message;