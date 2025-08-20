#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys
from bs4 import BeautifulSoup

def extract_prize(html_content):
    """HTMLコンテンツから賞金情報を抽出する"""
    from bs4 import BeautifulSoup
    import re
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # リストページの各馬の情報を含む要素を検索
    horse_cards = soup.find_all('div', class_=re.compile('auctionTableCard'))
    
    for card in horse_cards:
        # 馬名を取得
        name_elem = card.find('p', class_=re.compile('auctionTableCard__name'))
        horse_name = name_elem.get_text(strip=True) if name_elem else '不明な馬'
        
        # 賞金情報を検索
        prize_elems = card.find_all('div', class_=re.compile('auctionTableCard__data'))
        
        for elem in prize_elems:
            label = elem.find('div', class_=re.compile('auctionTableCard__label'))
            value = elem.find('div', class_=re.compile('auctionTableCard__value'))
            
            if label and '賞金' in label.get_text() and value:
                prize_text = value.get_text(strip=True)
                try:
                    # 数値部分を抽出（「万円」やカンマを削除）
                    prize = float(re.sub(r'[^\d.]', '', prize_text))
                    print(f"馬名: {horse_name}, 賞金: {prize}万円")
                    return prize
                except (ValueError, AttributeError) as e:
                    print(f"賞金の抽出に失敗しました: {e}")
                    continue
    
    # 正規表現によるフォールバック
    import re
    patterns = [
        r'<div class="value"[^>]*>([\d,.]+)[\s\u3000]*万円</div>',  # リストページ用
        r'総賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万円',
        r'総賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万',
        r'賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万円',
        r'([\d,]+(?:\.[\d,]+)?)[\s\u3000]*万円',
        r'([\d,]+(?:\.[\d,]+)?)[\s\u3000]*万'
    ]
    
    # テキストを抽出
    soup = BeautifulSoup(html_content, 'html.parser')
    text = soup.get_text()
    
    print("=== 抽出対象テキストの一部 ===")
    print(text[:1000] + "..." if len(text) > 1000 else text)
    print("=" * 50)
    
    for i, pattern in enumerate(patterns, 1):
        match = re.search(pattern, text)
        if match:
            try:
                prize = float(match.group(1).replace(',', ''))
                # 円単位の場合は万円に変換
                if '円' in pattern and '万円' not in pattern:
                    prize = prize / 10000
                print(f"パターン {i} で抽出成功: {prize}万円")
                print(f"マッチした部分: {match.group(0)}")
                return prize
            except (ValueError, TypeError) as e:
                print(f"パターン {i} でエラー: {e}")
                continue
    
    print("賞金情報が見つかりませんでした")
    return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用法: python test_prize_extraction.py <HTMLファイルパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        prize = extract_prize(html_content)
        if prize is not None:
            print(f"\n== 最終結果 ==")
            print(f"抽出された賞金: {prize}万円")
    except Exception as e:
        print(f"エラーが発生しました: {e}")
