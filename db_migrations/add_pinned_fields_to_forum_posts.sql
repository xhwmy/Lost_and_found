-- 为forum_posts表添加置顶相关字段
-- 这些字段用于支持论坛帖子的置顶功能

ALTER TABLE forum_posts ADD COLUMN is_pinned BOOLEAN DEFAULT 0;  -- 是否置顶
ALTER TABLE forum_posts ADD COLUMN pin_order INTEGER DEFAULT 0;  -- 置顶顺序

-- 创建索引以提高置顶排序查询性能
CREATE INDEX IF NOT EXISTS idx_forum_posts_pinned_order ON forum_posts(is_pinned DESC, pin_order DESC, created_at DESC);