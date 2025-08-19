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

# カスタムモジュールのインポート
from extract_race_record import extract_race_record

# スクリプトのディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルでログを出力
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_horse_details.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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
                logging.info(f"JBISにリクエストを送信中... (試行 {attempt + 1}/{max_retries})")
                response = requests.get(jbis_url, headers=headers, timeout=30)
                response.encoding = 'utf-8'  # エンコーディングをUTF-8に設定
                
                # ステータスコードを確認
                if response.status_code != 200:
                    logging.warning(f"ステータスコード {response.status_code} が返されました")
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
                                logging.info(f"方法1で総賞金を取得: {total_prize}万円")
                                return total_prize
                
                # 方法2: すべてのdt要素から総賞金を検索
                for dt in soup.find_all('dt'):
                    if dt.get_text(strip=True) == '総賞金':
                        dd = dt.find_next_sibling('dd')
                        if dd:
                            prize_text = dd.get_text(strip=True)
                            total_prize = parse_prize_text(prize_text)
                            if total_prize > 0 or prize_text.strip() == '0.0':
                                logging.info(f"方法2で総賞金を取得: {total_prize}万円")
                                return total_prize
                
                # 方法3: 正規表現で直接検索（フォールバック）
                prize_patterns = [
                    r'総賞金[^\d>]*([\d,]+(?:\.[\d,]+)?)',
                    r'総賞金[^<]*?<dd[^>]*>([^<]+)',
                    r'<dt[^>]*>\s*総賞金\s*</dt>\s*<dd[^>]*>([^<]+)'
                ]
                
                weight_patterns = [
                    # 基本的なパターン
                    r'馬体重[：:](?:\s*)(\d+)kg',  # 「馬体重：416kg」
                    r'馬体重[は](?:\s*)(\d+)kg',    # 「馬体重は416kg」
                    r'体重[：:](?:\s*)(\d+)kg',     # 「体重：416kg」
                    r'馬体重(?:\s*)(\d+)kg',        # 「馬体重 416kg」
                    
                    # テーブル関連のパターン
                    r'馬体重.*?<td[^>]*>(\d+)kg</td>',  # テーブル内の馬体重
                    r'<td[^>]*>馬体重</td>\s*<td[^>]*>(\d+)kg</td>',  # テーブルの行
                    r'<th[^>]*>馬体重</th>\s*<td[^>]*>(\d+)kg</td>',  # テーブルヘッダー付き
                    r'<td[^>]*>.*?馬体重.*?</td>\s*<td[^>]*>(\d+)kg</td>',  # テーブルセル内の複雑なパターン
                    r'<tr[^>]*>\s*<[^>]*>馬体重</[^>]*>\s*<[^>]*>(\d+)kg</[^>]*>',  # テーブル行内の複雑なパターン
                    
                    # div/spanタグ関連のパターン
                    r'<div[^>]*>馬体重</div>\s*<div[^>]*>(\d+)kg</div>',  # divタグ内の馬体重
                    r'<span[^>]*>馬体重</span>\s*<span[^>]*>(\d+)kg</span>',  # spanタグ内の馬体重
                    r'<div[^>]*>.*?馬体重.*?<div[^>]*>(\d+)kg</div>',  # 入れ子のdivタグ
                    r'<div[^>]*class=["\']horseInfo["\'][^>]*>.*?馬体重.*?<div[^>]*>(\d+)kg</div>',  # horseInfoクラス内の馬体重
                    
                    # 定義リスト関連のパターン
                    r'<dt[^>]*>馬体重</dt>\s*<dd[^>]*>(\d+)kg</dd>',  # 定義リスト形式
                    r'<dt[^>]*>.*?馬体重.*?</dt>\s*<dd[^>]*>(\d+)kg</dd>',  # 定義リスト（複雑）
                    
                    # その他の一般的なパターン
                    r'馬体重.*?<strong[^>]*>(\d+)kg</strong>',  # 太字タグ内の馬体重
                    r'<strong[^>]*>馬体重</strong>.*?(\d+)kg',  # 太字タグの後の馬体重
                    
                    # カスタムクラスやIDを含むパターン
                    r'<div[^>]*class=["\']horse-data["\'][^>]*>.*?馬体重.*?(\d+)kg',  # horse-dataクラス内の馬体重
                    r'<div[^>]*id=["\']horseDetail["\'][^>]*>.*?馬体重.*?(\d+)kg',  # horseDetail ID内の馬体重
                    
                    # 記述文内の体重表記（例：「480kg台でレースに出走していた」）
                    r'(\d{3})kg(?:台|代|前後|程度|くらい|ほど|程|前|後|強|弱|半|超|未満|以上|以下)',
                    r'(?:約|およそ|約|概ね|おおよそ|大体|約)(\d{3})kg',
                    r'(?:体重|馬体重|レース時体重|出走時体重|現役時体重)[はが]?(?:約|およそ|約|概ね|おおよそ|大体|約)?(\d{3})kg',
                    
                    # 緩やかなマッチングパターン（最終手段）
                    r'(?:馬体重|体重)[^\d]*(\d{3})\s*kg',  # 馬体重の後に数値が続くパターン
                    r'<[^>]*>(?:馬体重|体重)[^<]*(\d{3})\s*kg',  # タグ内の馬体重（数値3桁）
                    r'馬体重.*?(\d+)\s*kg',  # 緩やかなマッチング
                    r'<[^>]*馬体重[^>]*>.*?(\d+)\s*kg',  # タグ内の馬体重（緩やか）
                    r'<[^>]*>\s*馬体重[^<]*(\d+)\s*kg',  # タグ内のテキスト（緩やか）
                    r'(?:<[^>]+>)*\s*馬体重[^<]*(?:<[^>]+>)*\s*(\d+)\s*kg',  # タグが混在する場合
                    r'(?:<[^>]+>)*\s*(?:馬体重|体重)[^<]*(?:<[^>]+>)*\s*(\d+)\s*kg',  # 最も緩やかなマッチング
                    r'(?:<[^>]+>)*\s*(?:馬体重|体重)[^<]*?(\d{3})\s*kg',  # 数値3桁にマッチ
                    r'(?:<[^>]+>)*\s*(?:馬体重|体重).*?(\d{3})\s*kg',  # 最も緩やかなマッチング（数値3桁）
                    
                    # 記述文内の数値のみのパターン（最終手段）
                    r'(\d{3})kg(?!.*\d{3}kg)',  # 最後に現れる3桁の数値+kg
                    r'(?<!\d)(\d{3})\s*kg(?!.*\d{3}\s*kg)'  # 最後に現れる3桁の数値 + スペース + kg
                ]
                
                for pattern in prize_patterns:
                    matches = re.search(pattern, response.text, re.DOTALL)
                    if matches:
                        prize_text = matches.group(1).strip()
                        total_prize = parse_prize_text(prize_text)
                        if total_prize > 0 or prize_text.strip() == '0.0':
                            logging.info(f"方法3で総賞金を取得: {total_prize}万円")
                            return total_prize
                
                # 見つからなかった場合は0.0を返す
                logging.info("総賞金情報が見つかりませんでした")
                return 0.0
                
            except requests.exceptions.RequestException as e:
                if attempt == max_retries - 1:
                    raise
                logging.warning(f"リクエストエラー: {str(e)}。{retry_delay}秒後に再試行します...")
                time.sleep(retry_delay)
                
    except Exception as e:
        logging.error(f"賞金情報の取得中にエラーが発生: {str(e)}")
        return 0.0

