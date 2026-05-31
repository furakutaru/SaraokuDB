#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import unicodedata
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# Path setup
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
load_dotenv(os.path.join(os.path.dirname(__file__), '..', 'backend', '.env'))

from backend.database.models import Horse

# Safe clean name text function (matching our fixed improved_scraper.py)
def clean_name_text(raw_name: str) -> str:
    if not raw_name:
        return ""

    # Normalize to half-width first to ensure standard matching of age/digits
    name = unicodedata.normalize("NFKC", str(raw_name))
    name = name.strip().replace('\n', ' ')
    patterns = [
        r'※.*$', r'登録抹消.*$', r'新馬.*$', r'未出走.*$',
        r'\s+(?:セン|[牡牝セ])\s*(?:\d+|当)?\s*(?:歳|年)?',
        r'\(.*\)', r'\[.*\]'
    ]
    for pattern in patterns:
        name = re.sub(pattern, '', name)

    name = re.sub(r'\s+', ' ', name).strip()

    if name.endswith(' セン'):
        name = name[:-2].strip()

    return name or raw_name.strip()

def main():
    DATABASE_URL = os.getenv("DATABASE_URL")
    if not DATABASE_URL:
        print("Error: DATABASE_URL not found in .env")
        sys.exit(1)

    print(f"Connecting to database: {DATABASE_URL.split('@')[-1]}")
    engine = create_engine(DATABASE_URL)
    SessionLocal = sessionmaker(bind=engine)
    db = SessionLocal()

    try:
        # Fetch all horses that have a raw_name
        horses = db.query(Horse).filter(Horse.raw_name.isnot(None)).all()
        print(f"Fetched {len(horses)} horses with raw_name.")

        corrupted_horses = []
        for h in horses:
            correct_name = clean_name_text(h.raw_name)
            # Compare current name with correctly cleaned name
            if h.name != correct_name:
                corrupted_horses.append((h, correct_name))

        if not corrupted_horses:
            print("No corrupted horse names found! All horse names match their corrected normalization.")
            return

        print(f"\nFound {len(corrupted_horses)} horse names that need correction:")
        print("-" * 80)
        for h, correct_name in corrupted_horses:
            print(f"ID: {h.id:<5} | Raw: {h.raw_name:<30} | Current: {h.name:<20} -> Correct: {correct_name}")
        print("-" * 80)

        apply_changes = '--apply' in sys.argv
        if not apply_changes:
            confirm = input("\nDo you want to apply these corrections to the database? (yes/no): ").strip().lower()
            apply_changes = (confirm == 'yes')

        if apply_changes:
            print("Updating database...")
            for h, correct_name in corrupted_horses:
                h.name = correct_name
            db.commit()
            print("Database successfully updated and committed!")
        else:
            print("Database updates cancelled.")

    except Exception as e:
        print(f"An error occurred: {e}")
        db.rollback()
    finally:
        db.close()

if __name__ == "__main__":
    main()
