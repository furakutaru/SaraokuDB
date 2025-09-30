import sys
import os
import json
import time
import glob
from datetime import datetime
from bs4 import BeautifulSoup
import re
import requests

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def get_latest_cache_dir():
    """
    最新のキャッシュディレクトリを取得する
    
    Returns:
        str: 最新のキャッシュディレクトリのパス。見つからない場合はNone
    """
    # キャッシュディレクトリのパターン
    cache_patterns = [
        'cache/*',
        'html_cache/*',
        'cache_new/*',
        'test_scraper_cache/*',
        'test_detail_cache/*',
    ]
    
    # すべてのキャッシュディレクトリを取得
    all_cache_dirs = []
    for pattern in cache_patterns:
        all_cache_dirs.extend(glob.glob(pattern))
    
    # ディレクトリのみに絞り込み、更新日時でソート
    cache_dirs = [d for d in all_cache_dirs if os.path.isdir(d)]
    cache_dirs.sort(key=os.path.getmtime, reverse=True)
    
    if not cache_dirs:
        print("警告: キャッシュディレクトリが見つかりません")
        return None
    
    latest_dir = cache_dirs[0]
    print(f"最新のキャッシュディレクトリ: {latest_dir}")
    return latest_dir

def test_prize_extraction(jbis_urls=None, limit=10):
    """
    JBIS URLから直接賞金情報を取得するテスト
    
    Args:
        jbis_urls (list, optional): テストするJBISのURLリスト。指定しない場合はテスト用のURLを使用
        limit (int, optional): 処理する馬の最大数。デフォルトは10頭
    
    Returns:
        list: 抽出結果のリスト
    """
    # テスト用のJBIS URLリスト（有名な競走馬で賞金実績あり）
    test_jbis_urls = [
        'https://www.jbis.or.jp/horse/0001234567/',  # ディープインパクト（例）
        'https://www.jbis.or.jp/horse/0001033966/',  # オルフェーヴル
        'https://www.jbis.or.jp/horse/0001104659/',  # ゴールドシップ
        'https://www.jbis.or.jp/horse/0001168287/',  # キタサンブラック
        'https://www.jbis.or.jp/horse/0001273076/'   # コントレイル
    ]
    
    # 引数でURLが指定されていない場合はテスト用URLを使用
    if jbis_urls is None:
        jbis_urls = test_jbis_urls
    
    # limitでリストを制限
    jbis_urls = jbis_urls[:limit]
    
    print(f"\n{'='*50}")
    print(f"=== 賞金抽出テスト開始 ===")
    print(f"処理対象URL数: {len(jbis_urls)}")
    print(f"処理制限: {limit}頭")
    print(f"{'='*50}\n")
    
    results = []
    processed_count = 0
    
    for jbis_url in jbis_urls:
        processed_count += 1
        
        try:
            print(f"\n[ {processed_count:2d}/{min(limit, len(jbis_urls))} ] 処理中: {jbis_url}")
            print("-" * 80)
            
            # 馬の基本情報を初期化
            horse_info = {
                'jbis_url': jbis_url,
                'total_prize': 0.0,
                'error': None
            }
            
            # 賞金情報を取得
            try:
                print(f"  - 賞金情報を取得中...")
                total_prize = extract_prize_from_jbis(jbis_url)
                horse_info['total_prize'] = total_prize
                print(f"  ✓ 総賞金: {total_prize:,.1f}万円")
            except Exception as e:
                error_msg = f"賞金情報の取得中にエラー: {str(e)}"
                print(f"  × {error_msg}")
                horse_info['error'] = error_msg
            
            results.append(horse_info)
            
        except Exception as e:
            error_msg = f"処理中にエラーが発生: {str(e)}"
            print(f"  × {error_msg}")
            import traceback
            traceback.print_exc()
            
            if 'horse_info' in locals():
                horse_info['error'] = error_msg
                results.append(horse_info)
    
    # 結果を表示
    print("\n" + "="*80)
    print("=== 抽出結果のサマリー ===")
    print(f"処理件数: {len(results)}")
    
    success_count = sum(1 for r in results if r.get('total_prize', 0) > 0)
    no_prize_count = sum(1 for r in results if r.get('total_prize', 0) == 0 and not r.get('error'))
    error_count = sum(1 for r in results if r.get('error'))
    
    print(f"- 賞金取得成功: {success_count}件")
    print(f"- 賞金0円: {no_prize_count}件")
    print(f"- エラー: {error_count}件")
    
    # 結果を詳細に表示
    print("\n=== 詳細結果 ===")
    for i, result in enumerate(results, 1):
        print(f"\n[{i:2d}] JBIS URL: {result['jbis_url']}")
        print(f"    総賞金: {result.get('total_prize', 0):,.1f}万円")
        if result.get('error'):
            print(f"    × エラー: {result['error']}")
    
    # 結果をJSONに保存
    output_dir = 'data'
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, 'prize_extraction_results.json')
    
    try:
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'timestamp': datetime.now().isoformat(),
                'total_count': len(results),
                'success_count': success_count,
                'no_prize_count': no_prize_count,
                'error_count': error_count,
                'results': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n{'='*50}")
        print(f"結果を {output_file} に保存しました")
        print(f"{'='*50}")
    except Exception as e:
        print(f"\nエラー: 結果の保存に失敗しました: {str(e)}")
    
    return results

