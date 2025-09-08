import sys
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker

print('Python version:', sys.version)
print('SQLAlchemy version:', __import__('sqlalchemy').__version__)

# データベースエンジンを作成
DATABASE_URL = 'sqlite:////Users/yum.ishii/SaraokuDB/backend/data/horses.db'
engine = create_engine(DATABASE_URL, echo=True)
print('Engine created')

# ベースクラスを作成
Base = declarative_base()
print('Base created')

# テスト用のテーブルを定義
class TestTable(Base):
    __tablename__ = 'test_table'
    id = Column(Integer, primary_key=True)
    name = Column(String(50))
    value = Column(Integer)

print('Class defined')

# テーブルを作成
Base.metadata.create_all(engine)
print('Tables created')

# セッションを作成
Session = sessionmaker(bind=engine)
session = Session()

# テストデータを挿入
try:
    test_record = TestTable(name='test', value=42)
    session.add(test_record)
    session.commit()
    print('Test record inserted')
    
    # データを取得して表示
    result = session.query(TestTable).all()
    print('Records in test_table:')
    for row in result:
        print(f'ID: {row.id}, Name: {row.name}, Value: {row.value}')
        
except Exception as e:
    print(f'Error: {e}')
    session.rollback()
    
finally:
    session.close()
