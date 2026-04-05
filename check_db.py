from app import create_app

app = create_app('development')

with app.app_context():
    from models import db, ThreadComment, LostItem, FoundItem
    
    print("=== ThreadComment Table Structure ===")
    for column in ThreadComment.__table__.columns:
        print(f"{column.name}: {column.type}")
    
    print("\n=== LostItem Table Structure ===")
    for column in LostItem.__table__.columns:
        print(f"{column.name}: {column.type}")
    
    print("\n=== FoundItem Table Structure ===")
    for column in FoundItem.__table__.columns:
        print(f"{column.name}: {column.type}")
