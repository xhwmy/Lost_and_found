-- 为operation_logs表添加缺失的字段（安全版本）
-- 使用动态SQL检查字段是否存在，避免重复添加错误

-- 检查并添加target_type字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'operation_logs' AND column_name = 'target_type' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE operation_logs ADD COLUMN target_type VARCHAR(50)",  -- 目标类型
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 检查并添加user_agent字段
SET @s = (SELECT IF(
    (SELECT COUNT(*) FROM INFORMATION_SCHEMA.COLUMNS 
     WHERE table_name = 'operation_logs' AND column_name = 'user_agent' 
     AND table_schema = DATABASE()) = 0,
    "ALTER TABLE operation_logs ADD COLUMN user_agent TEXT",  -- 用户代理信息
    "SELECT 1"));

PREPARE stmt FROM @s;
EXECUTE stmt;
DEALLOCATE PREPARE stmt;

-- 为新增字段创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_operation_logs_target_type ON operation_logs(target_type);
CREATE INDEX IF NOT EXISTS idx_operation_logs_user_agent ON operation_logs(user_agent);