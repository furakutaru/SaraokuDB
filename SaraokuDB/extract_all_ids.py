import sys
import os
from pathlib import Path

# Add project root to sys.path
PROJECT_ROOT = Path("/Users/yum.ishii/SaraokuDB")
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# Ensure database models are loaded correctly
from backend.database.models import SessionLocal, Horse

db = SessionLocal()
try:
    # Extract non-empty auction IDs
    ids = [str(h.auction_id) for h in db.query(Horse).order_by(Horse.auction_id.desc()).all() if h.auction_id]
    output_path = "/Users/yum.ishii/SaraokuDB/SaraokuDB/all_auction_ids.txt"
    with open(output_path, "w", encoding="utf-8") as f:
        f.write("\n".join(ids))
    print(f"Total IDs extracted: {len(ids)}")
    print(f"Output saved to: {output_path}")
finally:
    db.close()
