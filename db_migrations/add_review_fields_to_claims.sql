-- 数据库迁移脚本：为claims表添加审核相关字段
-- 适用于校园众筹平台

-- 添加审核相关字段
ALTER TABLE claims ADD COLUMN reviewed_at DATETIME NULL;           -- 审核时间
ALTER TABLE claims ADD COLUMN reviewer_id INT NULL;                -- 审核管理员ID
ALTER TABLE claims ADD COLUMN review_note TEXT NULL;               -- 审核备注

-- 添加外键约束（可选）
-- ALTER TABLE claims ADD CONSTRAINT fk_claims_reviewer FOREIGN KEY (reviewer_id) REFERENCES admins(id);

-- 提示：添加这些字段后，记得将它们重新添加到models.py中的Claim模型
-- 添加如下字段定义：
-- reviewed_at = db.Column(db.DateTime)  # 审核时间
-- reviewer_id = db.Column(db.Integer, db.ForeignKey('admins.id'))  # 审核管理员
-- review_note = db.Column(db.Text)  # 审核备注
-- reviewer = db.relationship('Admin', backref='claims_reviewed')
