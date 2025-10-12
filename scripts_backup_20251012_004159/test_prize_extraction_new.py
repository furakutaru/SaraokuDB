#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from bs4 import BeautifulSoup
import re

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('prize_extraction_test.log')
    ]
)

def extract_prize_from_auction(html_content, horse_name):
    """
    オークションリストページから賞金情報を抽出する
    
    Args:
        html_content (str): オークションリストページのHTML
        horse_name (str): 馬名（デバッグ用）
        
    Returns:
        str or float: 総賞金（万円単位）。見つからない場合は0.0、繁殖牝馬の場合は'-'を返す
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 繁殖牝馬の場合は'-'を返す
        if any(text in html_content for text in ['繁殖牝馬', '受胎種牡馬']):
            logging.info(f"馬名 '{horse_name}' は繁殖牝馬のため、賞金は'-'を返します")
            return '-'
        
        # 未出走馬の場合は0を返す
        if '未出走' in html_content:
            logging.info(f"馬名 '{horse_name}' は未出走のため賞金は0円です")
            return 0.0
        
        # 賞金情報を含む要素を探す
        prize_div = soup.find('div', class_='auctionTableCard__price')
        if not prize_div:
            logging.warning(f"馬名 '{horse_name}': 賞金要素が見つかりませんでした")
            return 0.0
        
        # ラベルが「総賞金」であることを確認
        label_div = prize_div.find('div', class_='label')
        if not label_div or '総賞金' not in label_div.get_text():
            logging.warning(f"馬名 '{horse_name}': 総賞金のラベルが見つかりませんでした")
            return 0.0
        
        # 賞金の値を取得
        value_div = prize_div.find('div', class_='value')
        if not value_div:
            logging.warning(f"馬名 '{horse_name}': 賞金の値が見つかりませんでした")
            return 0.0
        
        prize_text = value_div.get_text(strip=True)
        
        # 数値部分を抽出（「1,234.0万円」→ 1,234.0）
        match = re.search(r'([\d,]+\.[\d]+)', prize_text)
        if match:
            total_prize = match.group(1)
            logging.info(f"馬名 '{horse_name}' の賞金を抽出: {total_prize}万円")
            return total_prize
        
        logging.warning(f"馬名 '{horse_name}' の賞金情報を抽出できませんでした")
        return 0.0
        
    except Exception as e:
        logging.error(f"賞金情報の抽出中にエラーが発生しました（馬名: {horse_name}）: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return 0.0

def test_prize_extraction(html_file):
    """HTMLファイルから賞金情報を抽出してテストする"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # 馬ごとのカードを取得
        soup = BeautifulSoup(html_content, 'html.parser')
        horse_cards = soup.find_all('div', class_=lambda x: x and 'auctionTableCard' in x)
        
        if not horse_cards:
            logging.warning("馬のカードが見つかりませんでした")
            return
        
        results = []
        for card in horse_cards:
            # 馬名を取得
            name_elem = card.find('div', class_=lambda x: x and 'name' in x.lower())
            horse_name = name_elem.get_text(strip=True) if name_elem else '不明な馬'
            
            # 賞金を抽出
            prize = extract_prize_from_auction(str(card), horse_name)
            results.append({
                'name': horse_name,
                'prize': prize
            })
        
        # 結果を表示
        print("\n=== 賞金抽出テスト結果 ===")
        for result in results:
            print(f"馬名: {result['name']}, 賞金: {result['prize']}万円")
        
        return results
        
    except Exception as e:
        logging.error(f"テスト実行中にエラーが発生しました: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return None

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用法: python test_prize_extraction_new.py <HTMLファイルパス>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not os.path.exists(html_file):
        print(f"エラー: ファイルが見つかりません: {html_file}")
        sys.exit(1)
    
    test_prize_extraction(html_file)
