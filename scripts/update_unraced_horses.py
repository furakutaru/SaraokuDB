import os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
from backend.database.models import Base

# .envファイルから環境変数を読み込む
load_dotenv()

# データベース設定
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DB_PATH = os.path.join(BASE_DIR, 'data', 'horses.db')

# データベースディレクトリが存在しない場合は作成
os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)

# SQLiteデータベースのURLを設定
DATABASE_URL = f"sqlite:///{DB_PATH}"

# データベースエンジンを作成
engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False})

# セッションファクトリを作成
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# テーブルが存在しない場合は作成
Base.metadata.create_all(bind=engine)

def get_unraced_horses():
    """未出走の馬を検索する"""
    with SessionLocal() as session:
        # 未出走の馬を検索（race_recordが空またはnull）
        query = """
        SELECT id, name, race_record, image_url 
        FROM horses 
        WHERE (race_record IS NULL OR race_record = '')
        AND image_url IS NOT NULL
        """
        result = session.execute(text(query))
        return result.fetchall()

def update_horse_race_record(horse_id, race_record):
    """馬のレース成績を更新する"""
    with SessionLocal() as session:
        query = """
        UPDATE horses 
        SET race_record = :race_record,
            updated_at = CURRENT_TIMESTAMP
        WHERE id = :horse_id
        """
        session.execute(
            text(query),
            {"horse_id": horse_id, "race_record": race_record}
        )
        session.commit()

def main():
    print("未出走の馬を検索中...")
    unraced_horses = get_unraced_horses()
    
    if not unraced_horses:
        print("未出走の馬は見つかりませんでした。")
        return
    
    print(f"\n{len(unraced_horses)}頭の未出走馬が見つかりました。再スクレイピングを開始します...")
    
    scraper = RakutenAuctionScraper()
    
    for i, horse in enumerate(unraced_horses, 1):
        try:
            print(f"\n{i}/{len(unraced_horses)}: {horse.name} (ID: {horse.id})")
            print(f"詳細URL: {horse.detail_url}")
            
            # 詳細ページをスクレイピング
            detail_data = scraper.scrape_horse_detail(horse.detail_url)
            
            if not detail_data or 'race_record' not in detail_data:
                print("  → レース成績の取得に失敗しました")
                continue
                
            new_race_record = detail_data['race_record']
            print(f"  現在のレース成績: {horse.race_record}")
            print(f"  新しいレース成績: {new_race_record}")
            
            # レコードを更新
            update_horse_race_record(horse.id, new_race_record)
            print("  → レコードを更新しました")
            
        except Exception as e:
            print(f"  → エラーが発生しました: {e}")
            continue
    
    print("\n再スクレイピングが完了しました。")

if __name__ == "__main__":
    main()
