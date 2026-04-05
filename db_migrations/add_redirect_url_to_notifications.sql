-- 为notifications表添加redirect_url字段
-- 用于支持通知跳转功能

-- 检查字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'notifications' AND column_name = 'redirect_url' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE notifications ADD COLUMN redirect_url VARCHAR(500)",
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为redirect_url字段创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_notifications_redirect_url ON notifications(redirect_url);