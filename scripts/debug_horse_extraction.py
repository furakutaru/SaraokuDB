#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import re
import json
import logging
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, Any, Optional, List
from datetime import datetime

# 定数定義
CACHE_DIR = Path(__file__).parent.parent / 'cache'  # プロダクションキャッシュディレクトリを指すように変更
PROJECT_ROOT = Path(__file__).parent.parent

# 最新のキャッシュディレクトリを取得
def get_latest_cache_dir() -> Path:
    """最新のキャッシュディレクトリを取得"""
    cache_dirs = sorted(CACHE_DIR.glob('20*'))  # 20で始まるディレクトリ（タイムスタンプ）
    if not cache_dirs:
        raise FileNotFoundError(f"キャッシュディレクトリが見つかりません: {CACHE_DIR}")
    return cache_dirs[-1]  # 最新のディレクトリ

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_extraction.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DebugHorseExtractor:
    def __init__(self, cache_dir=None):
        self.cache_dir = Path(cache_dir) if cache_dir else get_latest_cache_dir()
        
    def _extract_horse_info_from_row(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """馬の行から馬の情報を抽出する（本番スクリプトと同様のロジック）"""
        horse_info = {}
        try:
            # 馬名の抽出
            name_elem = soup.select_one('div.auctionTableCard__name a.auctionTableCard__name--link')
            if name_elem and name_elem.text.strip():
                horse_info['name'] = name_elem.text.strip()
                
            # 性別と年齢の抽出
            sex_age_elem = soup.select_one('div.auctionTableCard__info')
            if sex_age_elem:
                sex_age_text = sex_age_elem.get_text(strip=True)
                # 性別を抽出（牡・牝・せん）
                if '牡' in sex_age_text:
                    horse_info['sex'] = '牡'
                elif '牝' in sex_age_text:
                    horse_info['sex'] = '牝'
                elif 'せん' in sex_age_text:
                    horse_info['sex'] = 'せん'
                # 年齢を抽出（数字+才）
                age_match = re.search(r'(\d+)才', sex_age_text)
                if age_match:
                    try:
                        horse_info['age'] = int(age_match.group(1))
                    except (ValueError, IndexError):
                        pass
            
            # 販売者情報の抽出
            seller_elem = soup.select_one('div.auctionTableCard__seller')
            if seller_elem:
                seller_text = seller_elem.get_text(strip=True)
                # 販売申込者のテキストを削除
                if '販売申込者' in seller_text:
                    seller_text = seller_text.replace('販売申込者', '').strip()
                if seller_text:
                    horse_info['seller'] = seller_text
            
            # 賞金情報の抽出
            prize_elem = soup.select_one('div.auctionTableCard__prize')
            if prize_elem:
                prize_text = prize_elem.get_text(strip=True)
                if prize_text and '億' in prize_text:
                    try:
                        # 例: "1億5000万円" から 150000000 を抽出
                        if '億' in prize_text and '万' in prize_text:
                            billion = int(re.search(r'(\d+)億', prize_text).group(1))
                            million = int(re.search(r'(\d+)万', prize_text).group(1))
                            horse_info['total_prize'] = billion * 100000000 + million * 10000
                        elif '億' in prize_text:
                            billion = int(re.search(r'(\d+)億', prize_text).group(1))
                            horse_info['total_prize'] = billion * 100000000
                        elif '万' in prize_text:
                            million = int(re.search(r'(\d+)万', prize_text).group(1))
                            horse_info['total_prize'] = million * 10000
                    except (ValueError, AttributeError):
                        logger.warning(f"賞金のパースに失敗しました: {prize_text}")
            
            # スクレイプ日時を記録
            horse_info['scraped_at'] = datetime.now().isoformat()
            
            logger.debug(f"抽出した馬情報: {horse_info}")
            return horse_info
            
        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました: {e}")
            logger.error(f"エラーが発生した行のHTML: {soup}")
            return {}
    
    def _extract_auction_date(self, soup: BeautifulSoup) -> str:
        """
        オークション開催日を抽出する
        
        Returns:
            str: YYYY-MM-DD形式の日付文字列
        """
        try:
            # 1. 開始時間から日付を取得
            start_time_label = soup.find('span', class_='subData__label', string=lambda text: text and '開始時間' in text)
            if start_time_label:
                value_elem = start_time_label.find_next_sibling('span', class_='subData__value')
                if value_elem:
                    date_text = value_elem.get_text(strip=True)
                    match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', date_text)
                    if match:
                        year, month, day = match.groups()
                        return f"{year}-{int(month):02d}-{int(day):02d}"
            
            # 2. その他の日付表記を検索
            date_patterns = [
                r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日?',
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                r'(\d{2})/(\d{1,2})/(\d{1,2})'  # YY/MM/DD or MM/DD/YY
            ]
            
            for pattern in date_patterns:
                match = re.search(pattern, soup.get_text())
                if match:
                    if len(match.groups()) == 3:
                        year, month, day = match.groups()
                        # 年が2桁の場合は2000年代と仮定
                        if len(year) == 2:
                            year = f"20{year}"
                        return f"{year}-{int(month):02d}-{int(day):02d}"
            
            # 3. ファイル名から日付を抽出
            for script in soup.find_all('script', {'src': True}):
                src = script['src']
                date_match = re.search(r'(\d{4})(\d{2})(\d{2})', src)
                if date_match:
                    year, month, day = date_match.groups()
                    return f"{year}-{month}-{day}"
            
            logger.warning("オークション日をページから取得できませんでした。現在日付を使用します。")
            return datetime.now().strftime("%Y-%m-%d")
            
        except Exception as e:
            logger.error(f"開催日の取得に失敗: {e}")
            return datetime.now().strftime("%Y-%m-%d")
            
    def _extract_horse_detail_info(self, soup: BeautifulSoup) -> Dict[str, Any]:
        """馬の詳細情報を抽出する（本番スクリプトと同様のロジック）"""
        detail_info = {}
        try:
            # ページ全体のテキストを取得
            page_text = soup.get_text(separator=' ', strip=True)
            
            # オークション開催日の抽出
            auction_date = self._extract_auction_date(soup)
            if auction_date:
                detail_info['auction_date'] = auction_date
            
            # 血統情報の抽出
            detail_info.update(self._extract_pedigree(soup))
            
            # 馬体重の抽出
            weight_match = re.search(r'馬体重\s*[:：]?\s*(\d+)', page_text)
            if weight_match:
                try:
                    detail_info['weight'] = int(weight_match.group(1))
                except (ValueError, IndexError):
                    pass
            
            # 落札価格の抽出
            price_elem = soup.find(string=re.compile(r'落札価格|落札額'))
            if price_elem:
                price_text = price_elem.get_text(strip=True)
                price_match = re.search(r'[\d,]+', price_text)
                if price_match:
                    try:
                        detail_info['price'] = int(price_match.group().replace(',', ''))
                    except (ValueError, IndexError):
                        pass
            
            # コメントの抽出
            comments = []
            comment_sections = soup.find_all(string=re.compile(r'コメント|備考|特記事項'))
            for section in comment_sections:
                comment = section.get_text(' ', strip=True)
                if comment and len(comment) > 10:  # 短いテキストは無視
                    comments.append(comment)
            
            if comments:
                detail_info['comments'] = comments
            
            # 疾病情報の抽出
            health_issues = []
            health_sections = soup.find_all(string=re.compile(r'疾病|怪我|治療|異常'))
            for section in health_sections:
                health_text = section.get_text(' ', strip=True)
                if health_text and len(health_text) > 5:  # 短いテキストは無視
                    health_issues.append(health_text)
            
            if health_issues:
                detail_info['health_issues'] = health_issues
            
            return detail_info
            
        except Exception as e:
            logger.error(f"詳細情報の抽出中にエラーが発生しました: {e}")
            return {}
    
    def _extract_pedigree(self, soup: BeautifulSoup) -> Dict[str, str]:
        result = {
            'sire': '不明',
            'dam': '不明',
            'damsire': '不明'
        }
        
        try:
            # ページ全体のテキストを取得
            page_text = soup.get_text(separator=' ', strip=True)
            
            # 血統情報を含む可能性のある要素を検索
            pedigree_text = ''
            possible_elements = soup.find_all(['div', 'p', 'td', 'span'])
            
            for elem in possible_elements:
                text = elem.get_text(separator=' ', strip=True)
                if '父：' in text and '母：' in text and '母の父：' in text:
                    pedigree_text = text
                    break
            
            if not pedigree_text:
                pedigree_text = page_text
            
            # 血統情報のパターン
            pattern = r'父[：:]([^\s\n\r\u3000]+?)\s*母[：:]([^\s\n\r\u3000]+?)\s*母の父[：:]([^\n\r\u3000]+?)(?=\s|\n|\r|$)'
            match = re.search(pattern, pedigree_text)
            
            if match:
                result['sire'] = match.group(1).strip()
                result['dam'] = match.group(2).strip()
                result['damsire'] = match.group(3).split('(')[0].strip()  # 余分な情報を除去
            else:
                # フォールバック: 個別に抽出を試みる
                sire_match = re.search(r'父[：:]([^\s\n\r\u3000]+)', page_text)
                if sire_match:
                    result['sire'] = sire_match.group(1).strip()
                
                dam_match = re.search(r'母[：:]([^\s\n\r\u3000(（]+)', page_text)
                if dam_match:
                    result['dam'] = dam_match.group(1).strip()
                
                damsire_match = re.search(r'母の?父[：:]([^\s\n\r\u3000(（]+)', page_text)
                if damsire_match:
                    result['damsire'] = damsire_match.group(1).split('(')[0].strip()
                
                # 母の括弧内に母父名が記載されている場合
                if result['damsire'] == '不明' and result['dam'] != '不明':
                    dam_full_match = re.search(r'母[：:][^\n\r(（]*[（(]([^)）]+)[)）]', page_text)
                    if dam_full_match:
                        result['damsire'] = dam_full_match.group(1).strip()
            
            # 結果をクリーンアップ
            for key in result:
                if result[key] != '不明':
                    # 余分な空白や改行を削除
                    result[key] = re.sub(r'\s+', ' ', result[key]).strip()
                    # 末尾の記号を削除
                    result[key] = re.sub(r'[、。\s]+$', '', result[key])
            
            logging.info(f"抽出した血統情報: 父={result['sire']}, 母={result['dam']}, 母父={result['damsire']}")
            return result
            
        except Exception as e:
            logging.error(f"血統情報の抽出中にエラーが発生しました: {str(e)}")
            import traceback
            logging.error(traceback.format_exc())
            return result
    
    def extract_horse_info_from_file(self, html_file: str) -> Dict[str, Any]:
        """HTMLファイルから馬の情報を抽出する"""
        try:
            # ファイルをバイナリモードで読み込み
            with open(html_file, 'rb') as f:
                raw_content = f.read()
            
            # エンコーディングを自動検出（UTF-8を優先）
            for encoding in ['utf-8', 'shift_jis', 'euc-jp', 'cp932']:
                try:
                    content = raw_content.decode(encoding)
                    break
                except UnicodeDecodeError:
                    continue
            else:
                # どのエンコーディングでもデコードできない場合は、UTF-8で強制的にデコード（エラーを無視）
                content = raw_content.decode('utf-8', errors='ignore')
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(content, 'html.parser')
            
            # 馬の基本情報を抽出
            horse_info = self._extract_horse_info_from_row(soup)
            
            # 詳細情報を抽出
            detail_info = self._extract_horse_detail_info(soup)
            
            # 情報を統合
            horse_info.update(detail_info)
            
            # ファイル名からオークション日を抽出（例: 20230815_123456_...）
            file_stem = Path(html_file).stem
            date_match = re.search(r'(\d{8})_', file_stem)
            if date_match:
                try:
                    date_str = date_match.group(1)
                    horse_info['auction_date'] = f"{date_str[:4]}-{date_str[4:6]}-{date_str[6:8]}"
                except (IndexError, ValueError):
                    pass
            
            # 毛色の抽出
            color_match = re.search(r'([\u4e00-\u9fff]+毛)', content)
            if color_match:
                horse_info['color'] = color_match.group(1)
            
            return horse_info
            
        except Exception as e:
            logger.error(f"ファイル {html_file} の処理中にエラーが発生: {e}")
            return {}
    
    def _extract_pedigree_info(self, soup, horse_info):
        """血統情報を抽出する"""
        content = str(soup)
        
        # 父の抽出
        sire_match = re.search(r'父[：:]([^\n<]+)', content)
        if sire_match:
            horse_info['sire'] = sire_match.group(1).strip()
        
        # 母の抽出
        dam_match = re.search(r'母[：:]([^\n<]+)', content)
        if dam_match:
            horse_info['dam'] = dam_match.group(1).strip()
        
        # 母父の抽出
        damsire_match = re.search(r'母の?父[：:]([^\n<]+)', content)
        if damsire_match:
            horse_info['damsire'] = damsire_match.group(1).strip()
        
        # 馬主の抽出
        owner_match = re.search(r'馬主[：:]([^\n<]+)', content)
        if owner_match:
            horse_info['owner'] = owner_match.group(1).strip()
        
        # 生産者の抽出
        breeder_match = re.search(r'生産者[：:]([^\n<]+)', content)
        if breeder_match:
            horse_info['breeder'] = breeder_match.group(1).strip()
        
        # テーブルからも抽出を試みる
        table_rows = soup.select('table tr')
        for row in table_rows:
            cols = row.find_all('td')
            if len(cols) >= 2:
                key = cols[0].get_text(strip=True)
                value = cols[1].get_text(' ', strip=True)
                
                if '父' in key and '母の父' not in key and '母父' not in key and 'sire' not in horse_info:
                    horse_info['sire'] = value
                elif '母' in key and '父' not in key and 'dam' not in horse_info:
                    horse_info['dam'] = value
                elif ('母の父' in key or '母父' in key) and 'damsire' not in horse_info:
                    horse_info['damsire'] = value
                elif '馬主' in key and 'owner' not in horse_info:
                    horse_info['owner'] = value
                elif '生産者' in key and 'breeder' not in horse_info:
                    horse_info['breeder'] = value
    
    def _extract_weight_and_price(self, soup, horse_info):
        """馬体重と落札価格を抽出する"""
        content = str(soup)
        
        # 馬体重の抽出
        weight_match = re.search(r'馬体重[：:]([\d.]+)\s*kg', content)
        if not weight_match:
            weight_match = re.search(r'([\d.]+)\s*kg', content)
            
        if weight_match:
            try:
                horse_info['weight'] = float(weight_match.group(1).strip())
            except (ValueError, AttributeError):
                pass
        
        # 落札価格の抽出
        price_match = re.search(r'(\d{1,3}(?:,\d{3})+)\s*円', content)
        if not price_match:
            price_match = re.search(r'落札価格[：:]([\d,]+)', content)
            
        if price_match:
            try:
                price = int(price_match.group(1).replace(',', ''))
                horse_info['winning_bid'] = price
            except (ValueError, AttributeError):
                pass
    
    def _extract_comments_and_health(self, soup, horse_info):
        """コメントと疾病情報を抽出する"""
        content = str(soup)
        
        # コメントを抽出
        comments = []
        # 一般的なコメントセクションを検索
        comment_matches = re.findall(r'(?:コメント|備考|特記事項)[：:]([^<]+)', content)
        for match in comment_matches:
            comment = match.strip()
            if len(comment) > 5:  # 短いテキストは無視
                comments.append(comment)
        
        # コメントが見つからない場合は、長いテキストブロックを探す
        if not comments:
            text_blocks = re.findall(r'[^。]{20,}?(?=<|$)', content)
            for block in text_blocks:
                if len(block) > 50 and not any(keyword in block for keyword in ['利用規約', 'プライバシーポリシー', 'Copyright']):
                    comments.append(block.strip())
        
        if comments:
            horse_info['comments'] = comments
        
        # 疾病情報を抽出
        health_issues = []
        health_keywords = ['疾病', '怪我', '治療', '異常', '手術', '骨折', '炎症', '腫脹', '跛行', '脱臼', '捻挫']
        
        for keyword in health_keywords:
            matches = re.findall(f'[^。]*{keyword}[^。]*', content)
            for match in matches:
                if len(match) > 10:  # 短いテキストは無視
                    health_issues.append(match.strip())
        
        if health_issues:
            horse_info['health_issues'] = list(set(health_issues))  # 重複を削除

def save_to_cache(cache_dir: Path, filename: str, content: str):
    """キャッシュにデータを保存する"""
    try:
        # キャッシュディレクトリが存在しない場合は作成
        cache_dir.mkdir(parents=True, exist_ok=True)
        
        # ファイルに保存
        file_path = cache_dir / filename
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(content)
        
        logger.debug(f"キャッシュに保存しました: {file_path}")
        return True
    except Exception as e:
        logger.error(f"キャッシュの保存に失敗しました: {e}")
        return False

def extract_horse_info_from_html(html_content, is_detail_page=False):
    """HTMLコンテンツから馬の基本情報を抽出"""
    soup = BeautifulSoup(html_content, 'html.parser')
    horse_info = {}
    
    # テキスト全体を取得
    full_text = soup.get_text(' ', strip=True)
    
    # 馬名を抽出（太字の最初の要素）
    name_elem = soup.find('b')
    if name_elem:
        horse_name = name_elem.get_text(strip=True)
        if '本馬について' not in horse_name:  # 誤検出を防ぐ
            horse_info['name'] = horse_name
    
    # 基本情報行を抽出
    info_line = ''
    if is_detail_page:
        # 詳細ページの場合は最初のテーブル行を取得
        first_row = soup.find('tr')
        if first_row:
            info_line = first_row.get_text(' ', strip=True)
    else:
        # リストページの場合は最初の行を取得
        first_line = full_text.split('\n')[0] if '\n' in full_text else full_text
        info_line = first_line.strip()
    
    # 性別、毛色、生年月日を抽出
    if info_line:
        # 性別を抽出
        gender_match = re.search(r'([牡牝セ])(?: |　|$)', info_line)
        if gender_match:
            horse_info['gender'] = gender_match.group(1)
        
        # 毛色を抽出
        color_match = re.search(r'[牡牝セ](?: |　)([^ ]+?)(?: |　|$)', info_line)
        if color_match:
            horse_info['color'] = color_match.group(1)
        
        # 生年月日を抽出
        birth_match = re.search(r'(\d{4})年(\d{1,2})月(\d{1,2})日', info_line)
        if birth_match:
            horse_info['birth_date'] = f"{birth_match.group(1)}-{birth_match.group(2).zfill(2)}-{birth_match.group(3).zfill(2)}"
    
    # 血統情報を抽出
    pedigree_match = re.search(r'父：([^\n\r]+?)\s*母：([^\n\r]+?)\s*母の父：([^\n\r]+?)(?:\s|$)', full_text)
    if not pedigree_match:
        # 別の形式の血統情報を試す
        pedigree_match = re.search(r'父([^\n\r]+?)\s*母([^\n\r]+?)\s*母の父([^\n\r]+?)(?:\s|$)', full_text)
    
    if pedigree_match:
        horse_info['sire'] = pedigree_match.group(1).strip()
        horse_info['dam'] = pedigree_match.group(2).strip()
        horse_info['damsire'] = pedigree_match.group(3).strip()
    
    # 通算成績を抽出
    record_match = re.search(r'通算成績[：:](\d+)戦(\d+)勝(\d+)着(\d+)回', full_text)
    if not record_match:
        record_match = re.search(r'(\d+)戦(\d+)勝(\d+)着(\d+)回', full_text)
    
    if record_match:
        horse_info['record'] = {
            'races': int(record_match.group(1)),
            'wins': int(record_match.group(2)),
            'places': int(record_match.group(3)),
            'shows': int(record_match.group(4))
        }
    
    # 賞金情報を抽出
    prize_match = re.search(r'中央獲得賞金[：:]([\d,]+(?:\.\d+)?)万円', full_text)
    if not prize_match:
        prize_match = re.search(r'中央([\d,]+(?:\.\d+)?)万円', full_text)
    
    if prize_match:
        horse_info['prize_money_jra'] = float(prize_match.group(1).replace(',', '')) * 10000
    
    local_prize_match = re.search(r'地方獲得賞金[：:]([\d,]+(?:\.\d+)?)万円', full_text)
    if not local_prize_match:
        local_prize_match = re.search(r'地方([\d,]+(?:\.\d+)?)万円', full_text)
    
    if local_prize_match:
        horse_info['prize_money_local'] = float(local_prize_match.group(1).replace(',', '')) * 10000
    
    # コメントを抽出
    comment_section = soup.find('b', string=re.compile('本馬について'))
    if comment_section:
        comment_text = ''
        next_elem = comment_section.find_next()
        while next_elem and next_elem.name != 'table':
            if hasattr(next_elem, 'get_text'):
                comment_text += next_elem.get_text(' ', strip=True) + ' '
            next_elem = next_elem.next_sibling
        
        if comment_text:
            horse_info['comment'] = comment_text.strip()
    
    return horse_info

def process_list_page(extractor, list_page_path):
    """リストページを処理して馬の情報を抽出"""
    logger.info(f"リストページを処理中: {list_page_path}")
    
    # リストページのHTMLを読み込む
    try:
        with open(list_page_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logger.error(f"リストページの読み込みに失敗しました: {e}")
        return []
    
    soup = BeautifulSoup(content, 'html.parser')
    horses = []
    
    # 馬の情報を含むセクションを検索
    horse_sections = []
    
    # 1. 画像リンクから馬のIDを抽出
    img_links = soup.find_all('img', src=re.compile(r'/auction/data/item/\d+/\d+_horse_\d+/\d+\.jpg'))
    for img in img_links:
        src = img.get('src', '')
        # URLから馬のIDを抽出 (例: 250814_horse_48)
        match = re.search(r'/(\d+_horse_\d+)/', src)
        if match:
            horse_id = match.group(1)
            horse_sections.append({
                'id': horse_id,
                'img_src': src,
                'element': img.find_parent()  # 親要素を取得
            })
    
    # 各馬の情報を抽出
    for horse in horse_sections:
        try:
            horse_info = {
                'item_id': horse['id'],
                'image_url': horse['img_src']
            }
            
            # 親要素からテキストを抽出
            parent = horse['element']
            if parent:
                # 馬名を抽出 (例: ピュアカラー)
                name_elem = parent.find('b')
                if name_elem:
                    horse_info['name'] = name_elem.get_text(strip=True)
                
                # 性別と年齢を抽出 (例: 牝8歳)
                gender_age = parent.find(string=re.compile(r'[牡牝セ]\s*\d+歳'))
                if gender_age:
                    gender_age = gender_age.strip()
                    horse_info['gender'] = gender_age[0]  # 最初の1文字が性別
                    age_match = re.search(r'(\d+)', gender_age)
                    if age_match:
                        horse_info['age'] = int(age_match.group(1))
                
                # 毛色を抽出
                colors = ['鹿毛', '黒鹿毛', '青鹿毛', '栗毛', '栃栗毛', '青毛', '芦毛', '白毛']
                for color in colors:
                    if color in parent.get_text():
                        horse_info['color'] = color
                        break
                
                # 父、母、母父を抽出
                text = parent.get_text(' ', strip=True)
                pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)(?:\s*母の父：([^\s]+))?', text)
                if pedigree_match:
                    horse_info['sire'] = pedigree_match.group(1)
                    horse_info['dam'] = pedigree_match.group(2)
                    if pedigree_match.group(3):
                        horse_info['damsire'] = pedigree_match.group(3)
                
                # 詳細ページのパス
                details_dir = list_page_path.parent / 'details'
                details_dir.mkdir(exist_ok=True)
                detail_path = details_dir / f"{horse_info['item_id']}.html"
                
                # 詳細ページが存在する場合は情報を追加
                if detail_path.exists():
                    try:
                        with open(detail_path, 'r', encoding='utf-8') as f:
                            detail_content = f.read()
                        detail_info = extract_horse_info_from_html(detail_content, is_detail_page=True)
                        horse_info.update(detail_info)
                        logger.debug(f"詳細情報を抽出しました: {horse_info['item_id']}")
                    except Exception as e:
                        logger.error(f"詳細情報の抽出に失敗しました {horse_info['item_id']}: {e}")
                else:
                    logger.warning(f"詳細ページが存在しません: {detail_path}")
                
                # 馬の情報をキャッシュに保存
                cache_dir = list_page_path.parent / 'details'
                cache_dir.mkdir(exist_ok=True)
                cache_file = f"{horse_info['item_id']}.json"
                save_to_cache(cache_dir, cache_file, json.dumps(horse_info, ensure_ascii=False, indent=2))
                
                if horse_info.get('name'):  # 有効な馬情報のみ追加
                    horses.append(horse_info)
                    logger.info(f"馬情報を抽出しました: {horse_info.get('name')} (ID: {horse_info['item_id']})")
            
        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました: {e}")
            continue
    
    return horses

def main():
    try:
        # 最新のキャッシュディレクトリを取得
        cache_dir = get_latest_cache_dir()
        logger.info(f"使用中のキャッシュディレクトリ: {cache_dir}")
        
        # リストページのパス
        list_page = cache_dir / 'list.html'
        if not list_page.exists():
            raise FileNotFoundError(f"リストページが見つかりません: {list_page}")
        
        # 詳細ページのディレクトリが存在するか確認し、なければ作成
        details_dir = cache_dir / 'details'
        details_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"詳細ページの保存先: {details_dir}")
        
        extractor = DebugHorseExtractor()
        
        # リストページを処理
        all_horses = process_list_page(extractor, list_page)
        
        # 結果をJSONファイルに保存
        output_file = PROJECT_ROOT / 'extracted_horses.json'
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(all_horses, f, ensure_ascii=False, indent=2)
        
        logger.info(f"抽出が完了しました。結果は {output_file} に保存されました。")
        
        # メタデータを更新
        metadata = {
            'session_id': cache_dir.name,
            'start_time': datetime.now().isoformat(),
            'list_page': 'list.html',
            'details': [f.name for f in details_dir.glob('*.json')],
            'last_updated': datetime.now().isoformat()
        }
        
        with open(cache_dir / 'metadata.json', 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        logger.info(f"メタデータを更新しました: {cache_dir / 'metadata.json'}")
        
        # コンソールに結果を表示
        print("\n=== 抽出結果のサマリー ===")
        print(f"キャッシュディレクトリ: {cache_dir}")
        print(f"抽出した馬の数: {len(all_horses)}")
        
        if all_horses:
            print("\n最初の馬の情報:")
            first_horse = all_horses[0]
            for key, value in first_horse.items():
                if key not in ['comments', 'health_issues'] and value:
                    print(f"{key}: {value}")
            
            if 'comments' in first_horse and first_horse['comments']:
                print("\nコメント:")
                for comment in first_horse['comments']:
                    print(f"- {comment}")
            
            if 'health_issues' in first_horse and first_horse['health_issues']:
                print("\n健康情報:")
                for issue in first_horse['health_issues']:
                    print(f"- {issue}")
    
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        print(f"\nエラーが発生しました: {e}\n詳細はログファイルを確認してください。")
        return

if __name__ == "__main__":
    main()
