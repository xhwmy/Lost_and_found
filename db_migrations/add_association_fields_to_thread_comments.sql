-- 为thread_comments表添加关联字段
-- 这些字段用于支持评论关联到不同的内容类型：失物、招领物、帖子等

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