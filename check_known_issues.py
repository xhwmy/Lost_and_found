#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
检查已知的数据库字段缺失问题
"""

def check_model_properties():
    """检查模型中property定义的完整性"""
    
    # 读取models.py文件
    with open('models.py', 'r', encoding='utf-8') as f:
        content = f.read()
    
    print("🔍 检查模型中已知字段的property定义...")
    
    # 检查Admin模型
    print("\n📋 Admin模型字段检查:")
    admin_fields = ['email', 'real_name', 'role', 'last_login_time', 'is_active', 'login_attempts']
    for field in admin_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查User模型
    print("\n📋 User模型字段检查:")
    user_fields = ['is_frozen', 'failed_login_attempts', 'last_failed_login']
    for field in user_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查ForumPost模型
    print("\n📋 ForumPost模型字段检查:")
    forumpost_fields = ['author_name', 'user_id', 'view_count', 'like_count', 'reply_count', 'is_pinned', 'pin_order', 'views']
    for field in forumpost_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查ForumReply模型
    print("\n📋 ForumReply模型字段检查:")
    forumreply_fields = ['author_name']
    for field in forumreply_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查ThreadComment模型
    print("\n📋 ThreadComment模型字段检查:")
    threadcomment_fields = ['lost_item_id', 'found_item_id', 'post_id', 'status', 'parent_id', 'is_deleted']
    for field in threadcomment_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查IPBan模型
    print("\n📋 IPBan模型字段检查:")
    ipban_fields = ['is_active']
    for field in ipban_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查OperationLog模型
    print("\n📋 OperationLog模型字段检查:")
    operationlog_fields = ['target_type', 'target_id', 'user_agent']
    for field in operationlog_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查Favorite模型
    print("\n📋 Favorite模型字段检查:")
    favorite_fields = ['type']
    for field in favorite_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查Announcement模型
    print("\n📋 Announcement模型字段检查:")
    announcement_fields = ['author_id']
    for field in announcement_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")
    
    # 检查Claim模型
    print("\n📋 Claim模型字段检查:")
    claim_fields = ['reviewed_at', 'reviewer_id', 'review_note']
    for field in claim_fields:
        if f"@property\ndef {field}" in content or f"def {field}(self):" in content and f"getattr(self, '_{field}'" in content:
            print(f"   ✅ {field}: 已有property保护")
        else:
            print(f"   ❌ {field}: 缺少property保护")

def check_migration_scripts():
    """检查迁移脚本的存在性"""
    import os
    
    print("\n🔍 检查迁移脚本...")
    
    migration_scripts = [
        'fix_admin_dashboard_stats.sql',
        'add_missing_fields_to_admins.sql', 
        'add_author_name_to_forum_posts.sql',
        'add_author_name_to_forum_replies.sql',
        'add_stats_fields_to_forum_posts.sql',
        'add_user_id_to_forum_posts.sql',
        'add_pinned_fields_to_forum_posts.sql',
        'add_type_to_favorites.sql',
        'add_target_type_to_operation_logs.sql',
        'add_user_agent_to_operation_logs.sql',
        'add_missing_fields_to_operation_logs_v2.sql',
        'add_all_missing_fields_to_operation_logs.sql',
        'add_author_id_to_announcements.sql',
        'add_review_fields_to_claims.sql',
        'add_security_fields_to_users.sql',
        'add_banned_at_to_ip_bans.sql',
        'add_stats_fields_to_forum_posts_v2.sql',
        'add_security_fields_to_users_v2.sql',
        'add_is_active_to_ip_bans.sql',
        'add_association_fields_to_thread_comments.sql',
        'add_status_to_thread_comments.sql',
        'add_parent_id_to_thread_comments.sql',
        'add_is_deleted_to_thread_comments.sql'
    ]
    
    missing_scripts = []
    for script in migration_scripts:
        script_path = f'db_migrations/{script}'
        if os.path.exists(script_path):
            print(f"   ✅ {script}: 存在")
        else:
            print(f"   ❌ {script}: 缺失")
            missing_scripts.append(script)
    
    if missing_scripts:
        print(f"\n⚠️  发现 {len(missing_scripts)} 个缺失的迁移脚本:")
        for script in missing_scripts:
            print(f"      • {script}")

def main():
    print("🔍 全面检查数据库字段一致性问题")
    print("="*60)
    
    check_model_properties()
    check_migration_scripts()
    
    print("\n✅ 检查完成！")
    print("\n💡 提示：如果发现字段缺少property保护，需要为这些字段添加property装饰器")
    print("   以确保即使数据库中不存在这些字段，应用也能正常运行。")

if __name__ == "__main__":
    main()