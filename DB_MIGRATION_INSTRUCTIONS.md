# 数据库结构迁移说明

由于校园失物招领平台的数据库结构与模型定义不匹配，需要运行以下SQL迁移脚本来更新数据库结构。

## 重要说明

- 当前应用程序使用内存数据库或临时数据库，因此在每次重启时会丢失数据
- 如果您使用的是持久化数据库（如MySQL），请按照以下步骤运行迁移脚本
- 运行迁移脚本后，数据库结构将与模型定义完全匹配

## 迁移脚本列表

以下是需要按顺序运行的SQL迁移脚本：

### 1. 为admins表添加缺失字段
```sql
-- db_migrations/add_missing_fields_to_admins.sql
ALTER TABLE admins ADD COLUMN email VARCHAR(120) UNIQUE;  -- 邮箱
ALTER TABLE admins ADD COLUMN real_name VARCHAR(100);  -- 真实姓名
ALTER TABLE admins ADD COLUMN role VARCHAR(50) DEFAULT 'admin';  -- 角色
ALTER TABLE admins ADD COLUMN last_login_time DATETIME;  -- 上次登录时间
ALTER TABLE admins ADD COLUMN is_active BOOLEAN DEFAULT TRUE;  -- 是否激活
ALTER TABLE admins ADD COLUMN login_attempts INTEGER DEFAULT 0;  -- 登录尝试次数

CREATE INDEX IF NOT EXISTS idx_admins_email ON admins(email);
CREATE INDEX IF NOT EXISTS idx_admins_role ON admins(role);
```

### 2. 为forum_posts表添加author_name字段
```sql
-- db_migrations/add_author_name_to_forum_posts.sql
ALTER TABLE forum_posts ADD COLUMN author_name VARCHAR(100) NOT NULL DEFAULT 'Anonymous';
CREATE INDEX IF NOT EXISTS idx_forum_posts_author ON forum_posts(author_name);
```

### 3. 为forum_replies表添加author_name字段
```sql
-- db_migrations/add_author_name_to_forum_replies.sql
ALTER TABLE forum_replies ADD COLUMN author_name VARCHAR(100) NOT NULL DEFAULT 'Anonymous';
CREATE INDEX IF NOT EXISTS idx_forum_replies_author ON forum_replies(author_name);
```

### 4. 为forum_posts表添加统计字段（第一部分）
```sql
-- db_migrations/add_stats_fields_to_forum_posts.sql
ALTER TABLE forum_posts ADD COLUMN view_count INTEGER DEFAULT 0;  -- 浏览次数
ALTER TABLE forum_posts ADD COLUMN like_count INTEGER DEFAULT 0;  -- 点赞数
ALTER TABLE forum_posts ADD COLUMN reply_count INTEGER DEFAULT 0;  -- 回复数

CREATE INDEX IF NOT EXISTS idx_forum_posts_stats ON forum_posts(view_count DESC, like_count DESC, reply_count DESC);
```

### 14. 为forum_posts表添加统计字段（第二部分 - 安全版本）
```sql
-- db_migrations/add_stats_fields_to_forum_posts_v2.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'forum_posts' AND column_name = 'view_count' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE forum_posts ADD COLUMN view_count INTEGER DEFAULT 0",
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'forum_posts' AND column_name = 'like_count' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE forum_posts ADD COLUMN like_count INTEGER DEFAULT 0",
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'forum_posts' AND column_name = 'reply_count' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE forum_posts ADD COLUMN reply_count INTEGER DEFAULT 0",
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高统计查询性能
CREATE INDEX IF NOT EXISTS idx_forum_posts_stats ON forum_posts(view_count DESC, like_count DESC, reply_count DESC);
```

### 5. 为forum_posts表添加用户ID字段
```sql
-- db_migrations/add_user_id_to_forum_posts.sql
ALTER TABLE forum_posts ADD COLUMN user_id INTEGER;  -- 关联用户ID
CREATE INDEX IF NOT EXISTS idx_forum_posts_user ON forum_posts(user_id);
```

