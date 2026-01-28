from sqlalchemy.orm import Session
from backend.database.models import Horse, SessionLocal

def check_prize_status():
    db = SessionLocal()
    try:
        total = db.query(Horse).count()
        latest_null = db.query(Horse).filter(Horse.total_prize_latest == None).count()
        latest_zero = db.query(Horse).filter(Horse.total_prize_latest == 0).count()
        
        print(f"Total Horses: {total}")
        print(f"total_prize_latest is NULL: {latest_null}")
        print(f"total_prize_latest is 0: {latest_zero}")
        
    finally:
        db.close()

if __name__ == "__main__":
    check_prize_status()
