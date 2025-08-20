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

def get_cache_dir():
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

# グローバル変数の定義
cache_dir, details_dir = get_cache_dir()
metadata_file = os.path.join(cache_dir, 'metadata.json')

# メタデータが存在しない場合は初期化
if not os.path.exists(metadata_file):
    metadata = {
        'session_id': f"sess_{int(time.time())}",
        'created_at': datetime.datetime.now().isoformat(),
        'updated_at': datetime.datetime.now().isoformat(),
        'downloaded_pages': []
    }
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)

# Suppress BeautifulSoup warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

def download_detail_page(detail_url, output_dir, session_id, base_url="https://www.tb-selection.com/", save_cache=True):
    """
    馬の詳細ページをダウンロードする
    
    Args:
        detail_url (str): 詳細ページのURL
        output_dir (str): 出力ディレクトリのパス
        session_id (str): セッションID (例: 'sess_1755492270')
        base_url (str): ベースURL
        save_cache (bool): キャッシュを保存するかどうか（デフォルト: True）
        
    Returns:
        tuple: (ファイルパス, 成功フラグ)
    """
    try:
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # ファイル名を生成（例: sess_1755492270_item_14705.html）
        item_id = detail_url.split('item=')[-1] if 'item=' in detail_url else str(int(time.time()))
        filename = f"{session_id}_item_{item_id}.html"
        filepath = os.path.join(output_dir, filename)
        
        # 既存のファイルがあれば削除
        if os.path.exists(filepath):
            os.remove(filepath)
        
        # リクエストヘッダーを設定
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Referer': base_url,
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate, br',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'no-cache'
        }
        
        logging.info(f"ダウンロード中: {detail_url}")
        
        # セッションを使用して接続を維持
        session = requests.Session()
        response = session.get(detail_url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # エンコーディングを明示的に指定
        response.encoding = response.apparent_encoding or 'utf-8'
        
        # レスポンスをそのまま保存（デバッグ用）
        debug_filepath = os.path.join(output_dir, f"debug_{filename}.txt")
        with open(debug_filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # metaタグでcharsetが指定されていない場合は追加
        if soup.head and not soup.find('meta', {'charset': True}):
            meta = soup.new_tag('meta', charset='utf-8')
            soup.head.insert(0, meta)
        
        # ファイルに保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        logging.info(f"詳細ページを保存しました: {filepath}")
        return filepath, True
        
    except requests.exceptions.RequestException as e:
        logging.error(f"リクエストエラー: {e}")
        return None, False
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        logging.error(traceback.format_exc())
        return None, False
            
    except requests.exceptions.RequestException as e:
        logging.error(f"リクエストエラー: {e}")
        return None, False
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        logging.error(traceback.format_exc())
        return None, False

def extract_detail_links(html_file, base_url):
    """HTMLファイルから詳細ページのリンクを抽出し、ローカルキャッシュへのリンクに変換する"""
    try:
        # ファイルをバイナリモードで読み込み
        with open(html_file, 'rb') as f:
            raw_data = f.read()
            
        # エンコーディングを推測してデコード
        encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']
        content = None
        
        for enc in encodings:
            try:
                content = raw_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            logging.error("ファイルのデコードに失敗しました。サポートされていないエンコーディングの可能性があります。")
            return []
            
        links = set()
        cache_dir = os.path.dirname(html_file)
        details_dir = os.path.join(cache_dir, 'details')
        
        # 正規表現でリンクを抽出
        import re
        
        # 相対パスのリンクを抽出（例: "details/sess_14705.html"）
        pattern = r'href=["\'](details/sess_\d+\.html)["\']'
        matches = re.findall(pattern, content)
        
        for match in matches:
            # ファイル名からitem_idを抽出
            item_id = match.split('_')[-1].split('.')[0]
            if not item_id.isdigit():
                continue
                
            full_url = f'https://auction.keiba.rakuten.co.jp/item/{item_id}'
            links.add(full_url)
            
        # 変更したHTMLを保存
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f'抽出した詳細ページリンク: {len(links)}件')
        return list(links)
        
        # 変更したHTMLを保存
        with open(html_file, 'w', encoding='utf-8') as f:
            f.write(content)
            
        logging.info(f"抽出した詳細ページリンク: {len(links)}件")
        return list(links)
    except Exception as e:
        logging.error(f"詳細ページリンクの抽出中にエラーが発生しました: {str(e)}")
        return []
    except Exception as e:
        logging.error(f'リンクの抽出中にエラーが発生しました: {e}', exc_info=True)
        return []
        return []

def extract_prize_from_text(text: str) -> float:
    """テキストから賞金を抽出するヘルパー関数"""
    if not text:
        return 0.0

    # パターン1: 「447.2万円」形式
    match = re.search(r'([\d,.]+)\s*万円', text)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except (ValueError, AttributeError):
            pass

    # パターン2: 「総賞金 447.2万円」形式
    match = re.search(r'総賞金\s*([\d,.]+)\s*万円', text)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except (ValueError, AttributeError):
            pass

    # パターン3: オークション価格（落札価格）を検索
    match = re.search(r'落札価格[^\d]*([\d,]+)[^\d]*万円', text)
    if match:
        try:
            return float(match.group(1).replace(',', ''))
        except (ValueError, AttributeError):
            pass

    return 0.0

def extract_prize_from_list_page(section) -> float:
    """リストページのセクションから賞金情報を抽出する
    
    Args:
        section: BeautifulSoupオブジェクト（馬情報のセクション）
        
    Returns:
        float: 抽出した賞金額（万円単位）。見つからない場合は0.0
    """
    try:
        # 1. auctionTableCard__priceクラスを持つ要素を直接検索
        prize_div = section.find('div', class_='auctionTableCard__price')
        if prize_div:
            value_div = prize_div.find('div', class_='value')
            if value_div:
                prize_text = value_div.get_text(strip=True)
                # 数値部分を抽出（例: "123.4万円" -> 123.4）
                match = re.search(r'([\d,]+(?:\.[\d,]+)?)', prize_text)
                if match:
                    try:
                        return float(match.group(1).replace(',', ''))
                    except (ValueError, TypeError):
                        pass
        
        # 2. 従来の方法で賞金情報を検索（フォールバック）
        prize_elements = section.find_all(['div', 'span'], class_=re.compile(r'(prize|money|award|reward|total)', re.IGNORECASE))
        
        for elem in prize_elements:
            text = elem.get_text(separator=' ', strip=True)
            patterns = [
                r'(総賞金|賞金総額|獲得賞金|賞金)[:：\s]*([\d,]+(?:\.[\d,]+)?)',
                r'([\d,]+(?:\.\d+)?)\s*万円',
                r'¥\s*([\d,]+(?:\.[\d,]+)?)'
            ]
            
            for pattern in patterns:
                matches = re.findall(pattern, text)
                for match in matches:
                    if isinstance(match, tuple):
                        prize_str = match[1] if len(match) > 1 else match[0]
                    else:
                        prize_str = match
                    
                    try:
                        prize = float(prize_str.replace(',', ''))
                        if prize > 10000:
                            prize = prize / 10000
                        return prize
                    except (ValueError, TypeError):
                        continue
        
        # 3. セクション全体からも探す（最終手段）
        text = section.get_text(separator=' ', strip=True)
        prize_match = re.search(r'(総賞金|賞金総額|獲得賞金|賞金)[:：\s]*([\d,]+(?:\.[\d,]+)?)', text)
        if prize_match:
            try:
                return float(prize_match.group(2).replace(',', ''))
            except (ValueError, TypeError):
                pass
                
        # 4. ヘルパー関数で抽出を試みる
        return extract_prize_from_text(text)
            
    except Exception as e:
        logging.error(f"賞金情報の抽出中にエラーが発生: {str(e)}")
        logging.error(traceback.format_exc())
        return 0.0


def extract_weight_from_detail(html_content: str) -> int:
    """詳細ページのHTMLから馬体重を抽出する"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. テーブル内の「馬体重」行を探す
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = row.find_all(['th', 'td'])
                if len(cells) >= 2 and '馬体重' in cells[0].get_text():
                    weight_text = cells[1].get_text(strip=True)
                    weight_match = re.search(r'(\d+)(?:\s*kg)?', weight_text)
                    if weight_match:
                        return int(weight_match.group(1))
        
        # 2. テキストノードから直接検索
        text = soup.get_text(separator=' ')
        weight_match = re.search(r'馬体重[：:](?:\s*)(\d+)(?:\s*kg)?', text)
        if weight_match:
            return int(weight_match.group(1))
            
        # 3. 最終出走馬体重を検索
        weight_match = re.search(r'最終出走馬体重[：:](?:\s*)(\d+)(?:\s*kg)?', text)
        if weight_match:
            return int(weight_match.group(1))
            
    except Exception as e:
        logging.warning(f"体重情報の抽出中にエラーが発生しました: {str(e)}")
    
    return None

def extract_horse_info(html_file):
    """リストページのHTMLから馬情報を抽出する
    
    Args:
        html_file (str): リストページのHTMLファイルパス
        
    Returns:
        list: 抽出した馬情報のリスト
    """
    logging.info(f"リストページからの情報抽出を開始: {html_file}")
    
    try:
        # バイナリモードでファイルを読み込み、適切なエンコーディングを推測
        with open(html_file, 'rb') as f:
            raw_data = f.read()
        
        # エンコーディングを推測してデコード
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
                name = name_elem.get_text(strip=True) if name_elem else 'Unknown'

                # 馬名が短すぎる場合はスキップ
                if not name or len(name) < 2:
                    logging.warning(f"スキップされた馬: 名前が短すぎます - {name}")
                    continue

                # 賞金情報を抽出
                prize = 0.0
                prize_container = card.find('div', class_='auctionTableCard__price')
                if prize_container:
                    prize_elem = prize_container.find('div', class_='value')
                    if prize_elem:
                        prize_text = prize_elem.get_text(strip=True)
                        prize = extract_prize_from_text(prize_text)
                
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
                
                # 血統情報を抽出
                sire_elem = card.find('div', class_='auctionTableCard__sire')
                dam_elem = card.find('div', class_='auctionTableCard__dam')
                dam_sire_elem = card.find('div', class_='auctionTableCard__damsire')
                
                sire = sire_elem.get_text(strip=True).replace('父:', '') if sire_elem else ''
                dam = dam_elem.get_text(strip=True).replace('母:', '') if dam_elem else ''
                dam_sire = dam_sire_elem.get_text(strip=True).replace('母父:', '') if dam_sire_elem else ''
                
                # 価格情報を抽出
                price_elem = card.find('div', class_='auctionTableCard__price')
                price = price_elem.get_text(strip=True) if price_elem else ''
                
                # アイテムIDを抽出
                item_id = ''
                item_id_elem = card.find('a', href=re.compile(r'/item/\d+'))
                if item_id_elem and 'href' in item_id_elem.attrs:
                    item_id = item_id_elem['href'].split('/')[-1]
                
                # 馬情報を辞書に格納
                horse_info = {
                    'name': name,
                    'item_id': item_id,
                    'seller': seller,
                    'sex': sex,
                    'age': age,
                    'total_prize': prize,  # 賞金情報を追加
                    'sire': sire,
                    'dam': dam,
                    'dam_sire': dam_sire,
                    'price': price,
                    'detail_url': f"https://auction.keiba.rakuten.co.jp/item/{item_id}" if item_id else ''
                }
                
                # 詳細ページから追加情報を取得
                detail_file = os.path.join(os.path.dirname(html_file), 'details', 
                                        f"sess_*_item_{item_id}.html")
                import glob
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
                logging.error(traceback.format_exc())
                continue
                
        logging.info(f"{len(horses)}頭の馬情報を抽出しました")
        return horses
        
    except Exception as e:
        logging.error(f"リストページからの情報抽出中にエラーが発生しました: {str(e)}", exc_info=True)
        logging.error(f"Error processing file {html_file}: {str(e)}", exc_info=True)
        return []

    # リストページから賞金情報を抽出するヘルパー関数
    def extract_prize_from_list_page(section):
        # 既存のextract_prize_from_list_page関数の実装を使用
        # この関数は別途定義されているはずです
        return 0.0  # デフォルト値
        
    return horses  # Return the list of extracted horses

def load_config():
    """設定を読み込む"""
    return {
        'base_url': 'https://keiba.rakuten.co.jp/auction/',  # 実際のURLに置き換えてください
        'request_headers': {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
            'Referer': 'https://keiba.rakuten.co.jp/'
        },
        'request_timeout': 30,
        'delay_between_requests': 2,  # リクエスト間の遅延（秒）
        'max_retries': 3  # リトライ回数
    }

def main():
    try:
        # キャッシュディレクトリを取得
        cache_dir, details_dir = get_cache_dir()
        
        # メタデータファイルのパス
        metadata_file = os.path.join(cache_dir, 'metadata.json')
        
        # メタデータを読み込む（存在しない場合は新規作成）
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {
                'session_id': datetime.datetime.now().strftime('%Y%m%d'),
                'created_at': datetime.datetime.now().isoformat(),
                'updated_at': datetime.datetime.now().isoformat(),
                'downloaded_pages': []
            }
        
        # メタデータを更新
        metadata['updated_at'] = datetime.datetime.now().isoformat()
        
        # メタデータを保存
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"キャッシュディレクトリ: {cache_dir}")
        logging.info(f"セッションID: {metadata['session_id']}")
        
        # 設定を読み込む
        config = load_config()
        
        # リストページのパスを取得
        list_file = os.path.join(cache_dir, 'list.html')
        
        # リストページが存在するか確認
        if not os.path.exists(list_file):
            logging.error(f"リストページが見つかりません: {list_file}")
            print(f"エラー: リストページが見つかりません。{list_file} にリストページを配置してください。")
            return
        
        # 馬情報を抽出
        logging.info("馬情報の抽出を開始します...")
        horses = extract_horse_info(list_file)
        
        if not horses:
            logging.warning("馬情報の抽出に失敗しました。")
            print("警告: 馬情報の抽出に失敗しました。")
            return
        
        # 結果をJSONファイルに保存
        output_file = os.path.join(cache_dir, 'processed_horses_with_weights.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({'horses': horses}, f, ensure_ascii=False, indent=2)
        
        logging.info(f"馬情報を {output_file} に保存しました。{len(horses)}件の馬情報を抽出しました。")
        print(f"完了: {len(horses)}件の馬情報を抽出し、{output_file} に保存しました。")
        
        return True
        
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        print(f"エラー: {str(e)}")
        return False

def download_all_detail_pages(html_file, base_url):
    """リストページからすべての詳細ページをダウンロードする"""
    try:
        # ファイルをバイナリモードで読み込み
        with open(html_file, 'rb') as f:
            raw_data = f.read()
            
        # エンコーディングを推測してデコード
        encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']
        content = None
        
        for enc in encodings:
            try:
                content = raw_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
                
        if content is None:
            logging.error("ファイルのデコードに失敗しました。サポートされていないエンコーディングの可能性があります。")
            return []
            
        # 詳細ページのURLを抽出
        import re
        base_url_pattern = re.escape('https://auction.keiba.rakuten.co.jp')
        patterns = [
            f'({base_url_pattern}/item/\d+)',  # フルURL
            '(/item/\d+)'                     # 相対URL
        ]
        
        urls = set()
        for pattern in patterns:
            matches = re.findall(pattern, content)
            for match in matches:
                if match.startswith('/'):
                    urls.add(f'https://auction.keiba.rakuten.co.jp{match}')
                else:
                    urls.add(match)
        
        # 詳細ページをダウンロード
        cache_dir = os.path.dirname(html_file)
        details_dir = os.path.join(cache_dir, 'details')
        os.makedirs(details_dir, exist_ok=True)
        
        session = requests.Session()
        success_count = 0
        
        for url in urls:
            if download_detail_page(url, details_dir, session):
                success_count += 1
                
        logging.info(f'合計 {len(urls)} 件中 {success_count} 件の詳細ページをダウンロードしました')
        return list(urls)
        
    except Exception as e:
        logging.error(f'詳細ページのダウンロード中にエラーが発生しました: {str(e)}')
        return []

if __name__ == "__main__":
    # メタデータを読み込む（存在しない場合は初期化）
    if not os.path.exists(metadata_file):
        metadata = {
            'session_id': f"sess_{int(time.time())}",
            'created_at': datetime.datetime.now().isoformat(),
            'updated_at': datetime.datetime.now().isoformat(),
            'downloaded_pages': []
        }
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
    else:
        with open(metadata_file, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            
    # 必要なキーを初期化
    if 'session_id' not in metadata:
        metadata['session_id'] = f"sess_{int(time.time())}"
    if 'downloaded_pages' not in metadata:
        metadata['downloaded_pages'] = []
    if 'detail_pages' not in metadata:
        metadata['detail_pages'] = {}
    
    # リストページのURL
    LIST_PAGE_URL = "https://auction.keiba.rakuten.co.jp/"
    list_page = os.path.join(cache_dir, 'list.html')
    
    # 詳細ページの保存先ディレクトリ
    details_dir = os.path.join(cache_dir, 'details')
    os.makedirs(details_dir, exist_ok=True)
    
    if not os.path.exists(list_page):
        logging.error(f"リストページが見つかりません: {list_page}")
        exit(1)
    
    # 詳細ページのリンクを抽出
    detail_links = extract_detail_links(list_page, LIST_PAGE_URL)
    logging.info(f"抽出された詳細ページリンク: {len(detail_links)}件")
    
    # 詳細ページをダウンロード
    downloaded_count = 0
    for link in detail_links:
        filepath, success = download_detail_page(link, details_dir, metadata['session_id'])
        if success:
            downloaded_count += 1
            # メタデータを更新
            metadata['downloaded_pages'].append({
                'url': link,
                'filepath': os.path.relpath(filepath, cache_dir),
                'downloaded_at': datetime.datetime.now().isoformat()
            })
            # 5件ごとにメタデータを保存
            if downloaded_count % 5 == 0:
                metadata['updated_at'] = datetime.datetime.now().isoformat()
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    # 最終的なメタデータを保存
    metadata['updated_at'] = datetime.datetime.now().isoformat()
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logging.info(f"処理が完了しました。{downloaded_count}件の詳細ページをダウンロードしました。")
    
    # メタデータを保存
    with open(metadata_file, 'w', encoding='utf-8') as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    
    logging.info(f"キャッシュディレクトリ: {cache_dir}")
    if 'session_id' in metadata:
        logging.info(f"セッションID: {metadata['session_id']}")
    
    # メイン処理を実行
    # まず詳細ページをダウンロード
    list_file = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'cache', '20250818', 'list.html')
    if os.path.exists(list_file):
        print("詳細ページのダウンロードを開始します...")
        download_all_detail_pages(list_file, 'https://auction.keiba.rakuten.co.jp/')
    else:
        print(f"リストファイルが見つかりません: {list_file}")
    
    # メイン処理を実行
    try:
        main()
    except Exception as e:
        logging.error(f"メイン処理の実行中にエラーが発生しました: {e}", exc_info=True)
        raise
