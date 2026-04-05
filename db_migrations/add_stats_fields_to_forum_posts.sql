-- 为forum_posts表添加统计相关字段
-- 这些字段用于支持帖子的浏览量、点赞数和回复数统计功能

ALTER TABLE forum_posts ADD COLUMN view_count INTEGER DEFAULT 0;  -- 浏览次数
ALTER TABLE forum_posts ADD COLUMN like_count INTEGER DEFAULT 0;  -- 点赞数
ALTER TABLE forum_posts ADD COLUMN reply_count INTEGER DEFAULT 0;  -- 回复数

-- 创建索引以提高统计查询性能
CREATE INDEX IF NOT EXISTS idx_forum_posts_stats ON forum_posts(view_count DESC, like_count DESC, reply_count DESC);