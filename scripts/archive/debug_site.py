#!/usr/bin/env python3
"""
楽天サラブレッドオークションサイトの詳細構造確認スクリプト
"""

import requests
from bs4 import BeautifulSoup
import json

def debug_rakuten_site():
    """楽天サラブレッドオークションサイトの詳細構造を確認"""
    
    url = "https://auction.keiba.rakuten.co.jp/"
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    print(f"=== 楽天サラブレッドオークションサイト解析 ===")
    print(f"URL: {url}")
    
    try:
        response = session.get(url, timeout=30)
        print(f"ステータスコード: {response.status_code}")
        
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # タイトルを取得
            title = soup.find('title')
            if title:
                print(f"タイトル: {title.get_text().strip()}")
            
            # 全テキストから馬の情報を探す
            all_text = soup.get_text()
            print(f"\n=== 全テキストから馬の情報を検索 ===")
            
            # 馬名のパターンを探す
            import re
            
            # ☆マークを含む行を探す
            lines = all_text.split('\n')
            horse_lines = []
            for line in lines:
                line = line.strip()
                if '☆' in line and ('牝' in line or '牡' in line):
                    horse_lines.append(line)
            
            print(f"☆マークを含む行数: {len(horse_lines)}")
            for i, line in enumerate(horse_lines[:10]):
                print(f"  {i+1}. {line}")
            
            # 馬名のパターンを探す（☆マークなしでも）
            horse_patterns = []
            for line in lines:
                line = line.strip()
                if ('牝' in line or '牡' in line) and ('父' in line or '歳' in line):
                    horse_patterns.append(line)
            
            print(f"\n馬の情報を含む行数: {len(horse_patterns)}")
            for i, line in enumerate(horse_patterns[:10]):
                print(f"  {i+1}. {line}")
            
            # HTML要素を詳しく確認
            print(f"\n=== HTML要素の詳細確認 ===")
            
            # div要素を確認
            divs = soup.find_all('div')
            print(f"div要素数: {len(divs)}")
            
            # 馬の情報が含まれそうなdivを探す
            horse_divs = []
            for div in divs:
                div_text = div.get_text().strip()
                if '☆' in div_text or ('牝' in div_text and '牡' in div_text):
                    horse_divs.append(div_text[:100])  # 最初の100文字のみ
            
            print(f"馬の情報を含むdiv数: {len(horse_divs)}")
            for i, div_text in enumerate(horse_divs[:5]):
                print(f"  {i+1}. {div_text}...")
            
            # リンクを確認
            links = soup.find_all('a', href=True)
            print(f"\n総リンク数: {len(links)}")
            
            # 馬関連のリンクを探す
            horse_links = []
            for link in links:
                href = str(link.get('href', ''))
                text = link.get_text().strip()
                if '馬' in text or 'horse' in href.lower():
                    horse_links.append((text, href))
            
            print(f"馬関連リンク数: {len(horse_links)}")
            for i, (text, href) in enumerate(horse_links[:10]):
                print(f"  {i+1}. {text} -> {href}")
            
            # 画像を確認
            images = soup.find_all('img')
            print(f"\n画像数: {len(images)}")
            
            # 馬の画像を探す
            horse_images = []
            for img in images:
                src = str(img.get('src', ''))
                alt = str(img.get('alt', ''))
                if 'horse' in src.lower() or '馬' in alt:
                    horse_images.append((alt, src))
            
            print(f"馬関連画像数: {len(horse_images)}")
            for i, (alt, src) in enumerate(horse_images[:5]):
                print(f"  {i+1}. {alt} -> {src}")
            
            # HTMLの一部を保存（デバッグ用）
            with open('debug_site.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
            print(f"\nHTMLを debug_site.html に保存しました")
            
        else:
            print(f"アクセス失敗: {response.status_code}")
            
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    debug_rakuten_site() 