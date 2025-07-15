import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Horse, Base
from sqlalchemy.inspection import inspect

# プロジェクトルートの絶対パスを取得
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'horses.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def convert_auction_date_to_array():
    session = SessionLocal()
    horses = session.query(Horse).all()
    changed = 0
    for horse in horses:
        # インスタンス属性として値を取得
        auction_date_val = horse.__dict__.get('auction_date')
        if auction_date_val:
            try:
                val = json.loads(auction_date_val)
                if isinstance(val, list):
                    continue
            except Exception:
                pass
            # 文字列→配列化
            horse.__dict__['auction_date'] = json.dumps([auction_date_val])
            changed += 1
    session.commit()
    print(f"変換完了: {changed}件のauction_dateを配列化しました。")
    session.close()

if __name__ == "__main__":
    convert_auction_date_to_array() 