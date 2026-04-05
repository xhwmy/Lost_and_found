-- 为forum_posts表添加author_name字段
-- 此字段用于存储匿名发布者名称

ALTER TABLE forum_posts ADD COLUMN author_name VARCHAR(100) NOT NULL DEFAULT 'Anonymous';

-- 如果需要，可以创建索引以提高按作者查询的性能
CREATE INDEX IF NOT EXISTS idx_forum_posts_author ON forum_posts(author_name);