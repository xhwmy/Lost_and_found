-- 数据库迁移脚本：为announcements表添加is_published字段
-- 适用于校园众筹平台

-- 添加is_published字段，默认值为true（向后兼容）
ALTER TABLE announcements ADD COLUMN is_published BOOLEAN DEFAULT 1;

-- 提示：添加此字段后，您可以考虑将user_views.py中的查询改回使用is_published过滤
-- 例如：Announcement.query.filter_by(is_published=True).order_by(...)

-- 完成数据库结构更新后，记得更新models.py中的Announcement模型
-- 添加如下字段定义：
-- is_published = db.Column(db.Boolean, default=True)  # 是否已发布
