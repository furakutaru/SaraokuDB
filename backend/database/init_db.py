import os
from backend.database.models import Base, engine

def init_database():
    """データベースとテーブルを作成する"""
    # dataディレクトリが存在しない場合は作成
    os.makedirs("data", exist_ok=True)
    
    # テーブルを作成
    Base.metadata.create_all(bind=engine)
    print("データベースが正常に初期化されました。")

if __name__ == "__main__":
    init_database() 