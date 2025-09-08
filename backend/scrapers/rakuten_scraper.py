import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union, cast, Any, Tuple
from datetime import datetime
from urllib.parse import urljoin

# Add the project root to the Python path
import sys
import os
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

try:
    from backend.scrapers.data_helpers import (
        save_horse,
        save_auction_history,
        load_json_file
    )
    HAS_DATA_HELPERS = True
except ImportError as e:
    # For testing without data_helpers
    print(f"Warning: Could not import data_helpers: {e}")
    HAS_DATA_HELPERS = False
    def save_horse(*args, **kwargs):
        pass
    
    def save_auction_history(*args, **kwargs):
        pass
    
    def load_json_file(*args, **kwargs):
        return {}

class RakutenAuctionScraper:
    def __init__(self, data_dir: str = 'static-frontend/public/data'):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.data_dir = data_dir
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache',
            'Pragma': 'no-cache',
            'Sec-Fetch-Dest': 'document',
            'Sec-Fetch-Mode': 'navigate',
            'Sec-Fetch-Site': 'none',
            'Sec-Fetch-User': '?1',
        })

        # データディレクトリが存在することを確認
        os.makedirs(self.data_dir, exist_ok=True)

    def scrape_horse_detail(self, detail_url: str, auction_date: Optional[str] = None) -> dict:
        """
        個別の馬の詳細ページから情報を抽出
        
        Args:
            detail_url: 馬の詳細ページURL
            auction_date: オークション開催日（指定がない場合は現在日付を使用）
            
        Returns:
            dict: 馬の情報を含む辞書
        """
        # 馬データを初期化
        horse_data = {
            'name': '不明',
            'sex': '不明',
            'age': None,
            'sire': '不明',
            'dam': '不明',
            'damsire': '不明',
            'jbis_url': '',
            'auction_url': detail_url,
            'disease_tags': []
        }

        # オークションデータを初期化
        auction_data = {
            'weight': None,
            'seller': '不明',
            'auction_date': auction_date or datetime.now().strftime('%Y-%m-%d'),
            'sold_price': None,
            'total_prize_start': '',
            'total_prize_latest': '',
            'bid_num': '',
            'unsold': False,
            'comment': ''
        }

        try:
            # ページを取得
            response = self.session.get(detail_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        except Exception as e:
            print(f"ページの取得中にエラーが発生しました: {e}")
            return horse_data, auction_data

        try:
            # 1. 馬名を取得
            name_elem = soup.find('h1', class_='horseName')
            if name_elem:
                horse_data['name'] = name_elem.get_text(strip=True)

            # 2. 性別と年齢を取得
            title_elem = soup.find('div', class_='horseTitle')
            if title_elem:
                title_text = title_elem.get_text()
                # 性別（牡・牝・セ・騸）
                sex_match = re.search(r'[牡牝セ騸]', title_text)
                if sex_match:
                    horse_data['sex'] = sex_match.group(0)

                # 年齢（数字のみ）
                age_match = re.search(r'(\d+)歳', title_text)
                if not age_match:
                    age_match = re.search(r'\b(\d+)\s*(?:years?|yrs?|yo|才)', title_text, re.IGNORECASE)

                if age_match:
                    try:
                        horse_data['age'] = int(age_match.group(1))
                    except (ValueError, TypeError) as e:
                        print(f"[警告] 年齢の数値変換に失敗: {age_match.group(1)} - {str(e)}")

            # 3. 馬体重の抽出
            weight_elem = soup.find(class_=re.compile(r'weight|horse-weight|wt|kg'))
            if weight_elem:
                weight_text = weight_elem.get_text(strip=True)
                try:
                    # 数字のみを抽出
                    weight_match = re.search(r'(\d+\.?\d*)', weight_text)
                    if weight_match:
                        auction_data['weight'] = float(weight_match.group(1))
                except (ValueError, TypeError) as e:
                    print(f"[警告] 馬体重の数値変換に失敗: {weight_text} - {str(e)}")

            # 4. 売り手情報の取得
            seller_elem = soup.find(class_=re.compile(r'seller|vendor'))
            if seller_elem:
                auction_data['seller'] = seller_elem.get_text(strip=True)

            # 5. 落札価格の取得
            price_elem = soup.find(class_=re.compile(r'price|sold-price|bid-amount'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                try:
                    # 数字のみを抽出（カンマを削除）
                    price = int(re.sub(r'[^0-9]', '', price_text))
                    auction_data['sold_price'] = price
                except (ValueError, TypeError) as e:
                    print(f"[警告] 落札価格の数値変換に失敗: {price_text} - {str(e)}")

            # 6. 入札数の取得
            bid_elem = soup.find(class_=re.compile(r'bid-num|bid-count'))
            if bid_elem:
                auction_data['bid_num'] = bid_elem.get_text(strip=True)

            # 7. 主取りフラグの確認
            unsold_elem = soup.find(class_=re.compile(r'unsold|no-bid|passed'))
            if unsold_elem:
                auction_data['unsold'] = True

            # 8. コメントの取得
            comment_elem = soup.find(class_=re.compile(r'comment|note|remarks'))
            if comment_elem:
                auction_data['comment'] = comment_elem.get_text(strip=True)

        except Exception as e:
            print(f"[エラー] 馬の詳細情報の抽出中にエラーが発生しました: {e}")

        return horse_data, auction_data

    def process_horse_details(self, horses, auction_date=None):
        """各馬の詳細情報を処理する"""
        if not horses:
            return []

        processed_horses = []
        for i, horse in enumerate(horses, 1):
            try:
                print(f"  {i}/{len(horses)}: {horse.get('name', '未確認馬')}")
                # 賞金情報を初期化
                horse['total_prize_start'] = 0.0
                horse['total_prize_latest'] = 0.0

                # 詳細データを取得（auction_dateを渡す）
                if 'detail_url' in horse and horse['detail_url']:
                    detail_data = self.scrape_horse_detail(horse['detail_url'], auction_date)
                    if detail_data:
                        # 重要なフィールドを明示的にマージ
                        for key in [
                            'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller',
                            'auction_date', 'sold_price', 'bid_num', 'weight', 'comment', 'unsold'
                        ]:
                            if key in detail_data[1]:
                                horse[key] = detail_data[1][key]
                            elif key in detail_data[0]:
                                horse[key] = detail_data[0][key]

                processed_horses.append(horse)

            except Exception as e:
                print(f"[エラー] 馬の処理中にエラーが発生しました: {e}")
                continue

        return processed_horses

def get_horse_links():
    """オークションリストページから馬の詳細ページのURLを取得する"""
    import requests
    from bs4 import BeautifulSoup
    from urllib.parse import urljoin
    
    base_url = "https://auction.keiba.rakuten.co.jp/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    }
    
    try:
        print(f"オークションリストページにアクセス中: {base_url}")
        response = requests.get(base_url, headers=headers)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        horse_links = []
        
        # 馬の詳細ページへのリンクを取得
        for link in soup.select('a[href*="/auction/"]'):
            href = link.get('href')
            if href and 'detail' in href:  # 詳細ページへのリンクのみを対象
                full_url = urljoin(base_url, href)
                if full_url not in horse_links:  # 重複を避ける
                    horse_links.append(full_url)
        
        print(f"{len(horse_links)}件の馬の詳細ページURLを取得しました")
        return horse_links
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return []

# メイン実行部分
if __name__ == "__main__":
    print("=== スクレイピングを開始します ===")
    
    # 馬の詳細ページのURLを取得
    horse_links = get_horse_links()
    
    if not horse_links:
        print("馬の詳細ページが見つかりませんでした")
    else:
        # 最初の5件のみ処理（テスト用）
        test_links = horse_links[:5]
        scraper = RakutenAuctionScraper()
        
        for i, url in enumerate(test_links, 1):
            print(f"\n=== {i}/{len(test_links)}: {url} を処理中... ===")
            try:
                horse_data, auction_data = scraper.scrape_horse_detail(url)
                print("=== 取得した馬データ ===")
                print(json.dumps(horse_data, ensure_ascii=False, indent=2))
                print("=== 取得したオークションデータ ===")
                print(json.dumps(auction_data, ensure_ascii=False, indent=2))
            except Exception as e:
                print(f"エラーが発生しました: {e}")
    
    print("\n=== スクレイピング完了 ===")
