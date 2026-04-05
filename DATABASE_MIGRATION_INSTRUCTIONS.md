数据库迁移说明
==============

问题：应用启动时遇到错误 'Unknown column \'admins.last_login_time\' in \'field list\''

原因：数据库中的admins表结构与models.py中定义的Admin模型不匹配。

解决方法：

方法1：运行数据库迁移（推荐）
1. 在数据库客户端中执行以下SQL语句：
   ALTER TABLE admins ADD COLUMN last_login_time DATETIME NULL;
   ALTER TABLE admins ADD COLUMN login_attempts INT DEFAULT 0;
   ALTER TABLE admins ADD COLUMN is_active TINYINT(1) DEFAULT 1;

方法2：使用Flask-Migrate进行数据库迁移
1. 安装Flask-Migrate: pip install Flask-Migrate
2. 初始化迁移: flask db init
3. 创建迁移脚本: flask db migrate -m "Add missing admin fields"
4. 应用迁移: flask db upgrade

方法3：临时修复（快速启动应用）
1. 目前我们已经注释掉了models.py中的last_login_time字段定义
2. 应用现在应该可以启动
3. 之后仍需按照方法1或方法2修复数据库结构

注意：为了长期稳定运行，请务必使用方法1或方法2修复数据库结构，
而不是依赖临时修复方案。
