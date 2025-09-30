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

from scripts.components.horse_info_extractor import HorseInfoExtractor

class DebugHorseExtractor(HorseInfoExtractor):
    """デバッグ用の馬情報抽出クラス
    
    本番環境のスクレイピングロジックを模倣しつつ、
    デバッグ用の機能を追加したクラス
    """
    
    def __init__(self, test_mode: bool = True, logger: Optional[logging.Logger] = None):
        """初期化
        
        Args:
            test_mode: テストモードかどうか
            logger: ロガーインスタンス（指定がない場合は新規作成）
        """
        super().__init__(logger=logger or logging.getLogger(__name__))
        self.test_mode = test_mode
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept-Language': 'ja,en-US;q=0.9,en;q=0.8,',
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
        self.logger.info(f"馬情報の抽出を開始: {url}")
        
        # ページを取得
        html = self.fetch_page(url)
        if not html:
            return {}
            
        soup = BeautifulSoup(html, 'html.parser')
        
        # 基本情報を抽出（親クラスのextractメソッドを利用）
        horse_info, missing_fields = self.extract(soup)
        
        # 追加情報を抽出
        horse_info.update({
            'url': url,
            'sire': self._extract_sire(soup),
            'dam': self._extract_dam(soup),
            'damsire': self._extract_damsire(soup),
            'seller': self._extract_seller(soup),
            'auction_date': self._extract_auction_date(soup),
            'weight': self._extract_weight(soup),
            'comment': self._extract_comment(soup),
            'extracted_at': datetime.now().isoformat(),
        })
        
        return horse_info
    
    def _extract_name(self, horse_element) -> str:
        """
        馬名を抽出する（デバッグ用に拡張）
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            str: 抽出された馬名。抽出に失敗した場合は空文字列
        """
        # まずは親クラスの実装を試す
        name = super()._extract_name(horse_element)
        if name:
            return name
            
        # 親クラスで抽出できない場合、デバッグ用の追加ロジックを実行
        try:
            # タイトルタグから抽出を試みる（多くの場合、馬名が含まれている）
            title = horse_element.title.string if hasattr(horse_element, 'title') and horse_element.title else ""
            if not title and hasattr(horse_element, 'select_one') and horse_element.select_one('title'):
                title = horse_element.select_one('title').string or ""
                
            if title:
                # タイトルから馬名を抽出（「馬名 | サイト名」の形式を想定）
                name_match = re.search(r'^([^|\n\r\t]+?)(?:\s*[|\-]\s*|\s+の血統情報|\s+のプロフィール|\s+の情報|\s*$)', title)
                if name_match:
                    name = name_match.group(1).strip()
                    if name and len(name) > 1:
                        self.logger.debug(f'タイトルから馬名を抽出しました: {name}')
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
                    name_elems = horse_element.select(selector)
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
                except Exception as e:
                    self.logger.warning(f'馬名の抽出中にエラーが発生しました: {str(e)}')
                    continue
            
            # テーブルから探す（馬名が含まれている可能性のあるテーブルを検索）
            for table in horse_element.select('table'):
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
            for bold in horse_element.select('b, strong'):
                try:
                    name = bold.get_text(strip=True)
                    if (len(name) > 1 and 
                        not name.isdigit() and 
                        re.match(r'^[\w\s・（）()\-〜&]+$', name)):
                        return name
                except Exception as e:
                    self.logger.warning(f'太字からの馬名抽出中にエラーが発生しました: {str(e)}')
                    continue
            
            # 最終手段：ページ内で最も長いテキストノードを探す（馬名は通常、ページ内で目立つ）
            def get_text_nodes(element):
                try:
                    for child in element.descendants:
                        if isinstance(child, str) and child.strip():
                            text = child.strip()
                            if (len(text) > 1 and 
                                not text.isdigit() and 
                                re.match(r'^[\w\s・（）()\-〜&]+$', text)):
                                yield text
                except Exception as e:
                    self.logger.warning(f'テキストノードの取得中にエラーが発生しました: {str(e)}')
            
            # 長さでソートして最長のものを返す
            try:
                text_nodes = list(get_text_nodes(horse_element))
                if text_nodes:
                    return max(text_nodes, key=len)
            except Exception as e:
                self.logger.warning(f'最長テキストノードの取得中にエラーが発生しました: {str(e)}')
                        
        except Exception as e:
            self.logger.warning(f'馬名の抽出中にエラーが発生しました: {str(e)}')
            
        # 最終手段: ページの最初のh1タグを取得
        try:
            h1 = horse_element.find('h1')
            if h1:
                name = h1.get_text(strip=True)[:50]  # 50文字で切り詰め
                if name:
                    return name
        except Exception as e:
            self.logger.warning(f'h1タグからの馬名抽出中にエラーが発生しました: {str(e)}')
            
        return ""
    
    def _extract_sex(self, horse_element: BeautifulSoup) -> str:
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
                    elements = horse_element.select(selector)
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
            for table in horse_element.select('table'):
                try:
                    rows = table.select('tr')
                    for row in rows:
                        cells = row.select('th, td')
                        for i, cell in enumerate(cells):
                            try:
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
                            except Exception as e:
                                self.logger.debug(f"テーブルセルの処理中にエラー: {e}")
                                continue
                except Exception as e:
                    self.logger.debug(f"テーブルの処理中にエラー: {e}")
                    continue
            
            # 3. ページ全体から正規表現で検索
            try:
                page_text = horse_element.get_text(" ", strip=True)
                for pattern in sex_patterns:
                    matches = re.finditer(pattern, page_text, re.IGNORECASE)
                    for match in matches:
                        if match.groups():
                            sex = match.group(1).strip()
                            normalized_sex = self._normalize_sex(sex)
                            if normalized_sex:
                                return normalized_sex
            except Exception as e:
                self.logger.debug(f"ページテキストからの性別抽出中にエラー: {e}")
            
            # 4. コメントからも探してみる
            try:
                comment = self._extract_comment(horse_element)
                if comment:
                    for pattern in sex_patterns:
                        match = re.search(pattern, comment, re.IGNORECASE)
                        if match and match.groups():
                            sex = match.group(1).strip()
                            normalized_sex = self._normalize_sex(sex)
                            if normalized_sex:
                                return normalized_sex
            except Exception as e:
                self.logger.debug(f"コメントからの性別抽出中にエラー: {e}")
                        
        except Exception as e:
            self.logger.warning(f"性別の抽出中にエラーが発生しました: {e}")
            
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
        return 'セ'
        
        # 3. ページ全体から正規表現で検索
        try:
            page_text = horse_element.get_text(" ", strip=True)
            
            # パターン1: 「年齢: 3歳」のような形式
            age_matches = re.findall(r'(?:年齢|歳|才|age)[:：]?\s*(\d+\s*[歳才]?)', page_text, re.IGNORECASE)
            if age_matches:
                age = self._extract_age_from_text(age_matches[0])
                if age is not None:
                    self.logger.debug(f'年齢を抽出しました: {age}歳')
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
            
            return 0  # 年齢が抽出できなかった場合は0を返す
                    
        except Exception as e:
            self.logger.warning(f'年齢の抽出中にエラーが発生しました: {str(e)}')
            return 0
            
        try:
            # 体重を抽出するセレクタ
            weight_selectors = ['.weight', '.horse-weight', '.wt', '.weight-value']
            for selector in weight_selectors:
                weight_elems = horse_element.select(selector)
                for weight_elem in weight_elems:
                    weight_text = weight_elem.get_text(strip=True)
                    try:
                        # 数字部分を抽出（「500kg」や「500.0kg」などに対応）
                        match = re.search(r'([\d.]+)\s*[㎏kg]?', weight_text)
                        if match:
                            weight = float(match.group(1))
                            if 200 <= weight <= 600:  # 妥当な馬の体重範囲
                                self.logger.debug(f'馬体重を抽出しました: {weight}kg')
                                return weight
                    except (ValueError, IndexError) as e:
                        self.logger.warning(f'体重の抽出に失敗しました: {str(e)}')
                        continue
                
                # ページ全体から正規表現で検索
                page_text = horse_element.get_text()
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
            self.logger.warning(f"馬体重の抽出に失敗: {e}")
            
        return 0.0
    
    def _extract_comment(self, horse_element) -> str:
        """コメントを抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            str: 抽出されたコメント。抽出に失敗した場合は空文字列
        """
        try:
            # まずは親クラスの実装を試す（もしあれば）
            if hasattr(super(), '_extract_comment'):
                comment = super()._extract_comment(horse_element)
                if comment:
                    return comment
                    
            # 親クラスに実装がないか、抽出できなかった場合の独自ロジック
            # 「本馬について」セクションを探す
            comment_section = None
            for elem in horse_element.find_all(['div', 'section', 'article']):
                if '本馬について' in elem.get_text():
                    comment_section = elem
                    break
            
            if comment_section:
                # <hr>タグ以降を取得
                hr = comment_section.find('hr')
                if hr:
                    comment = ''
                    # <hr>以降の兄弟要素を取得
                    comment_parts = []
                    for sibling in hr.next_siblings:
                        if sibling.name == 'hr':
                            break
                        if hasattr(sibling, 'get_text'):
                            comment_parts.append(sibling.get_text(strip=True))
                        else:
                            comment_parts.append(str(sibling).strip())
                
                    # コメントを結合して返す
                    comment = '\n'.join(part for part in comment_parts if part)
                    self.logger.debug(f'コメントを抽出しました: {comment[:100]}...')
                    return comment
                
                # <hr>がない場合はセクション全体を取得
                comment_text = comment_section.get_text(' ', strip=True)
                # 「本馬について」のテキストを除去
                comment_text = re.sub(r'^[^\n]*本馬について[^\n]*\n?', '', comment_text, flags=re.MULTILINE)
                if comment_text.strip():
                    return comment_text.strip()
            
            # コメントセクションが見つからない場合、全体から長いテキストを探す
            longest_text = ''
            for elem in horse_element.find_all(['div', 'p', 'section', 'article']):
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
