from app import create_app
from models import db, User, LostItem, FoundItem
from datetime import datetime, timedelta
import random

def init_sample_data():
    app = create_app('default')
    with app.app_context():
        # 检查是否已有数据
        if User.query.first() is not None:
            print("数据库中已有数据，跳过初始化")
            return
        
        # 创建示例用户
        users = []
        for i in range(5):
            user = User(
                username=f'user{i+1}',
                email=f'user{i+1}@example.com',
                phone=f'1380013800{i+1}',
                real_name=f'用户{i+1}'
            )
            user.set_password('password123')
            users.append(user)
            db.session.add(user)
        
        db.session.commit()
        
        # 创建示例失物信息
        lost_titles = ['校园卡', '钥匙', '水杯', '眼镜', '书包', '手机', '钱包', '雨伞']
        locations = ['图书馆', '教学楼A', '教学楼B', '食堂', '宿舍楼下', '操场', '实验室', '咖啡厅']
        
        for i in range(20):
            days_ago = random.randint(0, 6)
            lost_date = datetime.now() - timedelta(days=days_ago)
            
            lost_item = LostItem(
                title=random.choice(lost_titles),
                description=f'这是一条关于{random.choice(lost_titles)}的失物信息描述',
                category='日常用品',
                location=random.choice(locations),
                lost_time=lost_date,
                contact_person='联系人',
                contact_phone='13800138000',
                creator_id=random.choice(users).id,
                status='approved'  # 设置为已审核通过
            )
            db.session.add(lost_item)
        
        # 创建示例招领信息
        found_titles = ['校园卡', '钥匙', '水杯', '眼镜', '书包', '手机', '钱包', '雨伞']
        
        for i in range(15):
            days_ago = random.randint(0, 6)
            found_date = datetime.now() - timedelta(days=days_ago)
            
            found_item = FoundItem(
                title=random.choice(found_titles),
                description=f'这是一条关于{random.choice(found_titles)}的招领信息描述',
                category='日常用品',
                location=random.choice(locations),
                found_time=found_date,
                contact_person='联系人',
                contact_phone='13800138000',
                creator_id=random.choice(users).id,
                status='approved'  # 设置为已审核通过
            )
            db.session.add(found_item)
        
        db.session.commit()
        print("示例数据初始化完成")

if __name__ == '__main__':
    init_sample_data()