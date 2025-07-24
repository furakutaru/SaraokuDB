#!/usr/bin/env python3
"""
クレテイユの詳細ページのHTML構造を調査するデバッグスクリプト
"""

import requests
from bs4 import BeautifulSoup
import re
import json

def debug_creteuil_page():
    """クレテイユの詳細ページを調査"""
    
    # クレテイユの詳細ページURL（実際のURLに置き換える必要があります）
    # 楽天オークションのクレテイユの詳細ページを探す
    base_url = "https://auction.keiba.rakuten.co.jp/"
    
    # まずトップページからクレテイユを探す
    print("トップページからクレテイユを検索中...")
    
    try:
        response = requests.get(base_url)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # クレテイユのリンクを探す
        creteuil_links = []
        
        # すべてのリンクをチェック
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True)
            if 'クレテイユ' in link_text:
                href = link.get('href')
                if href:
                    if not href.startswith('http'):
                        href = base_url + href.lstrip('/')
                    creteuil_links.append({
                        'text': link_text,
                        'url': href
                    })
        
        print(f"クレテイユのリンクを{len(creteuil_links)}個発見:")
        for i, link in enumerate(creteuil_links):
            print(f"{i+1}. {link['text']} -> {link['url']}")
        
        if not creteuil_links:
            print("クレテイユのリンクが見つかりませんでした。")
            print("ページ全体のテキストを確認します...")
            
            # ページ全体のテキストを確認
            page_text = soup.get_text()
            if 'クレテイユ' in page_text:
                print("クレテイユの名前がページ内に存在します")
                
                # クレテイユ周辺のテキストを抽出
                lines = page_text.split('\n')
                for i, line in enumerate(lines):
                    if 'クレテイユ' in line:
                        print(f"行 {i+1}: {line.strip()}")
                        # 前後の行も表示
                        for j in range(max(0, i-2), min(len(lines), i+3)):
                            if j != i:
                                print(f"  行 {j+1}: {lines[j].strip()}")
            else:
                print("クレテイユの名前がページ内に見つかりませんでした")
            
            return
        
        # 最初のリンクの詳細ページを調査
        detail_url = creteuil_links[0]['url']
        print(f"\n詳細ページを調査中: {detail_url}")
        
        detail_response = requests.get(detail_url)
        detail_response.raise_for_status()
        
        detail_soup = BeautifulSoup(detail_response.content, 'html.parser')
        
        # ページ全体のテキストを取得
        page_text = detail_soup.get_text()
        
        print("\n=== ページ全体のテキスト ===")
        print(page_text[:2000] + "..." if len(page_text) > 2000 else page_text)
        
        # 落札価格に関連する部分を探す
        print("\n=== 落札価格関連の検索 ===")
        
        # 様々なパターンで落札価格を探す
        price_patterns = [
            r'落札価格[^\d]*([\d,]+)円',
            r'税込[^\d]*([\d,]+)円',
            r'([\d,]+)円.*税込',
            r'([\d,]+)円.*落札',
            r'落札[^\d]*([\d,]+)円',
            r'価格[^\d]*([\d,]+)円'
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}' で発見: {matches}")
        
        # 賞金に関連する部分を探す
        print("\n=== 賞金関連の検索 ===")
        
        prize_patterns = [
            r'総賞金[^\d]*([\d.]+)万円',
            r'([\d.]+)万円.*総賞金',
            r'賞金[^\d]*([\d,]+)円',
            r'([\d,]+)円.*賞金'
        ]
        
        for pattern in prize_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}' で発見: {matches}")
        
        # 成績に関連する部分を探す
        print("\n=== 成績関連の検索 ===")
        
        record_patterns = [
            r'通算成績[：:]\s*([^\\n]+)',
            r'(\d+戦\d+勝[^\\n]*)',
            r'成績[：:]\s*([^\\n]+)'
        ]
        
        for pattern in record_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"パターン '{pattern}' で発見: {matches}")
        
        # HTMLの構造を確認
        print("\n=== HTML構造の確認 ===")
        
        # 価格に関連しそうな要素を探す
        price_elements = detail_soup.find_all(text=re.compile(r'[0-9,]+円'))
        print(f"円を含むテキスト要素: {len(price_elements)}個")
        for i, elem in enumerate(price_elements[:10]):  # 最初の10個のみ表示
            print(f"{i+1}. {elem.strip()}")
        
        # 親要素の情報も表示
        print("\n=== 価格要素の親要素情報 ===")
        for i, elem in enumerate(price_elements[:5]):
            parent = elem.parent
            if parent:
                print(f"{i+1}. 親要素: {parent.name} - {parent.get_text(strip=True)[:100]}")
        
        # 結果をファイルに保存
        with open('debug_creteuil_result.json', 'w', encoding='utf-8') as f:
            result = {
                'url': detail_url,
                'page_text': page_text,
                'creteuil_links': creteuil_links,
                'price_elements': [elem.strip() for elem in price_elements[:20]]
            }
            json.dump(result, f, ensure_ascii=False, indent=2)
        
        print(f"\n結果を debug_creteuil_result.json に保存しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    debug_creteuil_page() 