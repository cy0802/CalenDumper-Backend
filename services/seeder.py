from faker import Faker
from models import db, User, Note
import random
from datetime import datetime, timedelta

# 創建一個 Faker 實例
fake = Faker()

def seed_notes():
    # 手動創建一些用戶數據
    user1 = User(id="111", email="111@example.com", calendar_id="password123")
    user2 = User(id="222", email="222@example.com", calendar_id="password123")

    # 添加用戶到資料庫
    db.session.add(user1)
    db.session.add(user2)
    db.session.commit()  # 提交用戶數據

    print(f"Added users: {user1.id}, {user2.id}")
    # '''
    # 獲取所有用戶
    users = User.query.all()

    # 手動創建筆記數據
    for user in users:
        for _ in range(10):  # 每個用戶插入 10 條筆記
            # 隨機生成事件時間
            event_start = datetime.now() - timedelta(days=random.randint(1, 365))
            event_end = event_start + timedelta(hours=random.randint(1, 4))

            # 插入到 Note 模型中
            note = Note(
                user_id=user.id,
                event_id=str(random.randint(1000, 9999)),  # 假設你有事件 ID
                event_start=event_start,
                event_end=event_end,
                event_summary="某個事件",  # 手動定義事件摘要
                text="不嘻嘻",  # 手動定義事件描述
                picture="../famiy.jpg"  # 手動定義圖片路徑
            )

            # 添加到資料庫
            db.session.add(note)
    # '''
    # 提交所有變更到資料庫
    db.session.commit()
    print("Notes seeded successfully.")

    users = User.query.all()
    print(users)