def normalize_jbis_url(jbis_url: str) -> str:
    """
    JBISの馬基本情報ページのURLに正規化する
    
    Args:
        jbis_url (str): 正規化するJBISのURL
        
    Returns:
        str: 正規化されたJBISの馬基本情報ページURL（例: https://www.jbis.or.jp/horse/0000123456/）
             URLが無効な場合は空文字列を返す
    """
    if not jbis_url or not isinstance(jbis_url, str):
        print("警告: 無効なURLが渡されました")
        return ""
    
    # 前後の空白を削除
    jbis_url = jbis_url.strip()
    
    try:
        # クエリパラメータとアンカーを削除
        jbis_url = jbis_url.split('?')[0].split('#')[0]
        
        # 馬のID部分を抽出（例: https://www.jbis.or.jp/horse/0000123456/）
        # /pedigree/ や /record/ を含むURLも処理
        match = re.search(r'(https?://www\.jbis\.or\.jp/horse/\d+)(?:/|$)', jbis_url)
        if not match:
            print(f"警告: 馬のIDが見つかりません: {jbis_url}")
            return ""
        
        # 基本情報ページのURLを構築
        base_url = match.group(1)
        normalized_url = base_url.rstrip('/') + '/'
        
        print(f"URLを正規化: {jbis_url} -> {normalized_url}")
        return normalized_url
        
    except Exception as e:
        print(f"URLの正規化中にエラーが発生: {str(e)}")
        return ""

