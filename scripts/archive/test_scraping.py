#!/usr/bin/env python3
"""
楽天サラブレッドオークションサイトの構造確認スクリプト
"""

import requests
from bs4 import BeautifulSoup
import json

def test_rakuten_site():
    """楽天サラブレッドオークションサイトの構造を確認"""
    
    # 実際の楽天サラブレッドオークションURL
    urls_to_test = [
        "https://auction.keiba.rakuten.co.jp/",
        "https://auction.keiba.rakuten.co.jp/auction/",
        "https://auction.keiba.rakuten.co.jp/list/",
        "https://auction.keiba.rakuten.co.jp/result/",
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    for url in urls_to_test:
        print(f"\n=== テストURL: {url} ===")
        try:
            response = session.get(url, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                
                # タイトルを取得
                title = soup.find('title')
                if title:
                    print(f"タイトル: {title.get_text().strip()}")
                
                # リンクを確認
                links = soup.find_all('a', href=True)
                racehorse_links = []
                for link in links:
                    href = link.get('href', '')
                    if href and 'racehorse' in str(href):
                        racehorse_links.append(link)
                
                print(f"総リンク数: {len(links)}")
                print(f"racehorse関連リンク数: {len(racehorse_links)}")
                
                # 最初の10個のracehorse関連リンクを表示
                for i, link in enumerate(racehorse_links[:10]):
                    href = str(link.get('href', ''))
                    text = link.get_text().strip()
                    print(f"  {i+1}. {text} -> {href}")
                
                # テーブルやリスト要素を確認
                tables = soup.find_all('table')
                lists = soup.find_all(['ul', 'ol'])
                
                print(f"テーブル数: {len(tables)}")
                print(f"リスト数: {len(lists)}")
                
                # 画像要素を確認
                images = soup.find_all('img')
                print(f"画像数: {len(images)}")
                
            else:
                print(f"アクセス失敗: {response.status_code}")
                
        except Exception as e:
            print(f"エラー: {e}")

def test_alternative_sites():
    """代替の競馬オークションサイトを確認"""
    
    alternative_urls = [
        "https://www.jbis.or.jp/",
        "https://www.jra.go.jp/",
        "https://www.keiba.go.jp/",
    ]
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    for url in alternative_urls:
        print(f"\n=== 代替サイト: {url} ===")
        try:
            response = session.get(url, timeout=10)
            print(f"ステータスコード: {response.status_code}")
            
            if response.status_code == 200:
                soup = BeautifulSoup(response.content, 'html.parser')
                title = soup.find('title')
                if title:
                    print(f"タイトル: {title.get_text().strip()}")
                    
        except Exception as e:
            print(f"エラー: {e}")

if __name__ == "__main__":
    print("楽天サラブレッドオークションサイトの構造確認を開始...")
    test_rakuten_site()
    
    print("\n" + "="*50)
    print("代替サイトの確認...")
    test_alternative_sites() 