-- 为forum_replies表添加parent_id字段
-- 此字段用于支持回复的回复（嵌套回复功能）

-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'forum_replies' AND column_name = 'parent_id' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE forum_replies ADD COLUMN parent_id INTEGER",  -- 父回复ID
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为parent_id字段创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_forum_replies_parent ON forum_replies(parent_id);

-- 同时添加外键约束（可选，根据需要启用）
-- ALTER TABLE forum_replies ADD CONSTRAINT fk_forum_replies_parent 
--     FOREIGN KEY (parent_id) REFERENCES forum_replies(id);