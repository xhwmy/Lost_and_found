-- 为users表添加安全相关字段（增强版本）
-- 这些字段用于支持用户账户安全功能，如登录失败限制、账户冻结等

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