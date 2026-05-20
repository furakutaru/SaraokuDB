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
for h in horses:
    if h.name.endswith(' ン'):
        print(f"ID: {h.id}, Name: '{h.name}', Sex: {h.sex}")
