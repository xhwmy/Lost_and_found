-- 为forum_posts表添加user_id字段
-- 此字段用于关联发布帖子的用户

ALTER TABLE forum_posts ADD COLUMN user_id INTEGER;  -- 关联用户ID

-- 创建索引以提高按用户查询的性能
CREATE INDEX IF NOT EXISTS idx_forum_posts_user ON forum_posts(user_id);

-- 可选：如果需要，也可以添加外键约束（取决于具体需求）
-- ALTER TABLE forum_posts ADD CONSTRAINT fk_forum_posts_user FOREIGN KEY (user_id) REFERENCES users(id);