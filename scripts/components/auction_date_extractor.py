"""
Auction Date Extractor Module

This module provides functionality to extract auction dates from auction pages.
"""
import logging
import re
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

class AuctionDateExtractor:
    """
    A class to handle extraction of auction dates from auction pages.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the AuctionDateExtractor.
        
        Args:
            logger: Optional logger instance. If not provided, a new one will be created.
        """
        self.logger = logger or logging.getLogger(__name__)
        
        # 日付の優先度を決定するためのキーワード
        self.date_keywords = [
            'オークション', 'auction', '出品日', '開催日', 'date', 'sale', 'bid',
            '入札', '開始', '終了', '期間', '締切', '期限'
        ]
        
        # 無視するキーワード（これらの単語が含まれる場合は優先度を下げる）
        self.ignore_keywords = [
            '生年月日', '誕生日', 'birth', '年齢', '更新日', '作成日', 'modified',
            'created', 'update', 'published', '公開日', '最終更新', 'last update'
        ]
    
    def extract_from_html(self, html_content: str) -> Optional[str]:
        """
        Extract auction date from HTML content with improved pattern matching.
        
        Args:
            html_content: The HTML content of the auction page
            
        Returns:
            str: The extracted auction date in YYYY-MM-DD format, or None if not found
        """
        try:
            self.logger.info("オークション日付の抽出を開始します")
            self.logger.debug(f"HTMLサイズ: {len(html_content)} バイト")
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # デバッグ用にHTMLの一部をログに出力
            self.logger.debug(f"HTMLの先頭500文字: {str(soup)[:500]}...")
            
            # 0. 楽天詳細ページの開始時間ブロックを最優先で確認
            try:
                start_time_el = soup.select_one('.subData__startTime .subData__value')
                if start_time_el:
                    text = start_time_el.get_text(strip=True)
                    m = re.search(r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日', text)
                    if m:
                        y, mo, d = m.groups()
                        date_str = f"{y}-{mo.zfill(2)}-{d.zfill(2)}"
                        self.logger.info(f"Found auction start date from startTime block: {date_str}")
                        return date_str
            except Exception as e:
                self.logger.debug(f"Start time block parse error: {e}")
            
            # シンプルな全体テキストからの日本語日付パターン（早期フォールバック）
            try:
                text_all = soup.get_text(' ', strip=True)
                m_simple = re.search(r'(\d{4})年\s*(\d{1,2})月\s*(\d{1,2})日', text_all)
                if m_simple:
                    y, mo, d = m_simple.groups()
                    date_str = f"{y}-{str(mo).zfill(2)}-{str(d).zfill(2)}"
                    self.logger.info(f"Found auction date from simple page-wide JP pattern: {date_str}")
                    return date_str
            except Exception as e:
                self.logger.debug(f"Simple JP date fallback parse error: {e}")

            # 1. まずはオークション情報が含まれている可能性の高いセクションを特定
            possible_sections = []
            
            # より具体的なセレクタを優先的にチェック
            priority_selectors = [
                'div.auction-info', 'div.item-info', 'div.product-info',
                'div.item-details', 'div.auction-details', 'div.auction-header',
                'div.product-details', 'div.lot-info', 'div.auction-lot',
                'div.auction-item', 'div.sale-info', 'div.lot-details',
                'table.auction', 'table.schedule', 'div.schedule',
                'div.date', 'span.date', 'time', 'div.auction-date',
                'div.auction-schedule', 'p.date', 'div.info', 'div.detail',
                'div.auction-time', 'div.auction-period', 'div.period',
                'div.auctionTableCard__date', 'div.auctionTableCard__time',
                'div.auctionTableCard__period', 'div.auctionTableCard__schedule'
            ]
            
            # メタタグからも日付を探す
            meta_selectors = [
                'meta[property="og:updated_time"]',
                'meta[property="article:published_time"]',
                'meta[property="article:modified_time"]',
                'meta[name="pubdate"]',
                'meta[name="date"]',
                'meta[itemprop="datePublished"]',
                'meta[itemprop="dateModified"]',
                'time[datetime]',
                'meta[property="og:start_time"]',
                'meta[property="og:end_time"]'
            ]
            
            # 1.1 メタタグから日付を探す
            for selector in meta_selectors:
                for meta in soup.select(selector):
                    date_str = meta.get('content') or meta.get('datetime') or meta.get('value') or ''
                    if date_str:
                        # ISO形式の日付を抽出
                        date_match = re.search(r'(\d{4}[-/]\d{1,2}[-/]\d{1,2})', date_str)
                        if date_match:
                            try:
                                date_obj = datetime.strptime(date_match.group(1), '%Y-%m-%d')
                                self.logger.info(f"Found date in meta tag {selector}: {date_obj.strftime('%Y-%m-%d')}")
                                return date_obj.strftime('%Y-%m-%d')
                            except ValueError:
                                continue
            
            # 1.2 優先セレクタからセクションを収集
            for selector in priority_selectors:
                sections = soup.select(selector)
                if sections:
                    possible_sections.extend(sections)
                    self.logger.debug(f"Found section with selector: {selector}")
            
            # 1.3 見つからなかった場合は、テーブルやリスト、セクション全体を対象にする
            if not possible_sections:
                self.logger.debug("No specific sections found, checking tables, lists, and sections...")
                possible_sections = soup.find_all(['table', 'ul', 'ol', 'div', 'section', 'article'])
            
            # 2. 各セクション内で日付を探す
            date_candidates = []
            
            # 日付パターンの正規表現（オークション日付に特化して拡張）
            date_patterns = [
                # 特殊文字（﷐や﷯）を含むパターン（優先度: 最高）
                r'[﷐\s]*(\d{4}年\d{1,2}月\d{1,2}日\s+\d{1,2}:\d{2})[﷯\s]*',
                
                # オークション日付に特化したパターン（優先度: 高）
                r'(?:オークション|入札|開催|セール|開催日)[:：]?\s*([\d/\-年月日RHSMT\. 曜日]+)',
                r'(?:auction|sale|date)[:：]?\s*([\d/\-年月日RHSMT\. 曜日]+)',
                
                # 日付の形式（優先度: 中）
                # YYYY/MM/DD 形式（スラッシュ区切り）
                r'(\d{4})/(\d{1,2})/(\d{1,2})',
                # YYYY-MM-DD 形式（ハイフン区切り）
                r'(\d{4})-(\d{1,2})-(\d{1,2})',
                # YYYY年M月D日形式
                r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日?',
                # 日本語の完全な日付表現（例：2023年12月31日）
                r'(\d{4})年(\d{1,2})月(\d{1,2})日',
                # 和暦の日付表現（例：令和5年12月31日）
                r'([令和|平成|昭和|大正|明治]\d*)年(\d{1,2})月(\d{1,2})日',
                # 略記の和暦（例：R5.12.31）
                r'([RHSMT]\d*)\.(\d{1,2})\.(\d{1,2})',
                # 英語の月名（例：December 31, 2023）
                r'(?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec)[a-z]*\s+\d{1,2},?\s*\d{4}',
                # 日本語の曜日を含むパターン（例：2023年12月31日（日））
                r'(\d{4})[年/](\d{1,2})[月/](\d{1,2})日\s*[（(](?:月|火|水|木|金|土|日)[)）]',
                # 範囲指定の日付（例：2023/12/31-2024/01/05）
                r'(\d{4}/\d{1,2}/\d{1,2})\s*[〜~-]\s*(\d{4}/\d{1,2}/\d{1,2})',
                # タイムスタンプ（例：2023-12-31 15:30:00）
                r'(\d{4}-\d{1,2}-\d{1,2})\s+\d{1,2}:\d{2}(?::\d{2})?',
                # その他の一般的な日付形式（優先度: 低）
                r'(\d{1,2})/(\d{1,2})/(\d{4})',  # MM/DD/YYYY
                r'(\d{1,2})-(\d{1,2})-(\d{4})'   # DD-MM-YYYY
            ]
            
            for section in possible_sections[:30]:  # 最初の30セクションに制限
                try:
                    # セクション内のテキストを取得
                    section_text = section.get_text(' ', strip=True)
                    
                    # オークションに関連するキーワードが含まれているか確認（より多くのキーワードを追加）
                    has_auction_keyword = any(
                        keyword in section_text.lower() 
                        for keyword in self.date_keywords
                    )
                    
                    # 無視するキーワードが含まれている場合はスキップ
                    has_ignore_keyword = any(
                        keyword in section_text.lower()
                        for keyword in self.ignore_keywords
                    )
                    
                    if has_ignore_keyword:
                        continue
                    
                    # 複数の日付パターンでマッチングを試みる
                    for pattern in date_patterns:
                        date_matches = list(re.finditer(pattern, section_text))
                        
                        for match in date_matches:
                            # マッチ結果からできるだけ完全な日付文字列を構築
                            if len(match.groups()) >= 3 and all(g is not None for g in match.groups()[:3]):
                                y, mo, d = match.groups()[:3]
                                # 取り出した値が数字で構成されていることを確認
                                if not (str(y).strip().isdigit() and str(mo).strip().isdigit() and str(d).strip().isdigit()):
                                    continue
                                date_str = f"{y}年{mo}月{d}日"
                            elif len(match.groups()) >= 1 and match.group(1):
                                candidate = match.group(1)
                                # 少なくとも1つ数字が含まれていないものは除外
                                if not re.search(r'\d', candidate):
                                    continue
                                date_str = candidate
                            else:
                                candidate = match.group(0)
                                if not re.search(r'\d', candidate):
                                    continue
                                date_str = candidate
                            # 特殊文字（﷐や﷯）と空白を除去
                            date_str = re.sub(r'[\s﷐﷯]', '', date_str)
                            
                            # コンテキストを取得（前後50文字）
                            start = max(0, match.start() - 50)
                            end = min(len(section_text), match.end() + 50)
                            context = section_text[start:end]
                            
                            # 優先度の基本値を設定（パターンに基づいて重み付け）
                            base_priority = 0
                            # オークション関連のキーワードが含まれるパターンは優先度を上げる
                            if any(keyword in pattern for keyword in ['オークション', 'auction', 'sale', '開催']):
                                base_priority = 20
                            
                            # 優先度を計算
                            priority = base_priority + self._get_date_priority(date_str, context)
                            
                            # 同じ日付が既に登録されていないかチェック
                            existing = next((d for d in date_candidates if d['date_str'] == date_str), None)
                            if existing:
                                # 既存の候補より優先度が高い場合のみ更新
                                if priority > existing['priority']:
                                    existing['priority'] = priority
                                    existing['context'] = context
                                    existing['element'] = str(section)[:200] + '...'
                                continue
                                    
                            # 候補に追加
                            date_candidates.append({
                                'date_str': date_str,
                                'context': context,
                                'has_auction_keyword': has_auction_keyword,
                                'priority': priority,
                                'element': str(section)[:200] + '...'  # デバッグ用
                            })
                            
                            self.logger.debug(f"Found date candidate: {date_str} (priority: {priority}) in context: {context}")
                            
                except Exception as e:
                    self.logger.debug(f"Error processing section: {e}")
                    continue
            
            # 3. 候補から最適な日付を選択
            if not date_candidates:
                self.logger.warning("No date candidates found in specific sections, trying full page search...")
                
                # 最終手段: ページ全体から日付を探す
                all_text = soup.get_text(' ', strip=True)
                
                for pattern in date_patterns:
                    date_matches = list(re.finditer(pattern, all_text))
                    
                    for match in date_matches[:10]:  # 最初の10件のみ確認
                        if len(match.groups()) >= 3 and all(g is not None for g in match.groups()[:3]):
                            y, mo, d = match.groups()[:3]
                            if not (str(y).strip().isdigit() and str(mo).strip().isdigit() and str(d).strip().isdigit()):
                                continue
                            date_str = f"{y}年{mo}月{d}日"
                        elif len(match.groups()) >= 1 and match.group(1):
                            candidate = match.group(1)
                            if not re.search(r'\d', candidate):
                                continue
                            date_str = candidate
                        else:
                            candidate = match.group(0)
                            if not re.search(r'\d', candidate):
                                continue
                            date_str = candidate
                        start = max(0, match.start() - 50)
                        end = min(len(all_text), match.end() + 50)
                        context = all_text[start:end]
                        
                        # 無視するキーワードが含まれている場合はスキップ
                        if any(keyword in context.lower() for keyword in self.ignore_keywords):
                            continue
                            
                        # 優先度を計算（フルテキスト検索は優先度を下げる）
                        has_auction_keyword = any(
                            keyword in context.lower() 
                            for keyword in self.date_keywords
                        )
                        priority = self._get_date_priority(date_str, context) - 10
                        
                        date_candidates.append({
                            'date_str': date_str,
                            'context': context,
                            'has_auction_keyword': has_auction_keyword,
                            'priority': priority,
                            'element': "Full page search"
                        })
                        
                        self.logger.debug(f"Found fallback date: {date_str} (priority: {priority}) in context: {context}")
            
            if date_candidates:
                # 優先度でソート（降順）
                date_candidates.sort(key=lambda x: x['priority'], reverse=True)
                
                # 上位3つの候補をログに出力
                for i, candidate in enumerate(date_candidates[:3], 1):
                    self.logger.debug(f"Top {i} candidate: {candidate['date_str']} (priority: {candidate['priority']})")
                
                # 最適な候補を選択
                best_candidate = date_candidates[0]
                date_str = best_candidate['date_str']
                
                self.logger.info(f"Selected date: {date_str} (priority: {best_candidate['priority']})")
                self.logger.debug(f"Context: {best_candidate['context']}")
                
                # 日付文字列をクリーニングしてフォーマット
                formatted_date = self._clean_and_format_date(date_str)
                if formatted_date:
                    return formatted_date
                
                # フォーマットに失敗した場合、生の日付文字列を返す
                return date_str
            
            # 4. 日付要素が見つからなかった場合のデバッグ情報
            self.logger.debug("No date element found in the HTML content.")
            
            # 5. タイトルや見出しから日付を探す（最終手段）
            title = soup.find('title')
            if title:
                self.logger.debug(f"Page title: {title.text}")
                # タイトルから日付らしきものを探す
                for pattern in date_patterns:
                    date_match = re.search(pattern, title.text)
                    if date_match:
                        date_str = date_match.group(0)
                        self.logger.info(f"Found date in title: {date_str}")
                        formatted_date = self._clean_and_format_date(date_str)
                        if formatted_date:
                            return formatted_date
                        return date_str
            
            self.logger.warning("Could not find any valid date in the page")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting auction date: {e}", exc_info=True)
            return None
    
    def get_auction_date(self, html_content: str) -> Optional[str]:
        """
        Alias for extract_from_html for backward compatibility.
        """
        return self.extract_from_html(html_content)

    def _get_date_priority(self, date_text: str, context: str) -> int:
        """
        日付候補の優先度を計算する
        
        Args:
            date_text: 日付文字列
            context: 日付が含まれるコンテキスト（親要素のテキストなど）
            
        Returns:
            int: 優先度（高いほど優先）
        """
        priority = 0
        context_lower = context.lower()
        date_text_lower = date_text.lower()
        
        # 1. コンテキストに基づく優先度
        # オークション関連キーワード
        auction_keywords = {
            'オークション': 20,
            'auction': 20,
            '開催日': 25,
            '開催期間': 20,
            '入札期間': 25,
            '入札日': 25,
            '終了日': 20,
            '終了時刻': 15,
            '開始日': 20,
            '開始時刻': 15,
            '期間': 10,
            'date': 10,
            'sale': 10,
            'bid': 10,
            '締切': 20,
            '期限': 15,
            '〜': 5,
            '~': 5,
            'から': 5,
            'まで': 5,
            'from': 5,
            'to': 5
        }
        
        # 無視するキーワード
        ignore_keywords = {
            '生年月日': -30,
            '誕生日': -30,
            'birth': -30,
            '年齢': -30,
            'age': -30,
            '更新日': -20,
            '作成日': -20,
            'modified': -20,
            'created': -20,
            'update': -20,
            'published': -15,
            '公開日': -15,
            '最終更新': -20,
            'last update': -20,
            'update': -20,
            'copyright': -10
        }
        
        # キーワードに基づく優先度調整
        for keyword, score in auction_keywords.items():
            if keyword in context_lower:
                priority += score
                self.logger.debug(f"Priority +{score} for keyword: {keyword}")
        
        # 無視キーワードによる優先度調整
        for keyword, penalty in ignore_keywords.items():
            if keyword in context_lower or keyword in date_text_lower:
                priority += penalty
                self.logger.debug(f"Priority {penalty} for ignore keyword: {keyword}")
        
        # 2. 日付形式に基づく優先度
        # 完全な日付（年月日）
        if re.search(r'\d{4}[年/-]\d{1,2}[月/-]\d{1,2}', date_text):
            priority += 15
            self.logger.debug("Priority +15 for full date format")
        # 年月のみ
        elif re.search(r'\d{4}[年/-]\d{1,2}', date_text):
            priority += 10
            self.logger.debug("Priority +10 for year-month format")
        # 年のみ
        elif re.search(r'^\d{4}$', date_text):
            priority -= 5
            self.logger.debug("Priority -5 for year only")
        
        # 3. 時刻情報が含まれる場合
        if re.search(r'\d{1,2}:\d{2}', date_text):
            priority += 10
            self.logger.debug("Priority +10 for time information")
        
        # 4. 日付の範囲を表す記号が含まれる場合
        if any(sep in date_text for sep in ['〜', '~', '-', 'から', 'to']):
            priority += 5
            self.logger.debug("Priority +5 for date range")
        
        # 5. 日付が未来の日付かどうか（オークションは未来の日付であることが多い）
        try:
            clean_date = self._clean_and_format_date(date_text)
            if clean_date:
                date_obj = datetime.strptime(clean_date, '%Y-%m-%d')
                today = datetime.now()
                if date_obj > today:
                    priority += 20
                    self.logger.debug("Priority +20 for future date")
        except Exception as e:
            self.logger.debug(f"Error checking future date: {e}")
        
        self.logger.debug(f"Final priority for date '{date_text}': {priority}")
        return priority
    
    def _clean_and_format_date(self, date_str: str) -> Optional[str]:
        """
        日付文字列をクリーニングして標準フォーマットに変換する
        
        Args:
            date_str: クリーニング前の日付文字列
            
        Returns:
            Optional[str]: フォーマットされた日付文字列（YYYY-MM-DD）、失敗時はNone
        """
        if not date_str or not isinstance(date_str, str):
            return None
            
        try:
            # 不要な空白を削除
            date_str = re.sub(r'\s+', ' ', date_str).strip()
            
            # 日付の前後の不要な文字を削除（英数字、スラッシュ、ハイフン、ドット、日本語の年月日以外）
            date_str = re.sub(r'^[^\d\-/\.年月日]*', '', date_str)
            date_str = re.sub(r'[^\d\-/\.年月日]*$', '', date_str)
            
            # 日本語表記をスラッシュ区切りに統一
            date_str = date_str.replace('年', '/').replace('月', '/').replace('日', '')
            
            # ドットやハイフンをスラッシュに統一
            date_str = date_str.replace('.', '/').replace('-', '/')
            
            # スラッシュが連続している場合は1つにまとめる
            date_str = re.sub(r'[/]+', '/', date_str)
            
            # 先頭と末尾のスラッシュを削除
            date_str = date_str.strip('/')
            
            # 日付のフォーマットを試す
            date_formats = [
                '%Y/%m/%d',    # 2023/12/31
                '%Y/%m',       # 2023/12
                '%Y%m%d',      # 20231231
                '%Y%m',        # 202312
                '%d/%m/%Y',    # 31/12/2023
                '%m/%d/%Y',    # 12/31/2023
                '%Y-%m-%d',    # 2023-12-31
                '%Y',          # 2023
            ]
            
            for date_format in date_formats:
                try:
                    date_obj = datetime.strptime(date_str, date_format)
                    # 年が1900年より前の場合は無効
                    if date_obj.year < 1900 or date_obj.year > 2100:
                        continue
                    # 月が1-12の範囲外の場合は無効
                    if date_obj.month < 1 or date_obj.month > 12:
                        continue
                    # 日が1-31の範囲外の場合は無効
                    if hasattr(date_obj, 'day') and (date_obj.day < 1 or date_obj.day > 31):
                        continue
                    
                    # フォーマットに応じて返す
                    if '%d' in date_format and '%m' in date_format and '%Y' in date_format:
                        return date_obj.strftime('%Y-%m-%d')
                    elif '%m' in date_format and '%Y' in date_format:
                        return date_obj.strftime('%Y-%m-01')
                    elif '%Y' in date_format:
                        return date_obj.strftime('%Y-01-01')
                        
                except ValueError:
                    continue
            
            self.logger.warning(f"Failed to parse date string: {date_str}")
            return None
            
        except Exception as e:
            self.logger.warning(f"Error cleaning date string '{date_str}': {e}")
            return None  # エラーが発生した場合は元の文字列を返す

# For backward compatibility
get_auction_date = AuctionDateExtractor().get_auction_date
