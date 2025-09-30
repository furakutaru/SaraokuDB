#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from pathlib import Path

def read_file_contents(file_path):
    print(f"\nReading: {file_path}")
    print("=" * 50)
    
    try:
        # ファイルの存在確認
        if not file_path.exists():
            print(f"Error: File not found: {file_path}")
            return
            
        # ファイルサイズの確認
        file_size = file_path.stat().st_size
        print(f"File size: {file_size} bytes")
        
        # ファイルの内容を読み込む
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            print("\nFirst 500 characters:")
            print("-" * 50)
            print(content[:500])
            print("-" * 50)
            
    except Exception as e:
        print(f"\nError reading file: {e}")

def main():
    # 確認するファイルパス
    target_files = [
        Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"),
        Path("/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json.backup"),
        Path("/Users/yum.ishii/SaraokuDB/backend/data/horses.json")
    ]
    
    for file_path in target_files:
        read_file_contents(file_path)
        print("\n" + "="*50 + "\n")

if __name__ == "__main__":
    main()
