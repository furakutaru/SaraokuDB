#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import sys
from pathlib import Path

def check_file(file_path):
    """Check the structure of a JSON file"""
    try:
        print(f"\nChecking: {file_path}")
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print(f"Type: {type(data)}")
        
        if isinstance(data, dict):
            print("Top-level keys:", list(data.keys()))
            if 'horses' in data and isinstance(data['horses'], list):
                print(f"Number of horses: {len(data['horses'])}")
                if data['horses']:
                    print("First horse keys:", list(data['horses'][0].keys()))
        
        return True
    except Exception as e:
        print(f"Error reading {file_path}: {e}")
        return False

def main():
    # Check the main data file
    data_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"
    if not check_file(data_file):
        print("\nTrying to read raw file content...")
        try:
            with open(data_file, 'r', encoding='utf-8') as f:
                content = f.read(500)  # Read first 500 characters
                print(f"File content (first 500 chars):\n{content}")
        except Exception as e:
            print(f"Failed to read file: {e}")
    
    # Check backup file if exists
    backup_file = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json.backup"
    if Path(backup_file).exists():
        print("\nChecking backup file...")
        check_file(backup_file)

if __name__ == "__main__":
    main()
