#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
from pathlib import Path

def check_data_structure(file_path):
    """Check the structure of the horse data file"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"\nChecking file: {file_path}")
        print("=" * 50)
        
        # Check top-level keys
        print("Top-level keys:", list(data.keys()))
        
        # Check horses data
        if 'horses' in data and isinstance(data['horses'], list):
            print(f"Number of horses: {len(data['horses'])}")
            if data['horses']:
                first_horse = data['horses'][0]
                print("\nFirst horse keys:", list(first_horse.keys()))
                print("\nFirst horse data:")
                for key, value in first_horse.items():
                    print(f"{key}: {value}")
        else:
            print("No 'horses' list found in the data")
            
    except Exception as e:
        print(f"Error checking {file_path}: {e}")

if __name__ == "__main__":
    # Check the main data file
    data_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"
    check_data_structure(data_file)
    
    # Also check the backup file if it exists
    backup_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json.backup"
    if Path(backup_file).exists():
        print("\n" + "="*50)
        check_data_structure(backup_file)
