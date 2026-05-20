import os
import sys
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

sys.path.append(os.path.join(os.path.dirname(__file__), 'backend'))
load_dotenv(os.path.join(os.path.dirname(__file__), 'backend', '.env'))
from backend.database.models import Horse

DATABASE_URL = os.getenv("DATABASE_URL")
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(bind=engine)
db = SessionLocal()

horses = db.query(Horse).filter(Horse.name.like('%ン')).all()
fixed_count = 0
for h in horses:
    if h.name.endswith(' ン'):
        old_name = h.name
        new_name = h.name[:-2] # Remove ' ン'
        print(f"Fixing ID: {h.id}, Name: '{old_name}' -> '{new_name}'")
        h.name = new_name
        fixed_count += 1
    elif h.name.endswith('ン') and h.sex == 'セ':
        # Just in case there are names that ended with ン without space but should be fixed
        pass

if fixed_count > 0:
    print(f"Committing {fixed_count} changes to the database...")
    db.commit()
    print("Done!")
else:
    print("No horses needed fixing.")
db.close()
