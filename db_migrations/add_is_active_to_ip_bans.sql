-- 为ip_bans表添加is_active字段
-- 这个字段用于标识IP封禁记录是否处于活跃状态

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