def extract_horse_info(detail_file):
    """詳細ページのHTMLから馬情報を抽出する"""
    logging.info(f"Processing detail file: {detail_file}")
    
    try:
        # ファイルをバイナリモードで読み込み、エンコーディングを自動検出
        try:
            with open(detail_file, 'rb') as f:
                raw_content = f.read()
                
            file_size = len(raw_content)
            logging.debug(f"Processing file: {detail_file} (Size: {file_size} bytes)")
            
            if file_size == 0:
                logging.error(f"File is empty: {detail_file}")
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
                logging.error(f"Failed to decode file with any encoding: {detail_file}")
                return None
                
            # 戦績情報を抽出
            race_record = extract_race_record(html_content)
            
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
        except Exception as e:
            logging.error(f"Error reading file {detail_file}: {str(e)}")
            return None
        
        # 基本情報を格納する辞書
        horse_info = {
            'source_file': os.path.basename(detail_file),
            'extracted_at': datetime.now().isoformat(),
            'auction_price': 0.0,  # デフォルト値
            'total_prize': 0.0     # 総賞金のデフォルト値
        }

        # 1. 馬名を抽出
        name = None
        title = soup.title.string if soup.title else ''
        
        # デバッグ用にHTMLの最初の200文字をログに出力
        html_content = str(soup)[:200]
        logging.debug(f"Processing file: {detail_file}")
        logging.debug(f"Title: {title}")
        logging.debug(f"First 200 chars of HTML: {html_content}...")
        
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
                    jbis_url = f"https:{jbis_url}" if jbis_url.startswith('//') else f"https://www.jbis.or.jp{jbis_url if jbis_url.startswith('/') else '/' + jbis_url}"
                break
                
        # デバッグ用にHTMLを保存
        if not jbis_url:
            debug_file = f"debug_jbis_not_found_{os.path.basename(detail_file)}"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logging.warning(f"JBIS URLが見つかりませんでした。デバッグ用にHTMLを保存: {debug_file}")
        else:
            logging.info(f"JBIS URLを発見: {jbis_url}")
                
        # JBIS URLから賞金情報を取得
        if jbis_url:
            logging.info(f"JBIS URLを発見: {jbis_url}")
            try:
                horse_info['total_prize'] = extract_prize_from_jbis(jbis_url)
                logging.info(f"賞金情報を取得しました: {horse_info['total_prize']}万円")
            except Exception as e:
                logging.error(f"賞金情報の取得中にエラーが発生: {str(e)}")
        else:
            logging.warning("JBIS URLが見つかりませんでした")
        
        if title:
            # タイトルから「 | サラブレッドオークション」の前の部分を抽出
            name = title.split('|')[0].strip()
            
            # デバッグ用に抽出前の名前をログに出力
            logging.debug(f"Name before processing: {name}")
            
            # 馬名から性別、年齢、コメントなどを削除
            name = re.sub(r'\s*[牡牝セ]\s*\d+\s*[歳年].*$', '', name).strip()
            # 「セン２歳 ※地方競馬 在籍」のようなテキストを削除
            name = re.sub(r'\s*セ[ンン]\s*\d+\s*[歳年].*$', '', name).strip()
            # 余分なスペースを削除
            name = ' '.join(name.split())
            
            # デバッグ用に処理後の名前をログに出力
            logging.debug(f"Name after processing: {name}")
        
        if not name:
            logging.warning(f"Could not find horse name in {detail_file}")
            return None
        
        horse_info['name'] = name
        
        # 2. 性別と年齢を抽出
        # 性別は「牡」「牝」「セ」のいずれか
        # パターン1: 「性別 数字歳」の形式（例: 牡 3歳）
        sex_match = re.search(r'([牡牝セ])\s*\d+\s*[歳年]', title or '')
        
        # パターン2: 「センナンサイ」の形式（例: セン2歳）
        if not sex_match:
            sex_match = re.search(r'([セ]ン\s*\d+\s*[歳年])', title or '')
            if sex_match:
                horse_info['sex'] = 'セ'  # セに正規化
                logging.debug(f"Extracted sex (pattern 2): {horse_info['sex']}")
        
        # パターン3: 単純に「性別」のみ
        if not sex_match:
            sex_match = re.search(r'([牡牝セ])', title or '')
            if sex_match:
                horse_info['sex'] = sex_match.group(1)
                logging.debug(f"Extracted sex (fallback): {horse_info['sex']}")
        
        if not sex_match:
            logging.warning(f"Could not extract sex from title: {title}")
        elif 'sex' not in horse_info:  # パターン1でマッチした場合
            horse_info['sex'] = sex_match.group(1)
            logging.debug(f"Extracted sex: {horse_info['sex']}")
        
        # 年齢を抽出
        age_match = re.search(r'(\d+)\s*[歳年]', title or '')
        if age_match:
            try:
                horse_info['age'] = int(age_match.group(1))
            except (ValueError, IndexError):
                pass
        
        # 3. 血統情報を抽出
        # ページ全体のテキストを取得
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
                
        # 3. オークション価格を抽出
        price_text = soup.get_text()
        
        # オークション価格（落札価格）を抽出
        price_match = re.search(r'落札価格[^\d]*([\d,]+)[^\d]*万円', price_text)
        if price_match:
            try:
                horse_info['auction_prize'] = float(price_match.group(1).replace(',', ''))
                logging.debug(f"Extracted auction price: {horse_info['auction_prize']}万円")
            except (ValueError, TypeError) as e:
                logging.warning(f"Failed to parse auction price: {e}")
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
        date_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', html_content)
        if date_match:
            year = date_match.group(1)
            month = date_match.group(2).zfill(2)
            day = date_match.group(3).zfill(2)
            horse_info['auction_date'] = f"{year}-{month}-{day}"
        
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
            # デバッグ用にHTMLを保存
            debug_file = f"debug_record_not_found_{os.path.basename(detail_file)}"
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
                logging.warning(f"戦績情報が見つかりませんでした。デバッグ用にHTMLを保存: {debug_file}")
        
        # 8. 賞金情報を抽出（本番環境と同じロジック）
        def extract_prize(text):
            prize = 0.0
            # パターン1: 総賞金 1,234.5万円 形式
            match = re.search(r'総賞金\s*[：:]*\s*([\d,.]+)\s*万円', text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            # パターン2: 1,234.5万円 形式
            match = re.search(r'([\d,.]+)\s*万円', text)
            if match:
                try:
                    return float(match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            return prize
        
        horse_info['auction_prize'] = extract_prize(html_content)
        horse_info['current_prize'] = extract_prize(html_content)
        
        # 9. 疾病情報を抽出（本番環境と同じロジック）
        health_issues = []
        health_keywords = ['疾病', '怪我', '治療', '異常', '手術', '骨折', '屈腱炎', '跛行', '喘鳴']
        
        # コメント欄からも検索
        comment_text = ''
        comment_match = re.search(r'コメント[\s\n]*(.*?)(?=\n\s*[\u30A1-\u30FF]{2,}|$)', html_content, re.DOTALL)
        if comment_match:
            comment_text = comment_match.group(1).strip()
            horse_info['comment'] = comment_text
        
        # 疾病情報を検索
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
        
        # 10. 画像URLを抽出（本番環境と同じロジック）
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
        
        # 11. JBISリンクを抽出（本番環境と同じロジック）
        jbis_links = set()
        for a in soup.find_all('a', href=True):
            href = a['href'].strip()
            if 'jbis.or.jp' in href and 'horse' in href:
                # URLを正規化
                if not href.startswith(('http://', 'https://')):
                    href = 'https:' + href if href.startswith('//') else 'https://www.jbis.or.jp' + href
                jbis_links.add(href)
        
        if jbis_links:
            horse_info['jbis_links'] = list(jbis_links)
        
        # 12. その他のメタデータ
        horse_info['extracted_at'] = datetime.now().isoformat()
        horse_info['data_source'] = 'rakuten_auction'
        
        logging.info(f"Extracted info for horse: {name}")
        return horse_info
        
    except Exception as e:
        logging.error(f"Error processing {detail_file}: {str(e)}", exc_info=True)
        return None

def main():
    import argparse
    
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

    # Process each file
    logging.info(f'Found {len(detail_files)} HTML files to process')

    # Extract horse info
    horses = []
    for detail_file in detail_files:
        horse_info = extract_horse_info(detail_file)
        if horse_info:
            horses.append(horse_info)

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
