#!/usr/bin/env python3
"""
添加数据库索引以优化查询性能
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from models import db, User, Admin, LostItem, FoundItem, Claim, ThreadComment, Favorite, Notification, ForumPost, ForumReply, IPBan, IPWhitelist, SecurityRule, OperationLog

def add_indexes():
    """添加数据库索引"""
    app = create_app('development')
    
    with app.app_context():
        # 检查数据库连接
        try:
            db.session.execute('SELECT 1')
            print("数据库连接成功")
        except Exception as e:
            print(f"数据库连接失败: {e}")
            return
        
        # 获取数据库引擎
        engine = db.engine
        
        # 定义要添加的索引
        indexes = [
            # User表索引
            ('users', 'idx_users_username', ['username']),
            ('users', 'idx_users_email', ['email']),
            
            # Admin表索引
            ('admins', 'idx_admins_username', ['username']),
            ('admins', 'idx_admins_email', ['email']),
            
            # LostItem表索引
            ('lost_items', 'idx_lost_items_creator_id', ['creator_id']),
            ('lost_items', 'idx_lost_items_status', ['status']),
            ('lost_items', 'idx_lost_items_created_at', ['created_at']),
            
            # FoundItem表索引
            ('found_items', 'idx_found_items_creator_id', ['creator_id']),
            ('found_items', 'idx_found_items_status', ['status']),
            ('found_items', 'idx_found_items_created_at', ['created_at']),
            
            # Claim表索引
            ('claims', 'idx_claims_user_id', ['user_id']),
            ('claims', 'idx_claims_lost_item_id', ['lost_item_id']),
            ('claims', 'idx_claims_found_item_id', ['found_item_id']),
            ('claims', 'idx_claims_status', ['status']),
            
            # ThreadComment表索引
            ('thread_comments', 'idx_thread_comments_user_id', ['user_id']),
            ('thread_comments', 'idx_thread_comments_post_id', ['post_id']),
            ('thread_comments', 'idx_thread_comments_lost_item_id', ['lost_item_id']),
            ('thread_comments', 'idx_thread_comments_found_item_id', ['found_item_id']),
            ('thread_comments', 'idx_thread_comments_parent_id', ['parent_id']),
            
            # Favorite表索引
            ('favorites', 'idx_favorites_user_id', ['user_id']),
            ('favorites', 'idx_favorites_type', ['type']),
            
            # Notification表索引
            ('notifications', 'idx_notifications_user_id', ['user_id']),
            ('notifications', 'idx_notifications_is_read', ['is_read']),
            
            # ForumPost表索引
            ('forum_posts', 'idx_forum_posts_user_id', ['user_id']),
            ('forum_posts', 'idx_forum_posts_category', ['category']),
            ('forum_posts', 'idx_forum_posts_is_pinned', ['is_pinned']),
            ('forum_posts', 'idx_forum_posts_created_at', ['created_at']),
            
            # ForumReply表索引
            ('forum_replies', 'idx_forum_replies_post_id', ['post_id']),
            ('forum_replies', 'idx_forum_replies_user_id', ['user_id']),
            
            # IPBan表索引
            ('ip_bans', 'idx_ip_bans_ip_address', ['ip_address']),
            ('ip_bans', 'idx_ip_bans_is_active', ['is_active']),
            
            # IPWhitelist表索引
            ('ip_whitelist', 'idx_ip_whitelist_ip_address', ['ip_address']),
            
            # SecurityRule表索引
            ('security_rules', 'idx_security_rules_type', ['type']),
            
            # OperationLog表索引
            ('operation_logs', 'idx_operation_logs_user_type', ['user_type']),
            ('operation_logs', 'idx_operation_logs_operation_type', ['operation_type']),
            ('operation_logs', 'idx_operation_logs_created_at', ['created_at']),
        ]
        
        # 添加索引
        for table_name, index_name, columns in indexes:
            try:
                # 检查索引是否存在
                result = engine.execute(f"SHOW INDEX FROM {table_name} WHERE Key_name = '{index_name}'")
                if result.fetchone():
                    print(f"索引 {index_name} 已存在，跳过")
                    continue
                
                # 构建索引创建语句
                columns_str = ', '.join(columns)
                sql = f"CREATE INDEX {index_name} ON {table_name} ({columns_str})"
                
                # 执行SQL语句
                engine.execute(sql)
                print(f"成功添加索引 {index_name} 到表 {table_name}")
            except Exception as e:
                print(f"添加索引 {index_name} 到表 {table_name} 失败: {e}")
        
        print("索引添加完成")

if __name__ == '__main__':
    add_indexes()