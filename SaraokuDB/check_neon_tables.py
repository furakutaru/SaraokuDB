import os
import sys
from sqlalchemy import create_engine, inspect
from dotenv import load_dotenv

# Try to load .env from parent directory if not in current
if os.path.exists('.env'):
    load_dotenv('.env')
elif os.path.exists('../.env'):
    load_dotenv('../.env')

def check_database():
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        print("DATABASE_URL not found in .env")
        return

    # Helper to mask credentials
    masked_url = db_url.split('@')[1] if '@' in db_url else '...'
    print(f"Connecting to: ...@{masked_url}")
    
    try:
        # Create engine
        # Note: Neon uses postgresql:// but sqlalchemy might expect postgresql+psycopg2://
        # If the driver is not specified, it defaults to psycopg2.
        # If 'postgres://' is used, it might need 'postgresql://' replacement.
        if db_url.startswith("postgres://"):
            db_url = db_url.replace("postgres://", "postgresql://", 1)
            
        engine = create_engine(db_url)
        inspector = inspect(engine)
        tables = inspector.get_table_names()
        print("\nTables in database:")
        for table in tables:
            print(f"- {table}")
            try:
                print("  Columns:")
                for column in inspector.get_columns(table):
                    print(f"    - {column['name']}: {column['type']}")
            except Exception as e:
                 print(f"    Error inspecting columns: {e}")

    except Exception as e:
        print(f"Error connecting or inspecting: {e}")

if __name__ == "__main__":
    check_database()
