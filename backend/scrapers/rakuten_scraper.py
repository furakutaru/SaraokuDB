import re
import time
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager
from bs4 import BeautifulSoup
import requests
from typing import List, Dict, Optional
from datetime import datetime

class RakutenAuctionScraper:
    def __init__(self):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.driver = None
        
    def setup_driver(self):
        """Chromeドライバーをセットアップ"""
        chrome_options = Options()
        chrome_options.add_argument("--headless")  # ヘッドレスモード
        chrome_options.add_argument("--no-sandbox")
        chrome_options.add_argument("--disable-dev-shm-usage")
        chrome_options.add_argument("--disable-gpu")
        chrome_options.add_argument("--window-size=1920,1080")
        
        service = Service(ChromeDriverManager().install())
        self.driver = webdriver.Chrome(service=service, options=chrome_options)
        
    def close_driver(self):
        """ドライバーを閉じる"""
        if self.driver:
            self.driver.quit()
            
    def get_auction_date(self) -> str:
        """ページから開催日を取得"""
        try:
            # ページ上部から開催日を取得するロジック
            # 実際のサイト構造に合わせて調整が必要
            return datetime.now().strftime("%Y-%m-%d")
        except Exception as e:
            print(f"開催日の取得に失敗: {e}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def scrape_horse_list(self) -> List[Dict]:
        """トップページから馬のリストを取得"""
        horses = []
        
        try:
            self.driver.get(self.base_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.CLASS_NAME, "auctionTables"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            auction_tables = soup.find_all(class_="auctionTables")
            
            for table in auction_tables:
                horse_cards = table.find_all(class_="scrollArea__itemCard")
                
                for card in horse_cards:
                    horse_data = self._extract_horse_basic_info(card)
                    if horse_data:
                        horses.append(horse_data)
                        
        except Exception as e:
            print(f"馬リストの取得に失敗: {e}")
            
        return horses
    
    def _extract_horse_basic_info(self, card) -> Optional[Dict]:
        """馬カードから基本情報を抽出"""
        try:
            # 馬名とリンク
            name_element = card.find(class_="auctionTableRow__name")
            if name_element:
                name_link = name_element.find('a')
                if name_link:
                    horse_name = name_link.get_text(strip=True)
                    detail_url = name_link.get('href')
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = self.base_url + detail_url
                else:
                    return None
            else:
                return None
            
            # 総賞金
            price_element = card.find(class_="auctionTableRow__price")
            total_prize = 0.0
            if price_element:
                price_value = price_element.find(class_="value")
                if price_value:
                    price_text = price_value.get_text(strip=True)
                    # "0.0万円" から数値を抽出
                    match = re.search(r'(\d+\.?\d*)', price_text)
                    if match:
                        total_prize = float(match.group(1))
            
            # 販売申込者
            seller_element = card.find(class_="auctionTableRow__seller")
            seller = ""
            if seller_element:
                seller_value = seller_element.find(class_="value")
                if seller_value:
                    seller = seller_value.get_text(strip=True)
            
            return {
                'name': horse_name,
                'detail_url': detail_url,
                'total_prize_start': total_prize,
                'seller': seller
            }
            
        except Exception as e:
            print(f"基本情報の抽出に失敗: {e}")
            return None
    
    def scrape_horse_detail(self, detail_url: str) -> Optional[Dict]:
        """個別ページから詳細情報を取得"""
        try:
            self.driver.get(detail_url)
            WebDriverWait(self.driver, 10).until(
                EC.presence_of_element_located((By.TAG_NAME, "body"))
            )
            
            soup = BeautifulSoup(self.driver.page_source, 'html.parser')
            
            detail_data = {}
            
            # 馬名、性別、年齢
            name_element = soup.find('span', {'itemprop': 'name'})
            if name_element:
                name_text = name_element.get_text(strip=True)
                detail_data.update(self._parse_name_sex_age(name_text))
            
            # 落札価格
            price_element = soup.find('span', {'itemprop': 'price'})
            if price_element:
                price_text = price_element.get_text(strip=True)
                detail_data['sold_price'] = self._extract_price(price_text)
            
            # 血統情報
            pre_elements = soup.find_all('pre')
            for pre in pre_elements:
                pre_text = pre.get_text()
                if '父：' in pre_text:
                    detail_data.update(self._extract_pedigree(pre_text))
            
            # 馬体重
            detail_data['weight'] = self._extract_weight(soup)
            
            # 成績
            detail_data['race_record'] = self._extract_race_record(soup)
            
            # 獲得賞金
            detail_data.update(self._extract_prize_money(soup))
            
            # コメント
            detail_data['comment'] = self._extract_comment(soup)
            
            # 疾病タグ
            detail_data['disease_tags'] = self._extract_disease_tags(detail_data.get('comment', ''))
            
            # 馬体画像（1枚目）
            detail_data['primary_image'] = self._extract_primary_image(soup)
            
            return detail_data
            
        except Exception as e:
            print(f"詳細情報の取得に失敗: {e}")
            return None
    
    def _parse_name_sex_age(self, name_text: str) -> Dict:
        """馬名、性別、年齢を解析"""
        # 例: "ウアラネージュ　牝　3歳"
        parts = name_text.split('　')
        result = {'name': parts[0] if parts else ''}
        
        if len(parts) >= 2:
            sex_match = re.search(r'(牡|牝|セ)', parts[1])
            if sex_match:
                result['sex'] = sex_match.group(1)
        
        if len(parts) >= 3:
            age_match = re.search(r'(\d+)歳', parts[2])
            if age_match:
                result['age'] = int(age_match.group(1))
        
        return result
    
    def _extract_price(self, price_text: str) -> int:
        """価格を抽出（円単位）"""
        # "1,000万円" → 10000000
        match = re.search(r'([\d,]+)', price_text)
        if match:
            price_str = match.group(1).replace(',', '')
            if '万円' in price_text:
                return int(price_str) * 10000
            else:
                return int(price_str)
        return 0
    
    def _extract_pedigree(self, pre_text: str) -> Dict:
        """血統情報を抽出"""
        result = {}
        
        # 父
        sire_match = re.search(r'父：(.+?)(?:\n|$)', pre_text)
        if sire_match:
            result['sire'] = sire_match.group(1).strip()
        
        # 母
        dam_match = re.search(r'母：(.+?)(?:\n|$)', pre_text)
        if dam_match:
            result['dam'] = dam_match.group(1).strip()
        
        # 母父
        dam_sire_match = re.search(r'母父：(.+?)(?:\n|$)', pre_text)
        if dam_sire_match:
            result['dam_sire'] = dam_sire_match.group(1).strip()
        
        return result
    
    def _extract_weight(self, soup) -> Optional[int]:
        """馬体重を抽出"""
        # "最終出走馬体重：XXXkg" を探す
        text = soup.get_text()
        match = re.search(r'最終出走馬体重：(\d+)kg', text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_race_record(self, soup) -> str:
        """成績を抽出"""
        # "通算成績：2戦0勝［0-0-0-2］" を探す
        text = soup.get_text()
        match = re.search(r'通算成績：(.+?)(?:\n|$)', text)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_prize_money(self, soup) -> Dict:
        """獲得賞金を抽出"""
        result = {}
        text = soup.get_text()
        
        # 中央獲得賞金
        central_match = re.search(r'中央獲得賞金：([\d.]+)万円', text)
        if central_match:
            result['central_prize'] = float(central_match.group(1))
        
        # 地方獲得賞金
        local_match = re.search(r'地方獲得賞金：([\d.]+)万円', text)
        if local_match:
            result['local_prize'] = float(local_match.group(1))
        
        return result
    
    def _extract_comment(self, soup) -> str:
        """コメントを抽出"""
        # "本馬について" の後の <pre> タグを探す
        comment_section = soup.find('b', string='本馬について')
        if comment_section:
            pre_element = comment_section.find_next('pre')
            if pre_element:
                return pre_element.get_text(strip=True)
        return ""
    
    def _extract_disease_tags(self, comment: str) -> str:
        """疾病タグを抽出"""
        disease_keywords = [
            '喉頭片麻痺', '喘鳴症', '脚部不安', '関節炎', '腱炎',
            '骨折', '脱臼', '筋肉痛', '腰痛', '腹痛'
        ]
        
        found_diseases = []
        for disease in disease_keywords:
            if disease in comment:
                found_diseases.append(disease)
        
        return ','.join(found_diseases)
    
    def _extract_primary_image(self, soup) -> str:
        """馬体画像（1枚目）のURLを抽出"""
        try:
            # div.bigImageWrap img#bigImage を探す
            image_element = soup.select_one('div.bigImageWrap img#bigImage')
            if image_element and image_element.get('src'):
                return image_element.get('src')
            
            # 代替方法: 最初の馬体画像を探す
            image_elements = soup.find_all('img')
            for img in image_elements:
                src = img.get('src', '')
                if 'horse' in src.lower() and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'png' in src.lower()):
                    return src
            
            return ""
        except Exception as e:
            print(f"馬体画像の抽出に失敗: {e}")
            return ""
    
    def scrape_all_horses(self, auction_date: str = None) -> List[Dict]:
        """全馬の情報を取得"""
        if not auction_date:
            auction_date = self.get_auction_date()
        
        try:
            self.setup_driver()
            
            # 基本情報を取得
            horses = self.scrape_horse_list()
            print(f"{len(horses)}頭の馬を発見しました。")
            
            # 詳細情報を取得
            for i, horse in enumerate(horses):
                print(f"詳細情報を取得中... ({i+1}/{len(horses)}) {horse['name']}")
                
                if horse.get('detail_url'):
                    detail_data = self.scrape_horse_detail(horse['detail_url'])
                    if detail_data:
                        horse.update(detail_data)
                
                horse['auction_date'] = auction_date
                time.sleep(1)  # サーバーに負荷をかけないよう待機
            
            return horses
            
        finally:
            self.close_driver() 