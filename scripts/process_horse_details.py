#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import glob
import logging
from datetime import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from bs4.dammit import EncodingDetector

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルでログを出力
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('process_horse_details.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

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
                
            # HTMLをパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
        except Exception as e:
            logging.error(f"Error reading file {detail_file}: {str(e)}")
            return None
        
        # 基本情報を格納する辞書
        horse_info = {
            'source_file': os.path.basename(detail_file),
            'extracted_at': datetime.now().isoformat(),
            'auction_price': 0.0  # デフォルト値
        }

        # 1. 馬名を抽出
        name = None
        title = soup.title.string if soup.title else ''
        
        # デバッグ用にHTMLの最初の200文字をログに出力
        html_content = str(soup)[:200]
        logging.debug(f"Processing file: {detail_file}")
        logging.debug(f"Title: {title}")
        logging.debug(f"First 200 chars of HTML: {html_content}...")
        
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
        
        # 6. 馬体重を抽出（本番環境と同じロジック）
        weight = 0.0
        try:
            # まずは明示的な体重表記を検索
            weight_matches = re.findall(r'馬体重\s*[：:]*\s*([\d.]+)[\s㎏kg]?', html_content, re.IGNORECASE)
            if weight_matches:
                weight = float(weight_matches[-1].replace(',', ''))
            
            # 戦績欄からも検索
            if weight == 0 and 'race_record' in horse_info:
                weight_matches = re.findall(r'([\d.]+)㎏', horse_info['race_record'])
                if weight_matches:
                    weight = float(weight_matches[-1])
            
            if 200 <= weight <= 600:  # 妥当な範囲のみ保存
                horse_info['weight'] = weight
        except (ValueError, TypeError):
            pass
        
        # 7. 戦績情報を抽出（本番環境と同じロジック）
        record_match = re.search(r'通算成績[：:]*\s*([^\n\[\]]+)(?:\[([^\]]+)\])?', html_content)
        if record_match:
            race_record = record_match.group(1).strip()
            if record_match.group(2):
                race_record += f" [{record_match.group(2).strip()}]"
            horse_info['race_record'] = race_record
        
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
    # 最新のキャッシュディレクトリを取得
    cache_base = '/Users/yum.ishii/SaraokuDB/cache'
    cache_dirs = sorted([d for d in os.listdir(cache_base) if os.path.isdir(os.path.join(cache_base, d))])
    
    if not cache_dirs:
        logging.error("No cache directories found")
        return
    
    latest_cache = os.path.join(cache_base, cache_dirs[-1])
    details_dir = os.path.join(latest_cache, 'details')
    
    if not os.path.exists(details_dir):
        logging.error(f"Details directory not found: {details_dir}")
        return
    
    # 詳細ページのHTMLファイルを取得（sess_*_item_*.html パターンに一致するファイル）
    detail_files = glob.glob(os.path.join(details_dir, 'sess_*_item_*.html'))
    
    if not detail_files:
        logging.error(f"No detail files found in {details_dir}")
        return
    
    logging.info(f"Found {len(detail_files)} detail files to process")
    
    # 馬情報を抽出
    horses = []
    for detail_file in detail_files:
        horse_info = extract_horse_info(detail_file)
        if horse_info:
            horses.append(horse_info)
    
    # 結果を保存（エンコーディングを明示的に指定）
    output_file = os.path.join(latest_cache, 'processed_horses.json')
    try:
        with open(output_file, 'w', encoding='utf-8', errors='replace') as f:
            json.dump(horses, f, ensure_ascii=False, indent=2, sort_keys=True)
    except Exception as e:
        logging.error(f"Failed to save {output_file}: {str(e)}")
        # エラーが発生した場合の代替保存方法
        try:
            import codecs
            with codecs.open(output_file, 'w', encoding='utf-8', errors='replace') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2, sort_keys=True)
        except Exception as e2:
            logging.error(f"Alternative save also failed: {str(e2)}")
            return
    
    logging.info(f"Processed {len(horses)} horses and saved to {output_file}")

if __name__ == "__main__":
    main()
