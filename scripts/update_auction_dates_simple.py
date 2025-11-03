#!/usr/bin/env python3
import json
import logging
import os
import sys
import re
from typing import List, Optional, Dict, Any

import psycopg2
from psycopg2.extras import DictCursor
from dotenv import load_dotenv

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Load environment variables
load_dotenv()
DATABASE_URL = os.getenv("DATABASE_URL")

if not DATABASE_URL:
    logger.error("DATABASE_URL environment variable is not set")
    sys.exit(1)

def extract_date(date_str: str) -> Optional[str]:
    """Extract date from various string formats."""
    if not date_str or not isinstance(date_str, str):
        return None
    
    # Check if it's already in YYYY-MM-DD format
    if re.match(r'^\d{4}-\d{2}-\d{2}$', date_str):
        return date_str
    
    # Try to extract date from JSON array format
    try:
        # Handle both '["2023-01-01"]' and "['2023-01-01']" formats
        date_str = date_str.strip()
        if date_str.startswith('['):
            dates = json.loads(date_str)
            if isinstance(dates, list) and dates:
                return str(dates[0])
    except (json.JSONDecodeError, IndexError, TypeError):
        pass
    
    # Try to find a date pattern in the string
    date_match = re.search(r'(\d{4}-\d{2}-\d{2})', date_str)
    if date_match:
        return date_match.group(1)
    
    return None

def update_auction_dates():
    """Update auction_date format to standard YYYY-MM-DD."""
    conn = None
    updated_count = 0
    error_count = 0
    
    try:
        # Connect to the database
        conn = psycopg2.connect(DATABASE_URL, sslmode='require')
        conn.autocommit = False
        cursor = conn.cursor()
        
        # Get all records where auction_date is not null
        cursor.execute("""
            SELECT id, auction_date 
            FROM horses 
            WHERE auction_date IS NOT NULL
            ORDER BY id;
        """)
        
        records = cursor.fetchall()
        total_records = len(records)
        logger.info(f"Found {total_records} records with auction dates to check.")
        
        for idx, (horse_id, auction_date) in enumerate(records, 1):
            try:
                # Skip if already in the correct format
                if auction_date and re.match(r'^\d{4}-\d{2}-\d{2}$', auction_date):
                    continue
                
                # Extract the date
                new_date = extract_date(auction_date)
                
                if not new_date:
                    logger.warning(f"Could not parse date for horse_id={horse_id}: {auction_date}")
                    error_count += 1
                    continue
                
                # Update the record
                cursor.execute(
                    """
                    UPDATE horses 
                    SET auction_date = %s 
                    WHERE id = %s
                    """,
                    (new_date, horse_id)
                )
                
                updated_count += 1
                if updated_count % 100 == 0:
                    logger.info(f"Updated {updated_count} records...")
                
            except Exception as e:
                logger.error(f"Error processing horse_id={horse_id}: {e}")
                error_count += 1
                continue
        
        # Commit all changes
        conn.commit()
        logger.info(f"Update complete. Updated {updated_count} records with {error_count} errors.")
        
    except Exception as e:
        logger.error(f"Database error: {e}")
        if conn:
            conn.rollback()
        raise
        
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    logger.info("Starting auction date format update...")
    update_auction_dates()
    logger.info("Script completed.")
