#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

def print_file_info(file_path):
    print(f"\n{'='*80}")
    print(f"Checking file: {file_path}")
    print(f"File exists: {file_path.exists()}")
    
    if not file_path.exists():
        return
        
    try:
        # Read raw content first
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read(500)  # First 500 chars
            print(f"\nFirst 500 characters of file:")
            print("-" * 50)
            print(content)
            print("-" * 50)
            
        # Try to parse as JSON
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("\nJSON structure:")
        if isinstance(data, dict):
            print(f"Top-level keys: {list(data.keys())}")
            
            if 'horses' in data and isinstance(data['horses'], list):
                print(f"\nNumber of horses: {len(data['horses'])}")
                
                if data['horses']:
                    first_horse = data['horses'][0]
                    print("\nFirst horse keys:")
                    for i, key in enumerate(first_horse.keys(), 1):
                        print(f"  {i}. {key}")
                    
                    print("\nChecking required fields:")
                    required = ['name', 'auction_date', 'sire', 'dam', 'damsire']
                    for field in required:
                        exists = field in first_horse
                        value = first_horse.get(field, 'MISSING')
                        print(f"  {field}: {value} {'(MISSING)' if not exists else ''}")
        
    except json.JSONDecodeError as e:
        print(f"\nError decoding JSON: {e}")
    except Exception as e:
        print(f"\nError: {e}")

def main():
    # Check the main data file
    data_dir = Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data")
    main_file = data_dir / "horses.json"
    backup_file = data_dir / "horses.json.backup"
    
    print_file_info(main_file)
    
    if backup_file.exists():
        print_file_info(backup_file)

if __name__ == "__main__":
    main()
