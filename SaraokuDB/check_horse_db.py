import os
import sys
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("/Users/yum.ishii/SaraokuDB")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Force environment variables if needed
# os.environ["DATABASE_URL"] = "..."

from backend.database.models import SessionLocal, Horse, AuctionHistory
import json

db = SessionLocal()
try:
    # Check salvaged IDs
    salvage_ids = [str(i) for i in range(15560, 15575)]
    horses = db.query(Horse).filter(Horse.auction_id.in_(salvage_ids)).all()
    
    print(f"Checking salvaged horses (IDs 15560-15574): Found {len(horses)} horses")
    for h in horses:
        rr = json.loads(h.race_record) if h.race_record else {}
        prize = rr.get("total_prize_money", 0)
        print(f"Horse: {h.name} (AuctionID: {h.auction_id}) | Prize: {prize} | UpdateDue: {h.next_update_due_date}")
        
    # Check a specific horse like Folbelur (ID: 229 or name-based)
    folbelur = db.query(Horse).filter(Horse.name.like("%フォルベルール%")).first()
    if folbelur:
        print("\nChecking Folbelur:")
        rr = json.loads(folbelur.race_record) if folbelur.race_record else {}
        print(f"Name: {folbelur.name} | TotalPrize: {rr.get('total_prize_money')} | StartPrize: {folbelur.total_prize_start}")
    
finally:
    db.close()
