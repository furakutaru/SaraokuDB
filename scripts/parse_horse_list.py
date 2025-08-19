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

def download_detail_page(detail_url, output_dir, session_id, base_url="https://www.tb-selection.com/", save_cache=False):
    """
    馬の詳細ページをダウンロードする
    
    Args:
        detail_url (str): 詳細ページのURL
        output_dir (str): 出力ディレクトリのパス
        session_id (str): セッションID
        base_url (str): ベースURL
        save_cache (bool): キャッシュを保存するかどうか（デフォルト: False）
        
    Returns:
        str: HTMLコンテンツ（キャッシュを保存する場合はファイルパス、保存しない場合はHTMLテキスト）
    """
    try:
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
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # キャッシュを保存する場合のみファイルに書き込む
        if save_cache:
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
            
            # metaタグでcharsetが指定されていない場合は追加
            if not soup.find('meta', {'charset': True}) and soup.head:
                meta = soup.new_tag('meta', charset='utf-8')
                soup.head.insert(0, meta)
                
            # ファイルに保存
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            logging.info(f"キャッシュを保存しました: {filepath}")
            return filepath
        
        # キャッシュを保存しない場合はHTMLテキストを返す
        return response.text
            
    except requests.exceptions.RequestException as e:
        logging.error(f"リクエストエラー: {e}")
        return None
    except Exception as e:
        logging.error(f"エラーが発生しました: {e}")
        logging.error(traceback.format_exc())
        return None

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
    """リストページのセクションから賞金情報を抽出する"""
    try:
        # テキストを取得
        text = section.get_text(separator=' ', strip=True)
        
        # 賞金情報を抽出
        prize_match = re.search(r'(総賞金|賞金総額|獲得賞金)[:：\s]*([\d,]+)', text)
        if prize_match:
            prize_str = prize_match.group(2).replace(',', '')
            try:
                return float(prize_str)
            except (ValueError, TypeError):
                pass
                
        # テキストから直接賞金を抽出
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
        
        # JavaScriptから直接データを抽出
        import re
        import json
        
        # __NUXT_DATA__ 変数からデータを抽出
        nuxt_data = None
        script_tags = soup.find_all('script')
        for script in script_tags:
            if script.string and '__NUXT_DATA__' in script.string:
                match = re.search(r'__NUXT_DATA__\s*=\s*({.*?});', script.string, re.DOTALL)
                if match:
                    try:
                        nuxt_data = json.loads(match.group(1))
                        break
                    except json.JSONDecodeError as e:
                        logging.warning(f'Failed to parse __NUXT_DATA__: {e}')
                        continue
        
        if not nuxt_data:
            logging.error('Could not find __NUXT_DATA__ in the HTML')
            return []
            
        # 馬のリストを取得
        horses_data = nuxt_data.get('state', {}).get('horses', [])
        if not horses_data:
            logging.error('No horse data found in __NUXT_DATA__')
            return []
            
        logging.info(f'Found {len(horses_data)} horses in __NUXT_DATA__')
        
        horses = []
        
        for horse_data in horses_data:
            try:
                horse_info = {
                    'name': horse_data.get('name', '').strip(),
                    'item_id': horse_data.get('item_id', ''),
                    'sex': horse_data.get('sex', ''),
                    'age': horse_data.get('age', ''),
                    'color': horse_data.get('color', ''),
                    'sire': horse_data.get('sire', ''),
                    'dam': horse_data.get('dam', ''),
                    'dam_sire': horse_data.get('dam_sire', ''),
                    'breeder': horse_data.get('breeder', ''),
                    'owner': horse_data.get('owner', ''),
                    'trainer': horse_data.get('trainer', ''),
                    'record': horse_data.get('record', ''),
                    'earnings': horse_data.get('earnings', 0),
                    'weight': horse_data.get('weight'),
                    'detail_url': f"https://auction.keiba.rakuten.co.jp/item/{horse_data.get('item_id', '')}",
                    'auction_date': horse_data.get('auction_date', '')
                }
                
                # 詳細ページから追加情報を取得
                detail_file = os.path.join(os.path.dirname(html_file), 'details', 
                                        f"sess_*_item_{horse_info['item_id']}.html")
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
                        logging.warning(f'Error processing detail page {matching_files[0]}: {str(e)}')
                
                horses.append(horse_info)
                
            except Exception as e:
                logging.error(f'Error processing horse data: {str(e)}')
                continue
                
        return horses
        
    except Exception as e:
        logging.error(f"Error processing file {html_file}: {str(e)}", exc_info=True)
        return []

    # 馬名が短すぎる場合はスキップ
    if not name or len(name) < 2:
        logging.warning(f"Skipping horse with invalid name: {name}")
        continue
            
    # 馬名がカタカナで終わっていて、短い場合は警告を出力（デバッグ用）
    if re.search(r'[\u30A1-\u30FF]+$', name) and len(name) < 5:
        logging.warning(f"Horse name might be truncated: {name}")
    
    # Extract all text from the section
            details_text = section.get_text(separator='\n', strip=True)
            
            # Extract basic information
            # リストページから賞金情報を抽出
            list_prize = extract_prize_from_list_page(section)
            jbis_prize = 0.0
            jbis_url = None
            
            # JBISリンクを検索
            for a in section.find_all('a', href=True):
                if 'jbis.or.jp' in a['href']:
                    jbis_url = a['href']
                    if not jbis_url.startswith(('http://', 'https://')):
                        jbis_url = f"https:{jbis_url}" if jbis_url.startswith('//') else f"https://www.jbis.or.jp{jbis_url if jbis_url.startswith('/') else '/' + jbis_url}"
                    break
            
            # JBISから賞金情報を取得
            if jbis_url:
                try:
                    from process_horse_details import extract_prize_from_jbis
                    jbis_prize = extract_prize_from_jbis(jbis_url)
                except Exception as e:
                    logging.warning(f"JBISからの賞金取得に失敗: {str(e)}")
            
            # より信頼性の高い賞金情報を優先（JBIS > リストページ）
            prize_money = jbis_prize if jbis_prize > 0 else list_prize
            
            # 馬の情報を辞書に格納
            # 詳細ページから体重情報を再取得（既に取得済みの場合は再利用）
            weight = None
            if detail_link and 'weight' not in locals():
                try:
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
                                weight = extract_weight_from_detail(detail_content)
                                if weight is not None:
                                    logging.info(f"Extracted weight for {name}: {weight}kg")
                except Exception as e:
                    logging.warning(f"体重情報の取得中にエラーが発生しました: {str(e)}")
            
            horse_info = {
                'name': name,
                'is_name_truncated': is_name_truncated,
                'detail_link': detail_link,
                'jbis_url': jbis_url,
                'source_file': os.path.basename(html_file),
                'extracted_at': datetime.datetime.now().isoformat(),
                'prize_money': prize_money,
                'prize_source': 'jbis' if jbis_prize > 0 else ('list' if list_prize > 0 else 'none'),
                'weight': weight  # 体重情報を追加
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
                    horse_info['total_prize_start'] = float(prize_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            
            # オークション価格の抽出はsold_priceで行うため削除
            
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
