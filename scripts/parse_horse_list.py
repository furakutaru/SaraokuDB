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

def get_cache_dir():
    """日付ベースのキャッシュディレクトリを取得する"""
    today = datetime.datetime.now().strftime('%Y%m%d')
    cache_base_dir = Path(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))) / 'cache'
    cache_dir = cache_base_dir / today
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

def download_detail_page(detail_url, output_dir, session_id, base_url="https://www.tb-selection.com/"):
    """Download and save detail page for a horse."""
    try:
        # 出力ディレクトリが存在しない場合は作成
        os.makedirs(output_dir, exist_ok=True)
        
        # URLから一意の識別子を生成（ファイル名として使用）
        parsed_url = urlparse(detail_url)
        url_path = parsed_url.path.strip('/')
        filename = f"{session_id}_{url_path.replace('/', '_')}.html"
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
        
        # 詳細ページを取得
        logging.info(f"ダウンロード中: {detail_url}")
        
        # セッションを使用して接続を維持
        session = requests.Session()
        response = session.get(detail_url, headers=headers, timeout=30, allow_redirects=True)
        response.raise_for_status()
        
        # エンコーディングを明示的に指定
        response.encoding = response.apparent_encoding or 'utf-8'
        
        # HTMLをパースしてから再エンコードして保存
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # metaタグでcharsetが指定されていない場合は追加
        if not soup.find('meta', {'charset': True}) and soup.head:
            meta = soup.new_tag('meta', charset='utf-8')
            soup.head.insert(0, meta)
            
        # ファイルに保存
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(str(soup))
        
        # ファイルが正しく保存されたか確認
        if os.path.exists(filepath) and os.path.getsize(filepath) > 0:
            file_size = os.path.getsize(filepath)
            logging.info(f"ファイルを正常に保存しました: {filepath} ({file_size} バイト)")
            
            # メタデータを読み込む
            metadata_file = os.path.join(cache_dir, 'metadata.json')
            metadata = {}
            if os.path.exists(metadata_file):
                try:
                    with open(metadata_file, 'r', encoding='utf-8') as f:
                        metadata = json.load(f)
                except Exception as e:
                    logging.warning(f'メタデータの読み込みに失敗しました: {e}')
                    print(f'警告: メタデータの読み込みに失敗しました: {e}')
            
            # 必要なキーが存在しない場合は初期化
            if 'downloaded_pages' not in metadata:
                metadata['downloaded_pages'] = []
            if 'detail_pages' not in metadata:
                metadata['detail_pages'] = {}
            metadata['detail_pages'][detail_url] = os.path.basename(filepath)
            
            try:
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
            except Exception as e:
                logging.error(f"メタデータの保存に失敗しました: {e}")
            
            return filepath, True
        else:
            logging.error(f"ファイルの保存に失敗しました: {filepath}")
            return None, False
            
    except Exception as e:
        logging.error(f"ダウンロード中にエラーが発生しました: {detail_url}")
        logging.error(f"エラータイプ: {type(e).__name__}")
        logging.error(f"エラーメッセージ: {str(e)}")
        logging.error(f"出力先ディレクトリ: {output_dir}")
        if 'filepath' in locals() and os.path.exists(filepath):
            os.remove(filepath)  # エラーが発生した場合は不完全なファイルを削除
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

