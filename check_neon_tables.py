import os
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

load_dotenv()

def check_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    print(f"Connecting to: {db_url.split('@')[1] if '@' in db_url else '...'} ...") # Hide credentials
    
    try:
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table}")
            print("  Columns:")
            for column in inspector.get_columns(table):
                print(f"    - {column['name']}: {column['type']}")
                
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    check_database()
