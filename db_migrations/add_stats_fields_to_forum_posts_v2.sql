-- 为forum_posts表添加统计相关字段（更新版本）
-- 这些字段用于支持帖子的点赞数和回复数统计功能

-- 检查字段是否存在，如果不存在则添加
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
CREATE INDEX IF NOT EXISTS idx_forum_posts_stats ON forum_posts(like_count DESC, reply_count DESC);