def extract_horse_info(html_file):
    """Extract horse information from the list page HTML."""
    logging.info(f"Starting extraction from {html_file}")
    
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
            # どのエンコーディングでもデコードできない場合
            content = raw_data.decode('utf-8', errors='replace')
        
        # HTMLをパース
        soup = BeautifulSoup(content, 'html.parser')
        
    except Exception as e:
        logging.error(f"Error processing file {html_file}: {str(e)}", exc_info=True)
        return []
    
    horses = []
    
    # Find all horse entries - they seem to be in tables with specific styling
    horse_sections = []
    
    # Look for tables that contain horse information
    tables = soup.find_all('table')
    logging.info(f"Found {len(tables)} tables in the document")
    
    # 馬情報を含むテーブルを検索（クラス名で検索）
    for table in tables:
        # 馬名を含む要素を検索
        name_elem = table.select_one('.auctionTableCard__name')
        if name_elem:
            horse_sections.append(table)
    
    logging.info(f"Found {len(horse_sections)} potential horse sections")
    
    for section in horse_sections:
        try:
            # 馬名を抽出（複数のクラス名で検索）
            name_elem = (section.select_one('.auctionTableCard__name') or 
                        section.select_one('.horse-name') or
                        section.select_one('h1, h2, h3, strong'))
                        
            if not name_elem:
                logging.warning(f"馬名要素が見つかりません: {section}")
                continue
                
            name = ' '.join(name_elem.get_text().split())
            
            # 馬名が省略されているかどうかをチェック（...が含まれるか、短すぎる場合）
            is_name_truncated = ('...' in name or len(name) < 2)
            
            # 詳細ページのリンクを取得
            detail_link = None
            for a in section.find_all('a', href=True):
                if 'item' in a['href']:
                    detail_link = a['href']
                    if not detail_link.startswith(('http://', 'https://')):
                        detail_link = urljoin('https://auction.keiba.rakuten.co.jp', detail_link)
                    break
            
            # 馬名が省略されているか、短すぎる場合は詳細ページから取得を試みる
            if is_name_truncated and detail_link:
                try:
                    # 詳細ページのキャッシュを確認
                    cache_dir = os.path.dirname(html_file)
                    details_dir = os.path.join(cache_dir, 'details')
                    item_id = re.search(r'item[_-]?(\d+)', detail_link)
                    
                    if item_id:
                        item_id = item_id.group(1)
                        detail_file = os.path.join(details_dir, f"sess_*_item_{item_id}.html")
                        import glob
                        matching_files = glob.glob(detail_file)
                        
                        if matching_files:
                            with open(matching_files[0], 'r', encoding='utf-8') as f:
                                detail_content = f.read()
                                detail_soup = BeautifulSoup(detail_content, 'html.parser')
                                # 詳細ページから馬名を抽出（複数のパターンに対応）
                                full_name_elem = (
                                    detail_soup.select_one('h1.horse-name, h2.horse-name, h3.horse-name') or
                                    detail_soup.select_one('div.horse-name') or
                                    detail_soup.select_one('span.horse-name') or
                                    detail_soup.select_one('.auctionTableCard__name') or
                                    detail_soup.select_one('h1, h2, h3, strong')
                                )
                                
                                if full_name_elem:
                                    full_name = ' '.join(full_name_elem.get_text().split())
                                    if full_name and len(full_name) > len(name):
                                        name = full_name
                                        logging.info(f"詳細ページから完全な馬名を取得: {name}")
                                    else:
                                        logging.info(f"詳細ページから取得した馬名が現在のものより短いか同じです: {full_name} <= {name}")
                                else:
                                    logging.warning(f"詳細ページから馬名要素を見つけられませんでした: {detail_link}")
                                logging.info(f"Updated horse name from detail page: {name}")
                except Exception as e:
                    logging.warning(f"Failed to get full name from detail page: {e}")
            
            if not name or len(name) < 2:  # Skip if name is still too short
                continue
            
            # Extract all text from the section
            details_text = section.get_text(separator='\n', strip=True)
            
            # Extract basic information using regex patterns
            horse_info = {
                'name': name,
                'extracted_at': datetime.now().isoformat(),
                'source_file': os.path.basename(html_file)
            }
            
            # Extract pedigree information
            pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\n]+)', details_text)
            if pedigree_match:
                horse_info.update({
                    'sire': pedigree_match.group(1).strip(),
                    'dam': pedigree_match.group(2).strip(),
                    'damsire': pedigree_match.group(3).strip()
                })
            
            # Extract race record if available
            record_match = re.search(r'通算成績：([^\[]+)\[([^\]]+)\]', details_text)
            if record_match:
                horse_info['race_record'] = {
                    'summary': record_match.group(1).strip(),
                    'record': record_match.group(2).strip()
                }
            
            # Extract prize money
            prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', details_text)
            if prize_match:
                try:
                    horse_info['prize_money'] = float(prize_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            
            # Extract auction date if available
            auction_match = re.search(r'※(\d{4}年\d{1,2}月\d{1,2}日)落札', details_text)
            if auction_match:
                horse_info['auction_date'] = auction_match.group(1)
            
            # Extract comments about the horse
            comment_section = re.search(r'本馬について[^\n]*\n(.*?)(?=\n\s*※|$)', details_text, re.DOTALL)
            if comment_section:
                horse_info['comments'] = comment_section.group(1).strip()
            
            logging.info(f"Extracted info for horse: {name}")
            horses.append(horse_info)
            
        except Exception as e:
            logging.error(f"Error processing horse section: {str(e)}", exc_info=True)
            continue
    
    logging.info(f"Successfully extracted {len(horses)} horses")
    return horses

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
        
        # リストページのパスを取得（コマンドライン引数から取得するか、デフォルトのパスを使用）
        list_file = os.path.join(cache_dir, 'list.html')
        
        # リストページが存在するか確認
        if not os.path.exists(list_file):
            logging.error(f"リストページが見つかりません: {list_file}")
            print(f"エラー: リストページが見つかりません。{list_file} にリストページを配置してください。")
            return
        
        # 詳細ページのリンクを抽出
        detail_links = extract_detail_links(list_file, config['base_url'])
        
        if not detail_links:
            logging.warning("詳細ページのリンクが見つかりませんでした。")
            print("警告: 詳細ページのリンクが見つかりませんでした。")
            return
        
        # 詳細ページをダウンロード
        downloaded_files = []
        for i, link in enumerate(detail_links, 1):
            logging.info(f"ダウンロード中 ({i+1}/{len(detail_links)}): {link}")
            item_id = link.split('/')[-1]
            filepath = os.path.join(details_dir, f"sess_{item_id}.html")
            
            # 既にファイルが存在する場合はスキップ
            if os.path.exists(filepath):
                logging.info(f'既に存在します: {filepath}')
                downloaded_files.append(filepath)
                if filepath not in metadata['downloaded_pages']:
                    metadata['downloaded_pages'].append(filepath)
                continue
                
            # ファイルをダウンロード
            success = False
            try:
                # URLからitem_idを抽出
                item_id = link.split('/')[-1]
                filename = f"sess_{item_id}.html"
                filepath = os.path.join(details_dir, filename)
                
                # 既にファイルが存在する場合はスキップ
                if os.path.exists(filepath):
                    logging.info(f'既に存在します: {filepath}')
                    downloaded_files.append(filepath)
                    if filepath not in metadata['downloaded_pages']:
                        metadata['downloaded_pages'].append(filepath)
                    continue
                
                # ファイルをダウンロード
                downloaded_file, success = download_detail_page(link, details_dir, metadata['session_id'])
                
                if success and downloaded_file:
                    # ダウンロード成功時はファイルパスを返す
                    downloaded_files.append(downloaded_file)
                    # メタデータを更新
                    if downloaded_file not in metadata['downloaded_pages']:
                        metadata['downloaded_pages'].append(downloaded_file)
            except Exception as e:
                logging.error(f'詳細ページの処理中にエラーが発生しました: {link}')
                logging.error(f'エラー: {str(e)}')
                
                # メタデータを定期的に保存
                if i % 5 == 0:
                    with open(metadata_file, 'w', encoding='utf-8') as f:
                        json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # 最終的なメタデータを保存
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logging.info(f"完了: {len(downloaded_files)}/{len(detail_links)} 件の詳細ページをダウンロードしました。")
        print(f"\n完了: {len(downloaded_files)}/{len(detail_links)} 件の詳細ページをダウンロードしました。")
        print(f"ログファイル: {os.path.abspath('horse_extraction.log')}")
        
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        print(f"\nエラーが発生しました。詳細はログファイルを確認してください: {os.path.abspath('horse_extraction.log')}")
        raise

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
