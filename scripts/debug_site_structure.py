#!/usr/bin/env python3
"""
実際のサイトのHTML構造を詳しく調査するデバッグスクリプト
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def debug_site_structure():
    """サイトのHTML構造を調査"""
    
    base_url = "https://auction.keiba.rakuten.co.jp/"
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("=== サイト構造調査 ===")
        print(f"ページタイトル: {soup.title.string if soup.title else 'N/A'}")
        
        # 馬のリンクを探す
        horse_links = []
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/item/' in href:
                link_text = link.get_text(strip=True)
                if (link_text and len(link_text) > 1 and 
                    '詳細血統表' not in link_text and 
                    '血統表' not in link_text and
                    '詳細' not in link_text):
                    if not href.startswith('http'):
                        href = base_url + href.lstrip('/')
                    horse_links.append({
                        'text': link_text,
                        'url': href
                    })
        
        print(f"\n馬のリンク数: {len(horse_links)}")
        
        # 最初の馬の詳細ページを調査
        if horse_links:
            first_horse = horse_links[0]
            print(f"\n=== {first_horse['text']}の詳細ページ調査 ===")
            
            detail_response = requests.get(first_horse['url'])
            detail_response.raise_for_status()
            
            detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
            page_text = detail_soup.get_text()
            
            print(f"詳細ページURL: {first_horse['url']}")
            print(f"ページテキスト長: {len(page_text)}文字")
            
            # 賞金関連のテキストを探す
            print("\n=== 賞金関連のテキスト ===")
            prize_patterns = [
                r'中央獲得賞金[：:]\s*([\d.]+)万円',
                r'地方獲得賞金[：:]\s*([\d.]+)万円',
                r'総賞金[：:]\s*([\d.]+)万円',
                r'獲得賞金[：:]\s*([\d.]+)万円',
                r'賞金[：:]\s*([\d.]+)万円',
                r'([\d.]+)万円.*賞金',
                r'賞金.*([\d.]+)万円'
            ]
            
            for pattern in prize_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    print(f"パターン '{pattern}': {matches}")
            
            # 落札価格関連のテキストを探す
            print("\n=== 落札価格関連のテキスト ===")
            price_patterns = [
                r'落札価格[：:]\s*([\d,]+)円',
                r'現在価格[：:]\s*([\d,]+)円',
                r'(\d{1,3}(?:,\d{3})*)円\(税込\s*(\d{1,3}(?:,\d{3})*)円\)',
                r'税込\s*(\d{1,3}(?:,\d{3})*)円',
                r'([\d,]+)円.*税込',
                r'税込.*([\d,]+)円'
            ]
            
            for pattern in price_patterns:
                matches = re.findall(pattern, page_text)
                if matches:
                    print(f"パターン '{pattern}': {matches}")
            
            # 成績関連のテキストを探す
            print("\n=== 成績関連のテキスト ===")
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
            
            # ページの一部を表示
            print("\n=== ページテキストの一部（最初の2000文字） ===")
            print(page_text[:2000])
            
            # HTMLの構造も確認
            print("\n=== HTML構造の一部 ===")
            main_content = detail_soup.find('main') or detail_soup.find('div', class_='content') or detail_soup.find('body')
            if main_content:
                print(main_content.prettify()[:1000])
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_site_structure() 