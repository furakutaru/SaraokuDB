#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import glob
import logging
import traceback
import sys
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector

# ロガーの設定
logger = logging.getLogger(__name__)

# カスタムモジュールのインポート
from extract_race_record import extract_race_record
from extract_sold_price import extract_sold_price
from extract_seller import extract_seller

def extract_prize_from_auction(html_content, horse_name):
    """
    オークションリストページから賞金情報を抽出する
    
    Args:
        html_content (str): オークションリストページのHTML
        horse_name (str): 馬名（デバッグ用）
        
    Returns:
        str or float: 総賞金（万円単位）。見つからない場合は0.0、繁殖牝馬の場合は'-'を返す
    """
    try:
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 繁殖牝馬の場合は'-'を返す
        if any(text in html_content for text in ['繁殖牝馬', '受胎種牡馬']):
            logging.info(f"馬名 '{horse_name}' は繁殖牝馬のため、賞金は'-'を返します")
            return '-'
        
        # 未出走馬の場合は0を返す
        if '未出走' in html_content:
            logging.info(f"馬名 '{horse_name}' は未出走のため賞金は0円です")
            return 0.0
        
        # 賞金情報を含む要素を探す
        prize_div = soup.find('div', class_='auctionTableCard__price')
        if not prize_div:
            logging.warning(f"馬名 '{horse_name}': 賞金要素が見つかりませんでした")
            return 0.0
        
        # ラベルが「総賞金」であることを確認
        label_div = prize_div.find('div', class_='label')
        if not label_div or '総賞金' not in label_div.get_text():
            logging.warning(f"馬名 '{horse_name}': 総賞金のラベルが見つかりませんでした")
            return 0.0
        
        # 賞金の値を取得
        value_div = prize_div.find('div', class_='value')
        if not value_div:
            logging.warning(f"馬名 '{horse_name}': 賞金の値が見つかりませんでした")
            return 0.0
        
        prize_text = value_div.get_text(strip=True)
        
        # 数値部分を抽出（「1,234.0万円」→ 1,234.0）
        match = re.search(r'([\d,]+\.[\d]+)', prize_text)
        if match:
            total_prize = match.group(1)
            logging.info(f"馬名 '{horse_name}' の賞金を抽出: {total_prize}万円")
            return total_prize
        
        logging.warning(f"馬名 '{horse_name}' の賞金情報を抽出できませんでした")
        return 0.0
        
    except Exception as e:
        logging.error(f"賞金情報の抽出中にエラーが発生しました（馬名: {horse_name}）: {str(e)}")
        import traceback
        logging.error(traceback.format_exc())
        return 0.0

# スクリプトのディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# 健康関連のキーワード
health_keywords = [
    '骨折', '屈腱炎', 'ソエ', '跛行', '跛行あり', '跛行歴あり', '跛行歴',
    '屈腱', '靭帯', '靭帯炎', '骨瘤', '骨膜炎', '骨腫', '骨棘', '骨端症',
    '関節炎', '関節症', '関節軟骨', '関節内骨折', '関節ねんざ', '関節水腫',
    '脱臼', '亜脱臼', '捻挫', '捻転', '捻転症', '捻転性', '捻転性疾患'
]

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('process_horse_details.log', encoding='utf-8')
    ]
)
logger = logging.getLogger('process_horse_details')

