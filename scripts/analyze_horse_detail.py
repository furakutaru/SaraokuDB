#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
from bs4 import BeautifulSoup
from pathlib import Path

def load_html_file(filepath):
    """HTMLファイルを読み込む"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return None

def analyze_html_structure(html_content):
    """HTMLの構造を解析する"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 1. ページの基本情報を表示
    print("\n=== ページ基本情報 ===")
    print(f"タイトル: {soup.title.string if soup.title else 'N/A'}")
    
    # 2. 馬名の要素を検索
    print("\n=== 馬名の候補 ===")
    name_selectors = ['h1', 'h2', 'h3', '.horseName', '.name', '.title', 'div.horseName']
    for selector in name_selectors:
        elements = soup.select(selector)
        for i, elem in enumerate(elements, 1):
            text = elem.get_text(strip=True)
            if text and len(text) < 50:  # 長すぎるテキストは除外
                print(f"セレクタ: {selector}, テキスト: {text}")
    
    # 3. 性別・年齢の要素を検索
    print("\n=== 性別・年齢の候補 ===")
    sex_age_selectors = ['.horseInfo', '.horse-detail', '.profile', '.info', 'table']
    for selector in sex_age_selectors:
        elements = soup.select(selector)
        for i, elem in enumerate(elements, 1):
            text = elem.get_text(' ', strip=True)
            if '牡' in text or '牝' in text or 'セ' in text or '歳' in text:
                print(f"\nセレクタ: {selector}")
                print(f"内容: {text[:200]}..." if len(text) > 200 else f"内容: {text}")
    
    # 4. 血統情報の要素を検索
    print("\n=== 血統情報の候補 ===")
    pedigree_keywords = ['父', '母', '母父', 'sire', 'dam', 'damsire']
    for text in soup.stripped_strings:
        if any(keyword in text for keyword in pedigree_keywords):
            print(f"血統情報候補: {text[:200]}..." if len(text) > 200 else f"血統情報候補: {text}")
    
    # 5. 画像URLの要素を検索
    print("\n=== 画像URLの候補 ===")
    img_selectors = ['img', '.horseImage', '.image', '.photo', 'div.horseImage']
    for selector in img_selectors:
        elements = soup.select(selector)
        for i, elem in enumerate(elements, 1):
            src = elem.get('src', '')
            if src and ('http' in src or 'data:image' in src):
                print(f"セレクタ: {selector}, 画像URL: {src[:100]}..." if len(src) > 100 else f"セレクタ: {selector}, 画像URL: {src}")
    
    # 6. 販売者情報の要素を検索
    print("\n=== 販売者情報の候補 ===")
    seller_keywords = ['販売申込者', '出品者', 'seller']
    for text in soup.stripped_strings:
        if any(keyword in text for keyword in seller_keywords):
            print(f"販売者情報候補: {text[:200]}..." if len(text) > 200 else f"販売者情報候補: {text}")
    
    # 7. テーブル構造の確認
    print("\n=== テーブル構造の確認 ===")
    tables = soup.find_all('table')
    for i, table in enumerate(tables, 1):
        print(f"\nテーブル {i}:")
        rows = table.find_all('tr')
        for row in rows[:5]:  # 最初の5行のみ表示
            cols = [col.get_text(strip=True) for col in row.find_all(['th', 'td'])]
            print(f"  - {' | '.join(cols)}")
        if len(rows) > 5:
            print(f"  ... 他 {len(rows)-5} 行 ...")

if __name__ == "__main__":
    # キャッシュディレクトリから最新のHTMLファイルを取得
    cache_dir = Path("cache")
    detail_pages = list(cache_dir.glob("**/details/*.html"))
    
    if not detail_pages:
        print("詳細ページのHTMLファイルが見つかりません。")
        print("キャッシュディレクトリ: ", cache_dir.absolute())
        exit(1)
    
    # 最初のHTMLファイルを解析
    html_file = detail_pages[0]
    print(f"\n{'='*80}")
    print(f"解析ファイル: {html_file}")
    print(f"{'='*80}")
    
    html_content = load_html_file(html_file)
    if html_content:
        analyze_html_structure(html_content)
    
    # 必要に応じて他のファイルも解析
    if len(detail_pages) > 1:
        print("\n" + "="*80)
        print("他のファイルも解析しますか？ (y/n): ")
        if input().lower() == 'y':
            for i in range(1, min(3, len(detail_pages))):  # 最大3ファイルまで
                print(f"\n{'='*80}")
                print(f"解析ファイル: {detail_pages[i]}")
                print(f"{'='*80}")
                html_content = load_html_file(detail_pages[i])
                if html_content:
                    analyze_html_structure(html_content)
