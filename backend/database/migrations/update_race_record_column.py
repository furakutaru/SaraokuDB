from sqlalchemy import text
from database.models import engine

def upgrade():
    """Update race_record column to store JSON data"""
    with engine.connect() as conn:
        # SQLite doesn't support ALTER COLUMN to change type to JSON directly
        # So we'll create a new table, copy data, drop old table, and rename
        conn.execute(text("""
            CREATE TABLE horses_new (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                sex TEXT,
                age TEXT,
                sire VARCHAR(100),
                dam VARCHAR(100),
                dam_sire VARCHAR(100),
                race_record TEXT,  -- Will store JSON data
                weight INTEGER,
                total_prize_start FLOAT,
                total_prize_latest FLOAT,
                sold_price TEXT,
                auction_date TEXT,
                seller TEXT,
                disease_tags TEXT,
                comment TEXT,
                image_url VARCHAR(500),
                primary_image VARCHAR(500),
                unsold_count INTEGER DEFAULT 0,
                created_at DATETIME DEFAULT (datetime('now')),
                updated_at DATETIME DEFAULT (datetime('now'))
            )
        """))
        
        # Copy data from old table to new table
        conn.execute(text("""
            INSERT INTO horses_new (
                id, name, sex, age, sire, dam, dam_sire, race_record, 
                weight, total_prize_start, total_prize_latest, sold_price,
                auction_date, seller, disease_tags, comment, image_url,
                primary_image, unsold_count, created_at, updated_at
            )
            SELECT 
                id, name, sex, age, sire, dam, dam_sire,
                CASE 
                    WHEN race_record = '繁殖牝馬' THEN '{"status": "broodmare"}'
                    WHEN race_record = '未出走' THEN '{"status": "unraced"}'
                    ELSE json_object(
                        'status', 'active',
                        'summary', race_record
                    )
                END as race_record,
                weight, total_prize_start, total_prize_latest, sold_price,
                auction_date, seller, disease_tags, comment, image_url,
                primary_image, unsold_count, created_at, updated_at
            FROM horses
        """))
        
        # Drop old table and rename new one
        conn.execute(text("DROP TABLE horses"))
        conn.execute(text("ALTER TABLE horses_new RENAME TO horses"))
        
        # Recreate indexes if any (adjust as needed)
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_sire ON horses(sire)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_dam ON horses(dam)"))
        
        conn.commit()

def downgrade():
    """Revert the changes if needed"""
    with engine.connect() as conn:
        # Create a backup table with the old schema
        conn.execute(text("""
            CREATE TABLE horses_backup (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name VARCHAR(100) NOT NULL,
                sex TEXT,
                age TEXT,
                sire VARCHAR(100),
                dam VARCHAR(100),
                dam_sire VARCHAR(100),
                race_record VARCHAR(200),  -- Revert to string
                weight INTEGER,
                total_prize_start FLOAT,
                total_prize_latest FLOAT,
                sold_price TEXT,
                auction_date TEXT,
                seller TEXT,
                disease_tags TEXT,
                comment TEXT,
                image_url VARCHAR(500),
                primary_image VARCHAR(500),
                unsold_count INTEGER DEFAULT 0,
                created_at DATETIME,
                updated_at DATETIME
            )
        """))
        
        # Copy data back to old format
        conn.execute(text("""
            INSERT INTO horses_backup (
                id, name, sex, age, sire, dam, dam_sire, race_record, 
                weight, total_prize_start, total_prize_latest, sold_price,
                auction_date, seller, disease_tags, comment, image_url,
                primary_image, unsold_count, created_at, updated_at
            )
            SELECT 
                id, name, sex, age, sire, dam, dam_sire,
                CASE 
                    WHEN json_extract(race_record, '$.status') = 'broodmare' THEN '繁殖牝馬'
                    WHEN json_extract(race_record, '$.status') = 'unraced' THEN '未出走'
                    ELSE json_extract(race_record, '$.summary')
                END as race_record,
                weight, total_prize_start, total_prize_latest, sold_price,
                auction_date, seller, disease_tags, comment, image_url,
                primary_image, unsold_count, created_at, updated_at
            FROM horses
        """))
        
        # Drop the current table and rename backup
        conn.execute(text("DROP TABLE horses"))
        conn.execute(text("ALTER TABLE horses_backup RENAME TO horses"))
        
        # Recreate indexes
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_name ON horses(name)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_sire ON horses(sire)"))
        conn.execute(text("CREATE INDEX IF NOT EXISTS idx_horses_dam ON horses(dam)"))
        
        conn.commit()

if __name__ == "__main__":
    print("Running migration: update_race_record_column")
    upgrade()
    print("Migration completed successfully")