def extract_prize_from_jbis(jbis_url: str) -> float:
    """
    JBISの馬基本情報ページから総賞金を抽出する
    
    Args:
        jbis_url (str): JBISの馬基本情報ページURL
        
    Returns:
        float: 総賞金（万円単位）。見つからない場合は0.0
    """
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
        logging.warning("無効なURLが指定されました")
        return 0.0

    try:
        # リトライ設定（1回のみ実行）
        max_retries = 1
        retry_delay = 0  # 遅延なし
        
        for attempt in range(max_retries):
            try:
                # より自然なユーザーエージェントに更新
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36',
                    'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
                    'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7',
                    'Referer': 'https://www.google.com/',
                    'Sec-Ch-Ua': '"Google Chrome";v="125", "Chromium";v="125"',
                    'Sec-Ch-Ua-Mobile': '?0',
                    'Sec-Ch-Ua-Platform': '"macOS"',
                    'Sec-Fetch-Dest': 'document',
                    'Sec-Fetch-Mode': 'navigate',
                    'Sec-Fetch-Site': 'none',
                    'Sec-Fetch-User': '?1',
                    'Upgrade-Insecure-Requests': '1',
                    'Dnt': '1'
                }
                
                # リクエスト送信
                response = requests.get(jbis_url, headers=headers, timeout=30)
                response.encoding = 'utf-8'  # エンコーディングをUTF-8に設定
                
                # ステータスコードを確認
                if response.status_code != 200:
                    if response.status_code >= 400:  # エラーのみログ出力
                        logging.warning("HTTPエラー: ステータスコード %d" % response.status_code)
                    response.raise_for_status()
                
                # レスポンスをパース
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # 方法1: data-4__item-2クラスから総賞金を検索
                prize_div = soup.find('div', class_='data-4__item-2')
                if prize_div:
                    dt_elem = prize_div.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
                    if dt_elem:
                        dd_elem = dt_elem.find_next_sibling('dd')
                        if dd_elem:
                            prize_text = dd_elem.get_text(strip=True)
                            total_prize = parse_prize_text(prize_text)
                            if total_prize > 0 or prize_text.strip() == '0.0':
                                logging.info("方法1で総賞金を取得: %s万円" % total_prize)
                                return total_prize
                
                # 方法2: すべてのdt要素から総賞金を検索
                for dt in soup.find_all('dt'):
                    if dt.get_text(strip=True) == '総賞金':
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            total_prize = parse_prize_text(prize_text)
                            if total_prize > 0 or prize_text.strip() == '0.0':
                                logging.info("方法2で総賞金を取得: %s万円" % total_prize)
                                return total_prize
                
                # 方法3: 正規表現で直接検索（フォールバック）
                prize_patterns = [
                    r'総賞金[^\d>]*([\d,]+(?:\.[\d,]+)?)',
                    r'総賞金[^<]*?<dd[^>]*>([^<]+)',
                    r'<dt[^>]*>\s*総賞金\s*</dt>\s*<dd[^>]*>([^<]+)'
                ]
                
                for pattern in prize_patterns:
                    matches = re.search(pattern, response.text, re.DOTALL)
                    if matches:
                        prize_text = matches.group(1).strip()
                        total_prize = parse_prize_text(prize_text)
                        if total_prize > 0 or prize_text.strip() == '0.0':
                            logging.info("方法3で総賞金を取得: %s万円" % total_prize)
                            return total_prize
                
                # 見つからなかった場合は0.0を返す
                logging.info("総賞金情報が見つかりませんでした")
                return 0.0
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning("リクエストエラー: %s。%d秒後に再試行します..." % (str(e), 0))
                time.sleep(0)
                
    except Exception as e:
        logging.error("賞金情報の取得中にエラーが発生: %s" % str(e))
        return 0.0

def _extract_disease_tags(comment: str) -> str:
    """
    コメントから病気タグを抽出する
    
    Args:
        comment (str): 抽出元のコメントテキスト
        
    Returns:
        str: カンマ区切りの病気タグ。見つからない場合は「なし」を返します。
    """
    if not comment:
        return "なし"

    try:
        # 病気キーワードとその文脈パターン
        disease_patterns = {
            '喉頭片麻痺': r'喉頭片麻痺',
            '喘鳴症': r'喘鳴症',
            '脚部不安': r'脚部不安',
            '関節炎': r'関節炎',
            '腱炎': r'(?<!屈)腱炎(?!\w)',  # 「屈腱炎」を除く
            '屈腱炎': r'屈腱炎',
            '骨折': r'骨折(?!\w)',
            '脱臼': r'脱臼(?!\w)',
            '球節炎': r'球節炎',
            'さく癖': r'さく癖',
            # 筋肉痛は削除（一般的な症状のため）
        }

        import re
        found_diseases = set()  # 重複を防ぐためセットを使用
        
        for disease, pattern in disease_patterns.items():
            # 病気としての文脈を考慮した検索
            if re.search(rf'(?:[、。]|^|の|に|が|を|は)\s*{pattern}(?:[、。]|$|の|に|が|を|は)', comment):
                found_diseases.add(disease)

        return '、'.join(sorted(found_diseases)) if found_diseases else "なし"
    except Exception as e:
        logger.error(f"病気タグの抽出中にエラーが発生しました: {e}")
        logger.error(traceback.format_exc())
        return "なし"

