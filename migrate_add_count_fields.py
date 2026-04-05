#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
数据库迁移脚本：为forum_posts表添加统计字段（回复数、浏览量、点赞数）
"""

from app import create_app
from models import db

def migrate():
    app = create_app()
    with app.app_context():
        try:
            # 添加统计字段
            with db.engine.connect() as conn:
                # 检查reply_count字段是否已存在
                result = conn.execute(db.text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'forum_posts' 
                    AND COLUMN_NAME = 'reply_count'
                """))
                reply_count_exists = result.fetchone()[0]
                
                # 检查view_count字段是否已存在
                result = conn.execute(db.text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'forum_posts' 
                    AND COLUMN_NAME = 'view_count'
                """))
                view_count_exists = result.fetchone()[0]
                
                # 检查like_count字段是否已存在
                result = conn.execute(db.text("""
                    SELECT COUNT(*) 
                    FROM INFORMATION_SCHEMA.COLUMNS 
                    WHERE TABLE_SCHEMA = DATABASE() 
                    AND TABLE_NAME = 'forum_posts' 
                    AND COLUMN_NAME = 'like_count'
                """))
                like_count_exists = result.fetchone()[0]
                
                if not reply_count_exists:
                    conn.execute(db.text('ALTER TABLE forum_posts ADD COLUMN reply_count INT DEFAULT 0;'))
                    print('✅ 添加 reply_count 字段成功')
                else:
                    print('⚠️  reply_count 字段已存在，跳过添加')
                    
                if not view_count_exists:
                    conn.execute(db.text('ALTER TABLE forum_posts ADD COLUMN view_count INT DEFAULT 0;'))
                    print('✅ 添加 view_count 字段成功')
                else:
                    print('⚠️  view_count 字段已存在，跳过添加')
                    
                if not like_count_exists:
                    conn.execute(db.text('ALTER TABLE forum_posts ADD COLUMN like_count INT DEFAULT 0;'))
                    print('✅ 添加 like_count 字段成功')
                else:
                    print('⚠️  like_count 字段已存在，跳过添加')
                
                conn.commit()
                
                # 更新现有帖子的回复数
                result = conn.execute(db.text("""
                    UPDATE forum_posts fp 
                    SET reply_count = (
                        SELECT COUNT(*) 
                        FROM forum_replies fr 
                        WHERE fr.post_id = fp.id 
                        AND fr.is_deleted = 0
                    )
                """))
                print(f'✅ 更新了 {result.rowcount} 个帖子的回复数')
                
                # 更新现有帖子的浏览量
                conn.execute(db.text("""
                    UPDATE forum_posts fp 
                    SET view_count = 0  -- 初始化为0，后续通过实际访问更新
                """))
                print('✅ 初始化帖子浏览量')
                
        except Exception as e:
            print(f'❌ 数据库迁移失败: {str(e)}')
            raise

if __name__ == '__main__':
    migrate()