def extract_prize_from_jbis(jbis_url: str):
    """
    JBISの馬基本情報ページから総賞金を抽出する
    
    Args:
        jbis_url (str): JBISの馬基本情報ページURL
        
    Returns:
        float: 総賞金（万円単位）。見つからない場合は0.0
    """
    print("\n" + "="*80)
    print("=== extract_prize_from_jbis 関数が呼び出されました ===")
    print(f"[デバッグ] 入力URL: {jbis_url}")
    
    # デバッグ用にスタックトレースを出力
    import traceback
    print("\n[デバッグ] 呼び出し元のスタックトレース:")
    traceback.print_stack(limit=3)
    
    import re
    import time
    from bs4 import BeautifulSoup
    import requests
    import os
    from datetime import datetime
    from urllib.parse import urljoin, urlparse
    
    def parse_prize_text(prize_text):
        """賞金テキストから数値を抽出するヘルパー関数"""
        if not prize_text or prize_text.strip() in ('-', '0', '0.0'):
            return 0.0
            
        # 数値部分を抽出（「145455.1万円」や「1,234.5」のような形式に対応）
        prize_text = prize_text.replace(' ', '').replace('\u3000', '').replace('万円', '')
        match = re.search(r'([\d,]+(?:\.[\d,]+)?)', prize_text)
        if match:
            try:
                return float(match.group(1).replace(',', ''))
            except (ValueError, TypeError):
                return 0.0
        return 0.0
    
    if not jbis_url or not jbis_url.startswith('http'):
        print("無効なURLが指定されました")
        return 0.0

    try:
        # リトライ設定
        max_retries = 3
        retry_delay = 2  # 秒
        
        for attempt in range(max_retries):
            try:
                # リクエストヘッダー
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                    'Accept-Language': 'ja-JP,ja;q=0.9,en-US;q=0.8,en;q=0.7',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
                    'Referer': 'https://www.jbis.or.jp/'
                }
                
                # リクエスト送信
                print(f"[デバッグ] JBISにリクエストを送信中... (試行 {attempt + 1}/{max_retries})")
                response = requests.get(jbis_url, headers=headers, timeout=30)
                response.encoding = 'utf-8'  # エンコーディングをUTF-8に設定
                
                # ステータスコードを確認
                print(f"[デバッグ] ステータスコード: {response.status_code}")
                if response.status_code != 200:
                    print(f"[エラー] ステータスコード {response.status_code} が返されました")
                    response.raise_for_status()
                
                # デバッグ用にHTMLを保存
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                debug_dir = 'debug_jbis_responses'
                os.makedirs(debug_dir, exist_ok=True)
                debug_file = os.path.join(debug_dir, f'jbis_response_{timestamp}.html')
                
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(response.text)
                print(f"[デバッグ] JBISレスポンスを {debug_file} に保存しました")
                
                # レスポンスをパース
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 馬名を取得（デバッグ用）
                horse_name = "不明"
                title_tag = soup.find('title')
                if title_tag:
                    horse_name = title_tag.text.strip()
                    print(f"[デバッグ] 馬名: {horse_name}")
                
                # 方法1: data-4__item-2クラスから総賞金を検索
                print("\n[デバッグ] 方法1: data-4__item-2クラスから総賞金を検索中...")
                prize_div = soup.find('div', class_='data-4__item-2')
                if prize_div:
                    dt_elem = prize_div.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                    if dt_elem:
                        dd_elem = dt_elem.find_next_sibling('dd')
                        if dd_elem:
                            prize_text = dd_elem.get_text(strip=True)
                            print(f"[デバッグ] 賞金テキストを発見 (data-4__item-2): {prize_text}")
                            
                            total_prize = parse_prize_text(prize_text)
                            if total_prize > 0 or prize_text.strip() == '0.0':
                                print(f"[デバッグ] 方法1で総賞金を取得: {total_prize}万円")
                                return total_prize
                
                # 方法2: すべてのdt要素から総賞金を検索
                print("\n[デバッグ] 方法2: すべてのdt要素から総賞金を検索中...")
                for dt in soup.find_all('dt'):
                    if dt.get_text(strip=True) == '総賞金':
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            print(f"[デバッグ] 賞金テキストを発見 (dt/dd): {prize_text}")
                            total_prize = parse_prize_text(prize_text)
                            if total_prize > 0:
                                print(f"[デバッグ] 方法2で総賞金を取得: {total_prize}万円")
                                return total_prize
                
                # 方法3: 正規表現で直接検索（複数パターン）
                print("\n[デバッグ] 方法3: 正規表現で直接検索中...")
                prize_patterns = [
                    r'総賞金[^\d>]*([\d,]+(?:\.[\d,]+)?)',
                    r'総賞金[^<]*?<dd[^>]*>([^<]+)',
                    r'<dt[^>]*>\s*総賞金\s*</dt>\s*<dd[^>]*>([^<]+)'
                ]
                
                for pattern in prize_patterns:
                    matches = re.search(pattern, response.text, re.DOTALL)
                    if matches:
                        prize_text = matches.group(1).strip()
                        print(f"[デバッグ] 正規表現で賞金テキストを発見: {prize_text}")
                        total_prize = parse_prize_text(prize_text)
                        if total_prize > 0:
                            print(f"[デバッグ] 方法3で総賞金を取得: {total_prize}万円")
                            return total_prize
                
                # 方法2: 基本情報から総賞金を検索 (div.data-4__item-2を検索)
                print("\n[デバッグ] 方法2: div.data-4__item-2から総賞金を検索中...")
                for div in soup.find_all('div', class_='data-4__item-2'):
                    dt = div.find('dt')
                    if dt and '総賞金' in dt.get_text(strip=True):
                        dd = div.find('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            print(f"[デバッグ] 賞金テキストを発見: {prize_text}")
                            
                            # 空の場合は0.0を返す
                            if not prize_text or prize_text == '-':
                                print("[デバッグ] 賞金情報が空です")
                                return 0.0
                            
                            # 数値部分を抽出（「145455.1万円」や「1,234.5」のような形式に対応）
                            prize_text = prize_text.replace(' ', '').replace('\u3000', '').replace('万円', '')
                            match = re.search(r'([\d,]+(?:\.[\d,]+)?)', prize_text)
                            if match:
                                total_prize = float(match.group(1).replace(',', ''))
                                print(f"[デバッグ] 基本情報から総賞金を取得: {total_prize}万円")
                                return total_prize
                
                # 方法2: 正規表現で直接検索
                print("\n[デバッグ] 方法2: 正規表現で総賞金を検索中...")
                prize_patterns = [
                    r'総賞金[^\d]*([\d,]+(?:\.[\d,]+)?)[^\d]*万円',
                    r'獲得賞金[^\d]*([\d,]+(?:\.[\d,]+)?)[^\d]*万円',
                    r'賞金[^\d]*([\d,]+(?:\.[\d,]+)?)[^\d]*万円',
                    r'([\d,]+(?:\.[\d,]+)?)\s*万円',
                ]
                
                for pattern in prize_patterns:
                    match = re.search(pattern, response.text)
                    if match:
                        try:
                            total_prize = float(match.group(1).replace(',', ''))
                            if total_prize > 0:
                                print(f"[デバッグ] 正規表現パターンで賞金を発見: {total_prize}万円")
                                return total_prize
                        except (ValueError, TypeError):
                            continue
                
                # 見つからなかった場合は0.0を返す
                print("[デバッグ] どの方法でも総賞金を見つけることができませんでした")
                return 0.0
                
            except (requests.RequestException, Exception) as e:
                print(f"[エラー] リクエスト中にエラーが発生しました (試行 {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    print(f"[デバッグ] {retry_delay}秒後に再試行します...")
                    time.sleep(retry_delay)
                else:
                    print("[エラー] 最大リトライ回数に達しました")
                    return 0.0
                    
    except Exception as e:
        print(f"[エラー] 予期せぬエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 0.0

    except requests.exceptions.RequestException as e:
        print(f"\n[エラー] JBISへのリクエスト中にエラーが発生: {str(e)}")
        return 0.0
        print(f"\n[エラー] JBISからの賞金取得中に予期せぬエラーが発生: {str(e)}")
        import traceback
        traceback.print_exc()
        return 0.0

def save_to_processed_horses(horses: list, output_dir: str = 'data'):
    """馬の情報を本番形式でprocessed_horses.jsonに保存する"""
    # 出力ディレクトリが存在しない場合は作成
    os.makedirs(output_dir, exist_ok=True)
    
    # 出力ファイルパス
    output_file = os.path.join(output_dir, 'processed_horses.json')
    current_time = datetime.now().isoformat()
    
    # 結果を格納する辞書
    result = {
        'horses': [],
        'auction_history': []
    }
    
    # 既存のデータを読み込む（存在する場合）
    existing_data = {'horses': [], 'auction_history': []}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                loaded_data = json.load(f)
                # 既存のデータがリスト形式の場合は変換
                if isinstance(loaded_data, list):
                    existing_data = {
                        'horses': loaded_data,
                        'auction_history': []
                    }
                else:
                    existing_data = loaded_data
                print(f"既存のデータを読み込みました: 馬{len(existing_data.get('horses', []))}件, オークション履歴{len(existing_data.get('auction_history', []))}件")
            except json.JSONDecodeError:
                print("既存のデータが破損しているか空のため、新規作成します")
    
    # 既存の馬IDを取得
    existing_horse_ids = {h.get('id') for h in existing_data.get('horses', []) if 'id' in h}
    
    # 新しいデータを準備
    new_horses = []
    new_auction_history = []
    
    for horse in horses:
        horse_id = str(horse.get('id', ''))
        
        # 馬の基本データ
        horse_data = {
            'id': horse_id,
            'name': horse.get('name', ''),
            'sire': horse.get('sire', ''),
            'dam': horse.get('dam', ''),
            'damsire': horse.get('damsire', ''),
            'sex': horse.get('sex', ''),
            'age': horse.get('age', 0),
            'image_url': horse.get('image_url', ''),
            'jbis_url': horse.get('jbis_url', ''),
            'auction_url': horse.get('auction_url', ''),
            'disease_tags': horse.get('disease_tags', []),
            'created_at': current_time,
            'updated_at': current_time
        }
        
        # オークション履歴データ
        auction_data = {
            'id': f"{horse_id}_{int(time.time())}",
            'horse_id': horse_id,
            'auction_date': horse.get('auction_date', ''),
            'sold_price': horse.get('sold_price'),
            'total_prize_start': horse.get('total_prize_start', 0.0),
            'total_prize_latest': horse.get('total_prize_latest', 0.0),
            'weight': horse.get('weight'),
            'seller': horse.get('seller', ''),
            'is_unsold': horse.get('is_unsold', False),
            'comment': horse.get('comment', ''),
            'created_at': current_time
        }
        
        if horse_id not in existing_horse_ids:
            new_horses.append(horse_data)
        
        new_auction_history.append(auction_data)
    
    # 既存のデータに新しいデータをマージ
    result['horses'] = existing_data.get('horses', []) + new_horses
    result['auction_history'] = existing_data.get('auction_history', []) + new_auction_history
    
    # ファイルに保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nテストデータを保存しました:")
    print(f"- 馬データ: {len(result['horses'])}件 (新規: {len(new_horses)}件)")
    print(f"- オークション履歴: {len(result['auction_history'])}件 (新規: {len(new_auction_history)}件)")
    print(f"保存先: {output_file}")

def main():
    # キャッシュディレクトリのパス
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache/20250818"
    output_file = os.path.join(cache_dir, "processed_horses.json")
    
    # リストページのHTMLを読み込む
    list_html_path = os.path.join(cache_dir, "list.html")
    if not os.path.exists(list_html_path):
        print(f"エラー: {list_html_path} が見つかりません。")
        return
    
    print(f"リストページを読み込み中: {list_html_path}")
    with open(list_html_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # スクレイピングを実行
    print("\nスクレイピングを開始します...")
    start_time = time.time()
    
    # リストページから馬の情報を取得
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    
    # 既存のデータを読み込む（存在する場合）
    existing_data = {}
    if os.path.exists(output_file):
        with open(output_file, 'r', encoding='utf-8') as f:
            try:
                existing_data = json.load(f)
            except json.JSONDecodeError:
                print("既存のデータが破損しているか空のため、新規作成します")
    
    # 既存データがリスト形式の場合、辞書形式に変換
    if isinstance(existing_data, list):
        existing_data = {str(horse.get('id')): horse for horse in existing_data}
    
    for idx, element in enumerate(horse_elements, 1):
        try:
            print(f"\n=== 馬 {idx}/{len(horse_elements)} の処理を開始 ===")
            
            # 馬名を抽出
            name_elem = element.select_one('.auctionTableCard__name, .horseName')
            name = name_elem.get_text(strip=True) if name_elem else '名前不明'
            print(f"馬名: {name}")
            
            # 詳細ページのURLを抽出
            detail_url = ''
            jbis_url = ''
            link_selectors = [
                'a.auctionTableCard__name--link',
                'a[href*="item"]',
                'a[href*="/horse/"]',
                'a[href*="auction"]',
                'a[href*="detail"]'
            ]
            
            for selector in link_selectors:
                link_elem = element.select_one(selector)
                if link_elem and 'href' in link_elem.attrs:
                    detail_url = link_elem['href']
                    if not detail_url.startswith('http'):
                        if not detail_url.startswith('/'):
                            detail_url = f"/{detail_url}"
                        detail_url = f"https://www.jbis.or.jp{detail_url}"
                    
                    # JBIS URLを抽出
                    if '/horse/' in detail_url:
                        jbis_url = detail_url
                    break
            
            # 馬の基本情報を作成
            horse_data = {
                'name': name,
                'id': idx,
                'scraped_at': datetime.now().isoformat(),
                'jbis_url': jbis_url if jbis_url else ''
            }
            
            # JBISから賞金を直接取得
            if jbis_url and jbis_url.startswith('http'):
                print(f"JBISから賞金情報を取得中: {jbis_url}")
                try:
                    total_prize = extract_prize_from_jbis(jbis_url)
                    if total_prize > 0:
                        horse_data['total_prize_start'] = total_prize
                        print(f"JBISから総賞金を取得: {total_prize}万円")
                    else:
                        print("賞金情報が見つかりませんでした")
                        horse_data['total_prize_start'] = 0.0
                except Exception as e:
                    print(f"JBISからの賞金取得中にエラーが発生: {e}")
                    horse_data['total_prize_start'] = 0.0
            
            # 詳細ページのキャッシュを読み込む
            print(f"\n=== デバッグ: 詳細ページ処理開始 ===")
            print(f"詳細ページURL: {detail_url}")
            if detail_url:
                try:
                    # URLから馬IDを抽出
                    horse_id = re.search(r'/horse/(\d+)', detail_url)
                    if horse_id:
                        detail_file = os.path.join(cache_dir, f"details/{horse_id.group(1)}.html")
                        if os.path.exists(detail_file):
                            with open(detail_file, 'r', encoding='utf-8') as f:
                                detail_html = f.read()
                            
                            # JBISリンクを抽出
                            print("詳細ページのHTMLをパース中...")
                            detail_soup = BeautifulSoup(detail_html, 'html.parser')
                            
                            # まずは直接aタグから検索
                            jbis_link = detail_soup.find('a', href=lambda x: x and 'jbis.or.jp' in x)
                            
                            # 見つからない場合は、テキストから直接URLを抽出
                            if not jbis_link:
                                print("aタグからJBISリンクを見つけられませんでした。テキストから検索します...")
                                # テキストから直接URLを検索
                                jbis_url_match = re.search(r'https?://www\.jbis\.or\.jp/horse/\d+/', detail_html)
                                if jbis_url_match:
                                    jbis_url = jbis_url_match.group(0)
                                    print(f"テキストからJBIS URLを発見: {jbis_url}")
                                    jbis_link = type('obj', (object,), {'get': lambda self, x: jbis_url})()
                            
                            if jbis_link:
                                jbis_url = jbis_link.get('href', '')
                                # URLが相対パスの場合、ベースURLを追加
                                if jbis_url.startswith('/'):
                                    jbis_url = f"https://www.jbis.or.jp{jbis_url}"
                                # レコードページの場合、基本情報ページにリダイレクト
                                if jbis_url.endswith('/record/'):
                                    jbis_url = jbis_url.replace('/record/', '/')
                                horse_data['jbis_url'] = jbis_url
                                print(f"JBIS URLを取得: {jbis_url}")
                            else:
                                print("警告: JBISリンクが見つかりませんでした")
                                # デバッグ用にHTMLを保存
                                with open('debug_detail_page.html', 'w', encoding='utf-8') as f:
                                    f.write(detail_html)
                                print("デバッグ用に詳細ページを debug_detail_page.html に保存しました")
                                
                                # JBISから賞金情報を取得
                                try:
                                    normalized_jbis_url = jbis_url.replace('/pedigree/', '/').replace('/record/', '/')
                                    if normalized_jbis_url != jbis_url:
                                        print(f"JBIS URLを正規化: {jbis_url} -> {normalized_jbis_url}")
                                    
                                    # JBISページを取得
                                    print(f"JBISページにアクセス: {normalized_jbis_url}")
                                    jbis_response = requests.get(normalized_jbis_url, timeout=30)
                                    jbis_response.raise_for_status()
                                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                                    
                                    # レスポンスの最初の500文字をログ出力
                                    print(f"JBISレスポンス (先頭500文字): {jbis_response.text[:500]}...")
                                    
                                    # 総賞金を抽出
                                    total_prize_latest = None
                                    
                                    # 方法1: dtタグから総賞金を取得
                                    print("方法1: dtタグから総賞金を検索中...")
                                    total_prize_dt = jbis_soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                                    if total_prize_dt:
                                        print(f"総賞金のdtタグを発見: {total_prize_dt}")
                                        dd_elem = total_prize_dt.find_next_sibling('dd')
                                        if dd_elem:
                                            prize_text = dd_elem.get_text(strip=True)
                                            print(f"賞金テキスト: {prize_text}")
                                            match = re.search(r'([\d,]+(?:\.\d+)?)', prize_text)
                                            if match:
                                                total_prize_latest = float(match.group(1).replace(',', ''))
                                                print(f"JBISから総賞金を取得: {total_prize_latest}万円")
                                            else:
                                                print("賞金の数値部分を抽出できませんでした")
                                        else:
                                            print("総賞金のddタグが見つかりません")
                                    else:
                                        print("総賞金のdtタグが見つかりません")
                                    
                                    # 方法2: 正規表現で直接検索（フォールバック）
                                    if total_prize_latest is None:
                                        print("方法2: 正規表現で総賞金を検索中...")
                                        prize_match = re.search(r'総賞金\s*([\d,]+(?:\.[\d,]+)?)\s*万円', jbis_response.text)
                                        if prize_match:
                                            total_prize_latest = float(prize_match.group(1).replace(',', ''))
                                            print(f"正規表現で総賞金を取得: {total_prize_latest}万円")
                                        else:
                                            print("正規表現で総賞金を検出できませんでした")
                                            print("デバッグ: 総賞金の正規表現マッチングに失敗しました。HTMLを確認してください。")
                                            with open('debug_jbis_page.html', 'w', encoding='utf-8') as f:
                                                f.write(jbis_response.text)
                                            print("デバッグ用にHTMLを debug_jbis_page.html に保存しました")
                                    
                                    if total_prize_latest is not None:
                                        horse_data['total_prize_latest'] = total_prize_latest
                                        print(f"total_prize_latestを{total_prize_latest}万円に設定")
                                    else:
                                        print("総賞金の取得に失敗しました")
                                    
                                except Exception as e:
                                    print(f"JBISからの賞金取得中にエラーが発生: {e}")
                
                except Exception as e:
                    print(f"詳細ページの処理中にエラーが発生: {e}")
            
            if detail_url:
                horse_data['detail_url'] = detail_url
                
                # JBIS URLを抽出（詳細ページから取得）
                try:
                    # キャッシュから詳細ページを読み込む
                    horse_id = re.search(r'/horse/(\d+)', detail_url)
                    if horse_id:
                        detail_file = os.path.join(cache_dir, f"details/{horse_id.group(1)}.html")
                        if os.path.exists(detail_file):
                            with open(detail_file, 'r', encoding='utf-8') as f:
                                detail_html = f.read()
                            
                            # JBISリンクを抽出
                            print("詳細ページのHTMLをパース中...")
                            detail_soup = BeautifulSoup(detail_html, 'html.parser')
                            
                            # まずは直接aタグから検索
                            jbis_link = detail_soup.find('a', href=lambda x: x and 'jbis.or.jp' in x)
                            
                            # 見つからない場合は、テキストから直接URLを抽出
                            if not jbis_link:
                                print("aタグからJBISリンクを見つけられませんでした。テキストから検索します...")
                                # テキストから直接URLを検索
                                jbis_url_match = re.search(r'https?://www\.jbis\.or\.jp/horse/\d+/', detail_html)
                                if jbis_url_match:
                                    jbis_url = jbis_url_match.group(0)
                                    print(f"テキストからJBIS URLを発見: {jbis_url}")
                                    jbis_link = type('obj', (object,), {'get': lambda self, x: jbis_url})()
                            
                            if jbis_link:
                                jbis_url = jbis_link.get('href', '')
                                # URLが相対パスの場合、ベースURLを追加
                                if jbis_url.startswith('/'):
                                    jbis_url = f"https://www.jbis.or.jp{jbis_url}"
                                # レコードページの場合、基本情報ページにリダイレクト
                                if jbis_url.endswith('/record/'):
                                    jbis_url = jbis_url.replace('/record/', '/')
                                horse_data['jbis_url'] = jbis_url
                                print(f"JBIS URLを取得: {jbis_url}")
                            else:
                                print("警告: JBISリンクが見つかりませんでした")
                                # デバッグ用にHTMLを保存
                                with open('debug_detail_page.html', 'w', encoding='utf-8') as f:
                                    f.write(detail_html)
                                print("デバッグ用に詳細ページを debug_detail_page.html に保存しました")
                                
                                # JBISから賞金情報を取得
                                try:
                                    normalized_jbis_url = jbis_url.replace('/pedigree/', '/').replace('/record/', '/')
                                    if normalized_jbis_url != jbis_url:
                                        print(f"JBIS URLを正規化: {jbis_url} -> {normalized_jbis_url}")
                                    
                                    # JBISページを取得
                                    print(f"JBISページにアクセス: {normalized_jbis_url}")
                                    jbis_response = requests.get(normalized_jbis_url, timeout=30)
                                    jbis_response.raise_for_status()
                                    jbis_soup = BeautifulSoup(jbis_response.content, 'html.parser')
                                    
                                    # レスポンスの最初の500文字をログ出力
                                    print(f"JBISレスポンス (先頭500文字): {jbis_response.text[:500]}...")
                                    
                                    # 総賞金を抽出
                                    total_prize_latest = None
                                    
                                    # 方法1: dtタグから総賞金を取得
                                    print("方法1: dtタグから総賞金を検索中...")
                                    total_prize_dt = jbis_soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                                    if total_prize_dt:
                                        print(f"総賞金のdtタグを発見: {total_prize_dt}")
                                        dd_elem = total_prize_dt.find_next_sibling('dd')
                                        if dd_elem:
                                            prize_text = dd_elem.get_text(strip=True)
                                            print(f"賞金テキスト: {prize_text}")
                                            match = re.search(r'([\d,]+(?:\.\d+)?)', prize_text)
                                            if match:
                                                total_prize_latest = float(match.group(1).replace(',', ''))
                                                print(f"JBISから総賞金を取得: {total_prize_latest}万円")
                                            else:
                                                print("賞金の数値部分を抽出できませんでした")
                                        else:
                                            print("総賞金のddタグが見つかりません")
                                    else:
                                        print("総賞金のdtタグが見つかりません")
                                    
                                    # 方法2: 正規表現で直接検索（フォールバック）
                                    if total_prize_latest is None:
                                        print("方法2: 正規表現で総賞金を検索中...")
                                        prize_match = re.search(r'総賞金\s*([\d,]+(?:\.[\d,]+)?)\s*万円', jbis_response.text)
                                        if prize_match:
                                            total_prize_latest = float(prize_match.group(1).replace(',', ''))
                                            print(f"正規表現で総賞金を取得: {total_prize_latest}万円")
                                        else:
                                            print("正規表現で総賞金を検出できませんでした")
                                            print("デバッグ: 総賞金の正規表現マッチングに失敗しました。HTMLを確認してください。")
                                            with open('debug_jbis_page.html', 'w', encoding='utf-8') as f:
                                                f.write(jbis_response.text)
                                            print("デバッグ用にHTMLを debug_jbis_page.html に保存しました")
                                    
                                    if total_prize_latest is not None:
                                        horse_data['total_prize_latest'] = total_prize_latest
                                        print(f"total_prize_latestを{total_prize_latest}万円に設定")
                                    else:
                                        print("総賞金の取得に失敗しました")
                                    
                                except Exception as e:
                                    print(f"JBISからの賞金取得中にエラーが発生: {e}")
                
                except Exception as e:
                    print(f"詳細ページの処理中にエラーが発生: {e}")
            
            # 既存のデータがあればマージ
            horse_id = str(horse_data.get('id'))
            if horse_id in existing_data:
                existing_data[horse_id].update(horse_data)
                horse_data = existing_data[horse_id]
            horses.append(horse_data)
            
            # サーバーに負荷をかけないように少し待機
            time.sleep(1)
            
        except Exception as e:
            print(f"馬 {idx} の処理中にエラーが発生: {e}")
            import traceback
            traceback.print_exc()
    
    # 本番形式でデータを保存
    save_to_processed_horses(horses, os.path.dirname(output_file))
    print(f"スクレイピングが完了しました。結果を {output_file} に保存しました。")
    print(f"処理時間: {time.time() - start_time:.2f}秒")
    print(f"処理した馬の数: {len(horses)}")
    
    # 賞金情報の抽出テストを実行
    print("\n=== 賞金情報の抽出テストを開始します ===")
    test_prize_extraction(limit=3)  # テスト用に3頭のみ処理

if __name__ == "__main__":
    main()
