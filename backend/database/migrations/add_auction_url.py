from sqlalchemy import text
from database.models import engine
from datetime import datetime

def upgrade():
    with engine.connect() as conn:
        # Add auction_url column if it doesn't exist
        conn.execute(text("""
            ALTER TABLE horses 
            ADD COLUMN IF NOT EXISTS auction_url VARCHAR(500)
        "))
        print("Added auction_url column to horses table")
        
        # For existing data, we'll leave auction_url as NULL for now
        # It will be populated when the data is updated through the scraper
        
        conn.commit()

if __name__ == "__main__":
    print("Starting migration to add auction_url to horses table...")
    upgrade()
    print("Migration completed successfully")
