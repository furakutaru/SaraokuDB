#!/usr/bin/env python3
"""
現在の楽天オークションサイトの構造を確認するスクリプト
"""

import requests
from bs4 import BeautifulSoup
import json
from datetime import datetime

def debug_site_structure():
    """サイトの構造をデバッグ"""
    url = "https://auction.keiba.rakuten.co.jp/"
    
    print("=== 楽天オークションサイト構造デバッグ ===")
    print(f"URL: {url}")
    print(f"実行時刻: {datetime.now()}")
    print()
    
    try:
        # リクエストヘッダーを設定
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        }
        
        print("1. サイトへのアクセス...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        print(f"   ステータスコード: {response.status_code}")
        print(f"   コンテンツタイプ: {response.headers.get('content-type', 'N/A')}")
        print()
        
        # HTMLをパース
        soup = BeautifulSoup(response.content, 'html.parser')
        
        print("2. ページタイトルの確認...")
        title = soup.find('title')
        if title:
            print(f"   タイトル: {title.get_text(strip=True)}")
        else:
            print("   タイトルが見つかりません")
        print()
        
        print("3. 馬のリスト要素の検索...")
        
        # 様々なクラス名で馬のリストを探す
        possible_selectors = [
            '.auctionTables',
            '.auctionTableRow',
            '.scrollArea__itemCard',
            '.horse-list',
            '.auction-item',
            '.item-card',
            '[class*="auction"]',
            '[class*="horse"]',
            '[class*="item"]'
        ]
        
        found_elements = []
        for selector in possible_selectors:
            elements = soup.select(selector)
            if elements:
                found_elements.append((selector, len(elements)))
                print(f"   {selector}: {len(elements)}個の要素を発見")
        
        if not found_elements:
            print("   馬のリスト要素が見つかりませんでした")
        
        print()
        
        print("4. ページ全体の構造確認...")
        
        # 主要なdiv要素を確認
        main_divs = soup.find_all('div', class_=True)
        class_counts = {}
        for div in main_divs:
            for class_name in div.get('class', []):
                class_counts[class_name] = class_counts.get(class_name, 0) + 1
        
        print("   主要なクラス名と出現回数:")
        for class_name, count in sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:20]:
            print(f"     {class_name}: {count}回")
        
        print()
        
        print("5. テキスト内容の確認...")
        
        # 馬の名前らしきテキストを探す
        page_text = soup.get_text()
        
        # 馬の名前のパターンを探す
        import re
        
        # 日本語の馬名らしきパターン
        horse_name_patterns = [
            r'[ァ-ヶー]{2,}',  # カタカナ2文字以上
            r'[一-龯]{2,}',   # 漢字2文字以上
        ]
        
        potential_names = []
        for pattern in horse_name_patterns:
            matches = re.findall(pattern, page_text)
            potential_names.extend(matches[:10])  # 最初の10個
        
        if potential_names:
            print("   潜在的な馬名らしき文字列:")
            for name in set(potential_names):
                print(f"     {name}")
        else:
            print("   馬名らしき文字列が見つかりませんでした")
        
        print()
        
        print("6. リンクの確認...")
        
        # 馬の詳細ページへのリンクを探す
        links = soup.find_all('a', href=True)
        detail_links = []
        
        for link in links:
            href = link.get('href', '')
            text = link.get_text(strip=True)
            
            # 馬の詳細ページらしきリンクを探す
            if any(keyword in href.lower() for keyword in ['horse', 'detail', 'item', 'auction']):
                detail_links.append((text, href))
            elif any(keyword in text for keyword in ['詳細', '詳細血統表', '血統']):
                detail_links.append((text, href))
        
        if detail_links:
            print("   詳細ページへのリンク:")
            for text, href in detail_links[:10]:
                print(f"     {text}: {href}")
        else:
            print("   詳細ページへのリンクが見つかりませんでした")
        
        print()
        
        print("7. 画像の確認...")
        
        # 馬の画像を探す
        images = soup.find_all('img', src=True)
        horse_images = []
        
        for img in images:
            src = img.get('src', '')
            alt = img.get('alt', '')
            
            if any(keyword in src.lower() for keyword in ['horse', 'auction', 'item']):
                horse_images.append((alt, src))
        
        if horse_images:
            print("   馬の画像らしきもの:")
            for alt, src in horse_images[:5]:
                print(f"     {alt}: {src}")
        else:
            print("   馬の画像が見つかりませんでした")
        
        print()
        
        print("8. 現在のオークション情報の確認...")
        
        # オークション開催日や価格情報を探す
        price_patterns = [
            r'(\d{1,3}(?:,\d{3})*)円',
            r'(\d+\.?\d*)万円',
            r'(\d+)万',
        ]
        
        for pattern in price_patterns:
            matches = re.findall(pattern, page_text)
            if matches:
                print(f"   価格パターン '{pattern}': {len(matches)}個発見")
                print(f"     例: {matches[:5]}")
        
        print()
        
        print("=== デバッグ完了 ===")
        
        # 結果をJSONファイルに保存
        debug_result = {
            'timestamp': datetime.now().isoformat(),
            'url': url,
            'status_code': response.status_code,
            'title': title.get_text(strip=True) if title else None,
            'found_selectors': found_elements,
            'top_classes': dict(sorted(class_counts.items(), key=lambda x: x[1], reverse=True)[:20]),
            'potential_names': list(set(potential_names)),
            'detail_links': detail_links[:10],
            'horse_images': horse_images[:5]
        }
        
        with open('debug_result.json', 'w', encoding='utf-8') as f:
            json.dump(debug_result, f, ensure_ascii=False, indent=2)
        
        print("デバッグ結果を debug_result.json に保存しました")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_site_structure() 