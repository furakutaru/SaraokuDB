#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import time
import random
import logging
import re
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
from pathlib import Path

# プロジェクトのルートディレクトリを追加
sys.path.append(str(Path(__file__).parent.parent))

from bs4 import BeautifulSoup
import requests
from urllib.parse import urljoin, urlparse

# ロガーの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('horse_extraction_debug.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class DebugHorseExtractor:
    """デバッグ用の馬情報抽出クラス
    
    本番環境のスクレイピングロジックを模倣しつつ、
    デバッグ用の機能を追加したクラス
    """
    
    def __init__(self, test_mode: bool = True):
        """初期化
        
        Args:
            test_mode: テストモードかどうか
        """
        self.test_mode = test_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8',
        })
        
        # リトライ設定
        self.retry_attempts = 3
        self.retry_delay = 5
    
    def fetch_page(self, url_or_path: str) -> Optional[str]:
        """ページを取得する
        
        Args:
            url_or_path: 取得するページのURLまたはローカルファイルパス
            
        Returns:
            str: ページのHTMLコンテンツ
        """
        # ローカルファイルパスの場合
        if os.path.exists(url_or_path):
            try:
                with open(url_or_path, 'r', encoding='utf-8') as f:
                    return f.read()
            except Exception as e:
                logger.error(f"ローカルファイルの読み込みに失敗: {url_or_path}: {e}")
                return None
                
        # URLの場合
        for attempt in range(self.retry_attempts):
            try:
                # URLにスキームが含まれていない場合、httpsを追加
                if not url_or_path.startswith(('http://', 'https://')):
                    url = 'https://' + url_or_path
                else:
                    url = url_or_path
                    
                response = self.session.get(url, timeout=30)
                response.raise_for_status()
                return response.text
            except requests.RequestException as e:
                logger.warning(f"リクエストエラー (試行 {attempt + 1}/{self.retry_attempts}): {e}")
                if attempt < self.retry_attempts - 1:
                    time.sleep(self.retry_delay * (attempt + 1))
                else:
                    logger.error(f"ページの取得に失敗: {url_or_path}")
                    return None
    
    def extract_horse_info(self, url: str) -> Dict[str, Any]:
        """馬の詳細情報を抽出する
        
        Args:
            url: 馬の詳細ページURL
            
        Returns:
            Dict[str, Any]: 馬の情報を含む辞書
        """
        logger.info(f"馬情報の抽出を開始: {url}")
        
        # ページを取得
        html = self.fetch_page(url)
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 馬の基本情報を抽出
        horse_info = {
            'url': url,
            'name': self._extract_name(soup),
            'sex': self._extract_sex(soup),
            'age': self._extract_age(soup),
            'sire': self._extract_sire(soup),
            'dam': self._extract_dam(soup),
            'damsire': self._extract_damsire(soup),
            'seller': self._extract_seller(soup),
            'auction_date': self._extract_auction_date(soup),
            'weight': self._extract_weight(soup),
            'comment': self._extract_comment(soup),
            'extracted_at': datetime.now().isoformat(),
        }
        
        return horse_info
    
    def _extract_name(self, soup: BeautifulSoup) -> str:
        """馬名を抽出する"""
        try:
            # タイトルタグから抽出を試みる（多くの場合、馬名が含まれている）
            title = soup.title.string if soup.title else ""
            if title:
                # タイトルから馬名を抽出（「馬名 | サイト名」の形式を想定）
                name_match = re.search(r'^([^|\n\r\t]+?)(?:\s*[|\-]\s*|\s+の血統情報|\s+のプロフィール|\s+の情報|\s*$)', title)
                if name_match:
                    name = name_match.group(1).strip()
                    if name and len(name) > 1:
                        return name
            
            # 一般的なセレクタで探す
            selectors = [
                'h1.horse-name',
                '.horse-name',
                'h1',
                'div.horse-info h2',
                'div.horse-title',
                'span.horse-name',
                'div.horse-header h2',
                'div.horse_title',
                'div.horseName',
                'span.horse_name',
                'div#horseName',
                'div#horse_name',
                'div.horse_name',
                'div.horseName',
                'div.horse_name',
                'div.horseData h2',
                'div.horse_data h2',
                'div.horse_data h1',
                'div.horseData h1',
                'div.horseInfo h2',
                'div.horse_info h2',
                'div.horseInfo h1',
                'div.horse_info h1'
            ]
            
            # セレクタで直接探す
            for selector in selectors:
                try:
                    name_elems = soup.select(selector)
                    for elem in name_elems:
                        name = elem.get_text(strip=True)
                        # 余分な文字列を削除
                        name = re.sub(r'[\s\n\r\t]+', ' ', name)
                        name = re.sub(r'^[\s\d.]+', '', name)  # 先頭の数字やピリオドを削除
                        name = name.strip()
                        
                        # 馬名として適切かチェック（2文字以上、数字のみでない、一般的な記号のみ含む）
                        if (name and len(name) > 1 and 
                            not name.isdigit() and 
                            re.match(r'^[\w\s・（）()\-〜&]+$', name)):
                            return name
                except:
                    continue
            
            # テーブルから探す（馬名が含まれている可能性のあるテーブルを検索）
            for table in soup.select('table'):
                rows = table.select('tr')
                for row in rows:
                    cells = row.select('th, td')
                    for i, cell in enumerate(cells):
                        cell_text = cell.get_text(strip=True).lower()
                        if '馬名' in cell_text or 'name' in cell_text or 'うまめい' in cell_text:
                            # 同じ行の次のセルを確認
                            if i + 1 < len(cells):
                                name = cells[i+1].get_text(strip=True)
                                if name and len(name) > 1:
                                    return name
            
            # ページ内の太字テキストから探す（馬名は太字で表示されていることが多い）
            for bold in soup.select('b, strong'):
                name = bold.get_text(strip=True)
                if (len(name) > 1 and 
                    not name.isdigit() and 
                    re.match(r'^[\w\s・（）()\-〜&]+$', name)):
                    return name
            
            # 最終手段：ページ内で最も長いテキストノードを探す（馬名は通常、ページ内で目立つ）
            def get_text_nodes(element):
                for child in element.descendants:
                    if isinstance(child, str) and child.strip():
                        text = child.strip()
                        if (len(text) > 1 and 
                            not text.isdigit() and 
                            re.match(r'^[\w\s・（）()\-〜&]+$', text)):
                            yield text
            
            # 長さでソートして最長のものを返す
            text_nodes = list(get_text_nodes(soup))
            if text_nodes:
                return max(text_nodes, key=len)
                        
        except Exception as e:
            logger.warning(f"馬名の抽出に失敗: {e}")
            
        # 最終手段: ページの最初のh1タグを取得
        try:
            h1 = soup.find('h1')
            if h1:
                return h1.get_text(strip=True)[:50]  # 50文字で切り詰め
        except:
            pass
            
        return ""
    
    def _extract_sex(self, soup: BeautifulSoup) -> str:
        """性別を抽出する"""
        try:
            # 性別を表す可能性のあるテキストパターン
            sex_patterns = [
                # パターン1: 性別: 牡/牝/騸
                r'(?:性別|せいべつ)[:：]?\s*([牡牝騸♂♀セ])(?:馬|\b)',
                # パターン2: 牡/牝/騸 のみ
                r'\b([牡牝騸♂♀セ])(?:馬|\b)(?!\d)',
                # パターン3: 性別: 牡馬/牝馬/騸馬
                r'(?:性別|せいべつ)[:：]?\s*([牡牝騸]馬)',
                # パターン4: 牡馬/牝馬/騸馬 のみ
                r'\b([牡牝騸]馬)\b',
                # パターン5: 性別: 牡・牝・セ
                r'(?:性別|せいべつ)[:：]?\s*([牡・牝・セ])',
                # パターン6: 性別: 牡 または 牝 または セ
                r'(?:性別|せいべつ)[:：]?\s*([牡]|[牝]|[セ])',
                # パターン7: 性別: 牡馬 (牡馬)
                r'性別[:：]?\s*[（(]?([牡牝騸])[)）]?',
                # パターン8: 英語表記 (M/F/G)
                r'\b(?:Sex|性別)[:：]?\s*([MFG]|Male|Female|Gelding)\b',
                # パターン9: セックス: 牡/牝/セ
                r'セックス[:：]?\s*([牡牝セ])',
                # パターン10: 日本語のフルネーム
                r'\b(牡馬|牝馬|騸馬|牡|牝|セ|せいべつ|オス|メス|オス馬|メス馬|去勢馬)\b',
                # パターン11: 英語の略語
                r'\b([MFG]|Colt|Filly|Horse|Mare|Gelding|Stallion)\b',
                # パターン12: 記号のみ
                r'[♂♀]'
            ]
            
            # 性別を表す可能性のあるセレクタ（優先度順）
            selectors = [
                'div.sex', 'span.sex', 'div.horse-sex', 'span.horse-sex',
                'td:contains("性別")', 'th:contains("性別") + td',
                'td:contains("Sex")', 'th:contains("Sex") + td',
                'div.horse-info', 'div.horse-details', 'div.horse_data', 
                'div.horseData', 'table.horse-info', 'table.horse_info',
                'div.horseProfile', 'div.profile', 'div.horse-profile',
                'div.horseHeader', 'div.horse-header', 'div.horseName',
                'span.horse-name', 'h1.horse-name', 'div.horse_title',
                'div.horseTitle', 'div.horse-title', 'div.horseName',
                'div.horse_name', 'div.horseName', 'div.horseData h2',
                'div.horse_data h2', 'div.horse_data h1', 'div.horseData h1',
                'div.horseInfo h2', 'div.horse_info h2', 'div.horseInfo h1',
                'div.horse_info h1', 'table tr:has(td:contains("性別"))',
                'table tr:has(th:contains("性別"))', 'table tr:has(td:contains("Sex"))',
                'table tr:has(th:contains("Sex"))', 'div[class*="sex"]',
                'span[class*="sex"]', 'div[class*="Sex"]', 'span[class*="Sex"]'
            ]
            
            # 1. まずセレクタで探す
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        text = elem.get_text(" ", strip=True)
                        # 親要素のテキストも確認（テーブルセルの場合など）
                        parent_text = ""
                        if elem.parent:
                            parent_text = elem.parent.get_text(" ", strip=True)
                        
                        # テキストと親要素のテキストを組み合わせて検索
                        for text_to_search in [text, f"{text} {parent_text}"]:
                            for pattern in sex_patterns:
                                match = re.search(pattern, text_to_search, re.IGNORECASE)
                                if match:
                                    sex = match.group(1).strip()
                                    return self._normalize_sex(sex)
                except Exception as e:
                    logger.debug(f"セレクタ {selector} での性別抽出中にエラー: {e}")
                    continue
            
            # 2. テーブルから探す
            for table in soup.select('table'):
                try:
                    rows = table.select('tr')
                    for row in rows:
                        cells = row.select('th, td')
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(" ", strip=True).lower()
                            if '性別' in cell_text or 'sex' in cell_text or 'せいべつ' in cell_text:
                                # 同じ行の次のセルを確認
                                if i + 1 < len(cells):
                                    sex_text = cells[i+1].get_text(" ", strip=True)
                                    return self._normalize_sex(sex_text)
                                # 同じセル内に値がある場合
                                elif ':' in cell_text or '：' in cell_text:
                                    parts = re.split(r'[:：]', cell_text, 1)
                                    if len(parts) > 1:
                                        return self._normalize_sex(parts[1])
                except:
                    continue
            
            # 3. ページ全体から正規表現で検索
            page_text = soup.get_text(" ", strip=True)
            for pattern in sex_patterns:
                matches = re.finditer(pattern, page_text, re.IGNORECASE)
                for match in matches:
                    if match.groups():
                        sex = match.group(1).strip()
                        normalized_sex = self._normalize_sex(sex)
                        if normalized_sex:
                            return normalized_sex
            
            # 4. コメントからも探してみる
            comment = self._extract_comment(soup)
            if comment:
                for pattern in sex_patterns:
                    match = re.search(pattern, comment, re.IGNORECASE)
                    if match and match.groups():
                        sex = match.group(1).strip()
                        normalized_sex = self._normalize_sex(sex)
                        if normalized_sex:
                            return normalized_sex
                        
        except Exception as e:
            logger.warning(f"性別の抽出に失敗: {e}")
            
        return ""
        
    def _normalize_sex(self, sex_text: str) -> str:
        """性別テキストを正規化する"""
        if not sex_text:
            return ""
            
        # 小文字に統一
        sex_lower = sex_text.lower()
        
        # 牡馬パターン
        male_patterns = ['牡', '♂', '牡馬', 'おす', 'おすうま', 'おんま', 'male', 'm', 'colt', 'stallion', 's']
        if any(p in sex_lower for p in male_patterns):
            return '牡'
            
        # 牝馬パターン
        female_patterns = ['牝', '♀', '牝馬', 'めす', 'めすうま', 'めま', 'female', 'f', 'filly', 'mare', 'h', 'm']
        if any(p in sex_lower for p in female_patterns):
            return '牝'
            
        # 騸馬パターン
        gelding_patterns = ['騸', '騸馬', 'せん', 'せんば', '去勢', '去勢馬', 'gelding', 'g']
        if any(p in sex_lower for p in gelding_patterns):
            return '騸'
            
        # セ（性別不明または未登録）
        if 'セ' in sex_text or 'せ' in sex_lower or '性別' in sex_text or 'sex' in sex_lower:
            return 'セ'
            
        return ""
    
    def _extract_age(self, soup: BeautifulSoup) -> int:
        """年齢を抽出する"""
        try:
            # 年齢が含まれていそうな要素を検索
            age_keywords = ['歳', '才', '年齢', 'age']
            
            # 1. まずは一般的なセレクタで探す
            selectors = [
                '.age', '.horse-age', '.horseAge', '.horse_age',
                'div:contains("年齢")', 'span:contains("年齢")',
                'td:contains("年齢")', 'th:contains("年齢")',
                'td:contains("歳")', 'th:contains("歳")',
                'td:contains("才")', 'th:contains("才")',
                'td:contains("Age")', 'th:contains("Age")',
                'div.horse-info', 'div.horse_info', 'div.horseData',
                'div.horse_data', 'div.horse-details', 'div.horseDetails',
                'table.horse-info', 'table.horse_info', 'table.profile',
                'div.profile', 'div.horse-profile', 'div.horseProfile'
            ]
            
            # セレクタで直接探す
            for selector in selectors:
                try:
                    elements = soup.select(selector)
                    for elem in elements:
                        # 要素のテキストとその周辺のテキストも確認
                        text = self._get_combined_text(elem)
                        # 年齢パターンで検索
                        age = self._extract_age_from_text(text)
                        if age is not None:
                            return age
                except Exception as e:
                    logger.debug(f"セレクタ {selector} での年齢抽出中にエラー: {e}")
                    continue
            
            # 2. テーブルから探す
            for table in soup.select('table'):
                try:
                    rows = table.select('tr')
                    for row in rows:
                        cells = row.select('th, td')
                        for i, cell in enumerate(cells):
                            cell_text = cell.get_text(" ", strip=True).lower()
                            # 年齢に関連するキーワードを含むセルを探す
                            if any(kw in cell_text for kw in age_keywords):
                                # 同じ行の次のセルを確認
                                if i + 1 < len(cells):
                                    age_text = cells[i+1].get_text(" ", strip=True)
                                    age = self._extract_age_from_text(age_text)
                                    if age is not None:
                                        return age
                                # 同じセル内に値がある場合
                                elif ':' in cell_text or '：' in cell_text:
                                    parts = re.split(r'[:：]', cell_text, 1)
                                    if len(parts) > 1:
                                        age = self._extract_age_from_text(parts[1])
                                        if age is not None:
                                            return age
                except Exception as e:
                    logger.debug(f"テーブルからの年齢抽出中にエラー: {e}")
                    continue
            
            # 3. ページ全体から正規表現で検索
            page_text = soup.get_text(" ", strip=True)
            
            # パターン1: 「年齢: 3歳」のような形式
            age_matches = re.findall(r'(?:年齢|歳|才|age)[:：]?\s*(\d+\s*[歳才]?)', page_text, re.IGNORECASE)
            if age_matches:
                age = self._extract_age_from_text(age_matches[0])
                if age is not None:
                    return age
            
            # パターン2: 「3歳」のような形式
            age_matches = re.findall(r'\b(\d+)\s*[歳才]\b', page_text)
            if age_matches:
                age = self._extract_age_from_text(age_matches[0])
                if age is not None:
                    return age
            
            # パターン3: 数字のみ（周囲の文脈から年齢と判断）
            # 馬の年齢として妥当な範囲の数字を探す
            age_matches = re.findall(r'\b([0-9]|[12][0-9]|30)\b', page_text)
            if age_matches:
                # 出現頻度が最も高い年齢を採用（外れ値を避けるため）
                age_counts = {}
                for m in age_matches:
                    age = int(m)
                    if 1 <= age <= 30:  # 馬の年齢として妥当な範囲
                        age_counts[age] = age_counts.get(age, 0) + 1
                
                if age_counts:
                    return max(age_counts.items(), key=lambda x: x[1])[0]
            
            # 4. コメントからも探してみる
            comment = self._extract_comment(soup)
            if comment:
                age_matches = re.findall(r'(?:年齢|歳|才|age)[:：]?\s*(\d+\s*[歳才]?)', comment, re.IGNORECASE)
                if age_matches:
                    age = self._extract_age_from_text(age_matches[0])
                    if age is not None:
                        return age
                
                # コメント内の「○歳」を探す
                age_matches = re.findall(r'\b(\d+)\s*[歳才]\b', comment)
                if age_matches:
                    age = self._extract_age_from_text(age_matches[0])
                    if age is not None:
                        return age
            
            # 5. 生年月日から計算してみる
            birth_year = self._extract_birth_year(soup)
            if birth_year:
                current_year = datetime.now().year
                age = current_year - birth_year
                if 0 < age < 30:  # 馬の年齢として妥当な範囲
                    return age
                    
        except Exception as e:
            logger.warning(f"年齢の抽出に失敗: {e}")
            
        return 0
    
    def _extract_pedigree(self, soup: BeautifulSoup) -> Tuple[str, str, str]:
        """血統情報を抽出する（父、母、母父）"""
        sire = dam = damsire = ""
        try:
            # 本番環境のセレクタに合わせる
            pedigree = soup.select('.pedigree')
            if not pedigree:
                # 別のセレクタを試す
                pedigree_text = soup.get_text()
                import re
                match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\s]+)', pedigree_text)
                if match:
                    return match.group(1), match.group(2), match.group(3)
            
            if pedigree and len(pedigree) >= 3:
                sire = pedigree[0].get_text(strip=True)
                dam = pedigree[1].get_text(strip=True)
                damsire = pedigree[2].get_text(strip=True)
                
                # 血統情報から不要なテキストを除去
                sire = sire.replace('父', '').strip()
                dam = dam.replace('母', '').strip()
                damsire = damsire.replace('母父', '').strip()
                
        except Exception as e:
            logger.warning(f"血統情報の抽出に失敗: {e}")
            
        return sire, dam, damsire
    
    def _extract_sire(self, soup: BeautifulSoup) -> str:
        """父馬名を抽出する"""
        try:
            sire, _, _ = self._extract_pedigree(soup)
            return sire
        except Exception as e:
            logger.warning(f"父馬名の抽出に失敗: {e}")
            return ""
    
    def _extract_dam(self, soup: BeautifulSoup) -> str:
        """母馬名を抽出する"""
        try:
            _, dam, _ = self._extract_pedigree(soup)
            return dam
        except Exception as e:
            logger.warning(f"母馬名の抽出に失敗: {e}")
            return ""
            
    def _extract_damsire(self, soup: BeautifulSoup) -> str:
        """母父名を抽出する"""
        try:
            _, _, damsire = self._extract_pedigree(soup)
            return damsire
        except Exception as e:
            logger.warning(f"母父名の抽出に失敗: {e}")
            return ""
    
    
    def _extract_seller(self, soup: BeautifulSoup) -> str:
        """販売者を抽出する"""
        try:
            # 複数のセレクタを試す
            selectors = [
                '.sellerInfo',
                '.seller-info',
                '.seller',
                'div:contains("売主")',
                'div:contains("販売者"):not(:has(*))'  # 子要素を持たない販売者を含む要素
            ]
            
            for selector in selectors:
                seller_elem = soup.select_one(selector)
                if seller_elem:
                    seller = seller_elem.get_text(strip=True)
                    # インボイス番号などの不要な情報を除去
                    seller = re.sub(r'[（(].*?[)）]', '', seller)  # 括弧内を除去
                    seller = re.sub(r'[0-9]{4,}', '', seller)  # 4桁以上の数字を除去
                    seller = re.sub(r'[\s　]+', ' ', seller).strip()  # 連続する空白を1つに
                    if seller and len(seller) > 1:  # 1文字の場合はスキップ
                        return seller
            
            # フッターからも検索
            footer = soup.find('footer') or soup.find('div', class_='footer')
            if footer:
                footer_text = footer.get_text(' ', strip=True)
                # フッターテキストから販売者らしき部分を抽出
                match = re.search(r'(?:売主|販売者)[:：]\s*([^\s].*?)(?:\s*\||\s*©|\s*$)', footer_text)
                if match:
                    return match.group(1).strip()
                    
        except Exception as e:
            logger.warning(f"販売者の抽出に失敗: {e}")
            
            # 8. 最終手段: ファイル名やディレクトリ名から日付を推測
            if hasattr(self, 'current_file_path'):
                date_str = self._extract_date_from_text(self.current_file_path)
                if date_str:
                    return date_str
                    
        except Exception as e:
            logger.warning(f"オークション日付の抽出に失敗: {e}")
            
        # デフォルトで現在日付を返す
        logger.warning("オークション日付が見つからないため、現在日時を使用します")
        return datetime.now().strftime('%Y-%m-%d')
    
    def _extract_date_from_text(self, text: str) -> Optional[str]:
        """テキストから日付を抽出するヘルパーメソッド"""
        if not text:
            return None
            
        # 和暦を西暦に変換
        jp_eras = {
            '令和': 2018,  # 2019年が令和元年
            '平成': 1988,  # 1989年が平成元年
            '昭和': 1925,  # 1926年が昭和元年
            '大正': 1911,  # 1912年が大正元年
            '明治': 1867   # 1868年が明治元年
        }
        
        # 和暦表記を西暦に変換
        for era, base_year in jp_eras.items():
            if era in text:
                pattern = f'{era}(?:\s*)(\d+)年(?:\s*)(\d+)月(?:\s*)(\d+)日?'
                match = re.search(pattern, text)
                if match:
                    year = base_year + int(match.group(1))
                    month = int(match.group(2))
                    day = int(match.group(3) or '1')
                    if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                        return f"{year}-{month:02d}-{day:02d}"
        
        # 西暦表記（YYYY/MM/DD または YYYY-MM-DD）
        patterns = [
            # YYYY/MM/DD または YYYY-MM-DD
            r'(\d{4})[/-](\d{1,2})[/-](\d{1,2})',
            # YYYY年MM月DD日
            r'(\d{4})年(\d{1,2})月(\d{1,2})日?',
            # YY/MM/DD (2000年以降を想定)
            r'\b(20\d{2})[/-](\d{1,2})[/-](\d{1,2})\b',
            # MM/DD/YYYY
            r'\b(\d{1,2})/(\d{1,2})/(\d{4})\b',
            # DD-MM-YYYY
            r'\b(\d{1,2})-(\d{1,2})-(\d{4})\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, text)
            for match in matches:
                try:
                    if len(match.groups()) >= 3:
                        # パターンに応じて年、月、日を取得
                        if '年' in pattern:  # YYYY年MM月DD日 形式
                            year, month, day = map(int, match.groups()[:3])
                        elif pattern == patterns[3]:  # MM/DD/YYYY 形式
                            month, day, year = map(int, match.groups()[:3])
                        elif pattern == patterns[4]:  # DD-MM-YYYY 形式
                            day, month, year = map(int, match.groups()[:3])
                        else:  # その他の形式（YYYY/MM/DD など）
                            year, month, day = map(int, match.groups()[:3])
                        
                        # 年が2桁の場合は2000年代と仮定
                        if year < 100:
                            year += 2000
                        
                        # 日付の妥当性チェック
                        if 2000 <= year <= 2100 and 1 <= month <= 12 and 1 <= day <= 31:
                            return f"{year}-{month:02d}-{day:02d}"
                except (ValueError, IndexError):
                    continue
        
        return None  # エラー時は現在日付を返す
    
    def _extract_weight(self, soup: BeautifulSoup) -> float:
        """馬体重を抽出する"""
        try:
            # まずはコメントから体重を探す（コメントに体重が含まれていることが多い）
{{ ... }}
            if comment:
                # コメント内の体重表記を検索（例：「馬体重424㎏」）
                weight_matches = re.findall(r'馬体重\s*([\d.]+)[\s㎏kg]', comment)
                if weight_matches:
                    weight = float(weight_matches[-1])  # 最新の体重を取得
                    if 200 <= weight <= 600:  # 妥当な馬の体重範囲
                        return weight
            
            # 一般的なセレクタで探す
            selectors = [
                '.weight',
                '.horseWeight',
                'div:contains("馬体重")',
                'div:contains("体重")',
                'td:contains("馬体重") + td',
                'th:contains("馬体重") + td',
                'span:contains("馬体重") + span',
                'span:contains("体重") + span',
                'div:contains("Weight") + div',
                'td:contains("Weight") + td',
                'th:contains("Weight") + td'
            ]
            
            for selector in selectors:
                try:
                    weight_elems = soup.select(selector)
                    for weight_elem in weight_elems:
                        weight_text = weight_elem.get_text(strip=True)
                        # 数字部分を抽出（「500kg」や「500.0kg」などに対応）
                        match = re.search(r'([\d.]+)\s*[㎏kg]?', weight_text)
                        if match:
                            weight = float(match.group(1))
                            if 200 <= weight <= 600:  # 妥当な馬の体重範囲
                                return weight
                except:
                    continue
            
            # テーブルから検索
            for row in soup.select('tr'):
                cells = row.select('th, td')
                for i, cell in enumerate(cells):
                    cell_text = cell.get_text(strip=True).lower()
                    if '体重' in cell_text or 'weight' in cell_text:
                        # 同じ行の次のセルを確認
                        if i + 1 < len(cells):
                            weight_text = cells[i+1].get_text(strip=True)
                            match = re.search(r'([\d.]+)', weight_text)
                            if match:
                                weight = float(match.group(1))
                                if 200 <= weight <= 600:
                                    return weight
                        
                        # 同じセル内に数値がある場合
                        match = re.search(r'[\d.]+', cell_text)
                        if match:
                            weight = float(match.group())
                            if 200 <= weight <= 600:
                                return weight
            
            # ページ全体から正規表現で検索
            page_text = soup.get_text()
            weight_matches = re.findall(r'馬体重\s*[：:]*\s*([\d.]+)[\s㎏kg]?', page_text, re.IGNORECASE)
            if weight_matches:
                weight = float(weight_matches[-1])
                if 200 <= weight <= 600:
                    return weight
                    
            # 単純な体重表記を検索
            weight_matches = re.findall(r'(?:体重|weight)[：:]*\s*([\d.]+)[\s㎏kg]?', page_text, re.IGNORECASE)
            if weight_matches:
                weight = float(weight_matches[-1])
                if 200 <= weight <= 600:
                    return weight
            
            # 数値のみで、妥当な範囲のものを検索（最終手段）
            weight_matches = re.findall(r'\b([3-5]\d{2}|[4-5]\d{2}\.\d)\b', page_text)
            if weight_matches:
                # 中央値を使用（外れ値の影響を減らすため）
                weights = sorted([float(w) for w in weight_matches])
                median_weight = weights[len(weights)//2]
                if 300 <= median_weight <= 550:  # より厳密な範囲
                    return median_weight
                        
        except Exception as e:
            logger.warning(f"馬体重の抽出に失敗: {e}")
            
        return 0.0
    
    def _extract_comment(self, soup: BeautifulSoup) -> str:
        """コメントを抽出する"""
        try:
            # 「本馬について」セクションを探す
            comment_section = None
            for elem in soup.find_all(['div', 'section', 'article']):
                if '本馬について' in elem.get_text():
                    comment_section = elem
                    break
            
            if comment_section:
                # <hr>タグ以降を取得
                hr = comment_section.find('hr')
                if hr:
                    comment = ''
                    # <hr>以降の兄弟要素を取得
                    for sibling in hr.find_next_siblings():
                        comment += sibling.get_text(' ', strip=True) + '\n'
                    if comment.strip():
                        return comment.strip()
                
                # <hr>がない場合はセクション全体を取得
                comment_text = comment_section.get_text(' ', strip=True)
                # 「本馬について」のテキストを除去
                comment_text = re.sub(r'^[^\n]*本馬について[^\n]*\n?', '', comment_text, flags=re.MULTILINE)
                if comment_text.strip():
                    return comment_text.strip()
            
            # コメントセクションが見つからない場合、全体から長いテキストを探す
            longest_text = ''
            for elem in soup.find_all(['div', 'p', 'section', 'article']):
                text = elem.get_text(' ', strip=True)
                if len(text) > len(longest_text) and len(text) > 100:  # 100文字以上の長いテキスト
                    longest_text = text
            
            if longest_text:
                # 不要なテキストを除去
                longest_text = re.sub(r'\s+', ' ', longest_text)  # 連続する空白を1つに
                return longest_text.strip()
                
        except Exception as e:
            logger.warning(f"コメントの抽出に失敗: {e}")
            
        return ""


def main():
    """メイン関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='デバッグ用馬情報抽出スクリプト')
    parser.add_argument('url', help='抽出する馬の詳細ページURL')
    parser.add_argument('--output', '-o', help='結果を保存するJSONファイルのパス')
    args = parser.parse_args()
    
    # 抽出器の作成
    extractor = DebugHorseExtractor()
    
    # 馬情報を抽出
    horse_info = extractor.extract_horse_info(args.url)
    
    # 結果を表示
    print("\n=== 抽出結果 ===")
    print(json.dumps(horse_info, ensure_ascii=False, indent=2))
    
    # ファイルに保存
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(horse_info, f, ensure_ascii=False, indent=2)
        print(f"\n結果を {args.output} に保存しました")


if __name__ == "__main__":
    main()
