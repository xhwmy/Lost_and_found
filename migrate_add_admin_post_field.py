#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本：为forum_posts表添加is_admin_post字段
"""

from app import create_app
from models import db

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 添加is_admin_post字段
            with db.engine.connect() as conn:
                # 检查字段是否已存在
                result = conn.execute(db.text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'forum_posts' 
                    AND COLUMN_NAME = 'is_admin_post'
                """))
                column_exists = result.fetchone()[0]
                
                if not column_exists:
                    conn.execute(db.text('ALTER TABLE forum_posts ADD COLUMN is_admin_post TINYINT(1) DEFAULT 0;'))
                    conn.commit()
                    print('✅ 数据库字段 is_admin_post 添加成功')
                else:
                    print('⚠️  字段 is_admin_post 已存在，跳过添加')
        except Exception as e:
            print(f'❌ 数据库迁移失败: {str(e)}')
            raise

if __name__ == '__main__':
    migrate()