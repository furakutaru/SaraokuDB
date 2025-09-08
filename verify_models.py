import sys
import os
from sqlalchemy import create_engine, inspect, text
from sqlalchemy.orm import sessionmaker

def verify_models():
    print("=== データベースモデル検証ツール ===\n")
    
    # データベースのパスを確認
    db_path = '/Users/yum.ishii/SaraokuDB/backend/data/horses.db'
    db_url = f'sqlite:///{db_path}'
    
    print(f"データベースパス: {db_path}")
    print(f"データベースURL: {db_url}")
    print(f"ファイルの存在: {'あり' if os.path.exists(db_path) else 'なし'}\n")
    
    try:
        # データベースエンジンを作成
        engine = create_engine(db_url)
        print("✅ データベースに接続しました")
        
        # テーブル一覧を取得
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        
        if 'horses' not in tables:
            print("\n⚠️ 'horses' テーブルが見つかりません。作成を試みます...")
            
            # モデルをインポートしてテーブルを作成
            try:
                from backend.database.models import Base
                Base.metadata.create_all(engine)
                print("✅ 'horses' テーブルを作成しました")
                
                # テーブルを再確認
                inspector = inspect(engine)
                tables = inspector.get_table_names()
                
            except Exception as e:
                print(f"\n❌ テーブルの作成中にエラーが発生しました: {e}")
                return
        
        print("\n=== データベースのテーブル一覧 ===")
        for table in tables:
            print(f"\nテーブル: {table}")
            print("カラム:")
            for column in inspector.get_columns(table):
                print(f"  - {column['name']}: {column['type']}")
        
        # horses テーブルが存在するか確認
        if 'horses' in tables:
            print("\n✅ 'horses' テーブルが存在します")
            
            # サンプルデータを挿入してテスト
            try:
                with engine.connect() as conn:
                    # サンプルデータを挿入
                    sample_data = {
                        'name': 'テスト馬',
                        'sex': '["牡"]',
                        'age': '[3]',
                        'sire': 'テスト父',
                        'dam': 'テスト母',
                        'dam_sire': 'テスト母父',
                        'race_record': '{"starts": 5, "wins": 2}',
                        'weight': 450,
                        'total_prize_start': 10000000,
                        'total_prize_latest': 15000000,
                        'sold_price': '[12000000]',
                        'auction_date': '["2023-09-09"]',
                        'seller': '["テスト牧場"]',
                        'disease_tags': '[]',
                        'comment': '["テストコメント"]',
                        'image_url': 'http://example.com/image.jpg',
                        'primary_image': 'http://example.com/primary.jpg',
                        'unsold_count': 0
                    }
                    
                    # データを挿入
                    columns = ', '.join(sample_data.keys())
                    placeholders = ', '.join([f':{key}' for key in sample_data.keys()])
                    
                    # SQL文を作成してパラメータをバインド
                    stmt = text(f"""
                        INSERT INTO horses ({columns}) 
                        VALUES ({placeholders})
                    """)
                    
                    # パラメータを辞書形式で渡す
                    conn.execute(stmt, sample_data)
                    conn.commit()
                    
                    # データを取得して表示
                    result = conn.execute(text("SELECT * FROM horses")).fetchall()
                    print("\n✅ サンプルデータの挿入に成功しました")
                    print(f"\n=== サンプルデータ (全{len(result)}件) ===")
                    for row in result:
                        print("\nレコード:")
                        for key, value in row._mapping.items():
                            print(f"  {key}: {value}")
                            
            except Exception as e:
                print(f"\n❌ サンプルデータの挿入中にエラーが発生しました: {e}")
        
    except Exception as e:
        print(f"\n❌ データベース接続エラー: {e}")
        print("\nトラブルシューティングのヒント:")
        print("1. データベースファイルのパスを確認してください")
        print("2. データベースファイルの権限を確認してください")
        print("3. 必要に応じてデータベースファイルを削除して再作成してください")
        print(f"    rm {db_path}")

if __name__ == "__main__":
    verify_models()
