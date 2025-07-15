#!/usr/bin/env python3
"""
クレテイユの詳細ページを特別に調査するスクリプト
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def debug_creteuil_page():
    """クレテイユの詳細ページを調査"""
    
    base_url = "https://auction.keiba.rakuten.co.jp/"
    
    try:
        # まずトップページからクレテイユのリンクを探す
        response = requests.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # クレテイユのリンクを探す
        creteuil_url = None
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/item/' in href:
                link_text = link.get_text(strip=True)
                if 'クレテイユ' in link_text:
                    if not href.startswith('http'):
                        href = base_url + href.lstrip('/')
                    creteuil_url = href
                    break
        
        if not creteuil_url:
            print("クレテイユのリンクが見つかりませんでした")
            return
        
        print(f"クレテイユの詳細ページURL: {creteuil_url}")
        
        # クレテイユの詳細ページを取得
        detail_response = requests.get(creteuil_url)
        detail_response.raise_for_status()
        
        detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
        page_text = detail_soup.get_text()
        
        print(f"ページテキスト長: {len(page_text)}文字")
        
        # 賞金関連のテキストを詳しく探す
        print("\n=== 賞金関連のテキスト（詳細） ===")
        
        # より広範囲のパターンで賞金を探す
        prize_patterns = [
            r'中央獲得賞金[：:]\s*([\d.]+)万円',
            r'地方獲得賞金[：:]\s*([\d.]+)万円',
            r'総賞金[：:]\s*([\d.]+)万円',
            r'獲得賞金[：:]\s*([\d.]+)万円',
            r'賞金[：:]\s*([\d.]+)万円',
            r'([\d.]+)万円.*賞金',
            r'賞金.*([\d.]+)万円',
            r'([\d,]+)円.*賞金',
            r'賞金.*([\d,]+)円',
            r'([\d.]+)万円',
            r'([\d,]+)円'
        ]
        
        for pattern in prize_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}': {matches}")
        
        # 落札価格関連のテキストを詳しく探す
        print("\n=== 落札価格関連のテキスト（詳細） ===")
        price_patterns = [
            r'落札価格[：:]\s*([\d,]+)円',
            r'現在価格[：:]\s*([\d,]+)円',
            r'(\d{1,3}(?:,\d{3})*)円\(税込\s*(\d{1,3}(?:,\d{3})*)円\)',
            r'税込\s*(\d{1,3}(?:,\d{3})*)円',
            r'([\d,]+)円.*税込',
            r'税込.*([\d,]+)円',
            r'([\d,]+)円'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}': {matches}")
        
        # 成績関連のテキストを詳しく探す
        print("\n=== 成績関連のテキスト（詳細） ===")
        record_patterns = [
            r'通算成績[：:]\s*(\d+戦\d+勝［\d+-\d+-\d+-\d+］)',
            r'成績[：:]\s*(\d+戦\d+勝［\d+-\d+-\d+-\d+］)',
            r'(\d+戦\d+勝［\d+-\d+-\d+-\d+］)',
            r'(\d+戦\d+勝)',
            r'\[(\d+-\d+-\d+-\d+)\]'
        ]
        
        for pattern in record_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}': {matches}")
        
        # ページの一部を表示（賞金関連の部分を重点的に）
        print("\n=== ページテキストの一部（賞金関連を重点的に） ===")
        
        # 賞金が含まれる行を探す
        lines = page_text.split('\n')
        prize_lines = []
        for i, line in enumerate(lines):
            if '賞金' in line or '万円' in line or '円' in line:
                prize_lines.append(f"行{i+1}: {line.strip()}")
        
        for line in prize_lines[:20]:  # 最初の20行
            print(line)
        
        # 完全なページテキストも保存
        with open('creteuil_debug.txt', 'w', encoding='utf-8') as f:
            f.write(page_text)
        
        print(f"\n完全なページテキストを creteuil_debug.txt に保存しました")
        
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_creteuil_page() 