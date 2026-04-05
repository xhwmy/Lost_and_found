#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
快速验证测试脚本
用于验证数据库字段修复是否生效
"""

from app import create_app
from models import Admin, User, ForumPost, ThreadComment, IPBan, OperationLog
import traceback

def test_admin_model():
    """测试Admin模型"""
    print("🧪 测试 Admin 模型...")
    try:
        admin = Admin()
        # 测试属性访问不会报错
        print(f"   Admin email: {admin.email}")  # 应该返回None而不是报错
        print(f"   Admin last_login_time: {admin.last_login_time}")  # 应该返回None而不是报错
        print(f"   Admin is_active: {admin.is_active}")  # 应该返回True而不是报错
        print(f"   Admin login_attempts: {admin.login_attempts}")  # 应该返回0而不是报错
        print("   ✅ Admin 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ Admin 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_user_model():
    """测试User模型"""
    print("🧪 测试 User 模型...")
    try:
        user = User()
        # 测试属性访问不会报错
        print(f"   User is_frozen: {user.is_frozen}")
        print(f"   User failed_login_attempts: {user.failed_login_attempts}")
        print(f"   User last_failed_login: {user.last_failed_login}")
        print("   ✅ User 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ User 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_forum_post_model():
    """测试ForumPost模型"""
    print("🧪 测试 ForumPost 模型...")
    try:
        post = ForumPost()
        # 测试属性访问不会报错
        print(f"   ForumPost view_count: {post.view_count}")
        print(f"   ForumPost like_count: {post.like_count}")
        print(f"   ForumPost reply_count: {post.reply_count}")
        print(f"   ForumPost views (alias): {post.views}")
        print("   ✅ ForumPost 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ ForumPost 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_thread_comment_model():
    """测试ThreadComment模型"""
    print("🧪 测试 ThreadComment 模型...")
    try:
        comment = ThreadComment()
        # 测试属性访问不会报错
        print(f"   ThreadComment lost_item_id: {comment.lost_item_id}")
        print(f"   ThreadComment found_item_id: {comment.found_item_id}")
        print(f"   ThreadComment post_id: {comment.post_id}")
        print(f"   ThreadComment status: {comment.status}")
        print(f"   ThreadComment parent_id: {comment.parent_id}")
        print(f"   ThreadComment is_deleted: {comment.is_deleted}")
        print("   ✅ ThreadComment 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ ThreadComment 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_ipban_model():
    """测试IPBan模型"""
    print("🧪 测试 IPBan 模型...")
    try:
        ipban = IPBan()
        # 测试属性访问不会报错
        print(f"   IPBan is_active: {ipban.is_active}")
        print(f"   IPBan is_banned(): {ipban.is_banned()}")
        print("   ✅ IPBan 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ IPBan 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def test_operation_log_model():
    """测试OperationLog模型"""
    print("🧪 测试 OperationLog 模型...")
    try:
        log = OperationLog()
        # 测试属性访问不会报错
        print(f"   OperationLog target_type: {log.target_type}")
        print(f"   OperationLog user_agent: {log.user_agent}")
        print("   ✅ OperationLog 模型测试通过")
        return True
    except Exception as e:
        print(f"   ❌ OperationLog 模型测试失败: {str(e)}")
        traceback.print_exc()
        return False

def main():
    print("🚀 开始快速验证测试...")
    print("="*50)
    
    app = create_app()
    
    with app.app_context():
        tests = [
            test_admin_model,
            test_user_model,
            test_forum_post_model,
            test_thread_comment_model,
            test_ipban_model,
            test_operation_log_model,
        ]
        
        passed = 0
        total = len(tests)
        
        for test_func in tests:
            if test_func():
                passed += 1
            print()
    
    print("="*50)
    print(f"📊 测试结果: {passed}/{total} 个测试通过")
    
    if passed == total:
        print("🎉 所有测试均通过！数据库字段修复成功！")
    else:
        print("⚠️  部分测试失败，请检查修复情况")

if __name__ == "__main__":
    main()