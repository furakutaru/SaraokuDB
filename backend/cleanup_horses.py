import os
import sys
from sqlalchemy import create_engine, desc
from sqlalchemy.orm import sessionmaker
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database import Base, get_db
from backend.models.horse import Horse  # 馬のモデルをインポート

def cleanup_old_horses():
    # データベース接続の設定
    engine = create_engine('sqlite:///instance/horses.db')
    Session = sessionmaker(bind=engine)
    session = Session()

    try:
        # 最新の5頭のIDを取得
        latest_horses = session.query(Horse.id)\
            .order_by(desc(Horse.id))\
            .limit(5)\
            .all()
        
        latest_ids = [h[0] for h in latest_horses]
        
        if not latest_ids:
            print("削除する馬のデータはありません。")
            return
            
        # 最新の5頭以外の馬を削除
        result = session.query(Horse)\
            .filter(Horse.id.notin_(latest_ids))\
            .delete(synchronize_session=False)
        
        session.commit()
        print(f"{result}件の古い馬のデータを削除しました。")
        print(f"最新の馬ID: {', '.join(map(str, latest_ids))}")
        
    except Exception as e:
        session.rollback()
        print(f"エラーが発生しました: {e}")
    finally:
        session.close()

if __name__ == "__main__":
    print("古い馬のデータを削除します...")
    cleanup_old_horses()
