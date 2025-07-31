import os
import re
import time
import json
import requests
from bs4 import BeautifulSoup
from typing import List, Dict, Optional, Union, cast, Any, Tuple
from datetime import datetime
from .data_helpers import (
    save_horse,
    save_auction_history,
    load_json_file
)

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
        
    def is_valid_auction_url(self, url: str) -> bool:
        """
        有効な楽天オークションのURLかどうかをチェックする
        
        Args:
            url: チェックするURL
            
        Returns:
            bool: 有効なURLの場合はTrue、それ以外はFalse
        """
        if not url or not isinstance(url, str):
            return False
            
        # 基本的なURLパターンのチェック
        valid_domains = [
            'auction.keiba.rakuten.co.jp',
            'www.auction.keiba.rakuten.co.jp'
        ]
        
        try:
            from urllib.parse import urlparse
            parsed = urlparse(url)
            
            # ドメインのチェック
            if parsed.netloc not in valid_domains:
                return False
                
            # パスのチェック（/horse/ で始まることを確認）
            if not parsed.path.startswith('/horse/'):
                return False
                
            return True
            
        except Exception as e:
            print(f"URLの検証中にエラーが発生しました: {e}")
            return False
            
    def get_auction_date(self, soup: Optional[BeautifulSoup] = None) -> str:
        """
        ページから開催日を取得
        
        Args:
            soup: BeautifulSoupオブジェクト（省略時は現在日を返す）
            
        Returns:
            str: YYYY-MM-DD形式の日付文字列
        """
        try:
            if soup is None:
                return datetime.now().strftime("%Y-%m-%d")
            
            # 「開始時間」ラベルを検索
            start_time_label = soup.find('span', class_='subData__label', string=lambda text: text and '開始時間' in text)
            if start_time_label:
                # 次の兄弟要素（subData__valueクラス）を取得
                value_elem = start_time_label.find_next_sibling('span', class_='subData__value')
                if value_elem:
                    date_text = value_elem.get_text(strip=True)
                    # 「2016年09月08日 12:00」形式をパース
                    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
                    if match:
                        year, month, day = match.groups()
                        # YYYY-MM-DD形式に変換
                        return f"{year}-{int(month):02d}-{int(day):02d}"
                    
            print("オークション日をページから取得できませんでした。現在日付を使用します。")
            return datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            print(f"開催日の取得に失敗: {e}")
            return datetime.now().strftime("%Y-%m-%d")
    
    def _extract_horse_info_from_detail(self, detail_url: str) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        馬の詳細ページから情報を抽出
        
        Args:
            detail_url: 馬の詳細ページURL
            
        Returns:
            Tuple[horse_data, auction_data]: 馬データとオークションデータのタプル
        """
        # URLのバリデーション
        if not self.is_valid_auction_url(detail_url):
            print(f"無効なURLのためスキップします: {detail_url}")
            # 空のデータを返す
            return ({
                'name': '',
                'sire': '',
                'dam': '',
                'damsire': '',
                'sex': '',
                'age': 0,
                'image_url': '',
                'jbis_url': '',
                'auction_url': detail_url,
                'disease_tags': []
            }, {
                'auction_date': self.get_auction_date(),
                'sold_price': None,
                'total_prize_start': 0.0,
                'total_prize_latest': 0.0,
                'weight': None,
                'seller': '',
                'is_unsold': False,
                'comment': ''
            })
        
        # 基本情報の抽出
        horse_data = {
            'name': '',
            'sire': '',
            'dam': '',
            'damsire': '',
            'sex': '',
            'age': 0,
            'image_url': '',
            'jbis_url': '',
            'auction_url': detail_url,
            'disease_tags': []
        }
        
        # オークション情報（auction_dateは後でsoupが利用可能になったら設定）
        auction_data = {
            'auction_date': '',  # 後で設定
            'sold_price': None,
            'total_prize_start': 0.0,
            'total_prize_latest': 0.0,
            'weight': None,
            'seller': '',
            'is_unsold': False,
            'comment': ''
        }
        
        try:
            print(f"詳細ページにアクセス中: {detail_url}")
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 馬名の抽出
            name_elem = soup.find('h1', class_='horse-name')
            if name_elem:
                horse_data['name'] = name_elem.get_text(strip=True)
            
            # 性別・年齢の抽出（例: "牡3" から性別と年齢を分離）
            info_elem = soup.find('div', class_='horse-info')
            if info_elem:
                info_text = info_elem.get_text()
                # 性別の抽出（例: "牡3" から "牡" を抽出）
                sex_match = re.search(r'([牡牝セ])', info_text)
                if sex_match:
                    horse_data['sex'] = sex_match.group(1)
                
                # 年齢の抽出（例: "牡3" から 3 を抽出）
                age_match = re.search(r'([0-9]+)歳?', info_text)
                if age_match:
                    try:
                        horse_data['age'] = int(age_match.group(1))
                    except (ValueError, TypeError):
                        pass
            
            # 血統情報の抽出
            pedigree_elem = soup.find('div', class_='pedigree')
            if pedigree_elem:
                # 父馬
                sire_elem = pedigree_elem.find('span', class_='sire')
                if sire_elem:
                    horse_data['sire'] = sire_elem.get_text(strip=True)
                
                # 母馬
                dam_elem = pedigree_elem.find('span', class_='dam')
                if dam_elem:
                    horse_data['dam'] = dam_elem.get_text(strip=True)
                
                # 母父
                damsire_elem = pedigree_elem.find('span', class_='damsire')
                if damsire_elem:
                    horse_data['damsire'] = damsire_elem.get_text(strip=True)
            
            # 画像URLの抽出
            img_elem = soup.find('img', class_='horse-image')
            if img_elem and 'src' in img_elem.attrs:
                horse_data['image_url'] = img_elem['src']
            
            # JBIS URLの抽出
            jbis_link = soup.find('a', href=lambda x: x and 'jbis.or.jp' in x)
            if jbis_link:
                horse_data['jbis_url'] = jbis_link['href']
            
            # 落札価格の抽出
            price_elem = soup.find('div', class_='price')
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                if '主取り' in price_text:
                    auction_data['is_unsold'] = True
                else:
                    price_match = re.search(r'([0-9,]+)万円', price_text)
                    if price_match:
                        try:
                            auction_data['sold_price'] = int(price_match.group(1).replace(',', '')) * 10000
                        except (ValueError, TypeError):
                            pass
            
            # 賞金情報の抽出
            prize_elem = soup.find('div', class_='prize-money')
            if prize_elem:
                prize_text = prize_elem.get_text()
                prize_match = re.search(r'([0-9,.]+)万円', prize_text)
                if prize_match:
                    try:
                        prize = float(prize_match.group(1).replace(',', ''))
                        auction_data['total_prize_start'] = prize
                        auction_data['total_prize_latest'] = prize
                    except (ValueError, TypeError):
                        pass
            
            # 馬体重の抽出
            weight_elem = soup.find('div', class_='weight')
            if weight_elem:
                weight_text = weight_elem.get_text(strip=True)
                weight_match = re.search(r'([0-9]+)kg', weight_text)
                if weight_match:
                    try:
                        auction_data['weight'] = int(weight_match.group(1))
                    except (ValueError, TypeError):
                        pass
            
            # 売り主情報の抽出
            seller_elem = soup.find('div', class_='seller')
            if seller_elem:
                auction_data['seller'] = seller_elem.get_text(strip=True)
            
            # コメントの抽出
            comment_elem = soup.find('div', class_='comment')
            if comment_elem:
                auction_data['comment'] = comment_elem.get_text(strip=True)
            
            # 疾病タグの抽出
            disease_elems = soup.find_all('span', class_='disease-tag')
            if disease_elems:
                horse_data['disease_tags'] = [elem.get_text(strip=True) for elem in disease_elems]
            
            print(f"詳細情報を抽出完了: {horse_data['name']}")
            
        except Exception as e:
            print(f"詳細ページの処理中にエラーが発生: {str(e)}")
        
        return horse_data, auction_data

    def scrape_horse_list(self, max_horses: int = 5) -> List[Dict]:
        """
        トップページから馬のリストを取得し、各馬の詳細情報をスクレイピング
        
        Args:
            max_horses: 処理する最大の馬の数（デバッグ用）
            
        Returns:
            List[Dict]: スクレイピングした馬のリスト
        """
        try:
            print("トップページにアクセス中...")
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            print(f"レスポンスステータス: {response.status_code}")
            
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # デバッグ: ページタイトルを確認
            title = soup.find('title')
            if title:
                print(f"ページタイトル: {title.get_text(strip=True)}")
            
            # デバッグ: 全div要素の数を確認
            all_divs = soup.find_all('div')
            print(f"全div要素数: {len(all_divs)}")
            
            # 馬のリストを取得
            horse_elems = soup.select('.auctionTableCard')
            print(f"{len(horse_elems)}頭の馬を検出 (最大{max_horses}頭まで処理)")
            
            processed_count = 0
            for i, horse_elem in enumerate(horse_elems, 1):
                if processed_count >= max_horses > 0:
                    print(f"最大処理数 {max_horses} 頭に達したため処理を終了します")
                    break
                    
                try:
                    # 馬名と詳細URLを取得
                    name_elem = horse_elem.select_one('.auctionTableCard__name a')
                    if not name_elem or not name_elem.get('href'):
                        print(f"{i}頭目: 馬名または詳細URLが見つかりません")
                        continue
                        
                    horse_name = name_elem.get('title', '').strip() or name_elem.get_text(strip=True)
                    detail_url = name_elem.get('href', '').strip()
                    
                    if not detail_url:
                        print(f"{i}頭目 ({horse_name}): 詳細URLが空です")
                        continue
                    
                    # 相対URLを絶対URLに変換
                    if not detail_url.startswith('http'):
                        detail_url = self.base_url.rstrip('/') + '/' + detail_url.lstrip('/')
                    
                    # URLのバリデーション
                    if not self.is_valid_auction_url(detail_url):
                        print(f"{i}頭目 ({horse_name}): 無効なURLのためスキップします: {detail_url}")
                        continue
                    
                    print(f"\n--- {i}頭目: {horse_name} の処理を開始します ---")
                    
                    # 詳細ページから情報を取得
                    horse_data, auction_data = self._extract_horse_info_from_detail(detail_url)
                    
                    if not horse_data.get('name'):
                        horse_data['name'] = horse_name  # 詳細ページから名前が取得できなかった場合はリストの名前を使用
                    
                    # 総賞金を取得（リストページの値を使用）
                    prize_elem = horse_elem.select_one('.auctionTableCard__price .value')
                    if prize_elem:
                        prize_text = prize_elem.get_text(strip=True)
                        prize_match = re.search(r'([\d,]+)(?:\.\d+)?万?円?', prize_text)
                        if prize_match:
                            try:
                                prize = float(prize_match.group(1).replace(',', ''))
                                auction_data['total_prize_start'] = prize
                                auction_data['total_prize_latest'] = prize
                            except (ValueError, TypeError):
                                pass
                    
                    # 馬情報を保存（辞書形式で渡す）
                    horse_data_to_save = {
                        'name': horse_data['name'],
                        'age': horse_data['age'],
                        'sire': horse_data.get('sire', ''),
                        'dam': horse_data.get('dam', ''),
                        'damsire': horse_data.get('damsire', ''),
                        'sex': horse_data.get('sex', ''),
                        'image_url': horse_data.get('image_url', ''),
                        'jbis_url': horse_data.get('jbis_url', ''),
                        'auction_url': horse_data.get('auction_url', ''),
                        'disease_tags': horse_data.get('disease_tags', [])
                    }
                    saved_horse = save_horse(horse_data_to_save, self.data_dir)
                    
                    # オークション履歴を保存（辞書形式で渡す）
                    history_data = {
                        'horse_id': saved_horse['id'],
                        'auction_date': auction_data.get('auction_date', ''),
                        'sold_price': auction_data.get('sold_price'),
                        'total_prize_start': auction_data.get('total_prize_start', 0.0),
                        'total_prize_latest': auction_data.get('total_prize_latest', 0.0),
                        'weight': auction_data.get('weight'),
                        'seller': auction_data.get('seller', ''),
                        'is_unsold': auction_data.get('is_unsold', False),
                        'comment': auction_data.get('comment', '')
                    }
                    save_auction_history(history_data, self.data_dir)
                    
                    print(f"{i}頭目: {horse_name} の情報を保存しました")
                    processed_count += 1
                    
                    # サーバーに負荷をかけないように少し待機
                    time.sleep(1)
                    
                except Exception as e:
                    print(f"{i}頭目の処理中にエラーが発生: {str(e)}")
                    import traceback
                    traceback.print_exc()
                    continue
            
            print(f"\n--- 処理完了 ---")
            print(f"合計 {processed_count} 頭の馬の情報を処理しました")
            
            # 処理した馬のリストを返す
            horses_file = os.path.join(self.data_dir, 'horses.json')
            if os.path.exists(horses_file):
                with open(horses_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            return []
                    
        except Exception as e:
            print(f"馬リストの取得中にエラーが発生: {str(e)}")
            import traceback
            traceback.print_exc()
            return []
    
    def _extract_horse_basic_info(self, card) -> Optional[Dict]:
        """馬カードから基本情報を抽出"""
        try:
            # 馬名とリンク
            name_element = card.find(class_="auctionTableCard__name")
            if name_element:
                name_link = name_element.find('a')
                if name_link:
                    # title属性があれば優先
                    horse_name = name_link.get('title') or name_link.get_text(strip=True)
                    detail_url = name_link.get('href')
                    if detail_url and not detail_url.startswith('http'):
                        detail_url = self.base_url + detail_url
                else:
                    return None
            else:
                return None
            
            # 総賞金（万円単位）
            price_element = card.find(class_="auctionTableCard__price")
            total_prize = 0
            if price_element:
                value_element = price_element.find(class_="value")
                if value_element:
                    price_text = value_element.get_text(strip=True)
                    # "72.0万円" から数値を抽出（万円単位で保存）
                    match = re.search(r'(\d+\.?\d*)', price_text)
                    if match:
                        total_prize = float(match.group(1))  # 万円単位で保存
            
            # 販売申込者
            seller_element = card.find(class_="auctionTableCard__seller")
            seller = ""
            if seller_element:
                value_element = seller_element.find(class_="value")
                if value_element:
                    seller = value_element.get_text(strip=True)
            
            # 性別と年齢
            sex_age_element = card.find(class_="horseLabelWrapper")
            sex = ""
            age = 0
            if sex_age_element:
                sex_element = sex_age_element.find(class_="horseLabelWrapper__horseSex")
                age_element = sex_age_element.find(class_="horseLabelWrapper__horseAge")
                
                if sex_element:
                    sex = sex_element.get_text(strip=True)
                if age_element:
                    age_text = age_element.get_text(strip=True)
                    age_match = re.search(r'(\d+)', age_text)
                    if age_match:
                        age = int(age_match.group(1))
            
            return {
                'name': horse_name,
                'detail_url': detail_url,
                'total_prize_start': total_prize,
                'total_prize_latest': total_prize,
                'seller': seller,
                'sex': sex,
                'age': age
            }
            
        except Exception as e:
            print(f"基本情報の抽出に失敗: {e}")
            return None
    
    def scrape_horse_detail(self, detail_url: str, auction_date: Optional[str] = None) -> Optional[Dict]:
        """個別ページから詳細情報を取得"""
        # URLのバリデーション
        if not self.is_valid_auction_url(detail_url):
            print(f"無効なURLのためスキップします: {detail_url}")
            return None
            
        try:
            print(f"詳細ページにアクセス中: {detail_url}")
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            detail_data = {}

            # 馬名（h1.itemDetail__title or titleタグ）
            name_tag = soup.find('h1', class_='itemDetail__title')
            full_name = name_tag.get_text(strip=True) if name_tag and name_tag.get_text() is not None else ''
            if not full_name:
                title_tag = soup.find('title')
                if title_tag and title_tag.get_text() is not None:
                    full_name = title_tag.get_text(strip=True)
            name_match = re.match(r'^([\w\-ァ-ヶ一-龠ぁ-んＡ-Ｚａ-ｚA-Za-z0-9]+)', full_name)
            horse_name = name_match.group(1) if name_match else full_name.split()[0] if full_name else ''
            if not horse_name:
                print(f"[異常] 馬名が抽出できません: {detail_url}")
                horse_name = ''
            detail_data['name'] = horse_name

            # --- JBISリンク抽出を追加 ---
            jbis_url = ''
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    # /record/が付いている場合は除去して基本情報ページのURLを作成
                    if '/record/' in href:
                        basic_info_url = href.replace('/record/', '')
                        if not basic_info_url.endswith('/'):
                            basic_info_url += '/'
                        jbis_url = basic_info_url
                    else:
                        jbis_url = href
                    break
            detail_data['jbis_url'] = jbis_url
            # --- ここまで追加 ---

            # 馬齢（「○歳」や「牡/牝○歳」パターン）
            page_text = soup.get_text() or ''
            age = ''
            age_match = re.search(r'([0-9]{1,2})歳', page_text)
            if age_match:
                age = age_match.group(1)
            detail_data['age'] = age if age else '0'  # デフォルト値を'0'に設定
            if not age:
                print(f"[警告] 馬齢が抽出できません: {detail_url}")
                detail_data['age'] = '0'  # デフォルト値を'0'に設定

            # 性別（「牡」「牝」「セン」パターン）
            sex = ''
            # タイトルやh1タグから必ず抽出
            title_text = ''
            if name_tag and name_tag.get_text() is not None:
                title_text = name_tag.get_text().strip()
            else:
                title_tag = soup.find('title')
                if title_tag and title_tag.get_text() is not None:
                    title_text = title_tag.get_text().strip()
            
            try:
                sex_match = re.match(r'^.+?[ \t\u3000]+(牡|牝|セン)[ \t\u3000]*\d{1,2}歳', title_text)
                if sex_match:
                    sex = sex_match.group(1)
                else:
                    print(f"[警告] 性別がタイトルから抽出できません: {title_text} ({detail_url})")
            except Exception as e:
                print(f"[警告] 性別の抽出中にエラーが発生: {e}")
            
            detail_data['sex'] = sex if sex else '不明'  # デフォルト値を'不明'に設定
            if not sex:
                print(f"[警告] 性別が抽出できません: {detail_url}")
                detail_data['sex'] = '不明'  # デフォルト値を'不明'に設定

            # 血統（父・母・母父）
            pedigree = self._extract_pedigree_from_page(soup)
            # 血統情報を取得（damsireとdam_sireの両方を設定）
            detail_data['sire'] = str(pedigree.get('sire', '')) if pedigree.get('sire') else '不明'  # デフォルト値を'不明'に設定
            detail_data['dam'] = str(pedigree.get('dam', '')) if pedigree.get('dam') else '不明'  # デフォルト値を'不明'に設定
            damsire = str(pedigree.get('damsire', '')) if pedigree.get('damsire') else '不明'  # デフォルト値を'不明'に設定
            detail_data['damsire'] = damsire
            detail_data['dam_sire'] = damsire  # 後方互換性のため
            
            # デバッグ用に血統情報を出力
            print(f"血統情報 - 父: {detail_data['sire'] or 'N/A'}, 母: {detail_data['dam'] or 'N/A'}, 母父: {damsire or 'N/A'}")
            
            # 血統情報が空の場合は警告を出力
            if not detail_data['sire'] or detail_data['sire'] == '不明':
                print(f"[警告] 父が抽出できません: {detail_url}")
                detail_data['sire'] = '不明'  # デフォルト値を'不明'に設定
                
            if not detail_data['dam'] or detail_data['dam'] == '不明':
                print(f"[警告] 母が抽出できません: {detail_url}")
                detail_data['dam'] = '不明'  # デフォルト値を'不明'に設定
                
            if not damsire or damsire == '不明':
                print(f"[警告] 母父が抽出できません: {detail_url}")
                detail_data['damsire'] = '不明'  # デフォルト値を'不明'に設定
                detail_data['dam_sire'] = '不明'  # デフォルト値を'不明'に設定
                
            # オークション日付を設定
            if auction_date:
                detail_data['auction_date'] = auction_date
            else:
                detail_data['auction_date'] = self.get_auction_date() or datetime.now().strftime('%Y-%m-%d')
            
            # オークション日付がまだ空の場合は現在日付を設定
            if not detail_data.get('auction_date'):
                detail_data['auction_date'] = datetime.now().strftime('%Y-%m-%d')
                print(f"[警告] オークション日付が設定されていないため、現在日時を設定: {detail_data['auction_date']}")

            # 販売申込者（「（」以降を除去）
            seller = ''
            seller_match = re.search(r'販売申込者[：:]([^\n\r\t]+)', page_text)
            if seller_match:
                seller = seller_match.group(1).strip()
                seller = re.sub(r'（.*$', '', seller).strip()
            detail_data['seller'] = seller if seller else '不明'  # デフォルト値を'不明'に設定
            if not seller:
                print(f"[警告] 販売申込者が抽出できません: {detail_url}")
                detail_data['seller'] = '不明'  # デフォルト値を'不明'に設定

            # 総賞金（auctionTableRow__priceからlabel=総賞金のvalueを取得）
            # total_prize = self._extract_prize_money_from_soup(soup)  # ←未実装なので削除
            # 総賞金は詳細ページでは設定しない（リストで取得した値を使用）
            # 詳細ページの総賞金は信頼性が低いため、scrape_all_horsesで上書きする
            detail_data['total_prize_start'] = ''
            detail_data['total_prize_latest'] = ''

            # 賞金情報を正規表現で抽出
            central_prize = 0.0
            local_prize = 0.0
            
            # 中央競馬の賞金を抽出（正規表現）
            central_prize = 0.0
            central_match = re.search(r'中央[\s\S]*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)[\s\u3000]*万円', page_text)
            if central_match:
                try:
                    central_prize = float(central_match.group(1).replace(',', ''))
                except (ValueError, AttributeError) as e:
                    print(f"中央競馬の賞金抽出エラー: {e}")
            
            # 地方競馬の賞金を抽出（正規表現）
            local_prize = 0.0
            local_match = re.search(r'地方[\s\S]*?(\d{1,3}(?:,\d{3})*(?:\.\d+)?)[\s\u3000]*万円', page_text)
            if local_match:
                try:
                    local_prize = float(local_match.group(1).replace(',', ''))
                except (ValueError, AttributeError) as e:
                    print(f"地方競馬の賞金抽出エラー: {e}")
            
            # 総賞金を計算（万円単位で保存）
            total_prize_float = central_prize + local_prize
            if total_prize_float > 0:
                detail_data['total_prize_start'] = str(total_prize_float)  # 万円単位で保存
                detail_data['total_prize_latest'] = str(total_prize_float)  # 万円単位で保存
                detail_data['prize'] = f"{total_prize_float}万円"
            else:
                detail_data['total_prize_start'] = ''  # 空文字列で統一
                detail_data['total_prize_latest'] = ''  # 空文字列で統一
                detail_data['prize'] = ""  # 空文字列

            # --- ここから主取り判定・入札数取得 ---
            # 開始価格
            start_price = ''
            start_price_elem = soup.find('th', string='開始価格')
            if start_price_elem and start_price_elem.find_next_sibling('td'):
                start_price_text = start_price_elem.find_next_sibling('td').get_text(strip=True)
                if start_price_text and start_price_text != '-':
                    try:
                        start_price = str(int(start_price_text.replace('万円', '').replace(',', '')))
                    except (ValueError, AttributeError):
                        start_price = ''
            detail_data['start_price'] = start_price

            # 落札価格（itemprop="price" で検索）
            sold_price = 0  # デフォルト値は0
            price_elem = soup.find(attrs={"itemprop": "price"})
            if price_elem and price_elem.get_text(strip=True):
                try:
                    sold_price_text = price_elem.get_text(strip=True)
                    # カンマを削除して数値に変換
                    sold_price = int(sold_price_text.replace(',', ''))
                    # 万円単位に変換（必要に応じて調整）
                    if sold_price < 10000:  # 1万円未満の場合は1万円単位とみなす
                        sold_price *= 10000
                    sold_price = sold_price // 10000  # 万円単位に変換
                except (ValueError, AttributeError) as e:
                    print(f"落札価格の抽出に失敗: {e}")
                    sold_price = 0
            detail_data['sold_price'] = sold_price
            print(f"落札価格を設定: {sold_price}万円")  # デバッグ用

            # 入札数
            bid_num = ''
            bid_num_elem = soup.find('th', string='入札数')
            if bid_num_elem and bid_num_elem.find_next_sibling('td'):
                bid_num_text = bid_num_elem.find_next_sibling('td').get_text(strip=True)
                if bid_num_text and bid_num_text != '-':
                    try:
                        bid_num = str(int(bid_num_text.replace('回', '').strip()))
                    except (ValueError, AttributeError):
                        bid_num = ''
            detail_data['bid_num'] = bid_num

            # 主取り判定
            unsold = False
            if (bid_num == '') or (start_price != '' and sold_price != '' and start_price == sold_price):
                unsold = True
            detail_data['unsold'] = unsold
            # --- ここまで主取り判定・入札数取得 ---

            # コメント抽出を改善
            comment = self._extract_comment(soup)
            
            # デバッグ情報を出力
            if comment:
                print(f"【デバッグ】コメントを抽出: {comment[:100]}...")
            else:
                print(f"[警告] コメントが見つかりませんでした: {detail_url}")
                # デバッグ用にページの構造を出力
                with open('debug_page.html', 'w', encoding='utf-8') as f:
                    f.write(str(soup))
            detail_data['comment'] = comment

            # デバッグ用にHTMLを保存
            with open('debug_pedigree_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
                print("デバッグ: 血統情報抽出前のHTMLをdebug_pedigree_page.htmlに保存しました")
            
            # その他（既存ロジック）
            detail_data['weight'] = self._extract_weight(soup)
            
            # レース成績を取得（未出走の場合は「未出走」、成績が見つからない場合はNoneが返る）
            race_record = self._extract_race_record(soup)
            detail_data['race_record'] = race_record or ''  # Noneの場合は空文字列に
            
            # 未出走馬の場合の処理
            if race_record == '未出走':
                detail_data['total_prize_start'] = ''  # 空文字列で統一
                detail_data['total_prize_latest'] = ''  # 空文字列で統一
                detail_data['prize'] = ""  # 空文字列
                print(f"  - 未出走馬のため総賞金を0.0万円に設定")
            # 成績が見つからない場合はログを出力（エラー検知のため）
            elif race_record is None:
                print(f"  - 警告: レース成績が見つかりませんでした")
            
            detail_data['disease_tags'] = self._extract_disease_tags(detail_data.get('comment', ''))
            detail_data['primary_image'] = self._extract_primary_image(soup)
            detail_data['jbis_url'] = self._extract_jbis_url(soup)
            
            # auction_dateを設定
            if auction_date:
                detail_data['auction_date'] = auction_date

            return detail_data
        except Exception as e:
            print(f"詳細情報の取得に失敗: {e}")
            return None
    
    def _extract_pedigree_from_page(self, soup) -> dict:
        """
        ページから血統情報（父・母・母父）を抽出する
        
        Returns:
            dict: 以下のキーを含む辞書
                - sire: 父馬名
                - dam: 母馬名
                - damsire: 母父馬名
        """
        try:
            # テキストを取得（改行や連続スペースを1つのスペースに正規化）
            text = ' '.join(soup.get_text(separator=' ').split())
            
            # デバッグ用にテキストを出力
            print(f"【デバッグ】抽出テキスト: {text[:200]}...")
            
            # デフォルト値
            sire = ""
            dam = ""
            damsire = ""
            
            # パターン1: 「父：XXX 母：YYY 母の父：ZZZ」形式
            pattern1 = r'父[：:]\s*([^ 　(（]+)(?:\s*[(（][^)）]+[)）])?\s*母[：:]\s*([^ 　(（]+)(?:\s*[(（][^)）]+[)）])?\s*(?:母の?父|母父)[：:]\s*([^ 　(（]+)'
            match = re.search(pattern1, text)
            if match:
                sire = match.group(1).strip()
                dam = match.group(2).strip()
                if len(match.groups()) >= 3 and match.group(3):
                    damsire = match.group(3).strip()
                print(f"【デバッグ】パターン1で抽出: 父={sire}, 母={dam}, 母父={damsire}")
                return {'sire': sire, 'dam': dam, 'damsire': damsire}
            
            # パターン2: 「父：XXX 母：YYY」形式（母父なし）
            pattern2 = r'父[：:]\s*([^ 　(（]+)(?:\s*[(（][^)）]+[)）])?\s*母[：:]\s*([^ 　(（]+)'
            match = re.search(pattern2, text)
            if match:
                sire = match.group(1).strip()
                dam = match.group(2).strip()
                print(f"【デバッグ】パターン2で抽出: 父={sire}, 母={dam}")
                return {'sire': sire, 'dam': dam, 'damsire': damsire}
            
            # パターン3: テーブル形式など別のレイアウト
            # 父・母・母父のラベルを直接探す
            for label, key in [('父', 'sire'), ('母', 'dam'), ('母の父', 'damsire'), ('母父', 'damsire')]:
                elem = soup.find(string=re.compile(f'^{label}[：:]'))
                if elem:
                    parent_text = elem.find_next(string=True).strip()
                    if key == 'sire':
                        sire = parent_text.split()[0] if parent_text else ""
                    elif key == 'dam':
                        dam = parent_text.split()[0] if parent_text else ""
                    elif key == 'damsire':
                        damsire = parent_text.split()[0] if parent_text else ""
            
            # デバッグ情報を出力
            print(f"【デバッグ】最終抽出結果: 父={sire}, 母={dam}, 母父={damsire}")
            
            return {
                'sire': sire or '',
                'dam': dam or '',
                'damsire': damsire or ''
            }
            
        except Exception as e:
            print(f"血統情報の抽出に失敗: {e}")
            # エラー時も空文字を返す
            return {
                'sire': '',
                'dam': '',
                'damsire': ''
            }

    def _extract_weight(self, soup) -> str:
        """
        馬体重を抽出
        
        Returns:
            str: 馬体重（例: "450"）または空文字列（見つからない場合）
        """
        try:
            page_text = soup.get_text()
            weight_match = re.search(r'(\d{3,4})[㎏kg]', page_text)
            if weight_match:
                return str(int(weight_match.group(1)))  # 文字列に変換して返す
        except Exception as e:
            print(f"馬体重の抽出に失敗: {e}")
        return ""  # 見つからない場合は空文字列を返す
    
    def _extract_race_record(self, soup) -> str:
        """
        成績を抽出
        
        Returns:
            str: 
                - レース成績（例: "24戦4勝［4-6-2-12］"）
                - 明示的に未出走の場合は「未出走」
                - 成績が見つからない場合は空文字列
        """
        try:
            page_text = soup.get_text()
            
            # 成績パターンを探す（例: "24戦4勝［4-6-2-12］"）
            record_match = re.search(r'(\d+戦\d+勝［\d+-\d+-\d+-\d+］)', page_text)
            if record_match:
                result = record_match.group(1)
                if result is not None:
                    return str(result)
            
            # 明示的に未出走と記載がある場合のみ「未出走」を返す
            if '未出走' in page_text or '出走前' in page_text:
                return "未出走"
            
            # 成績が見つからない場合は空文字列を返す
            return ""
            
        except Exception as e:
            print(f"成績の抽出に失敗: {e}")
            return ""  # エラー時は空文字列を返す
    
    def _extract_comment(self, soup) -> str:
        """
        コメント欄を抽出する。
        「本馬について」の見出しの直後の<pre>タグ内のテキストを取得する。
        
        Returns:
            str: 抽出されたコメントテキスト。見つからない場合は空文字列。
        """
        try:
            # デバッグ用にHTML全体を保存
            with open('debug_comment_page.html', 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            # 「本馬について」の見出しを探す
            about_heading = soup.find('b', string='本馬について')
            if not about_heading:
                print("「本馬について」の見出しが見つかりませんでした")
                # ページ内の全テキストを確認
                all_text = soup.get_text()
                print(f"ページの先頭500文字: {all_text[:500]}...")
                return ""
                
            print(f"「本馬について」見出しを発見: {about_heading}")
            
            # 見出しの直後のhrタグを探す
            hr_tag = about_heading.find_next('hr')
            if not hr_tag:
                print("hrタグが見つかりませんでした")
                # hrタグがなくても、次の要素を探してみる
                next_element = about_heading.find_next()
                print(f"見出しの次にある要素: {next_element}")
                return ""
                
            # hrタグの直後のpreタグを探す
            pre_tag = hr_tag.find_next('pre')
            if not pre_tag:
                print("preタグが見つかりませんでした")
                # preタグがなければ、hrタグ以降のテキストを取得してみる
                next_siblings = []
                current = hr_tag.next_sibling
                while current and len(next_siblings) < 10:  # 最大10要素まで
                    if hasattr(current, 'name') and current.name:
                        next_siblings.append(str(current))
                    current = current.next_sibling
                print(f"hrタグの後の要素: {' | '.join(next_siblings[:3])}...")
                return ""
                
            # preタグ内のテキストを取得して返す
            comment = pre_tag.get_text(separator='\n', strip=True)
            print(f"コメントを抽出しました（長さ: {len(comment)}文字）")
            return comment
            
        except Exception as e:
            print(f"コメントの抽出に失敗: {e}")
            # エラーが発生した箇所を特定するため、スタックトレースを出力
            import traceback
            traceback.print_exc()
            return ""
    
    def _extract_disease_tags(self, comment: str) -> str:
        """
        コメントから疾病タグを抽出（複数該当時はカンマ区切り、重複なし）
        
        Args:
            comment: 抽出対象のコメントテキスト
            
        Returns:
            str: 抽出されたタグをカンマ区切りで返す。該当なしの場合は空文字を返す
        """
        try:
            if not comment or not isinstance(comment, str):
                print("【デバッグ】コメントが空または文字列ではありません")
                return ""
                
            print(f"【デバッグ】コメントの最初の100文字: {comment[:100]}...")  # デバッグ用
            
            # 正規化: 全角・半角の統一、改行・タブをスペースに置換
            normalized_comment = comment.translate(
                str.maketrans({
                    '\n': ' ', '\t': ' ', '　': ' ',  # 全角スペースも半角に
                    '（': '(', '）': ')', '［': '[', '］': ']',
                    '，': ',', '．': '.', '：': ':', '；': ';',
                    '・': ' ', '、': ' ', '。': ' '  # 句読点もスペースに
                })
            )
            
            print(f"【デバッグ】正規化後: {normalized_comment[:100]}...")  # デバッグ用
            
            # 疾病キーワードと正規表現パターンのマッピング（シンプル化）
            disease_patterns = {
                '骨折': [r'骨折', r'こっせつ'],
                '屈腱炎': [r'屈腱炎', r'くっけんえん'],
                '球節炎': [r'球節炎', r'きゅうせつえん'],
                '蹄葉炎': [r'蹄葉炎', r'ていようえん'],
                '靭帯損傷': [r'靭帯(損傷|断裂)'],
                '捻挫': [r'捻挫', r'ねんざ'],
                '腫れ': [r'腫[れ脹]', r'はれ'],
                '炎症': [r'(?<![無な])炎症', r'えんしょう(?![なな])'],
                '裂蹄': [r'裂蹄', r'れってい'],
                '骨瘤': [r'骨瘤', r'こつりゅう'],
                '関節炎': [r'関節炎', r'かんせつえん'],
                '筋炎': [r'筋炎', r'きんえん'],
                '筋肉痛': [r'筋肉痛', r'きんにくつう'],
                '神経麻痺': [r'神経麻痺', r'しんけいまひ'],
                '腰痛': [r'腰痛', r'ようつう'],
                '跛行': [r'跛行', r'はこう'],
                '蹄壁疾患': [r'蹄壁(疾患|異常)'],
                '蹄叉腐爛': [r'蹄叉腐爛', r'ていさふらん'],
                '骨膜炎': [r'骨膜炎', r'こつまくえん'],
                '亀裂': [r'亀裂', r'きれつ'],
                '外傷': [r'外傷', r'がいしょう'],
                '脱臼': [r'脱[臼]?', r'だっ[きゅう]'],
                '肉離れ': [r'肉離れ', r'にくばなれ'],
                '裂傷': [r'裂傷', r'れっしょう'],
                '打撲': [r'打撲', r'だぼく'],
                '挫傷': [r'挫傷', r'ざしょう'],
                '腫瘍': [r'腫瘍', r'しゅよう'],
                '出血': [r'出血', r'しゅっけつ'],
                '貧血': [r'貧血', r'ひんけつ'],
                '皮膚病': [r'皮膚病', r'ひふびょう', r'皮膚炎'],
                '呼吸器疾患': [r'呼吸器(疾患|異常)'],
                '心臓病': [r'心臓(病|疾患|異常)'],
                '腎臓病': [r'腎臓(病|疾患|異常)'],
                '肝臓病': [r'肝臓(病|疾患|異常)'],
                '消化器疾患': [r'消化器(疾患|異常)'],
                '眼病': [r'眼(病|疾患|異常)'],
                '歯牙疾患': [r'歯(牙)?(疾患|異常)'],
                '蹄病': [r'蹄(病|疾患|異常)'],
                '関節疾患': [r'関節(疾患|異常)'],
                '骨疾患': [r'骨(疾患|異常)'],
                '筋肉疾患': [r'筋肉(疾患|異常)'],
                '神経疾患': [r'神経(疾患|異常)'],
                '循環器疾患': [r'循環器(疾患|異常)'],
                '感染症': [r'感染症', r'かんせんしょう'],
                'ウイルス性疾患': [r'ウイルス(性)?(疾患|感染)'],
                '細菌性疾患': [r'細菌(性)?(疾患|感染)'],
                '真菌性疾患': [r'真菌(性)?(疾患|感染)'],
                'アレルギー': [r'アレルギー', r'あれるぎー'],
                '自己免疫疾患': [r'自己免疫(疾患|異常)'],
                '代謝性疾患': [r'代謝(性)?(疾患|異常)'],
                '内分泌疾患': [r'内分泌(疾患|異常)'],
                '腫瘍性疾患': [r'腫瘍(性)?(疾患|異常)'],
                '先天性疾患': [r'先天性(疾患|異常)'],
                '後天性疾患': [r'後天性(疾患|異常)'],
                '外傷性疾患': [r'外傷(性)?(疾患|異常)'],
                '中毒性疾患': [r'中毒(性)?(疾患|異常)'],
                '栄養性疾患': [r'栄養(性)?(疾患|異常)'],
                '環境性疾患': [r'環境(性)?(疾患|異常)'],
                'ストレス性疾患': [r'ストレス(性)?(疾患|異常)'],
                '加齢性疾患': [r'加齢(性)?(疾患|異常)']
            }
            
            # 除外パターン（整理版）
            exclude_patterns = [
                # 骨折関連の除外パターン
                r'骨折[な無]い',         # 「骨折ない」
                r'骨折[はも]?無い',      # 「骨折は無い」「骨折も無い」
                r'骨折[はも]?ない',      # 「骨折はない」「骨折もない」
                r'骨折[はも]?無し',      # 「骨折は無し」「骨折も無し」
                r'骨折[はも]?なし',      # 「骨折はなし」「骨折もなし」
                r'骨折[はも]?無',        # 「骨折は無」「骨折も無」
                r'骨折[はも]?無[かっ]?た', # 「骨折は無かった」「骨折も無かった」
                r'骨折[はも]?な[かっ]?た', # 「骨折はなかった」「骨折もなかった」
                r'骨折[はも]?無いです',  # 「骨折は無いです」「骨折も無いです」
                r'骨折[はも]?無いと',    # 「骨折は無いと」「骨折も無いと」
                r'骨折[はも]?無いが',    # 「骨折は無いが」「骨折も無いが」
                r'骨折[はも]?無いので',  # 「骨折は無いので」「骨折も無いので」
                r'無骨折',               # 「無骨折」
                
                # 炎症関連の除外パターン
                r'[な無]?炎症',          # 「無炎症」「な炎症」
                r'炎症[はも]?無い',      # 「炎症は無い」「炎症も無い」
                r'炎症[はも]?ない',      # 「炎症はない」「炎症もない」
                r'炎症[はも]?無し',      # 「炎症は無し」「炎症も無し」
                r'炎症[はも]?なし',      # 「炎症はなし」「炎症もなし」
                r'炎症[はも]?無',        # 「炎症は無」「炎症も無」
                r'炎症[はも]?無かった',  # 「炎症は無かった」「炎症も無かった」
                r'炎症[はも]?な[かっ]?た', # 「炎症はなかった」「炎症もなかった」
                r'炎症[はも]?無[かっ]?た', # 「炎症は無かった」「炎症も無かった」
                r'炎症[はも]?無いです',  # 「炎症は無いです」「炎症も無いです」
                r'炎症[はも]?無いと',    # 「炎症は無いと」「炎症も無いと」
                r'炎症[はも]?無いが',    # 「炎症は無いが」「炎症も無いが」
                r'炎症[はも]?無いので',  # 「炎症は無いので」「炎症も無いので」
                
                # その他の一般的な除外パターン
                r'異常[な無]',    # 「異常なし」「異常な」
                r'問題[な無]',    # 「問題なし」「問題な」
                r'心配[な無]',    # 「心配なし」「心配な」
                r'懸念[な無]',    # 「懸念なし」「懸念な」
                r'所見[な無]',    # 「所見なし」「所見な」
                r'特記[な無]',    # 「特記なし」「特記な」
                r'以上[な無]',    # 「以上なし」「以上な」
                r'その他[な無]',  # 「その他なし」「その他な」
                r'特にな[し無]',  # 「特になし」「特に無」
                r'現在[はも]?無い', # 「現在は無い」「現在も無い」
                r'現在[はも]?ない', # 「現在はない」「現在もない」
                r'現在[はも]?無し', # 「現在は無し」「現在も無し」
                r'現在[はも]?なし', # 「現在はなし」「現在もなし」
                r'現在[はも]?無',   # 「現在は無」「現在も無」
                r'現在[はも]?無かった', # 「現在は無かった」「現在も無かった」
                r'現在[はも]?な[かっ]?た', # 「現在はなかった」「現在もなかった」
                r'現在[はも]?無[かっ]?た', # 「現在は無かった」「現在も無かった」
                r'現在[はも]?無いです', # 「現在は無いです」「現在も無いです」
                r'現在[はも]?無いと',   # 「現在は無いと」「現在も無いと」
                r'現在[はも]?無いが',   # 「現在は無いが」「現在も無いが」
                r'現在[はも]?無いので'  # 「現在は無いので」「現在も無いので」
            ]
            
            found = set()
            
            # 各パターンでマッチング
            for tag, patterns in disease_patterns.items():
                for pattern in patterns:
                    if re.search(pattern, normalized_comment, re.IGNORECASE):
                        found.add(tag)
                        break  # 1つでもマッチしたら次のタグへ
            
            # 除外パターンにマッチするタグを削除
            filtered_tags = []
            for tag in found:
                exclude = False
                for pattern in exclude_patterns:
                    if re.search(pattern, normalized_comment, re.IGNORECASE):
                        exclude = True
                        break
                if not exclude:
                    filtered_tags.append(tag)
            
            # 重複を削除してソート
            unique_sorted_tags = sorted(list(set(filtered_tags)))
            
            # デバッグ用に抽出されたタグをログに出力
            if unique_sorted_tags:
                print(f"抽出された疾病タグ: {', '.join(unique_sorted_tags)}")
            
            return ','.join(unique_sorted_tags) if unique_sorted_tags else ""
            
        except Exception as e:
            print(f"疾病タグの抽出に失敗: {e}")
            return ""
    
    def _extract_primary_image(self, soup) -> str:
        """馬体画像を抽出"""
        try:
            images = soup.find_all('img', src=True)
            for img in images:
                src = img.get('src', '')
                if 'horse' in src.lower() and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                    return src
        except Exception as e:
            print(f"画像の抽出に失敗: {e}")
        return ""

    def _extract_jbis_url(self, soup) -> str:
        """JBIS URLを抽出し、基本情報ページのURLに正規化して返す"""
        try:
            links = soup.find_all('a', href=True)
            
            # JBISリンクを探す
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    # URLを正規化して基本情報ページのURLを取得
                    return self._normalize_jbis_url(href)
                    
            # JBISリンクが見つからない場合は空文字を返す
            return ""
        except Exception as e:
            print(f"JBIS URLの抽出に失敗: {e}")
        return ""

    def _normalize_jbis_url(self, jbis_url: str) -> str:
        """
        JBIS URLを基本情報ページのURLに正規化する
        
        Args:
            jbis_url: 正規化するJBISのURL
            
        Returns:
            str: 正規化された基本情報ページのURL（例: https://www.jbis.or.jp/horse/0001378353/）
        """
        if not jbis_url:
            return ""
            
        # 相対URLの場合はベースURLを追加
        if jbis_url.startswith('//'):
            jbis_url = 'https:' + jbis_url
        elif not jbis_url.startswith('http'):
            jbis_url = 'https://www.jbis.or.jp' + ('' if jbis_url.startswith('/') else '/') + jbis_url
        
        # クエリパラメータを除去
        jbis_url = jbis_url.split('?')[0]
        
        # 馬IDを抽出（例: /horse/0001378353/ から 0001378353 を抽出）
        horse_id_match = re.search(r'/horse/(\d+)', jbis_url)
        if not horse_id_match:
            return ""
            
        horse_id = horse_id_match.group(1)
        
        # 基本情報ページのURLを構築
        normalized_url = f"https://www.jbis.or.jp/horse/{horse_id}/"
        
        return normalized_url

    def _extract_seller(self, page_text: str) -> str:
        """販売申込者を抽出"""
        seller_match = re.search(r'販売申込者：([^\n\r\t]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            seller = re.sub(r'（.*$', '', seller).strip()
            return seller
        return ""
    
    def scrape_all_horses(self, auction_date: Optional[str] = None) -> List[Dict]:
        """全馬のデータを取得"""
        print("=== 楽天オークション スクレイピング開始 ===")
        
        if auction_date is None:
            auction_date = self.get_auction_date()
        
        # 馬のリストを取得
        horses = self.scrape_horse_list()
        
        if not horses:
            print("取得した馬データがありません。")
            return []
        
        print(f"{len(horses)}頭の馬の詳細情報を取得中...")
        
        # 各馬の詳細情報を取得
        for i, horse in enumerate(horses, 1):
            print(f"  {i}/{len(horses)}: {horse['name']}")
            if horse.get('detail_url'):
                # 詳細データを取得（auction_dateを渡す）
                detail_data = self.scrape_horse_detail(horse['detail_url'], auction_date)
                if detail_data:
                    # 重要なフィールドを明示的にマージ
                    for key in ['name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller', 'auction_date',
                              'start_price', 'sold_price', 'bid_num', 'unsold', 'comment', 'disease_tags',
                              'primary_image', 'jbis_url', 'total_prize_start', 'total_prize_latest', 'prize']:
                        if key in detail_data and detail_data[key] is not None:
                            horse[key] = detail_data[key]
                    
                    # 血統情報が不足している場合は警告を表示
                    if not horse.get('sire'):
                        print(f"  [警告] 父馬名が取得できません: {horse.get('name')}")
                    if not horse.get('dam'):
                        print(f"  [警告] 母馬名が取得できません: {horse.get('name')}")
                    if not horse.get('damsire'):
                        print(f"  [警告] 母父馬名が取得できません: {horse.get('name')}")
                    
            # サーバーに負荷をかけないよう少し待機
            time.sleep(1)
        
        # JBISから現在の総賞金を取得し、差額を計算
        print("=== JBISから現在の総賞金を取得中... ===")
        for i, horse in enumerate(horses, 1):
            print(f"  {i}/{len(horses)}: {horse['name']} - JBIS賞金取得中...")
            
            # JBISから現在の総賞金を取得
            if horse.get('jbis_url'):
                try:
                    # JBIS URLを正規化（血統情報ページを基本情報ページに変換）
                    normalized_jbis_url = self._normalize_jbis_url(horse['jbis_url'])
                    if normalized_jbis_url != horse['jbis_url']:
                        print(f"    JBIS URL正規化: {horse['jbis_url']} -> {normalized_jbis_url}")
                    
                    # JBISの基本情報ページから総賞金を取得
                    jbis_response = self.session.get(normalized_jbis_url, timeout=30)
                    jbis_response.raise_for_status()
                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                    
                    # 総賞金を抽出（JBISのページ構造に合わせて修正）
                    total_prize_latest = None
                    
                    # 方法1: dtタグから総賞金を取得（最も確実）
                    total_prize_dt = jbis_soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                    if total_prize_dt:
                        dd = total_prize_dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            # 数値を抽出（例: "9077.9万円" -> 9077.9）
                            prize_num_match = re.search(r'([\d,]+\.?\d*)', prize_text)
                            if prize_num_match:
                                try:
                                    prize_str = prize_num_match.group(1).replace(',', '')
                                    total_prize_latest = float(prize_str)
                                    print(f"    dtタグから賞金取得成功: {total_prize_latest}万円")
                                except ValueError:
                                    print(f"    dtタグの賞金を数値変換できませんでした: {prize_text}")
                    
                    # 方法2: スペースを考慮した正規表現（dtタグが失敗した場合のフォールバック）
                    if total_prize_latest is None:
                        page_text = jbis_soup.get_text()
                        # スペースを考慮したパターン
                        prize_match = re.search(r'総賞金\s*([\d,]+\.?\d*)\s*万円', page_text)
                        if prize_match:
                            try:
                                prize_str = prize_match.group(1).replace(',', '')
                                total_prize_latest = float(prize_str)
                                print(f"    正規表現から賞金取得成功: {total_prize_latest}万円")
                            except ValueError:
                                print(f"    正規表現の賞金を数値変換できませんでした: {prize_match.group(1)}")
                        else:
                            print(f"    賞金データが見つかりませんでした")
                    
                    if total_prize_latest is not None:
                        # オークション時と現在の賞金を比較して、より信頼性の高い方を採用
                        start_prize = horse.get('total_prize_start', 0)
                        
                        # オークション直後の場合は、オークション時の賞金を優先
                        # 数ヶ月後は現在の賞金を採用
                        if start_prize > 0 and total_prize_latest == 0:
                            # オークション時は賞金があるが、現在は0 → オークション時の値を採用
                            horse['total_prize_latest'] = start_prize
                        elif start_prize == 0 and total_prize_latest > 0:
                            # オークション時は0だが、現在は賞金がある → 現在の値を採用
                            horse['total_prize_start'] = total_prize_latest
                            horse['total_prize_latest'] = total_prize_latest
                        else:
                            # 通常の差額計算
                            horse['total_prize_latest'] = total_prize_latest
                            diff = round(total_prize_latest - start_prize, 1)
                            sign = '+' if diff >= 0 else ''
                            horse['prize_diff'] = f"{sign}{diff}万円"
                    else:
                        horse['prize_diff'] = '-'
                        
                except Exception as e:
                    print(f"    JBIS賞金取得に失敗: {e}")
                    horse['prize_diff'] = '-'
            else:
                horse['prize_diff'] = '-'
            
            # サーバーに負荷をかけないよう少し待機
            time.sleep(1)
        
        # 共通フィールドを追加
        for i, horse in enumerate(horses, 1):
            horse['id'] = i  # IDを追加
            if 'auction_date' not in horse and auction_date:
                horse['auction_date'] = auction_date
            horse['created_at'] = datetime.now().isoformat()
            horse['updated_at'] = datetime.now().isoformat()
        
        print(f"=== スクレイピング完了: {len(horses)}頭の馬データを取得 ===")
        return horses

    def get_jbis_basic_info_url_from_detail(self, detail_url: str) -> str:
        """
        楽天オークション詳細ページからJBIS基本情報ページのURLを取得する（recordを除去して返す）
        """
        try:
            print(f"楽天詳細ページからJBIS基本情報URL取得: {detail_url}")
            response = self.session.get(detail_url, timeout=30)
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')
            links = soup.find_all('a', href=True)
            for link in links:
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href and '/record/' in href:
                    # /record/を除去し、末尾にスラッシュを付与
                    basic_info_url = href.replace('/record/', '')
                    if not basic_info_url.endswith('/'):
                        basic_info_url += '/'
                    print(f"DEBUG: JBIS基本情報URL: {basic_info_url}")
                    return basic_info_url
            print("JBISリンクが見つかりませんでした")
            return ''
        except Exception as e:
            print(f"JBIS基本情報URLの取得に失敗: {e}")
            return ''

# === テスト関数 ===
def test_extract_pedigree():
    class DummySoup:
        def __init__(self, text):
            self._text = text
        def get_text(self, separator=' ', strip=True):
            return self._text
        def find(self, tag, class_=None):
            class Dummy:
                def __init__(self, text):
                    self.text = text
            if tag == 'pre':
                return Dummy(self._text)
            return None
        def find_all(self, tags):
            class Dummy:
                def __init__(self, text):
                    self.text = text
            return [Dummy(self._text)]
    # テストパターン
    patterns = [
        "父：イスラボニータ　母：ハイエストクイーン　母の父：シンボリクリスエス",
        "父：ディープインパクト 母：ウインドインハーヘア 母の父：Alzao",
        "父：キングカメハメハ　母：マンファス　母の父：Last Tycoon",
        "父：ハーツクライ(成績:GI馬) 母：アイリッシュダンス(重賞馬) 母の父：トニービン",
        "父：オルフェーヴル　母：オリエンタルアート　母の父：メジロマックイーン",
        "父：ロードカナロア　母：レディブラッサム　母の父：Storm Cat",
        "父：エピファネイア　母：シーザリオ　母の父：スペシャルウィーク",
        "父：キズナ　母：キャットクイル　母の父：Storm Cat",
        "父：サンデーサイレンス　母：ウインドインハーヘア",
        "父：ダイワメジャー　母：スカーレットブーケ",
        "父：キングカメハメハ",
        "母：ウインドインハーヘア",
        "母の父：Alzao",
        "父：ディープインパクト(成績:7冠馬) 母：ウインドインハーヘア(重賞馬) 母の父：Alzao(海外馬)",
    ]
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
    scraper = RakutenAuctionScraper()
    for i, text in enumerate(patterns):
        soup = DummySoup(text)
        result = scraper._extract_pedigree_from_page(soup)
        print(f"--- パターン{i+1} ---\n入力: {text}\n抽出結果: {result}\n")
def debug_horse_scraping(max_horses=5):
    """
    利用可能な馬の詳細情報をデバッグ情報付きで取得し、新しいデータ構造で保存する
    
    Args:
        max_horses: 処理する最大の馬の数
    """
    from pprint import pprint
    import os
    
    print("=== デバッグ: 馬の詳細情報取得を開始 ===")
    
    # データディレクトリを指定（フロントエンドのpublic/dataディレクトリ）
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                          'static-frontend', 'public', 'data')
    os.makedirs(data_dir, exist_ok=True)
    
    print(f"データ保存先: {data_dir}")
    
    scraper = RakutenAuctionScraper(data_dir=data_dir)
    
    # 馬のリストを取得して詳細情報を保存
    print(f"\n1. 馬リストの取得を開始（最大{max_horses}頭）...")
    horses = scraper.scrape_horse_list(max_horses=max_horses)
    
    if not horses:
        print("エラー: 馬リストが空です。")
        return
    
    print(f"\n2. 馬リストを取得しました（{len(horses)}頭）")
    print("保存された馬の情報:", os.path.join(data_dir, 'horses.json'))
    print("保存されたオークション履歴:", os.path.join(data_dir, 'auction_history.json'))
    
    # 保存されたデータを読み込んで表示
    horses_file = os.path.join(data_dir, 'horses.json')
    history_file = os.path.join(data_dir, 'auction_history.json')
    
    if os.path.exists(horses_file):
        with open(horses_file, 'r', encoding='utf-8') as f:
            horses_data = json.load(f)
            print(f"\n3. 保存された馬の情報（{len(horses_data)}頭）:")
            for i, horse in enumerate(horses_data[:5], 1):
                print(f"  {i}. {horse.get('name', '名前なし')} (ID: {horse.get('id', 'N/A')})")
                print(f"     性別: {horse.get('sex', 'N/A')}, 年齢: {horse.get('age', 'N/A')}")
                print(f"     父: {horse.get('sire', 'N/A')}")
                print(f"     母: {horse.get('dam', 'N/A')}")
                print(f"     母父: {horse.get('damsire', 'N/A')}")
                print(f"     疾病タグ: {', '.join(horse.get('disease_tags', [])) or 'なし'}")
    
    if os.path.exists(history_file):
        with open(history_file, 'r', encoding='utf-8') as f:
            history_data = json.load(f)
            print(f"\n4. 保存されたオークション履歴（{len(history_data)}件）:")
            for i, history in enumerate(history_data[:3], 1):
                print(f"  {i}. 馬ID: {history.get('horse_id', 'N/A')}")
                print(f"     オークション日: {history.get('auction_date', 'N/A')}")
                print(f"     落札価格: {history.get('sold_price', 'N/A')}円")
                print(f"     総賞金(開始時): {history.get('total_prize_start', 'N/A')}万円")
                print(f"     総賞金(最新): {history.get('total_prize_latest', 'N/A')}万円")
                print(f"     馬体重: {history.get('weight', 'N/A')}kg")
                print(f"     売り手: {history.get('seller', 'N/A')}")
                print(f"     主取り: {'はい' if history.get('is_unsold') else 'いいえ'}")
                print(f"     コメント: {history.get('comment', 'N/A')}")
    
    print("\n=== デバッグ完了 ===")

# テスト実行
if __name__ == "__main__":
    # デバッグ用: 利用可能な馬の詳細をデバッグ（最大5頭）
    debug_horse_scraping(max_horses=5)
    
    # 通常のスクレイピングを実行する場合は以下のコメントを外す
    # scraper = RakutenAuctionScraper()
    # horses = scraper.scrape_all_horses()
    # print(f"取得馬数: {len(horses)}")