### 6. 为forum_posts表添加置顶字段
```sql
-- db_migrations/add_pinned_fields_to_forum_posts.sql
ALTER TABLE forum_posts ADD COLUMN is_pinned BOOLEAN DEFAULT 0;  -- 是否置顶
ALTER TABLE forum_posts ADD COLUMN pin_order INTEGER DEFAULT 0;  -- 置顶顺序

CREATE INDEX IF NOT EXISTS idx_forum_posts_pinned_order ON forum_posts(is_pinned DESC, pin_order DESC, created_at DESC);
```

### 7. 为favorites表添加类型字段
```sql
-- db_migrations/add_type_to_favorites.sql
ALTER TABLE favorites ADD COLUMN type VARCHAR(20) DEFAULT NULL;

UPDATE favorites SET type = 'lost_item' WHERE lost_item_id IS NOT NULL;
UPDATE favorites SET type = 'found_item' WHERE found_item_id IS NOT NULL;
UPDATE favorites SET type = 'post' WHERE post_id IS NOT NULL;

CREATE INDEX IF NOT EXISTS idx_favorites_user_type ON favorites(user_id, type);
```

### 8. 为operation_logs表添加target_type字段
```sql
-- db_migrations/add_target_type_to_operation_logs.sql
ALTER TABLE operation_logs ADD COLUMN target_type VARCHAR(50);  -- 目标类型

CREATE INDEX IF NOT EXISTS idx_operation_logs_target_type ON operation_logs(target_type);
```

### 9. 为operation_logs表添加user_agent字段
```sql
-- db_migrations/add_user_agent_to_operation_logs.sql
ALTER TABLE operation_logs ADD COLUMN user_agent TEXT;  -- 用户代理信息
```

### 10. 为announcements表添加author_id字段
```sql
-- db_migrations/add_author_id_to_announcements.sql
ALTER TABLE announcements ADD COLUMN author_id INTEGER;  -- 作者ID
CREATE INDEX IF NOT EXISTS idx_announcements_author ON announcements(author_id);
```

### 11. 为claims表添加审核字段
```sql
-- db_migrations/add_review_fields_to_claims.sql
ALTER TABLE claims ADD COLUMN reviewed_at DATETIME;  -- 审核时间
ALTER TABLE claims ADD COLUMN reviewer_id INTEGER;  -- 审核员ID
ALTER TABLE claims ADD COLUMN review_note TEXT;  -- 审核备注

CREATE INDEX IF NOT EXISTS idx_claims_reviewer ON claims(reviewer_id);
```

### 12. 为users表添加安全字段（第一部分）
```sql
-- db_migrations/add_security_fields_to_users.sql
ALTER TABLE users ADD COLUMN is_frozen BOOLEAN DEFAULT FALSE;  -- 是否冻结
ALTER TABLE users ADD COLUMN freeze_reason TEXT;  -- 冻结原因
ALTER TABLE users ADD COLUMN frozen_until DATETIME;  -- 解冻时间
ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45);  -- 最后登录IP
ALTER TABLE users ADD COLUMN security_level INTEGER DEFAULT 1;  -- 安全等级

CREATE INDEX IF NOT EXISTS idx_users_frozen ON users(is_frozen);
```

### 15. 为users表添加安全字段（第二部分 - 增强版）
```sql
-- db_migrations/add_security_fields_to_users_v2.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'users' AND column_name = 'is_frozen' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE users ADD COLUMN is_frozen BOOLEAN DEFAULT FALSE",  -- 是否冻结
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'users' AND column_name = 'failed_login_attempts' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE users ADD COLUMN failed_login_attempts INTEGER DEFAULT 0",  -- 登录失败次数
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'users' AND column_name = 'last_failed_login' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE users ADD COLUMN last_failed_login DATETIME",  -- 最后一次登录失败时间
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高安全查询性能
CREATE INDEX IF NOT EXISTS idx_users_frozen ON users(is_frozen);
CREATE INDEX IF NOT EXISTS idx_users_login_attempts ON users(failed_login_attempts);
CREATE INDEX IF NOT EXISTS idx_users_last_failed_login ON users(last_failed_login);
```

