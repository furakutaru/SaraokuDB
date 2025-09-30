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

def test_top_page_extraction(html_file_path):
    """トップページのHTMLファイルから性別と年齢を抽出するテスト"""
    print(f"\n{'='*80}")
    print(f"Testing file: {html_file_path}")
    print(f"{'='*80}")
    
    # HTMLファイルを読み込む
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬のカード要素を取得（最初の1つ）
    horse_cards = soup.select('.horseCard')
    if not horse_cards:
        print("No horse cards found in the HTML")
        return
    
    # 抽出器を初期化
    extractor = HorseInfoExtractor()
    
    # 性別と年齢を抽出
    result = extractor._extract_sex_and_age(horse_cards[0])
    
    # 結果を表示
    print("\nExtraction Results:")
    print(f"Sex: {result.get('sex')}")
    print(f"Age: {result.get('age')}")
    
    # カードの内容を一部表示
    print("\nHorse card HTML snippet:")
    print(str(horse_cards[0])[:500] + "..." if len(str(horse_cards[0])) > 500 else str(horse_cards[0]))

if __name__ == '__main__':
    # テストするHTMLファイルのパスを指定
    test_file = Path('/Users/yum.ishii/SaraokuDB/cache/20250822_190555/list.html')
    
    if test_file.exists():
        test_top_page_extraction(test_file)
    else:
        print(f"Test file not found: {test_file}")
        print("Please update the test file path in the script.")
