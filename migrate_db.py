#!/usr/bin/env python3
"""
数据库迁移脚本 - 确保数据库表结构正确
"""

from app import create_app
from models import db
from sqlalchemy import text

app = create_app('production')

with app.app_context():
    print("开始数据库迁移...")
    
    try:
        # 检查数据库类型
        dialect = db.engine.dialect.name
        print(f"数据库类型: {dialect}")
        
        # 检查users表的列
        if dialect == 'mysql':
            # MySQL语法
            result = db.session.execute(text("SHOW COLUMNS FROM users"))
            columns = [row[0] for row in result]
        else:
            # SQLite语法
            result = db.session.execute(text("PRAGMA table_info(users)"))
            columns = [row[1] for row in result]
        
        print(f"Users表当前列: {columns}")
        
        # 添加缺失的列
        if 'login_attempts' not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN login_attempts INTEGER DEFAULT 0"))
            print("Added login_attempts column to users table")
        
        if 'last_failed_login' not in columns:
            db.session.execute(text("ALTER TABLE users ADD COLUMN last_failed_login DATETIME"))
            print("Added last_failed_login column to users table")
        
        # 检查security_rules表
        try:
            if dialect == 'mysql':
                result = db.session.execute(text("SHOW COLUMNS FROM security_rules"))
                columns = [row[0] for row in result]
            else:
                result = db.session.execute(text("PRAGMA table_info(security_rules)"))
                columns = [row[1] for row in result]
            
            print(f"Security_rules表当前列: {columns}")
            
            if 'name' not in columns:
                db.session.execute(text("ALTER TABLE security_rules ADD COLUMN name VARCHAR(100) NOT NULL DEFAULT 'unnamed'"))
                print("Added name column to security_rules table")
            
            if 'is_active' not in columns:
                db.session.execute(text("ALTER TABLE security_rules ADD COLUMN is_active BOOLEAN DEFAULT TRUE"))
                print("Added is_active column to security_rules table")
        except Exception as e:
            print(f"Warning: Could not check security_rules table: {e}")
        
        # 提交更改
        db.session.commit()
        print("数据库迁移完成！")
        
    except Exception as e:
        print(f"Error during database migration: {e}")
        db.session.rollback()
