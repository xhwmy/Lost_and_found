from app import create_app
from models import db
from sqlalchemy import text

app = create_app('production')

with app.app_context():
    print("开始添加id_card_number字段...")
    
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
        
        # 检查是否存在id_card_number字段
        if 'id_card_number' not in columns:
            # 添加id_card_number字段
            db.session.execute(text("ALTER TABLE users ADD COLUMN id_card_number TEXT"))
            print('Added id_card_number column to users table')
        else:
            print('id_card_number column already exists')
        
        # 提交更改
        db.session.commit()
        print("添加id_card_number字段完成！")
        
    except Exception as e:
        print(f"Error during adding id_card_number field: {e}")
        db.session.rollback()