def _extract_comment(html_content):
    """
    馬の詳細ページからコメントを抽出する
    
    Args:
        html_content (str): 馬の詳細ページのHTML
        
    Returns:
        str: 抽出されたコメントテキスト。見つからない場合は空文字列。
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 「本馬について」のセクションを探す
        section = None
        for elem in soup.find_all(['div', 'section', 'article']):
            if '本馬について' in elem.get_text():
                section = elem
                break
                
        if section:
            # 2. <hr>タグを探して、その後のテキストを取得
            hr_tag = section.find('hr')
            if hr_tag:
                comment_parts = []
                for sibling in hr_tag.next_siblings:
                    if hasattr(sibling, 'get_text'):
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            comment_parts.append(text)
                
                if comment_parts:
                    comment = ' '.join(comment_parts)
                    # 連続する空白を1つに正規化
                    return ' '.join(comment.split())
        
        # 3. 上記で見つからない場合は<pre>タグを探す
        pre_tag = soup.find('pre')
        if pre_tag:
            comment = pre_tag.get_text(separator='\n', strip=True)
            # 連続する空白を1つに正規化
            return ' '.join(comment.split())
            
        return ""
        
    except Exception as e:
        logger.error(f"コメントの抽出中にエラーが発生: {e}")
        logger.error(traceback.format_exc())
        return ""

def extract_horse_info(detail_file):
    """詳細ページのHTMLから馬情報を抽出する"""
    logging.info("Processing detail file: %s" % detail_file)
    
    # ファイルをバイナリモードで読み込み、エンコーディングを自動検出
    try:
        with open(detail_file, 'rb') as f:
            raw_content = f.read()
            
        file_size = len(raw_content)
        logging.debug("Processing file: %s (Size: %d bytes)" % (detail_file, file_size))
        
        if file_size == 0:
            logging.error("File is empty: %s" % detail_file)
            return None
            
        # エンコーディングを推測してデコード
        html_content = None
        for encoding in ['utf-8', 'shift_jis', 'euc_jisx0213', 'euc_jp', 'cp932']:
            try:
                html_content = raw_content.decode(encoding)
                break
            except UnicodeDecodeError:
                continue
                
        if not html_content:
            logging.error("Failed to decode file with any encoding: %s" % detail_file)
            return None
            
        # 戦績情報を抽出
        race_record = extract_race_record(html_content)
        
        # HTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 健康問題を格納するリストを初期化
        health_issues = []
        
        # コメントを抽出
        comment = _extract_comment(html_content)
        
        # 基本情報を格納する辞書
        horse_info = {
            'source_file': os.path.basename(detail_file),
            'extracted_at': datetime.now().isoformat(),
            'seller': "",                  # 販売者名
            'auction_date': "",            # オークション日
            'total_prize_start': 0.0,      # オークション時点の総賞金
            'total_prize_latest': 0.0,     # 最新の総賞金（初期値はオークション時点と同じ）
            'comment': comment             # 馬のコメント
        }
        
        # 病気タグを抽出
        horse_info['disease_tags'] = _extract_disease_tags(comment)
        
        # ここから処理を続行
        return _process_horse_info(soup, horse_info, health_issues, race_record, detail_file, html_content)
        
    except Exception as e:
        logging.error("Error processing file %s: %s" % (detail_file, str(e)))
        logging.error(traceback.format_exc())
        return None

def _process_horse_info(soup, horse_info, health_issues, race_record, detail_file, html_content):
    """馬情報の処理を実行するヘルパー関数"""
    # 1. 馬名を抽出
    name = None
    title = soup.title.string if soup.title else ''
    
    # デバッグ用にHTMLの最初の200文字をログに出力
    html_preview = str(soup)[:200]
    logging.debug("Processing file: %s" % detail_file)
    logging.debug("Title: %s" % title)
    logging.debug("First 200 chars of HTML: %s..." % html_preview)
    
    # JBIS URLを抽出
    jbis_url = None
    
    # パターン1: 直接のJBISリンク
    jbis_links = soup.find_all('a', href=True, string=re.compile(r'JBIS|血統|JBIS-Serve', re.IGNORECASE))
    
    # パターン2: 画像内のJBISリンク
    if not jbis_links:
        jbis_imgs = soup.find_all('img', src=re.compile(r'jbis', re.IGNORECASE))
        for img in jbis_imgs:
            parent_link = img.find_parent('a', href=True)
            if parent_link:
                jbis_links.append(parent_link)
    
    # パターン3: テキスト内のURL
    if not jbis_links:
        text_links = soup.find_all('a', href=re.compile(r'jbis\.or\.jp', re.IGNORECASE))
        jbis_links.extend(text_links)
    
    # 見つかったリンクを処理
    for link in jbis_links:
        href = link.get('href', '').strip()
        if not href:
            continue
            
        # URLを正規化
        if 'jbis.or.jp' in href:
            jbis_url = href
            # 相対URLの場合は絶対URLに変換
            if not jbis_url.startswith(('http://', 'https://')):
                if jbis_url.startswith('//'):
                    jbis_url = "https:%s" % jbis_url
                else:
                    jbis_url = "https://www.jbis.or.jp%s" % (jbis_url if jbis_url.startswith('/') else '/' + jbis_url)
            break
    
    if not jbis_url:
        debug_file = "debug_jbis_not_found_%s" % os.path.basename(detail_file)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(html_content)
        logging.warning("JBIS URLが見つかりませんでした。デバッグ用にHTMLを保存: %s" % debug_file)
    else:
        logging.info("JBIS URLを発見: %s" % jbis_url)
    
    # 馬名を設定
    if title:
        # タイトルから「 | サラブレッドオークション」の前の部分を抽出
        name = title.split('|')[0].strip()
        
        # デバッグ用に抽出前の名前をログに出力
        logging.debug("Name before processing: %s" % name)
        
        # 馬名から性別、年齢、コメントなどを削除
        name = re.sub(r'\s*[牡牝セ]\s*\d+\s*[歳年].*$', '', name).strip()
        # 「セン２歳 ※地方競馬 在籍」のようなテキストを削除
        name = re.sub(r'\s*セ[ンン]\s*\d+\s*[歳年].*$', '', name).strip()
        # 余分なスペースを削除
        name = ' '.join(name.split())
        
        # デバッグ用に処理後の名前をログに出力
        logging.debug("Name after processing: %s" % name)
    
    if not name:
        logging.warning("Could not find horse name in %s" % detail_file)
        return None
    
    horse_info['name'] = name
    
    # 性別と年齢を抽出
    sex_match = re.search(r'([牡牝セ])\s*\d+\s*[歳年]', title or '')
    if sex_match:
        horse_info['sex'] = sex_match.group(1)
    
    # 年齢を抽出
    age_match = re.search(r'(\d+)\s*[歳年]', title or '')
    if age_match:
        try:
            horse_info['age'] = int(age_match.group(1))
        except (ValueError, IndexError):
            pass
    
    # リストページから販売者情報を取得
    seller_div = soup.find('div', class_='auctionTableCard__seller')
    if seller_div:
        seller_span = seller_div.find('span', class_='value')
        if seller_span:
            seller = seller_span.get_text(strip=True)
            if seller:
                horse_info['seller'] = seller
                logging.info(f"販売者情報を取得: {seller}")
    
    # 販売者情報が取得できなかった場合はデフォルトの抽出方法を試す
    if 'seller' not in horse_info:
        try:
            seller = extract_seller(soup)
            if seller:
                horse_info['seller'] = seller
                logging.info(f"extract_seller関数から販売者情報を取得: {seller}")
            else:
                logging.warning("販売者情報を取得できませんでした")
                horse_info['seller'] = None
        except Exception as e:
            logging.error(f"販売者情報の抽出中にエラーが発生: {str(e)}")
            horse_info['seller'] = None
    
    # 血統情報を抽出
    page_text = soup.get_text(' ', strip=True)
    
    # 父、母、母の父を抽出
    sire_match = re.search(r'父[：:]([^\s]+)', page_text)
    if sire_match:
        horse_info['sire'] = sire_match.group(1).strip()
        
    dam_match = re.search(r'母[：:]([^\s]+)', page_text)
    if dam_match:
        horse_info['dam'] = dam_match.group(1).strip()
        
    damsire_match = re.search(r'母の父[：:]([^\s]+)', page_text)
    if damsire_match:
        horse_info['damsire'] = damsire_match.group(1).strip()
    
    # オークション価格を抽出
    price_text = soup.get_text()
    
    # オークション価格（落札価格）を抽出 - 複数のパターンに対応
    price_match = None
    
    # パターン1: 「落札価格 1,234万円」形式
    if not price_match:
        price_match = re.search(r'落札価格\s*[：:]*\s*(\d[\d,]*)', price_text)
    
    # パターン2: 「落札価格: 1,234万円」形式
    if not price_match:
        price_match = re.search(r'落札価格[^\d]*(\d[\d,]*)', price_text)
    
    # パターン3: 「1,234万円（落札価格）」形式
    if not price_match:
        price_match = re.search(r'(\d[\d,]*)\s*万円\s*[（(]落札価格[)）]', price_text)
    
    if price_match:
        try:
            # カンマを削除して数値に変換
            price_str = price_match.group(1).replace(',', '')
            horse_info['auction_prize'] = float(price_str)
            logging.info(f"オークション価格を抽出: {horse_info['auction_prize']}万円")
        except (ValueError, TypeError) as e:
            logging.warning(f"オークション価格のパースに失敗: {e}")
            horse_info['auction_prize'] = 0.0
    else:
        horse_info['auction_prize'] = 0.0
        logging.warning("オークション価格が見つかりませんでした")
    
    # 現在の賞金を抽出 - 複数のパターンに対応
    prize_match = None
    
    # パターン1: 「総賞金 1,234.5万円」形式
    if not prize_match:
        prize_match = re.search(r'総賞金[^\d]*([\d,.]+)[^\d]*万円', price_text)
    
    # パターン2: 「賞金: 1,234.5万円」形式
    if not prize_match:
        prize_match = re.search(r'賞金[：:][^\d]*([\d,.]+)[^\d]*万円', price_text)
    
    # パターン3: 単純な賞金表記「1,234.5万円」形式
    if not prize_match:
        prize_match = re.search(r'([\d,]+(?:\.[\d,]+)?)[^\d]*万円', price_text)
    
    if prize_match:
        try:
            # カンマを削除して数値に変換
            prize_str = prize_match.group(1).replace(',', '')
            horse_info['current_prize'] = float(prize_str)
            logging.info(f"現在の賞金を抽出: {horse_info['current_prize']}万円")
        except (ValueError, TypeError) as e:
            logging.warning(f"賞金のパースに失敗: {e}")
            horse_info['current_prize'] = 0.0
    else:
        horse_info['current_prize'] = 0.0
        logging.warning("賞金情報が見つかりませんでした")
    
    try:
        # オークション日を抽出
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html_content)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            horse_info['auction_date'] = f"{year}-{month}-{day}"
            logging.info(f"オークション日を抽出: {horse_info['auction_date']}")
    except Exception as e:
        logging.error("Error extracting auction date: %s" % str(e))
    
    # JBIS URLから最新の総賞金を取得
    if jbis_url:
        logging.info("JBIS URLから最新の総賞金を取得中: %s" % jbis_url)
        try:
            latest_prize = extract_prize_from_jbis(jbis_url)
            if latest_prize > 0:
                horse_info['total_prize_latest'] = latest_prize
                logging.info("最新の総賞金を更新: %s 万円" % latest_prize)
            else:
                logging.warning("JBISから総賞金を取得できませんでした")
        except Exception as e:
                logging.error("JBISからの賞金取得中にエラーが発生: %s" % str(e))
        
        # 性別を抽出（「牡」「牝」「セ」のいずれか）
        if 'sex' not in horse_info:
            # パターン1: 「性別 数字歳」の形式（例: 牡 3歳）
            sex_match = re.search(r'([牡牝セ])\s*\d+\s*[歳年]', title or '')
            
            if sex_match:
                horse_info['sex'] = sex_match.group(1)
                logging.debug("Extracted sex (pattern 1): %s" % horse_info['sex'])
            else:
                # パターン2: 「センナンサイ」の形式（例: セン2歳）
                sex_match = re.search(r'([セ]ン\s*\d+\s*[歳年])', title or '')
                if sex_match:
                    horse_info['sex'] = 'セ'  # セに正規化
                    logging.debug("Extracted sex (pattern 2): %s" % horse_info['sex'])
                else:
                    # パターン3: 単純に「性別」のみ
                    sex_match = re.search(r'([牡牝セ])', title or '')
                    if sex_match:
                        horse_info['sex'] = sex_match.group(1)
                        logging.debug("Extracted sex (fallback): %s" % horse_info['sex'])
                    else:
                        logging.warning("Could not extract sex from title: %s" % title)
        
        # 年齢を抽出（まだ抽出されていない場合）
        if 'age' not in horse_info:
            age_match = re.search(r'(\d+)\s*[歳年]', title or '')
            if age_match:
                try:
                    horse_info['age'] = int(age_match.group(1))
                    logging.debug("Extracted age: %s" % horse_info['age'])
                except (ValueError, IndexError) as e:
                    logging.warning("Failed to parse age: %s" % str(e))
        
        # 血統情報を抽出
        page_text = soup.get_text(' ', strip=True)
        
        # 父、母、母の父を抽出
        sire_match = re.search(r'父[：:]([^\s]+)', page_text)
        if sire_match:
            horse_info['sire'] = sire_match.group(1).strip()
            logging.debug("Extracted sire: %s" % horse_info['sire'])
        
        dam_match = re.search(r'母[：:]([^\s]+)', page_text)
        if dam_match:
            horse_info['dam'] = dam_match.group(1).strip()
            logging.debug("Extracted dam: %s" % horse_info['dam'])
        
        damsire_match = re.search(r'母の父[：:]([^\s]+)', page_text)
        if damsire_match:
            horse_info['damsire'] = damsire_match.group(1).strip()
            logging.debug("Extracted damsire: %s" % horse_info['damsire'])
        
        # オークション価格（落札価格）を抽出
        price_text = soup.get_text()
        price_match = re.search(r'落札価格[^\d]*([\d,]+)[^\d]*万円', price_text)
        if price_match:
            try:
                horse_info['auction_prize'] = float(price_match.group(1).replace(',', ''))
                logging.debug("Extracted auction price: %s万円" % horse_info['auction_prize'])
            except (ValueError, TypeError) as e:
                logging.warning("Failed to parse auction price: %s" % str(e))
                horse_info['auction_prize'] = 0.0
        else:
            horse_info['auction_prize'] = 0.0
            logging.debug("No auction price found")
            
        # 4. 現在の賞金を抽出
        # パターン1: 総賞金 1,234.5万円 形式
        prize_match = re.search(r'総賞金[^\d]*([\d,.]+)[^\d]*万円', price_text)
        if prize_match:
            try:
                horse_info['current_prize'] = float(prize_match.group(1).replace(',', ''))
                logging.debug(f"Extracted current prize: {horse_info['current_prize']}万円")
            except (ValueError, TypeError) as e:
                logging.warning(f"Failed to parse current prize: {e}")
                horse_info['current_prize'] = 0.0
        else:
            # パターン2: 単純な賞金表記 1,234.5万円 形式
            prize_match = re.search(r'([\d,.]+)[^\d]*万円', price_text)
            if prize_match:
                try:
                    horse_info['current_prize'] = float(prize_match.group(1).replace(',', ''))
                    logging.debug(f"Extracted current prize (alt pattern): {horse_info['current_prize']}万円")
                except (ValueError, TypeError) as e:
                    logging.warning(f"Failed to parse current prize (alt pattern): {e}")
                    horse_info['current_prize'] = 0.0
            else:
                horse_info['current_prize'] = 0.0
                logging.debug("No current prize found")
        
        # 5. オークション日を抽出してYYYY-MM-DD形式に変換
        date_match = re.search(r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日?', html_content)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            horse_info['auction_date'] = f"{year}-{month}-{day}"
            logging.info(f"オークション日を抽出: {horse_info['auction_date']}")
        else:
            logging.warning("オークション日が見つかりませんでした")
        
        # 6. 馬体重を抽出（直接HTMLから抽出を試みる）
        weight = None
        
        # パターン1: 馬体重：416kg 形式
        weight_match = re.search(r'馬体重[：:](\d+)kg', html_content, re.IGNORECASE)
        
        # パターン2: 馬体重は416kg 形式
        if not weight_match:
            weight_match = re.search(r'馬体重[は:](\d+)', html_content, re.IGNORECASE)
            
        # パターン3: 体重：416kg 形式
        if not weight_match:
            weight_match = re.search(r'体重[：:](\d+)kg', html_content, re.IGNORECASE)
            
        # パターン4: 馬体重 416kg 形式（スペース区切り）
        if not weight_match:
            weight_match = re.search(r'馬体重[\s　]+(\d+)\s*(?:kg|キロ|KG)', html_content, re.IGNORECASE)
            
        # パターン5: 馬体重が表形式で記載されている場合
        if not weight_match:
            # テーブル内の「馬体重」を含む行を検索
            for tr in soup.find_all('tr'):
                if '馬体重' in tr.text and 'kg' in tr.text:
                    weight_match = re.search(r'(\d+)\s*kg', tr.text)
                    if weight_match:
                        break
                        
        # パターン6: コメント欄に記載されている場合
        if not weight_match and 'comment' in horse_info:
            weight_match = re.search(r'(?:馬体重|体重)[：: 　]*(\d+)\s*(?:kg|キロ|KG)', horse_info['comment'], re.IGNORECASE)
        
        # パターン7: HTML内のどこかに数値+kgのパターンがある場合
        if not weight_match:
            weight_match = re.search(r'(\d+)\s*kg', html_content, re.IGNORECASE)
        
        if weight_match:
            try:
                weight = int(weight_match.group(1))
                # 馬体重の妥当性チェック（100kg 〜 600kgの範囲）
                if 100 <= weight <= 600:
                    horse_info['weight'] = weight
                    logging.info(f"馬体重を抽出しました: {weight}kg")
                else:
                    logging.warning(f"馬体重の値が不自然です: {weight}kg")
            except (ValueError, IndexError) as e:
                logging.warning(f"馬体重の数値変換に失敗: {e}")
        
        # それでも見つからない場合はhorse_weight_extractorを使用
        if 'weight' not in horse_info or not horse_info['weight']:
            try:
                from horse_weight_extractor import add_horse_weight
                horse_info = add_horse_weight(horse_info, str(soup))
                if 'weight' in horse_info and horse_info['weight']:
                    logging.info(f"horse_weight_extractor から馬体重を抽出: {horse_info['weight']}kg")
            except Exception as e:
                logging.warning(f"馬体重抽出中にエラーが発生: {e}")
        
        # 繁殖牝馬かどうかをチェック
        is_broodmare = '繁殖牝馬' in html_content or (horse_info.get('sex') == '牝' and '繁殖' in html_content)
        
        # 最終的に馬体重が見つからなかった場合
        if 'weight' not in horse_info or not horse_info['weight']:
            # 繁殖牝馬の場合は'-'を設定
            if is_broodmare:
                horse_info['weight'] = '-'
                logging.info(f"繁殖牝馬のため、馬体重を'-'に設定しました")
            else:
                # デバッグ用にHTMLを保存
                debug_file = f"debug_weight_not_found_{os.path.basename(detail_file)}"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(html_content)
                logging.warning(f"馬体重が見つかりませんでした。デバッグ用にHTMLを保存: {debug_file}")
                # デフォルト値は設定しない（Noneのまま）
        
        # 7. 戦績情報を抽出（本番環境と同じロジック）
        # まず繁殖牝馬かどうかをチェック
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
        if title_match:
            title = title_match.group(1)
            if '繁殖牝馬' in title or '※繁殖牝馬' in title or '空胎' in title:
                horse_info['race_record'] = '繁殖牝馬'
                logging.info(f"繁殖牝馬を検出しました: {title}")
                return horse_info
        
        # 繁殖牝馬でない場合は通常の戦績情報を抽出
        race_record = None
        
        # パターン1: 通算成績：3戦0勝［0-0-0-3］形式
        record_match = re.search(r'通算成績[：:]*\s*([^\n\[\]\s]+(?:\s*[^\n\[\]]+)*?)(?:\s*\[([^\]]+)\])?', html_content)
        if record_match:
            race_record = record_match.group(1).strip()
            if record_match.group(2):
                race_record += f" [{record_match.group(2).strip()}]"
            # 余分な改行や空白を削除
            race_record = ' '.join(race_record.split())
            logging.info(f"戦績を抽出しました: {race_record}")
        else:
            # パターン2: 表形式の場合
            for tr in soup.find_all('tr'):
                if '通算成績' in tr.text:
                    record_text = tr.get_text()
                    record_match = re.search(r'通算成績[：:]*\s*([^\n\[\]\s]+(?:\s*[^\n\[\]]+)*?)(?:\s*\[([^\]]+)\])?', record_text)
                    if record_match:
                        race_record = record_match.group(1).strip()
                        if record_match.group(2):
                            race_record += f" [{record_match.group(2).strip()}]"
                        # 余分な改行や空白を削除
                        race_record = ' '.join(race_record.split())
                        logging.info(f"表形式から戦績を抽出: {race_record}")
                        break
            
            # パターン3: コメント欄を確認
            if not race_record and 'comment' in horse_info:
                comment = horse_info['comment']
                record_match = re.search(r'通算成績[：:]*\s*([^\n\[\]\s]+(?:\s*[^\n\[\]]+)*?)(?:\s*\[([^\]]+)\])?', comment)
                if record_match:
                    race_record = record_match.group(1).strip()
                    if record_match.group(2):
                        race_record += f" [{record_match.group(2).strip()}]"
                    # 余分な改行や空白を削除
                    race_record = ' '.join(race_record.split())
                    logging.info(f"コメント欄から戦績を抽出: {race_record}")
        
        # 戦績が見つかった場合にのみ設定
        if race_record:
            horse_info['race_record'] = race_record
        else:
            logging.warning("戦績情報が見つかりませんでした")

        # 8. 賞金情報を抽出（改良版）
        def extract_prize(text):
            # パターン1: 総賞金 1,234.5万円 形式（全角スペース・半角スペース対応）
            patterns = [
                r'総賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万円',  # 総賞金：1,234.5万円
                r'総賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万',    # 総賞金：1,234.5万
                r'総賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)',                   # 総賞金：1,234.5
                r'賞金[\s\u3000]*[：:][\s\u3000]*([\d,.]+)[\s\u3000]*万円',    # 賞金：1,234.5万円
                r'([\d,]+(?:\.[\d,]+)?)[\s\u3000]*万円',                         # 1,234.5万円
                r'([\d,]+(?:\.[\d,]+)?)[\s\u3000]*万',                           # 1,234.5万
                r'([\d,]+(?:\.[\d,]+)?)[\s\u3000]*円',                           # 1,234.5円（万単位に変換）
                r'([\d,]+(?:\.[\d,]+)?)'                                          # 1,234.5
            ]
            
            for pattern in patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        prize = float(match.group(1).replace(',', ''))
                        # 円単位の場合は万円に変換
                        if '円' in pattern and '万円' not in pattern:
                            prize = prize / 10000
                        logging.info(f"賞金情報を抽出: {prize}万円 (パターン: {pattern})")
                        return prize
                    except (ValueError, TypeError) as e:
                        logging.warning(f"賞金のパースエラー: {e}, パターン: {pattern}")
                        continue
            
            logging.warning("賞金情報が見つかりませんでした")
            return None

        try:
            # 賞金情報の抽出を実行
            prize = extract_prize(html_content)
            if prize is not None:
                horse_info['total_prize_start'] = prize
                horse_info['total_prize_latest'] = prize  # 初期値は同じ値で設定

            # 落札価格を抽出
            logger.info("Extracting sold price from %s" % detail_file)
            # デバッグ用にHTMLの一部をログに出力
            logger.debug("HTML content sample (first 500 chars): %s..." % html_content[:500])
            
            sold_price = extract_sold_price(html_content)
            
            if sold_price is not None:
                if isinstance(sold_price, str):
                    logger.info(f"主取りを検出: {sold_price}")
                else:
                    logger.info(f"落札価格を抽出: {sold_price}円")
                
                # 主取りの場合は文字列のまま、それ以外は数値として格納
                horse_info['sold_price'] = sold_price
            else:
                logger.warning(f"Could not extract sold price from {detail_file}")
                horse_info['sold_price'] = None
                
        except Exception as e:
            logger.error(f"Error processing horse info: {str(e)}", exc_info=True)
            if 'sold_price' not in horse_info:
                horse_info['sold_price'] = None
    
        # デバッグ用のHTML保存はパフォーマンス向上のため削除
        
        # コメントを抽出
        try:
            comment_text = ""
            comment_match = re.search(r'コメント[\s\n]*(.*?)(?=\n\s*[\u30A1-\u30FF]{2,}|$)', html_content, re.DOTALL)
            if comment_match:
                comment_text = comment_match.group(1).strip()
                horse_info['comment'] = comment_text
        except Exception as e:
            logger.error(f"Error extracting comment: {str(e)}", exc_info=True)
    
        # 疾病情報を検索
        try:
            health_issues = []
            for keyword in health_keywords:
                if keyword in html_content or (comment_text and keyword in comment_text):
                    # 前後50文字を取得
                    for match in re.finditer(re.escape(keyword), html_content):
                        start = max(0, match.start() - 50)
                        end = min(len(html_content), match.end() + 50)
                        context = html_content[start:end].strip()
                        if context and len(context) > 10:  # 短いテキストは無視
                            health_issues.append(context)
        
            if health_issues:
                horse_info['health_issues'] = list(set(health_issues))  # 重複を削除
        except Exception as e:
            logger.error(f"Error searching health issues: {str(e)}", exc_info=True)
    
        # 10. 画像URLを抽出（本番環境と同じロジック）
        try:
            img_sources = []
            for img in soup.find_all('img', src=True):
                src = img['src'].strip()
                if src and ('horse' in src.lower() or 'photo' in src.lower() or 'image' in src.lower()):
                    if not src.startswith(('http://', 'https://')):
                        # 相対URLを絶対URLに変換
                        base_url = 'https://www.rakuten.co.jp/'
                        src = urljoin(base_url, src)
                    img_sources.append(src)
        
            if img_sources:
                horse_info['image_url'] = img_sources[0]  # 最初の画像をメイン画像として使用
        except Exception as e:
            logger.error(f"Error extracting image URL: {str(e)}", exc_info=True)
    
        # 11. JBISリンクを抽出（本番環境と同じロジック）
        try:
            jbis_links = set()
            for a in soup.find_all('a', href=True):
                href = a['href'].strip()
                if 'jbis.or.jp' in href and 'horse' in href:
                    # URLを正規化
                    if not href.startswith(('http://', 'https://')):
                        href = 'https:' + href if href.startswith('//') else 'https://www.jbis.or.jp' + (href if href.startswith('/') else '/' + href)
                    jbis_links.add(href)
            
            if jbis_links:
                horse_info['jbis_links'] = list(jbis_links)
        except Exception as e:
            logger.error(f"Error extracting JBIS link: {str(e)}", exc_info=True)
            
        # 12. その他のメタデータ
        try:
            horse_info['extracted_at'] = datetime.now().isoformat()
            horse_info['data_source'] = 'rakuten_auction'
        except Exception as e:
            logger.error(f"Error setting metadata: {str(e)}", exc_info=True)
        
    logging.info(f"Extracted info for horse: {horse_info.get('name', 'unknown')}")
    return horse_info

def process_single_file(detail_file):
    """1つのファイルを処理するヘルパー関数"""
    try:
        return extract_horse_info(detail_file)
    except Exception as e:
        logging.error(f"Error processing {detail_file}: {str(e)}")
        return None

def main():
    import argparse
    from concurrent.futures import ThreadPoolExecutor, as_completed
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='馬の詳細情報を抽出するスクリプト')
    parser.add_argument('--input-dir', '-i', default=None,
                      help='処理するHTMLファイルが含まれるディレクトリを指定')
    parser.add_argument('--output', '-o', default=None,
                      help='出力先のJSONファイルパスを指定（指定がない場合は入力ディレクトリに保存）')
    parser.add_argument('--pattern', '-p', default='sess_*.html',
                      help='処理するファイルのパターン（デフォルト: sess_*.html）')
    parser.add_argument('--stdout', action='store_true',
                      help='結果を標準出力に表示')
    parser.add_argument('--workers', '-w', type=int, default=4,
                      help='並列処理のワーカー数（デフォルト: 4）')
    parser.add_argument('--log-level', '-l', default='INFO',
                      choices=['DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'],
                      help='ログレベルを設定（デフォルト: INFO）')
    args = parser.parse_args()
    
    # 入力ディレクトリの決定
    details_dir = None
    if args.input_dir:
        details_dir = os.path.abspath(args.input_dir)
    else:
        # デフォルトのキャッシュディレクトリを使用
        cache_base = '/Users/yum.ishii/SaraokuDB/cache'
        if not os.path.exists(cache_base):
            logging.error(f"キャッシュディレクトリが見つかりません: {cache_base}")
            return
            
        cache_dirs = sorted([d for d in os.listdir(cache_base) 
                           if os.path.isdir(os.path.join(cache_base, d))])
        
        if not cache_dirs:
            logging.error("キャッシュディレクトリが見つかりません")
            return
        
        latest_cache = os.path.join(cache_base, cache_dirs[-1])
        details_dir = os.path.join(latest_cache, 'details')
    
    # ファイル一覧を取得
    detail_files = glob.glob(os.path.join(details_dir, args.pattern))
    
    # ディレクトリの存在確認
    if not detail_files:
        logging.error(f'HTMLファイルが見つかりません: {details_dir}')
        return

    # ログレベルの設定
    logging.getLogger().setLevel(getattr(logging, args.log_level))
    
    # ファイル処理の並列実行
    logging.info(f'Found {len(detail_files)} HTML files to process with {args.workers} workers')
    
    horses = []
    processed = 0
    total_files = len(detail_files)
    
    with ThreadPoolExecutor(max_workers=args.workers) as executor:
        # 全ファイルの処理をスケジューリング
        future_to_file = {executor.submit(process_single_file, file): file for file in detail_files}
        
        # 完了したタスクから順に処理
        for future in as_completed(future_to_file):
            file = future_to_file[future]
            try:
                horse_info = future.result()
                if horse_info:
                    horses.append(horse_info)
                processed += 1
                if processed % 10 == 0 or processed == total_files:
                    logging.info(f'Processed {processed}/{total_files} files ({processed/total_files*100:.1f}%)')
            except Exception as e:
                logging.error(f'Error processing {file}: {str(e)}')

    # Output results
    json_output = json.dumps(horses, ensure_ascii=False, indent=2, sort_keys=True)

    if args.stdout:
        # Output to stdout
        print(json_output)
        logging.info(f'Processed {len(horses)} horses and output to stdout')
    else:
        # Save to file
        try:
            with open(args.output, 'w', encoding='utf-8', errors='replace') as f:
                f.write(json_output)
            logging.info(f'Processed {len(horses)} horses and saved to {args.output}')
        except Exception as e:
            logging.error(f'Failed to save {args.output}: {str(e)}')
            # Fallback saving method
            try:
                import codecs
                with codecs.open(args.output, 'w', encoding='utf-8', errors='replace') as f:
                    f.write(json_output)
                logging.info(f'Saved using alternative method to {args.output}')
            except Exception as e2:
                logging.error(f'Alternative save method also failed: {str(e2)}')
                # As a last resort, print to stderr
                print(json_output, file=sys.stderr)
                logging.info('JSON data has been printed to stderr as a fallback')
            return

if __name__ == "__main__":
    main()
