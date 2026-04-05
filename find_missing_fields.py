#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
全面检查数据库字段一致性脚本
用于检测所有模型定义与数据库实际表结构之间的差异
"""

import os
import sys
import traceback
from sqlalchemy import text

# 添加项目根目录到Python路径
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def get_database_columns(connection, table_name):
    """获取数据库表中的实际列"""
    try:
        result = connection.execute(text(f"SHOW COLUMNS FROM {table_name}"))
        columns = [row[0] for row in result.fetchall()]
        return set(columns)
    except Exception as e:
        print(f"❌ 无法获取表 {table_name} 的列信息: {str(e)}")
        return set()

def get_model_columns(model_class):
    """获取模型类中定义的列"""
    columns = set()
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        if hasattr(attr, '__clause_element__'):  # 是SQLAlchemy列
            col = attr.__clause_element__()
            if hasattr(col, 'name'):
                columns.add(col.name)
    return columns

def get_model_properties(model_class):
    """获取模型类中定义的属性(property)"""
    properties = set()
    for attr_name in dir(model_class):
        attr = getattr(model_class, attr_name)
        if isinstance(attr, property):
            properties.add(attr_name)
    return properties

def check_model_consistency(app, model_class, table_name):
    """检查模型定义与数据库表结构的差异"""
    print(f"\n🔍 检查 {model_class.__name__} 模型 ({table_name})")
    print("-" * 60)
    
    with app.app_context():
        # 获取数据库中的列
        db_columns = get_database_columns(app.db.engine.connect(), table_name)
        print(f"📊 数据库中的列: {sorted(list(db_columns))}")
        
        # 获取模型定义的列
        model_columns = get_model_columns(model_class)
        print(f"📋 模型定义的列: {sorted(list(model_columns))}")
        
        # 获取模型中的属性
        model_properties = get_model_properties(model_class)
        print(f"⚙️  模型中的属性: {sorted(list(model_properties))}")
        
        # 找出模型中有但数据库中没有的列（缺失字段）
        missing_in_db = model_columns - db_columns
        if missing_in_db:
            print(f"\n❌ 数据库中缺失的字段: {sorted(list(missing_in_db))}")
            for field in sorted(missing_in_db):
                print(f"   • {field}")
        else:
            print(f"\n✅ 模型定义与数据库结构一致（字段层面）")
        
        # 找出数据库中有但模型中没有的列（多余字段）
        extra_in_db = db_columns - model_columns
        if extra_in_db:
            print(f"\n⚠️  数据库中多余的列: {sorted(list(extra_in_db))}")
            for field in sorted(extra_in_db):
                print(f"   • {field}")
        
        # 检查缺失字段是否有对应的property处理
        missing_with_property = set()
        missing_without_property = set()
        
        for field in missing_in_db:
            if field in model_properties:
                missing_with_property.add(field)
            else:
                missing_without_property.add(field)
        
        if missing_with_property:
            print(f"\n🛡️  有property保护的缺失字段: {sorted(list(missing_with_property))}")
        
        if missing_without_property:
            print(f"\n🚨 无property保护的缺失字段（需修复）: {sorted(list(missing_without_property))}")
            for field in sorted(missing_without_property):
                print(f"   • {field} - 需要在{model_class.__name__}模型中添加property装饰器")
        
        return {
            'model_columns': model_columns,
            'db_columns': db_columns,
            'missing_in_db': missing_in_db,
            'extra_in_db': extra_in_db,
            'missing_with_property': missing_with_property,
            'missing_without_property': missing_without_property
        }

def main():
    print("🔍 开始全面检查数据库字段一致性...")
    print("="*80)
    
    try:
        # 导入应用和模型
        from app import create_app
        from models import db, User, Admin, LostItem, FoundItem, Claim, ThreadComment, Favorite, Notification, ForumPost, ForumReply, Announcement, SecurityRule, IPBan, OperationLog
        
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
        total_missing_no_property = 0
        
        for model_class, table_name in models_to_check:
            try:
                result = check_model_consistency(app, model_class, table_name)
                all_results[model_class.__name__] = result
                total_missing_no_property += len(result['missing_without_property'])
            except Exception as e:
                print(f"❌ 检查 {model_class.__name__} 时出错: {str(e)}")
                traceback.print_exc()
        
        # 输出汇总报告
        print("\n" + "="*80)
        print("📊 汇总报告")
        print("="*80)
        
        problematic_models = []
        for model_name, result in all_results.items():
            missing_no_prop = len(result['missing_without_property'])
            if missing_no_prop > 0:
                problematic_models.append((model_name, missing_no_prop, result['missing_without_property']))
        
        if problematic_models:
            print(f"\n🚨 发现 {len(problematic_models)} 个模型存在问题，共 {total_missing_no_property} 个字段需要修复:")
            for model_name, count, fields in problematic_models:
                print(f"\n   🏷️  {model_name}: {count} 个缺失字段")
                for field in sorted(fields):
                    print(f"      • {field}")
        else:
            print(f"\n✅ 所有模型都已正确处理字段缺失问题！")
        
        # 统计总体情况
        total_model_fields = sum(len(result['model_columns']) for result in all_results.values())
        total_db_fields = sum(len(result['db_columns']) for result in all_results.values())
        total_missing = sum(len(result['missing_in_db']) for result in all_results.values())
        total_extra = sum(len(result['extra_in_db']) for result in all_results.values())
        
        print(f"\n📈 统计概览:")
        print(f"   • 总计模型字段: {total_model_fields}")
        print(f"   • 总计数据库字段: {total_db_fields}")
        print(f"   • 缺失字段总数: {total_missing}")
        print(f"   • 多余字段总数: {total_extra}")
        print(f"   • 需修复字段数: {total_missing_no_property}")
        
        # 提供修复建议
        if problematic_models:
            print(f"\n💡 修复建议:")
            print(f"   1. 为以下模型中的缺失字段添加property装饰器:")
            for model_name, count, fields in problematic_models:
                print(f"      • {model_name}: {', '.join(sorted(fields))}")
            print(f"   2. 参考现有property实现模式:")
            print(f"      @property")
            print(f"      def field_name(self):")
            print(f"          try:")
            print(f"              return getattr(self, '_field_name', default_value)")
            print(f"          except AttributeError:")
            print(f"              return default_value")
            print(f"      ")
            print(f"      @field_name.setter")
            print(f"      def field_name(self, value):")
            print(f"          try:")
            print(f"              setattr(self, '_field_name', value)")
            print(f"          except:")
            print(f"              pass  # 如果无法设置，忽略错误")
        else:
            print(f"\n🎉 所有模型字段一致性检查完成，无需进一步修复！")
    
    except ImportError as e:
        print(f"❌ 导入错误: {str(e)}")
        print("请确保在项目根目录下运行此脚本")
    except Exception as e:
        print(f"❌ 检查过程中发生错误: {str(e)}")
        traceback.print_exc()

if __name__ == "__main__":
    main()