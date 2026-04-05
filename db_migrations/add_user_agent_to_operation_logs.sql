-- 数据库迁移脚本：为operation_logs表添加user_agent字段
-- 适用于校园众筹平台

-- 添加user_agent字段
ALTER TABLE operation_logs ADD COLUMN user_agent TEXT;

-- 提示：添加此字段后，可以考虑从日志中移除相关的临时修复代码
