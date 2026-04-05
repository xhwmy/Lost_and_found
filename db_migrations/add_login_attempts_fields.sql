-- 为users表添加登录尝试次数和最后登录失败时间字段
-- 适用于校园众筹平台

-- 检查login_attempts字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'users' AND column_name = 'login_attempts' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE users ADD COLUMN login_attempts INT DEFAULT 0",  -- 登录尝试次数
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查last_failed_login字段是否存在，如果不存在则添加
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'users' AND column_name = 'last_failed_login' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE users ADD COLUMN last_failed_login DATETIME",  -- 最后一次登录失败时间
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_users_login_attempts ON users(login_attempts);
CREATE INDEX IF NOT EXISTS idx_users_last_failed_login ON users(last_failed_login);

-- 提示：添加这些字段后，登录失败次数和最后登录失败时间将被正确存储在数据库中