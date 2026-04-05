-- 为favorites表添加type字段以支持不同类型的收藏
-- 注意：此字段目前不在模型中使用，但为将来扩展保留

ALTER TABLE favorites ADD COLUMN type VARCHAR(20) DEFAULT NULL;

-- 更新现有记录的type值基于现有的外键
UPDATE favorites SET type = 'lost_item' WHERE lost_item_id IS NOT NULL;
UPDATE favorites SET type = 'found_item' WHERE found_item_id IS NOT NULL;
UPDATE favorites SET type = 'post' WHERE post_id IS NOT NULL;

-- 如果需要，可以创建索引以提高查询性能
CREATE INDEX IF NOT EXISTS idx_favorites_user_type ON favorites(user_id, type);