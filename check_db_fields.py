#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库字段一致性检查脚本
用于检测模型定义与数据库实际表结构之间的差异
"""

from app import create_app
from models import db, User, Admin, LostItem, FoundItem, Claim, ThreadComment, Favorite, Notification, ForumPost, ForumReply, Announcement, SecurityRule, IPBan, OperationLog
from sqlalchemy import text
import sys

def get_model_columns(model_class):
    """获取模型类中定义的列"""
    columns = {}
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        if hasattr(attr, '__clause_element__'):  # 是SQLAlchemy列
            col = attr.__clause_element__()
            if hasattr(col, 'name'):
                columns[col.name] = col
    return columns

def get_db_columns(table_name, connection):
    """获取数据库表中的实际列"""
    try:
        result = connection.execute(text(f"SHOW COLUMNS FROM {table_name}"))
        columns = {}
        for row in result.fetchall():
            col_name = row[0]  # 列名在第一个位置
            col_type = row[1]  # 类型在第二个位置
            columns[col_name] = {'type': col_type}
        return columns
    except Exception as e:
        print(f"❌ 无法获取表 {table_name} 的列信息: {str(e)}")
        return {}

def check_model_vs_db(app, model_class, table_name):
    """检查模型定义与数据库表结构的差异"""
    print(f"\n--- 检查 {model_class.__name__} 模型 ({table_name}) ---")
    
    with app.app_context():
        # 获取模型定义的列
        model_columns = get_model_columns(model_class)
        print(f"模型定义列: {list(model_columns.keys())}")
        
        # 获取数据库中的列
        db_columns = get_db_columns(table_name, db.engine.connect())
        print(f"数据库实际列: {list(db_columns.keys())}")
        
        # 找出模型中有但数据库中没有的列
        missing_in_db = set(model_columns.keys()) - set(db_columns.keys())
        if missing_in_db:
            print(f"❌ 数据库缺失列: {missing_in_db}")
        else:
            print("✅ 结构一致")
        
        # 找出数据库中有但模型中没有的列
        extra_in_db = set(db_columns.keys()) - set(model_columns.keys())
        if extra_in_db:
            print(f"ℹ️  数据库多余列: {extra_in_db}")
        
        return {
            'model_columns': set(model_columns.keys()),
            'db_columns': set(db_columns.keys()),
            'missing_in_db': missing_in_db,
            'extra_in_db': extra_in_db
        }

def main():
    print("🔍 开始检查数据库字段一致性...")
    
    app = create_app()
    
    # 定义所有模型及其对应的表名
    models_to_check = [
        (Admin, 'admins'),
        (User, 'users'),
        (LostItem, 'lost_items'),
        (FoundItem, 'found_items'),
        (Claim, 'claims'),
        (ThreadComment, 'thread_comments'),
        (Favorite, 'favorites'),
        (Notification, 'notifications'),
        (ForumPost, 'forum_posts'),
        (ForumReply, 'forum_replies'),
        (Announcement, 'announcements'),
        (SecurityRule, 'security_rules'),
        (IPBan, 'ip_bans'),
        (OperationLog, 'operation_logs'),
    ]
    
    all_results = {}
    total_issues = 0
    
    for model_class, table_name in models_to_check:
        try:
            result = check_model_vs_db(app, model_class, table_name)
            all_results[model_class.__name__] = result
            total_issues += len(result['missing_in_db'])
        except Exception as e:
            print(f"❌ 检查 {model_class.__name__} 时出错: {str(e)}")
    
    # 输出汇总报告
    print("\n" + "="*50)
    print("汇总报告")
    print("="*50)
    
    for model_name, result in all_results.items():
        missing_count = len(result['missing_in_db'])
        extra_count = len(result['extra_in_db'])
        
        if missing_count > 0:
            print(f"\n❌ {model_name}: 缺失 {missing_count} 个字段")
            for col in result['missing_in_db']:
                print(f"   - {col}")
        elif extra_count > 0:
            print(f"\n⚠️  {model_name}: 多余 {extra_count} 个字段")
        else:
            print(f"\n✅ {model_name}: 结构一致")
    
    print(f"\n总计发现问题: {total_issues} 个缺失字段")
    
    if total_issues > 0:
        print(f"\n修复建议:")
        print(f"- 使用 db_migrations/ 目录下的SQL脚本修复缺失字段")
    
    print(f"\n检查完成!")

if __name__ == "__main__":
    main()