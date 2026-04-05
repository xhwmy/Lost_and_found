-- 为forum_posts表添加统计字段
-- 包括回复数、点赞数等统计信息

-- 添加回复数字段
ALTER TABLE forum_posts ADD COLUMN reply_count INT DEFAULT 0;

-- 添加点赞数字段
ALTER TABLE forum_posts ADD COLUMN like_count INT DEFAULT 0;