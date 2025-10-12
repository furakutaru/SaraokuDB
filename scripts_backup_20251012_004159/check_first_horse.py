#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json

def main():
    file_path = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if 'horses' in data and data['horses']:
            first_horse = data['horses'][0]
            print("First horse data structure:")
            for key, value in first_horse.items():
                print(f"{key}: {value}")
            
            # Check for required fields
            required_fields = ['name', 'auction_date', 'sire', 'dam', 'damsire']
            print("\nChecking required fields:")
            for field in required_fields:
                exists = field in first_horse
                print(f"{field}: {'✓' if exists else '✗'}")
        else:
            print("No horse data found in the file.")
            
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
