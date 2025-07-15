import re
import requests
from bs4 import BeautifulSoup
from typing import Optional, Dict, Union
import time

class NetkeibaScraper:
    def __init__(self):
        self.search_url = "https://db.netkeiba.com/?pid=horse_search_detail"
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })
    
    def search_horse(self, horse_name: str) -> Optional[str]:
        """馬名でnetkeibaを検索してURLを取得"""
        try:
            # 馬名検索のPOSTリクエスト
            search_data = {
                'word': horse_name,
                'pid': 'horse_search_detail'
            }
            
            response = self.session.post(self.search_url, data=search_data)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 検索結果から最初の馬のリンクを取得
            horse_links = soup.find_all('a', href=re.compile(r'/horse/\d+/'))
            
            if horse_links:
                horse_url = horse_links[0]['href']
                if not horse_url.startswith('http'):
                    horse_url = 'https://db.netkeiba.com' + horse_url
                return horse_url
            
            return None
            
        except Exception as e:
            print(f"馬検索に失敗: {e}")
            return None
    
    def get_latest_prize_money(self, horse_url: str) -> Union[float, str, None]:
        """netkeibaページから最新の地方獲得賞金を取得（万円単位・小数点1桁まで）"""
        try:
            response = self.session.get(horse_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            prize_rows = soup.find_all('tr')
            for row in prize_rows:
                th_element = row.find('th')
                if th_element and '獲得賞金 (地方)' in th_element.get_text():
                    td_element = row.find('td')
                    if td_element:
                        prize_text = td_element.get_text(strip=True)
                        match = re.search(r'([\d,]+)', prize_text)
                        if match:
                            prize_str = match.group(1).replace(',', '')
                            prize_man = round(float(prize_str) / 10000, 1)  # 万円単位・小数点1桁
                            return prize_man
            return '-'
        except Exception as e:
            print(f"賞金取得に失敗: {e}")
            return '-'
    
    def update_horse_prize_money(self, horse_name: str) -> Optional[Dict]:
        """馬の最新賞金情報を取得・更新（万円単位・小数点1桁まで）"""
        try:
            horse_url = self.search_horse(horse_name)
            if not horse_url:
                print(f"馬が見つかりません: {horse_name}")
                return {'netkeiba_url': None, 'total_prize_latest': '-'}
            latest_prize = self.get_latest_prize_money(horse_url)
            if not isinstance(latest_prize, float):
                latest_prize = '-'
            return {
                'netkeiba_url': horse_url,
                'total_prize_latest': latest_prize
            }
        except Exception as e:
            print(f"賞金更新に失敗: {e}")
            return {'netkeiba_url': None, 'total_prize_latest': '-'}
    
    def batch_update_prize_money(self, horses: list) -> list:
        """複数の馬の賞金情報を一括更新（万円単位・小数点1桁まで、差分も同様）"""
        updated_horses = []
        for i, horse in enumerate(horses):
            print(f"賞金情報を更新中... ({i+1}/{len(horses)}) {horse['name']}")
            update_data = self.update_horse_prize_money(horse['name'])
            if update_data:
                horse.update(update_data)
                start_prize = horse.get('total_prize_start')
                latest_prize = horse.get('total_prize_latest')
                if (isinstance(start_prize, (int, float)) and isinstance(latest_prize, float)):
                    diff = round(latest_prize - (start_prize / 10000 if isinstance(start_prize, int) else start_prize), 1)
                    sign = '+' if diff >= 0 else ''
                    horse['prize_diff'] = f"{sign}{diff}万円"
                else:
                    horse['prize_diff'] = '-'
            updated_horses.append(horse)
        return updated_horses 