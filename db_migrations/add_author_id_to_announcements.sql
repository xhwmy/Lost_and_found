-- 数据库迁移脚本：为announcements表添加author_id字段
-- 适用于校园众筹平台

-- 添加author_id字段，关联到admins表
ALTER TABLE announcements ADD COLUMN author_id INT NOT NULL DEFAULT 1;  -- 默认为第一个管理员

-- 添加外键约束（可选）
-- ALTER TABLE announcements ADD CONSTRAINT fk_announcements_admin FOREIGN KEY (author_id) REFERENCES admins(id);

-- 同时需要确保表中已有的记录有适当的author_id值
-- UPDATE announcements SET author_id = 1 WHERE author_id IS NULL OR author_id = 0;

-- 提示：添加此字段后，记得更新models.py中的Announcement模型
-- 添加如下字段定义：
-- author_id = db.Column(db.Integer, db.ForeignKey('admins.id'), nullable=False)
-- author = db.relationship('Admin', backref='announcements')
