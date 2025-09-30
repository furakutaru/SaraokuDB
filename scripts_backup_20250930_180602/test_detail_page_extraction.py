#!/usr/bin/env python3
# -*- coding: utf-8

import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup
import re

# テスト対象のモジュールをインポート
sys.path.insert(0, str(Path(__file__).parent))
from components.horse_info_extractor import HorseInfoExtractor

def test_detail_page_extraction(html_file_path):
    """詳細ページのHTMLファイルから性別と年齢を抽出するテスト"""
    print(f"\n{'='*80}")
    print(f"Testing file: {html_file_path}")
    print(f"{'='*80}")
    
    # HTMLファイルを読み込む
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 抽出器を初期化
    extractor = HorseInfoExtractor()
    
    # 性別と年齢を抽出
    result = extractor._extract_sex_and_age(soup)
    
    # 結果を表示
    print("\nExtraction Results:")
    print(f"Sex: {result.get('sex')}")
    print(f"Age: {result.get('age')}")
    
    # タイトルを表示
    title = soup.title.string if soup.title else ""
    print(f"\nTitle: {title}")
    
    # 本文から性別と年齢が含まれていると思われる部分を表示
    content = soup.get_text(' ', strip=True)
    print("\nContent snippet with potential age/sex info:")
    print(content[:500] + "..." if len(content) > 500 else content)

if __name__ == '__main__':
    # テストするHTMLファイルのパスを指定
    test_dir = Path('/Users/yum.ishii/SaraokuDB/cache/20250822_190555/details')
    
    # 最初のHTMLファイルでテスト
    html_files = list(test_dir.glob('*.html'))
    if html_files:
        test_detail_page_extraction(html_files[0])
    else:
        print("No HTML files found in the test directory")
