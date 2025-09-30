#!/usr/bin/env python3
"""
Test cache file の馬カード構造を解析するスクリプト
"""
import os
from bs4 import BeautifulSoup

def analyze_horse_card(html_file):
    # HTMLファイルを読み込む
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬カードを検索
    horse_cards = soup.select('.auctionTableCard')
    
    if not horse_cards:
        print("馬カードが見つかりませんでした")
        return
    
    print(f"馬カードを {len(horse_cards)} 件見つけました")
    
    # 最初の馬カードを詳細に分析
    first_card = horse_cards[0]
    print("\n===== 馬カードの構造 =====")
    print(first_card.prettify()[:1000])  # 最初の1000文字を表示
    
    # 馬名を含む可能性のある要素を検索
    print("\n===== リンク一覧 =====")
    for i, link in enumerate(first_card.find_all('a'), 1):
        print(f"{i}. テキスト: {link.get_text(strip=True)}")
        print(f"   href: {link.get('href', 'N/A')}")
    
    # テキストをパイプ区切りで表示
    print("\n===== テキスト内容（パイプ区切り） =====")
    print(first_card.get_text('|', strip=True))
    
    # クラス属性を持つ要素を列挙
    print("\n===== クラス属性を持つ要素 =====")
    for i, elem in enumerate(first_card.find_all(class_=True), 1):
        print(f"{i}. タグ: {elem.name}, クラス: {elem.get('class')}")
        if i >= 10:  # 最初の10件のみ表示
            print("... 他にもあります")
            break

if __name__ == "__main__":
    # テストキャッシュファイルのパス
    cache_file = "test_cache/fixed_auction_list_updated.html"
    
    if not os.path.exists(cache_file):
        print(f"エラー: ファイルが見つかりません: {os.path.abspath(cache_file)}")
    else:
        analyze_horse_card(cache_file)
