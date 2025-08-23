#!/usr/bin/env python3
"""
scraped_horses.json の馬の数をカウントするスクリプト
"""

import json
import os

def main():
    file_path = os.path.join(os.path.dirname(__file__), '..', 'scraped_horses.json')
    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"scraped_horses.json の馬の数: {len(data)}")
    
    # 各馬の名前を表示
    print("\n馬の一覧:")
    for i, horse in enumerate(data, 1):
        print(f"{i}. {horse.get('name', '名前不明')} (ID: {horse.get('id', 'N/A')})")

if __name__ == "__main__":
    main()