### 13. 为ip_bans表添加必要字段（第一部分 - 原始字段）
```sql
-- db_migrations/add_banned_at_to_ip_bans.sql
ALTER TABLE ip_bans ADD COLUMN banned_at DATETIME DEFAULT CURRENT_TIMESTAMP;  -- 封禁时间

-- 如果没有is_active字段也要添加（旧方法）
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'ip_bans' AND column_name = 'is_active' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE ip_bans ADD COLUMN is_active BOOLEAN DEFAULT TRUE",  -- 是否激活
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引
CREATE INDEX IF NOT EXISTS idx_ip_bans_expires ON ip_bans(expires_at);
CREATE INDEX IF NOT EXISTS idx_ip_bans_active ON ip_bans(is_active);
```

### 14. 为ip_bans表添加is_active字段（第二部分 - 安全增强版）
```sql
-- db_migrations/add_is_active_to_ip_bans.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'ip_bans' AND column_name = 'is_active' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE ip_bans ADD COLUMN is_active BOOLEAN DEFAULT TRUE",  -- 是否活跃
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 更新现有记录，将过期的封禁设为非活跃
UPDATE ip_bans SET is_active = FALSE WHERE expires_at IS NOT NULL AND expires_at < NOW();

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_ip_bans_active ON ip_bans(is_active);
```

### 17. 为thread_comments表添加关联字段
```sql
-- db_migrations/add_association_fields_to_thread_comments.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'lost_item_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN lost_item_id INTEGER",  -- 关联失物ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'found_item_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN found_item_id INTEGER",  -- 关联招领物ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'post_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN post_id INTEGER",  -- 关联帖子ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高关联查询性能
CREATE INDEX IF NOT EXISTS idx_thread_comments_lost_item ON thread_comments(lost_item_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_found_item ON thread_comments(found_item_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_post ON thread_comments(post_id);
```

### 18. 为thread_comments表添加status字段
```sql
-- db_migrations/add_status_to_thread_comments.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'status' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN status VARCHAR(20) DEFAULT 'active'",  -- 评论状态
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高状态查询性能
CREATE INDEX IF NOT EXISTS idx_thread_comments_status ON thread_comments(status);
```

### 19. 为thread_comments表添加parent_id字段
```sql
-- db_migrations/add_parent_id_to_thread_comments.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'parent_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN parent_id INTEGER",  -- 父评论ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高父子评论查询性能
CREATE INDEX IF NOT EXISTS idx_thread_comments_parent ON thread_comments(parent_id);
```

### 20. 为thread_comments表添加is_deleted字段
```sql
-- db_migrations/add_is_deleted_to_thread_comments.sql
-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'is_deleted' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE",  -- 软删除标记
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高删除状态查询性能
CREATE INDEX IF NOT EXISTS idx_thread_comments_deleted ON thread_comments(is_deleted);
```

## 如何运行迁移脚本

### 方法1：使用MySQL命令行
```bash
mysql -u root -p -D campus_crowdfunding < db_migrations/add_missing_fields_to_admins.sql
mysql -u root -p -D campus_crowdfunding < db_migrations/add_author_name_to_forum_posts.sql
# ... 运行其他脚本
```

### 方法2：使用Python脚本
```python
import pymysql

connection = pymysql.connect(
    host='localhost',
    user='root',
    password='root',
    database='campus_crowdfunding',
    charset='utf8mb4'
)

cursor = connection.cursor()

# 读取并执行SQL文件
with open('db_migrations/add_missing_fields_to_admins.sql', 'r', encoding='utf-8') as f:
    sql_script = f.read()
    
for statement in sql_script.split(';'):
    statement = statement.strip()
    if statement:
        cursor.execute(statement)

connection.commit()
connection.close()
```

## 完成迁移后的验证

运行完所有迁移脚本后，您可以验证数据库结构是否正确：

```python
from app import create_app
from models import Admin, ForumPost

app = create_app()

with app.app_context():
    # 尝试访问所有字段
    admin = Admin.query.first()
    if admin:
        print(f"Admin role: {admin.role}")
        print(f"Admin email: {admin.email}")
        print(f"Admin real_name: {admin.real_name}")
    
    post = ForumPost.query.first()
    if post:
        print(f"Forum post user_id: {post.user_id}")
        print(f"Forum post is_pinned: {post.is_pinned}")
```

## 重要提醒

- 在生产环境中运行迁移脚本前，请务必备份数据库
- 某些字段可能需要设置适当的默认值
- 如果使用其他数据库系统（如PostgreSQL、SQLite），可能需要调整SQL语法