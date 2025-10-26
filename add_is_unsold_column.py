ipsql 'postgresql://neondb_owner:npg_PpdcmHfn73bl@ep-sweet-term-adm0rzzh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=require'postgresql://neondb_owner:npg_PpdcmHfn73bl@ep-sweet-term-adm0rzzh-pooler.c-2.us-east-1.aws.neon.tech/neondb?sslmode=require&channel_binding=requiremport os
import sys
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# データベース接続設定
# 以下の値を実際のデータベース接続情報に置き換えてください
DATABASE_URL = "postgresql://your_username:your_password@localhost/your_database"

def add_is_unsold_column():
    # データベースエンジンを作成
    engine = create_engine(DATABASE_URL)
    Session = sessionmaker(bind=engine)
    session = Session()
    
    try:
        # auction_histories テーブルに is_unsold カラムが存在するか確認
        check_column = """
        SELECT column_name 
        FROM information_schema.columns 
        WHERE table_name='auction_histories' AND column_name='is_unsold'
        """
        result = session.execute(text(check_column)).fetchone()
        
        if not result:
            # is_unsold カラムを追加
            print("Adding is_unsold column to auction_histories table...")
            alter_table = """
            ALTER TABLE auction_histories 
            ADD COLUMN is_unsold BOOLEAN DEFAULT FALSE
            """
            session.execute(text(alter_table))
            session.commit()
            print("Successfully added is_unsold column.")
        else:
            print("is_unsold column already exists.")
            
    except Exception as e:
        print(f"An error occurred: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    add_is_unsold_column()
