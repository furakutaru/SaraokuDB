#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import json
import time
import logging
import requests
from pathlib import Path
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auction_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class AuctionScraper:
    BASE_URL = 'https://auction.keiba.rakuten.co.jp/'
    
    def __init__(self):
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://auction.keiba.rakuten.co.jp/',
        })
    
    def fetch_page(self, url):
        """ページを取得する"""
        try:
            response = self.session.get(url, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            logger.error(f'ページの取得に失敗しました: {url} - {str(e)}')
            return None
    
    def extract_horse_data(self, html):
        """HTMLから馬のデータを抽出する"""
        # 正規表現で馬のデータを抽出
        pattern = r'topItemName:"([^"]+)",offererName:"([^"]*)",basicInfoUrl:"([^"]*)",movieUrl:[^,]+,\s*image:"[^"]+",(?:[^}]+)?price:"([^"]*)",sex:([^,]+),\s*age:([^,}]+)'
        matches = re.finditer(pattern, html)
        
        horses = []
        for match in matches:
            horse = {
                'name': match.group(1),
                'seller': match.group(2),
                'jbis_url': match.group(3),
                'price': match.group(4) if match.group(4) else '未定',
                'sex': match.group(5).strip('"'),
                'age': match.group(6).strip('"'),
                'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            }
            horses.append(horse)
            
        return horses
    
    def scrape(self):
        """オークション情報をスクレイピングする"""
        logger.info('オークションページを取得中...')
        html = self.fetch_page(self.BASE_URL)
        
        if not html:
            logger.error('ページの取得に失敗しました')
            return []
            
        logger.info('馬のデータを抽出中...')
        horses = self.extract_horse_data(html)
        
        if not horses:
            logger.warning('馬のデータが見つかりませんでした')
        else:
            logger.info(f'{len(horses)}頭の馬のデータを抽出しました')
            
        return horses
    
    def save_to_json(self, data, filename='auction_data.json'):
        """データをJSONファイルに保存する"""
        try:
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            logger.info(f'データを {filename} に保存しました')
        except Exception as e:
            logger.error(f'ファイルの保存に失敗しました: {str(e)}')

def main():
    scraper = AuctionScraper()
    horses = scraper.scrape()
    
    # 結果を表示
    for i, horse in enumerate(horses, 1):
        print(f'\n--- 馬 {i} ---')
        print(f'名前: {horse["name"]}')
        print(f'性別: {horse["sex"]}')
        print(f'年齢: {horse["age"]}')
        print(f'売主: {horse["seller"]}')
        print(f'価格: {horse["price"]}')
        print(f'JBIS: {horse["jbis_url"]}')
    
    # データを保存
    output_file = f'auction_data_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
    scraper.save_to_json(horses, output_file)
    
    print(f'\nデータを {output_file} に保存しました')

if __name__ == '__main__':
    main()
