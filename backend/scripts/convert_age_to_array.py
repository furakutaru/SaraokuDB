import os
import sys
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from backend.database.models import Horse, Base

# プロジェクトルートの絶対パスを取得
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
DB_PATH = os.path.join(BASE_DIR, 'data', 'horses.db')
DATABASE_URL = f"sqlite:///{DB_PATH}"

engine = create_engine(DATABASE_URL, echo=False)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def convert_age_to_array():
    session = SessionLocal()
    horses = session.query(Horse).all()
    changed = 0
    for horse in horses:
        age_val = horse.__dict__.get('age')
        if age_val is not None and age_val != '':
            try:
                # 既に配列ならスキップ
                val = json.loads(age_val)
                if isinstance(val, list):
                    continue
            except Exception:
                pass
            # 数値や文字列→配列化
            horse.__dict__['age'] = json.dumps([int(age_val)])
            changed += 1
    session.commit()
    print(f"変換完了: {changed}件のageを配列化しました。")
    session.close()

if __name__ == "__main__":
    convert_age_to_array() 