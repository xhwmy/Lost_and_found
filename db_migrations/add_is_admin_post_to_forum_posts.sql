-- 为forum_posts表添加is_admin_post字段
-- 此字段用于标识帖子是否由管理员发布

ALTER TABLE forum_posts ADD COLUMN is_admin_post TINYINT(1) DEFAULT 0;

-- 为该字段添加注释（如果数据库支持）
-- COMMENT ON COLUMN forum_posts.is_admin_post IS '是否为管理员发布的帖子，1-是，0-否';