-- 为operation_logs表添加target_type字段
-- 这个字段用于标识操作的目标类型

ALTER TABLE operation_logs ADD COLUMN target_type VARCHAR(50);  -- 目标类型

-- 创建索引以提高按目标类型查询的性能
CREATE INDEX IF NOT EXISTS idx_operation_logs_target_type ON operation_logs(target_type);