"""
馬のオークション履歴をhorsesテーブルからauction_historiesテーブルに移行するスクリプト
"""
import os
import sys
from datetime import datetime
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.database.models import Base, Horse, AuctionHistory

def migrate_to_auction_histories():
    """horsesテーブルからauction_historiesテーブルにデータを移行する"""
    # データベース接続設定
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    
    # 環境変数からデータベースURLを取得
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("エラー: DATABASE_URLが設定されていません。")
        return
        
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    db = SessionLocal()
    
    try:
        # sold_price が設定されている馬を取得
        horses = db.query(Horse).filter(Horse.sold_price.isnot(None)).all()
        migrated_count = 0
        
        print(f"Found {len(horses)} horses with sold_price")
        
        for horse in horses:
            # 既存の auction_histories を確認
            existing = db.query(AuctionHistory).filter(
                AuctionHistory.horse_id == horse.id
            ).first()
            
            if not existing and horse.sold_price:
                # 新しい auction_history レコードを作成
                auction_history = AuctionHistory(
                    horse_id=horse.id,
                    auction_date=horse.auction_date or datetime.now().strftime('%Y-%m-%d'),
                    price=horse.sold_price,
                    seller=horse.seller or '不明',
                    buyer=None,
                    auction_house=horse.auction_house or '不明',
                    auction_name=horse.auction_name or '不明',
                    lot_number=None,
                    auction_url=horse.detail_url
                )
                db.add(auction_history)
                migrated_count += 1
                
                # 進捗表示
                if migrated_count % 100 == 0:
                    print(f"Migrated {migrated_count} records...")
        
        db.commit()
        print(f"Successfully migrated {migrated_count} records to auction_histories table")
        
    except Exception as e:
        db.rollback()
        print(f"Error during migration: {str(e)}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    print("Starting migration from horses to auction_histories...")
    migrate_to_auction_histories()
    print("Migration completed.")
