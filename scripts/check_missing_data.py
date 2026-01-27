import sys
import os
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Add the project root to the Python path
project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from backend.database.models import Base, Horse
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Database setup
DATABASE_URL = os.getenv("DATABASE_URL")
if not DATABASE_URL:
    print("DATABASE_URL is not set")
    sys.exit(1)

if DATABASE_URL.startswith('postgres') and 'sslmode=' not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def check_missing_data():
    db = SessionLocal()
    try:
        # Check for horses with missing race_record or total_prize_start
        # Exclude broodmares as they might have different data structure
        horses = db.query(Horse).filter(
            Horse.auction_id.isnot(None),
            Horse.is_broodmare == False
        ).all()
        
        missing_data_horses = []
        for horse in horses:
            is_missing = False
            reasons = []
            
            # Check race_record
            if not horse.race_record or horse.race_record == "null":
                is_missing = True
                reasons.append("race_record is missing")
            
            # Check total_prize_start
            # If it's None, it's definitely missing
            if horse.total_prize_start is None:
                is_missing = True
                reasons.append("total_prize_start is NULL")
            
            # Check image_url
            if not horse.image_url or horse.image_url == "null":
                is_missing = True
                reasons.append("image_url is missing")
            
            # If race_record exists, check if it looks complete
            if horse.race_record and horse.race_record != "null":
                try:
                    record_data = json.loads(horse.race_record) if isinstance(horse.race_record, str) else horse.race_record
                    # Add more specific checks if needed
                    # e.g., if total_races > 0 but total_prize_money is missing from record
                except Exception:
                     # Parse error implies bad data
                    is_missing = True
                    reasons.append("race_record corrupt")

            if is_missing:
                missing_data_horses.append({
                    "id": horse.id,
                    "auction_id": horse.auction_id,
                    "name": horse.name,
                    "reasons": reasons
                })
        
        print(f"Total horses checked: {len(horses)}")
        print(f"Horses with potential missing data: {len(missing_data_horses)}")
        
        output_file = "missing_data_horses.txt"
        with open(output_file, "w") as f:
            for h in missing_data_horses:
                print(f"ID: {h['id']}, Name: {h['name']}, AuctionID: {h['auction_id']}, Reasons: {', '.join(h['reasons'])}")
                if h['auction_id']:
                    f.write(f"{h['auction_id']}\n")
        
        print(f"\nSaved {len(missing_data_horses)} auction IDs to {output_file}")
        
    except Exception as e:
        print(f"Error: {e}")
    finally:
        db.close()

if __name__ == "__main__":
    check_missing_data()
