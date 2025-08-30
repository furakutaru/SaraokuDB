#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import logging
import requests
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def fetch_auction_data():
    """オークションデータを取得する"""
    url = 'https://auction.keiba.rakuten.co.jp/'
    
    try:
        logger.info('オークションデータを取得中...')
        response = requests.get(url, timeout=30)
        response.raise_for_status()
        html = response.text
        
        # 正規表現で馬のデータを抽出
        pattern = r'topItemName:"([^"]+)",offererName:"([^"]*)",basicInfoUrl:"([^"]*)",movieUrl:[^,]+,\s*image:"[^"]+",(?:[^}]+)?price:"([^"]*)",sex:([^,]+),\s*age:([^,}]+)'
        matches = re.finditer(pattern, html)
        
        horses = []
        for match in matches:
            try:
                horse = {
                    'name': match.group(1),
                    'seller': match.group(2),
                    'jbis_url': match.group(3).replace('\\', ''),
                    'price': match.group(4) if match.group(4) else '未定',
                    'sex': convert_sex(match.group(5)),
                    'age': match.group(6).strip('"'),
                    'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                }
                horses.append(horse)
            except IndexError as e:
                logger.warning(f'データの抽出中にエラーが発生しました: {str(e)}')
                continue
        
        logger.info(f'{len(horses)}頭の馬のデータを抽出しました')
        return horses
        
    except Exception as e:
        logger.error(f'エラーが発生しました: {str(e)}')
        return []

def convert_sex(sex_code):
    """性別コードを日本語に変換"""
    sex_map = {
        'c': '牡',
        'f': '牝',
        'd': '騸',
        'h': 'せん',
        'm': 'せん',
        'g': 'せん',
        's': 'せん',
        'b': '不明',
        'q': '不明',
        'z': '不明'
    }
    return sex_map.get(sex_code.lower().strip('"'), sex_code)

def save_to_json(data, filename=None):
    """データをJSONファイルに保存する"""
    if not filename:
        filename = f'auction_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
        
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f'データを {filename} に保存しました')
        return filename
    except Exception as e:
        logger.error(f'ファイルの保存に失敗しました: {str(e)}')
        return None

def main():
    # データを取得
    horses = fetch_auction_data()
    
    if not horses:
        logger.error('データの取得に失敗しました')
        return
    
    # 結果を表示
    print(f'\n=== オークション情報 ({len(horses)}頭) ===\n')
    for i, horse in enumerate(horses, 1):
        print(f'【{i}頭目】')
        print(f'名前: {horse["name"]}')
        print(f'性別: {horse["sex"]}')
        print(f'年齢: {horse["age"]}')
        print(f'売主: {horse["seller"]}')
        print(f'価格: {horse["price"]}')
        print(f'JBIS: {horse["jbis_url"]}\n')
    
    # データを保存
    output_file = save_to_json(horses)
    if output_file:
        print(f'\nデータを {output_file} に保存しました')

if __name__ == '__main__':
    main()
