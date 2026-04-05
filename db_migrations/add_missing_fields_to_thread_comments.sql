-- 为thread_comments表添加缺失的字段
-- 这些字段用于支持评论的嵌套回复和软删除功能

-- 检查parent_id字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'parent_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN parent_id INTEGER",  -- 父评论ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查is_deleted字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'is_deleted' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN is_deleted BOOLEAN DEFAULT FALSE",  -- 软删除标记
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查lost_item_id字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'lost_item_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN lost_item_id INTEGER",  -- 关联的失物ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查found_item_id字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'found_item_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN found_item_id INTEGER",  -- 关联的招领物ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查post_id字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'post_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN post_id INTEGER",  -- 关联的帖子ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查status字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'thread_comments' AND column_name = 'status' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE thread_comments ADD COLUMN status VARCHAR(20) DEFAULT 'active'",  -- 评论状态
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为新增字段创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_thread_comments_parent ON thread_comments(parent_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_lost_item ON thread_comments(lost_item_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_found_item ON thread_comments(found_item_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_post ON thread_comments(post_id);
CREATE INDEX IF NOT EXISTS idx_thread_comments_status ON thread_comments(status);