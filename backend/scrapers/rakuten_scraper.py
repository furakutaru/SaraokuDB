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
            
            # デバッグ用: 最初の馬のHTMLをファイルに保存
            if not hasattr(self, '_debug_html_saved'):
                with open('debug_horse_page.html', 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"[デバッグ] HTMLを debug_horse_page.html に保存しました")
                self._debug_html_saved = True
                
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

            # 3. 馬体重の抽出（詳細なデバッグログ付き）
            print("[デバッグ] 馬体重の抽出を開始")
            
            # テキスト全体から体重を検索（全角・半角の「kg」や「kg」表記に対応）
            full_text = soup.get_text()
            weight_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ|KG|Kg|kG|KG)', full_text, re.IGNORECASE)
            
            for match in weight_matches:
                try:
                    weight_value = float(match.group(1))
                    # 馬体重として妥当な範囲かチェック（300kg〜700kg）
                    if 300 <= weight_value <= 700:
                        auction_data['weight'] = int(round(weight_value))
                        print(f"[成功] テキストから馬体重を抽出: {auction_data['weight']}kg (マッチ: {match.group(0)})")
                        break
                except (ValueError, TypeError) as e:
                    print(f"[警告] 馬体重の数値変換に失敗: {match.group(1)} - {str(e)}")
            
            # 体重がまだ見つかっていない場合、要素ベースで検索
            if 'weight' not in auction_data:
                print("[デバッグ] テキストからの抽出に失敗したため、要素ベースで検索します")
                weight_elems = soup.find_all(class_=re.compile(r'weight|horse[-_]?weight|wt|kg|馬体重|体重|バルク', re.IGNORECASE))
                print(f"[デバッグ] 体重関連の要素を {len(weight_elems)} 件発見")
            
            for i, elem in enumerate(weight_elems, 1):
                weight_text = elem.get_text(strip=True)
                print(f"[デバッグ] 要素 {i}: テキスト='{weight_text}'")
                
                # 数字 + kg のパターンを検索
                weight_match = re.search(r'(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ|KG|Kg|kG)?', weight_text)
                if weight_match:
                    try:
                        weight_value = float(weight_match.group(1))
                        # 馬体重として妥当な範囲かチェック（300kg〜700kg）
                        if 300 <= weight_value <= 700:
                            auction_data['weight'] = int(round(weight_value))
                            print(f"[成功] 馬体重を抽出: {auction_data['weight']}kg (元テキスト: '{weight_text}')")
                            break  # 最初に見つかった有効な値を使用
                        else:
                            print(f"[警告] 馬体重の値が範囲外です: {weight_value}kg (元テキスト: '{weight_text}')")
                    except (ValueError, TypeError) as e:
                        print(f"[警告] 馬体重の数値変換に失敗: {weight_text} - {str(e)}")
            
            # 体重が見つからなかった場合、テーブル形式のデータを確認
            if 'weight' not in auction_data:
                print("[デバッグ] 通常の要素で体重が見つからなかったため、テーブルを確認します")
                tables = soup.find_all('table')
                for table in tables:
                    rows = table.find_all('tr')
                    for row in rows:
                        th = row.find('th')
                        td = row.find('td')
                        if th and td and '体重' in th.get_text():
                            weight_text = td.get_text(strip=True)
                            print(f"[デバッグ] テーブルから体重を発見: {weight_text}")
                            weight_match = re.search(r'(\d+(?:\.\d+)?)', weight_text)
                            if weight_match:
                                try:
                                    weight_value = float(weight_match.group(1))
                                    if 300 <= weight_value <= 700:
                                        auction_data['weight'] = int(round(weight_value))
                                        print(f"[成功] テーブルから馬体重を抽出: {auction_data['weight']}kg")
                                        break
                                except (ValueError, TypeError) as e:
                                    print(f"[警告] テーブルからの馬体重抽出に失敗: {weight_text} - {str(e)}")

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
                            if key in detail_data[1]:  # auction_data
                                horse[key] = detail_data[1][key]
                                if key == 'weight' and detail_data[1][key] is not None:
                                    print(f"[デバッグ] 馬体重をauction_dataから設定: {detail_data[1][key]}kg")
                            elif key in detail_data[0]:  # horse_data
                                horse[key] = detail_data[0][key]
                                if key == 'weight' and detail_data[0][key] is not None:
                                    print(f"[デバッグ] 馬体重をhorse_dataから設定: {detail_data[0][key]}kg")

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
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and '/item/' in href:  # 詳細ページへのリンクを検出
                full_url = urljoin(base_url, href)
                if full_url not in horse_links:  # 重複を避ける
                    horse_links.append(full_url)
                    print(f"  - 発見: {full_url}")
        
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
    
    # データベースを更新
    print("\n=== データベースを更新しています... ===")
    try:
        db_script = os.path.join(project_root, 'scripts', 'update_database.py')
        if os.path.exists(db_script):
            import subprocess
            result = subprocess.run(['python3', db_script], capture_output=True, text=True)
            print("データベース更新結果:")
            print(result.stdout)
            if result.stderr:
                print("エラー:", result.stderr)
        else:
            print(f"警告: データベース更新スクリプトが見つかりません: {db_script}")
    except Exception as e:
        print(f"データベース更新中にエラーが発生しました: {e}")
