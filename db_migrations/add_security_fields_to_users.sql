-- 数据库迁移脚本：为users表添加安全相关字段
-- 适用于校园众筹平台

-- 添加安全相关字段
ALTER TABLE users ADD COLUMN is_frozen BOOLEAN DEFAULT FALSE;           -- 账户冻结状态
ALTER TABLE users ADD COLUMN freeze_reason VARCHAR(200);                -- 冻结原因
ALTER TABLE users ADD COLUMN frozen_until DATETIME;                     -- 冻结截止时间
ALTER TABLE users ADD COLUMN last_login_ip VARCHAR(45);                 -- 最后登录IP
ALTER TABLE users ADD COLUMN security_level INT DEFAULT 1;              -- 安全等级
ALTER TABLE users ADD COLUMN _real_name VARCHAR(100);                   -- 加密的真实姓名
ALTER TABLE users ADD COLUMN _phone VARCHAR(50);                        -- 加密的电话号码
ALTER TABLE users ADD COLUMN _student_id VARCHAR(50);                   -- 加密的学号

-- 提示：添加这些字段后，记得将它们保留在models.py中的User模型
-- 注意：real_name, phone, student_id 是通过属性访问器实现加密/解密的
