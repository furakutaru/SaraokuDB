#!/usr/bin/env python3
"""
修正されたHTMLファイルを使用してスクレイピングをテストするスクリプト
"""
import os
import sys
import json
from bs4 import BeautifulSoup
from pathlib import Path
from typing import List, Dict, Optional, Any

# プロジェクトのルートディレクトリを取得
PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# モジュールのパスを追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ロギング設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_scraping.log')
    ]
)
logger = logging.getLogger(__name__)

def parse_horse_list(html_content: str) -> List[Dict[str, Any]]:
    """
    馬の一覧ページから馬の情報を抽出する
    
    Args:
        html_content: 一覧ページのHTMLコンテンツ
        
    Returns:
        馬の情報のリスト
    """
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    
    # 馬のカードを検索
    horse_cards = soup.select('.auctionTableCard')
    
    for card in horse_cards:
        try:
            # 馬名とリンクを取得
            name_elem = card.select_one('.auctionTableCard__name--link')
            if not name_elem:
                continue
                
            horse_name = name_elem.get_text(strip=True)
            detail_url = name_elem.get('href', '')
            
            # 画像URLを取得
            img_elem = card.select_one('.auctionTableCard__img img')
            image_url = img_elem.get('src', '') if img_elem else ''
            
            # 性別と年齢を取得
            sex_age_elem = card.select_one('.auctionTableCard__sexAge')
            sex_age = sex_age_elem.get_text(strip=True) if sex_age_elem else ''
            
            # 賞金情報を取得
            prize_elem = card.select_one('.auctionTableCard__prize')
            prize_text = prize_elem.get_text(strip=True) if prize_elem else ''
            
            # 馬の情報を辞書に格納
            horse_info = {
                'name': horse_name,
                'detail_url': detail_url,
                'image_url': image_url,
                'sex_age': sex_age,
                'prize_text': prize_text,
                'auction_date': '2025-08-14'  # 固定値（実際にはHTMLから取得するのが望ましい）
            }
            
            horses.append(horse_info)
            
        except Exception as e:
            logger.error(f"馬の情報の抽出中にエラーが発生しました: {str(e)}")
            continue
    
    return horses

def main():
    # 修正されたHTMLファイルのパス
    fixed_html_path = os.path.join('test_cache', 'fixed_auction_list_updated.html')
    
    # HTMLファイルを読み込む
    try:
        with open(fixed_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
    except Exception as e:
        logger.error(f"HTMLファイルの読み込みに失敗しました: {str(e)}")
        return 1
    
    # 馬の情報を抽出
    horses = parse_horse_list(html_content)
    
    # 結果を表示
    print(f"\n=== 抽出結果 ===")
    print(f"抽出した馬の数: {len(horses)}")
    
    for i, horse in enumerate(horses, 1):
        print(f"\n--- 馬 {i} ---")
        print(f"名前: {horse['name']}")
        print(f"詳細URL: {horse['detail_url']}")
        print(f"画像URL: {horse['image_url']}")
        print(f"性別・年齢: {horse['sex_age']}")
        print(f"賞金情報: {horse['prize_text']}")
    
    # 結果をJSONファイルに保存
    output_path = os.path.join('test_cache', 'scraping_results.json')
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(horses, f, ensure_ascii=False, indent=2)
        logger.info(f"結果を {output_path} に保存しました")
    except Exception as e:
        logger.error(f"結果の保存中にエラーが発生しました: {str(e)}")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
