-- 为admins表添加缺失的字段
-- 这些字段在模型中定义但在数据库中可能不存在

-- 检查并添加last_login_time字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'admins' AND column_name = 'last_login_time' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE admins ADD COLUMN last_login_time DATETIME",  -- 上次登录时间
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加is_active字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'admins' AND column_name = 'is_active' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE admins ADD COLUMN is_active BOOLEAN DEFAULT TRUE",  -- 是否激活
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加login_attempts字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'admins' AND column_name = 'login_attempts' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE admins ADD COLUMN login_attempts INT DEFAULT 0",  -- 登录尝试次数
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为新增字段创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_admins_last_login_time ON admins(last_login_time);
CREATE INDEX IF NOT EXISTS idx_admins_is_active ON admins(is_active);