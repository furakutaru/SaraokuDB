import os
import re
import json
import time
import logging
import requests
import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse, parse_qs
from pathlib import Path
import traceback
import glob
from typing import Dict, List, Optional, Any

def get_cache_dir() -> tuple[str, str]:
    """キャッシュディレクトリを取得する"""
    # 固定の日付ディレクトリ（20250818）を使用
    fixed_date = '20250818'
    cache_base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'cache'
    cache_dir = cache_base_dir / fixed_date
    details_dir = cache_dir / 'details'
    
    # ディレクトリがなければ作成
    details_dir.mkdir(parents=True, exist_ok=True)
    return str(cache_dir), str(details_dir)

# ログ設定
log_file = Path('horse_extraction.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def extract_horse_info(html_file: str) -> List[Dict[str, Any]]:
    """リストページのHTMLから馬情報を抽出する
    
    Args:
        html_file: リストページのHTMLファイルパス
        
    Returns:
        抽出した馬情報のリスト
    """
    logging.info(f"リストページからの情報抽出を開始: {html_file}")
    
    try:
        # バイナリモードでファイルを読み込み、適切なエンコーディングを推測
        with open(html_file, 'rb') as f:
            raw_data = f.read()
        
        # エンコーディングを推測
        encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']
        content = None
        
        for enc in encodings:
            try:
                content = raw_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            content = raw_data.decode('utf-8', errors='replace')
        
        # HTMLをパース
        soup = BeautifulSoup(content, 'html.parser')
        
        # 馬情報を格納するリスト
        horses = []
        
        # 各馬のカードを取得
        horse_cards = soup.find_all('div', class_='auctionTableCard')
        
        for card in horse_cards:
            try:
                # 販売者情報を抽出
                seller = ''
                seller_elem = card.find('div', class_='auctionTableCard__seller')
                if seller_elem:
                    seller_span = seller_elem.find('span', class_='value')
                    if seller_span:
                        seller = seller_span.get_text(strip=True)
                
                # 馬名を抽出
                name_elem = card.find('h3', class_='auctionTableCard__name')
                name = name_elem.get_text(strip=True) if name_elem else ''
                
                # その他の情報を抽出
                item_id = card.get('data-item-id', '')
                
                # 性別・年齢を抽出
                sex_age_elem = card.find('span', class_='auctionTableCard__sexAge')
                sex = ''
                age = ''
                if sex_age_elem:
                    sex_age = sex_age_elem.get_text(strip=True)
                    if sex_age:
                        sex = sex_age[0]  # 性別（牡・牝・セ）
                        age_match = re.search(r'(\d+)', sex_age)
                        if age_match:
                            age = age_match.group(1)
                
                # 父・母・母父を抽出
                sire_elem = card.find('div', class_='auctionTableCard__sire')
                dam_elem = card.find('div', class_='auctionTableCard__dam')
                dam_sire_elem = card.find('div', class_='auctionTableCard__damsire')
                
                sire = sire_elem.get_text(strip=True).replace('父:', '') if sire_elem else ''
                dam = dam_elem.get_text(strip=True).replace('母:', '') if dam_elem else ''
                dam_sire = dam_sire_elem.get_text(strip=True).replace('母父:', '') if dam_sire_elem else ''
                
                # 馬情報を辞書に格納
                horse_info = {
                    'name': name,
                    'item_id': item_id,
                    'sex': sex,
                    'age': age,
                    'sire': sire,
                    'dam': dam,
                    'dam_sire': dam_sire,
                    'seller': seller,  # 販売者情報を追加
                    'detail_url': f"https://auction.keiba.rakuten.co.jp/item/{item_id}"
                }
                
                # 詳細ページから追加情報を取得
                detail_file = os.path.join(os.path.dirname(html_file), 'details', 
                                        f"sess_*_item_{item_id}.html")
                matching_files = glob.glob(detail_file)
                
                if matching_files:
                    try:
                        with open(matching_files[0], 'r', encoding='utf-8') as f:
                            detail_content = f.read()
                            detail_soup = BeautifulSoup(detail_content, 'html.parser')
                            
                            # 馬体重を抽出
                            weight_elem = detail_soup.find(string=re.compile(r'馬体重[:：]'))
                            if weight_elem:
                                weight_text = weight_elem.parent.get_text(strip=True)
                                weight_match = re.search(r'馬体重[:：]\s*(\d+)(?:\s*kg)?', weight_text)
                                if weight_match:
                                    horse_info['weight'] = int(weight_match.group(1))
                    
                    except Exception as e:
                        logging.warning(f'詳細ページの処理中にエラーが発生しました {matching_files[0]}: {str(e)}')
                
                horses.append(horse_info)
                
            except Exception as e:
                logging.error(f'馬情報の処理中にエラーが発生しました: {str(e)}')
                continue
                
        logging.info(f"{len(horses)}頭の馬情報を抽出しました")
        return horses
        
    except Exception as e:
        logging.error(f"ファイル処理中にエラーが発生しました {html_file}: {str(e)}", exc_info=True)
        return []

if __name__ == "__main__":
    # テスト用のコード
    cache_dir, _ = get_cache_dir()
    list_file = os.path.join(cache_dir, 'list.html')
    
    if os.path.exists(list_file):
        horses = extract_horse_info(list_file)
        print(f"抽出した馬の数: {len(horses)}")
        if horses:
            print("最初の馬の情報:")
            print(json.dumps(horses[0], ensure_ascii=False, indent=2))
    else:
        print(f"リストファイルが見つかりません: {list_file}")
