#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
数据库结构迁移脚本
用于将数据库表结构更新至最新模型定义
"""

import pymysql
from config import config
import re

def migrate_database():
    # 获取数据库配置
    config_obj = config['development']
    db_url = config_obj.SQLALCHEMY_DATABASE_URI
    
    # 解析数据库连接信息
    match = re.match(r'mysql\+pymysql://([^:]+):([^@]+)@([^:]+):?(\d*)/(.+)', db_url)
    if not match:
        print('无法解析数据库连接信息')
        return False
        
    user, password, host, port_str, database = match.groups()
    port = int(port_str) if port_str else 3306  # 默认MySQL端口
    
    try:
        connection = pymysql.connect(
            host=host,
            port=port,
            user=user,
            password=password,
            database=database
        )
        
        with connection.cursor() as cursor:
            # 检查 admins 表是否包含 last_login_time 字段
            cursor.execute('DESCRIBE admins;')
            columns = [col[0] for col in cursor.fetchall()]
            
            if 'last_login_time' not in columns:
                print('正在为 admins 表添加 last_login_time 字段...')
                cursor.execute('ALTER TABLE admins ADD COLUMN last_login_time DATETIME NULL;')
                print('last_login_time 字段添加成功')
            else:
                print('last_login_time 字段已存在')
                
            # 检查 admins 表是否包含 login_attempts 字段
            if 'login_attempts' not in columns:
                print('正在为 admins 表添加 login_attempts 字段...')
                cursor.execute('ALTER TABLE admins ADD COLUMN login_attempts INT DEFAULT 0;')
                print('login_attempts 字段添加成功')
            else:
                print('login_attempts 字段已存在')
                
            # 检查 admins 表是否包含 is_active 字段
            if 'is_active' not in columns:
                print('正在为 admins 表添加 is_active 字段...')
                cursor.execute('ALTER TABLE admins ADD COLUMN is_active TINYINT(1) DEFAULT 1;')
                print('is_active 字段添加成功')
            else:
                print('is_active 字段已存在')
                
            # 检查 forum_replies 表是否包含 is_deleted 字段
            cursor.execute('DESCRIBE forum_replies;')
            reply_columns = [col[0] for col in cursor.fetchall()]
            
            if 'is_deleted' not in reply_columns:
                print('正在为 forum_replies 表添加 is_deleted 字段...')
                cursor.execute('ALTER TABLE forum_replies ADD COLUMN is_deleted TINYINT(1) DEFAULT 0;')
                print('is_deleted 字段添加成功')
            else:
                print('is_deleted 字段已存在')
            
            # 检查 forum_replies 表是否包含 _admin_reply 字段
            if '_admin_reply' not in reply_columns:
                print('正在为 forum_replies 表添加 _admin_reply 字段...')
                cursor.execute('ALTER TABLE forum_replies ADD COLUMN _admin_reply TINYINT(1) DEFAULT 0;')
                print('_admin_reply 字段添加成功')
            else:
                print('_admin_reply 字段已存在')
                
            connection.commit()
            print('数据库迁移完成！')
            return True
            
    except Exception as e:
        print(f'数据库迁移失败: {e}')
        return False

if __name__ == '__main__':
    print('开始数据库结构迁移...')
    success = migrate_database()
    if success:
        print('迁移成功完成！现在可以启动应用了。')
    else:
        print('迁移失败，请检查数据库连接和权限。')