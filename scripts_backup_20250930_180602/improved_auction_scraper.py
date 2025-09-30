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
    
    def fetch_page(self):
        """ページを取得する"""
        try:
            logger.info('オークションページを取得中...')
            response = self.session.get(self.BASE_URL, timeout=30)
            response.raise_for_status()
            response.encoding = 'utf-8'
            return response.text
        except Exception as e:
            logger.error(f'ページの取得に失敗しました: {str(e)}')
            return None
    
    def extract_horse_data(self, html):
        """HTMLから馬のデータを抽出する"""
        try:
            # 馬のデータが含まれているスクリプト部分を抽出
            script_pattern = r'<script[^>]*>.*?(var\s+__NEXT_DATA__\s*=\s*\{.*?\}).*?</script>'
            script_match = re.search(script_pattern, html, re.DOTALL)
            
            if not script_match:
                logger.error('データが見つかりませんでした')
                return []
                
            script_content = script_match.group(1)
            
            # データをパース
            data_start = script_content.find('{')
            data_end = script_content.rfind('}') + 1
            json_data = script_content[data_start:data_end]
            
            try:
                data = json.loads(json_data)
                # ここで必要なデータを抽出
                # 実際のデータ構造に合わせてパスを調整してください
                horses = data.get('props', {}).get('pageProps', {}).get('horses', [])
                return horses
            except json.JSONDecodeError as e:
                logger.error(f'JSONのパースに失敗しました: {str(e)}')
                return []
            
            # 従来の正規表現での抽出（バックアップとして残す）
            pattern = r'topItemName:\"([^\"]+)\"\\n","offererName":"([^"]*)","basicInfoUrl":"([^"]*)","price":"?([^",}]+)"?(?:,"sex":"?([^",}]+)"?(?:,"age":"?([^",}]+)"?)?)?'
            matches = re.finditer(pattern, html)
            
            horses = []
            for match in matches:
                try:
                    horse = {
                        'name': match.group(1).replace('\"', ''),  # 馬名
                        'seller': match.group(2),  # 売主
                        'jbis_url': match.group(3).replace('\\', ''),  # JBIS URL
                        'price': match.group(4) if len(match.groups()) > 3 and match.group(4) else '未定',  # 価格
                        'sex': self._convert_sex(match.group(5)) if len(match.groups()) > 4 and match.group(5) else '不明',  # 性別
                        'age': match.group(6) if len(match.groups()) > 5 and match.group(6) else '不明',  # 年齢
                        'scraped_at': datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    }
                    horses.append(horse)
                except IndexError as e:
                    logger.warning(f'データの抽出中にエラーが発生しました: {str(e)}')
                    continue
                
            logger.info(f'{len(horses)}頭の馬のデータを抽出しました')
            return horses
            
        except Exception as e:
            logger.error(f'データの抽出中にエラーが発生しました: {str(e)}')
            return []
    
    def _convert_sex(self, sex_code):
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
        return sex_map.get(sex_code.lower(), sex_code)
    
    def save_to_json(self, data, filename=None):
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
    scraper = AuctionScraper()
    
    # ページを取得
    html = scraper.fetch_page()
    if not html:
        logger.error('ページの取得に失敗したため、処理を終了します')
        return
    
    # データを抽出
    horses = scraper.extract_horse_data(html)
    
    if not horses:
        logger.warning('馬のデータが見つかりませんでした')
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
    output_file = scraper.save_to_json(horses)
    if output_file:
        print(f'\nデータを {output_file} に保存しました')

if __name__ == '__main__':
    main()
