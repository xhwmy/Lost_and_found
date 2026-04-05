-- 数据库迁移脚本：为ip_bans表添加banned_at字段
-- 适用于校园众筹平台

-- 添加banned_at字段
ALTER TABLE ip_bans ADD COLUMN banned_at DATETIME DEFAULT CURRENT_TIMESTAMP;  -- 封禁时间

-- 提示：添加此字段后，可以考虑修改IPBan模型以包含banned_at字段
