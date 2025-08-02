#!/usr/bin/env python3
"""
改善されたスクレイピングスクリプト
seleniumを使わずにrequestsとBeautifulSoupで実装
正しいデータ抽出ロジックを含む
"""

import os
import sys
import requests
from bs4 import BeautifulSoup
import re
import json
import time
import uuid
import logging
from typing import List, Dict, Optional, Any, Tuple
from datetime import datetime
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry
from tqdm import tqdm

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# バックエンドのモジュールをインポート
from backend.scrapers.data_helpers import (
    save_horse,
    save_auction_history,
    load_json_file
)

class ImprovedRakutenScraper:
    def __init__(self, timeout=30, max_retries=3, backoff_factor=1):
        self.base_url = "https://auction.keiba.rakuten.co.jp/"
        self.timeout = timeout
        
        # セッションの初期化
        self.session = requests.Session()
        
        # リトライ設定
        retry_strategy = Retry(
            total=max_retries,
            backoff_factor=backoff_factor,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET", "POST"]
        )
        
        # アダプタの設定
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # ヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Accept-Encoding': 'gzip, deflate',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
        })
        
    def _make_request(self, url: str, method: str = 'GET', **kwargs) -> Optional[requests.Response]:
        """HTTPリクエストを送信する共通メソッド"""
        try:
            response = self.session.request(
                method=method,
                url=url,
                timeout=self.timeout,
                **kwargs
            )
            response.raise_for_status()
            return response
        except requests.exceptions.RequestException as e:
            logger.error(f"Request failed for {url}: {str(e)}")
            return None

    def get_auction_date(self) -> str:
        """ページから開催日を取得"""
        response = self._make_request(self.base_url)
        if not response:
            logger.warning("オークション日の取得に失敗しました。現在の日付を使用します。")
            return datetime.now().strftime("%Y-%m-%d")
        
        try:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # 開催日を探す（例: "2023年11月15日(水)"）
            date_pattern = r'\d{4}年\d{1,2}月\d{1,2}日\([月火水木金土日]\)'
            date_match = re.search(date_pattern, soup.get_text())
            
            if date_match:
                # 日付を"YYYY-MM-DD"形式に変換
                date_str = date_match.group()
                # 不要な文字を削除して日付オブジェクトに変換
                date_obj = datetime.strptime(re.sub(r'[\(\)]', '', date_str), '%Y年%m月%d日')
                return date_obj.strftime('%Y-%m-%d')
        except Exception as e:
            logger.error(f"オークション日の解析中にエラーが発生しました: {str(e)}")
            
        # 日付が見つからないかエラーが発生した場合は現在の日付を使用
        return datetime.now().strftime('%Y-%m-%d')

    def scrape_horse_list(self) -> List[Dict]:
        """トップページから馬のリストを取得"""
        logger.info("馬リストの取得を開始します...")
        horses = []
        
        response = self._make_request(self.base_url)
        if not response:
            logger.error("トップページの取得に失敗しました")
            return horses
            
        soup = BeautifulSoup(response.content, 'html.parser')
        
        # 馬のリンクを探す
        horse_links = []
        
        # すべてのリンクをチェック
        for link in soup.find_all('a', href=True):
            href = link.get('href')
            if href and '/item/' in href:
                link_text = link.get_text(strip=True)
                # 不要なリンクを除外
                if (link_text and len(link_text) > 1 and 
                    '詳細血統表' not in link_text and 
                    '血統表' not in link_text and
                    '詳細' not in link_text):
                    if not href.startswith('http'):
                        href = self.base_url + href.lstrip('/')
                    horse_links.append({
                        'text': link_text,
                        'url': href
                    })
        
        logger.info(f"馬のリンクを{len(horse_links)}個発見")
        
        if not horse_links:
            logger.warning("馬のリンクが見つかりませんでした")
            return horses
            
        # 進行状況表示用にtqdmを使用
        for link in tqdm(horse_links, desc="馬の詳細を取得中", unit="頭"):
            logger.debug(f"処理中: {link['text']} - {link['url']}")
            
            try:
                detail_data = self.scrape_horse_detail(link['url'])
                if detail_data and detail_data.get('name'):
                    # link['text']での上書きをやめ、scrape_horse_detailで取得した名前を使用
                    detail_data['detail_url'] = link['url']
                    horses.append(detail_data)
                    logger.debug(f"取得成功: {detail_data['name']}")
                else:
                    logger.warning(f"詳細データの取得に失敗: {link['url']}")
                
                # サーバーに優しくするために少し待機
                time.sleep(1)
                
            except Exception as e:
                logger.error(f"馬の詳細取得中にエラーが発生しました ({link['text']}): {str(e)}")
                continue
                
        logger.info(f"合計{len(horses)}頭の馬の情報を取得しました")
        return horses
    
    def scrape_horse_detail(self, detail_url: str) -> Optional[Dict]:
        """個別ページから詳細情報を取得"""
        try:
            response = self.session.get(detail_url)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            page_text = soup.get_text()
            
            detail_data = {}
            
            # 馬名、性別、年齢
            detail_data.update(self._extract_name_sex_age(page_text))
            
            # 落札価格（税込価格を取得）
            detail_data['sold_price'] = self._extract_sold_price(page_text)
            
            # 血統情報を抽出
            print("\n[デバッグ] 血統情報抽出を開始します...")
            pedigree_data = self._extract_pedigree(page_text)
            print(f"[デバッグ] 抽出された血統情報: {pedigree_data}")
            detail_data.update(pedigree_data)
            print(f"[デバッグ] 更新後のdetail_data: sire='{detail_data.get('sire')}', dam='{detail_data.get('dam')}', damsire='{detail_data.get('damsire')}'")
            
            # 馬体重
            detail_data['weight'] = self._extract_weight(page_text)
            
            # 成績
            detail_data['race_record'] = self._extract_race_record(page_text)
            
            # JBIS URLを取得
            jbis_url = self._extract_jbis_url(soup)
            
            # 獲得賞金（JBIS URLを渡して最新情報を取得）
            detail_data.update(self._extract_prize_money(page_text, jbis_url))
            
            # コメント
            detail_data['comment'] = self._extract_comment(page_text)
            
            # 疾病タグ
            detail_data['disease_tags'] = self._extract_disease_tags(detail_data.get('comment', ''))
            
            # 馬体画像
            detail_data['primary_image'] = self._extract_primary_image(soup)
            
            # 販売申込者
            detail_data['seller'] = self._extract_seller(page_text)
            
            # JBIS URLを抽出
            detail_data['jbis_url'] = self._extract_jbis_url(soup)
            
            return detail_data
            
        except Exception as e:
            print(f"詳細情報の取得に失敗: {e}")
            return None
    
    def _extract_name_sex_age(self, page_text: str) -> Dict:
        """馬名、性別、年齢を解析
        
        フォーマット例:
        - "アイドルフェスタ　　牝３歳　　※中央競馬　登録抹消"
        - "馬名　牡5歳　コメント"
        """
        result = {}
        
        # パターン: 馬名 + スペース + 性別 + 年齢 + "歳" + 任意の文字
        # 馬名にスペースや全角スペースが含まれる場合もマッチするように修正
        pattern = r'([^\n\r\t]+?)\s+([牡牝セ])\s*(\d+)歳'
        match = re.search(pattern, page_text)
        
        if match:
            # 馬名を正規化して保存
            result['name'] = self._clean_horse_name(match.group(1).strip())
            result['sex'] = match.group(2).strip()
            try:
                result['age'] = int(match.group(3).strip())
            except (ValueError, AttributeError) as e:
                raise ValueError(f"年齢の抽出に失敗しました: {e}")
        else:
            # デバッグ用: マッチしなかった場合のログ
            print(f"性別・年齢の抽出に失敗: {page_text[:100]}...")
            
            # 必須フィールドが取得できない場合はエラーを投げる
            if 'name' not in result:
                raise ValueError("馬名を抽出できませんでした")
            if 'sex' not in result:
                raise ValueError("性別を抽出できませんでした")
            if 'age' not in result:
                raise ValueError("年齢を抽出できませんでした")
        
        return result
    
    def _extract_sold_price(self, page_text: str) -> str:
        """落札価格を抽出（税込価格）"""
        # 現在価格の税込価格を取得（例: "2,000,000円(税込 2,200,000円)"）
        price_match = re.search(r'(\d{1,3}(?:,\d{3})*)円\(税込\s*(\d{1,3}(?:,\d{3})*)円\)', page_text)
        if price_match:
            # 税込価格を使用
            return price_match.group(2).replace(',', '')
        
        # フォールバック: 単純な税込価格パターン
        price_match = re.search(r'税込\s*(\d{1,3}(?:,\d{3})*)円', page_text)
        if price_match:
            return price_match.group(1).replace(',', '')
        
        return ''
    
    def _clean_horse_name(self, name: str) -> str:
        """
        馬名をクリーンアップするヘルパー関数
        
        Args:
            name: クリーンアップする馬名（「父：サクラバクシンオー 母：**」のような形式）
            
        Returns:
            クリーンアップされた馬名（省略なし）
        """
        if not name:
            return ''
            
        original_name = name
        
        # 1. 不要な接頭辞を削除（父：、母：、母父：など）
        name = re.sub(r'^\s*(父|母|母の?父|母父)[：:]?\s*', '', name, flags=re.IGNORECASE)
        
        # 2. 不要な文字や記号を削除（改行やタブはスペースに置換）
        name = re.sub(r'[\n\r\t]', ' ', name)
        
        # 3. 括弧内の情報を削除（例：「（牡1999）」など）
        name = re.sub(r'\s*[(（][^)）]*[)）]', '', name)
        
        # 4. 特殊文字や不要な記号を削除（「...」は削除しない）
        name = re.sub(r'[\*\#\@\!\?\|\/\\]', '', name)
        
        # 5. 先頭と末尾の空白を削除
        name = name.strip()
        
        # 6. 複数スペースを1つに置換
        name = re.sub(r'\s+', ' ', name)
        
        # 7. 元の名前に「...」が含まれていて、処理後に消えている場合は元に戻す
        if '...' in original_name and '...' not in name:
            name = original_name
        
        # デバッグ用に変更前後の名前を出力
        if name != original_name.strip():
            print(f"[デバッグ] 名前を正規化: '{original_name}' -> '{name}'")
            
        return name

    def _extract_pedigree(self, page_text: str) -> Dict:
        """血統情報を抽出・正規化
        
        Returns:
            Dict: 抽出した血統情報（sire, dam, damsire, dam_sire を含む）
        """
        result = {
            'sire': '',
            'dam': '',
            'damsire': '',
            'dam_sire': ''  # 互換性のため
        }
        
        try:
            # デバッグ用: ページテキストの関連部分を表示
            print(f"\n[デバッグ] 血統情報抽出開始 ===================")
            
            # 血統情報が含まれていそうな部分を抽出（「父：」から始まり「母の父：」までの間のテキスト）
            pedigree_section = re.search(r'父[：:].*?(?:母の?父|母父)[：:].*?[\n\r]', page_text, re.DOTALL)
            if pedigree_section:
                print(f"[デバッグ] 血統情報セクション: {pedigree_section.group(0)[:200]}...")
            else:
                print("[デバッグ] 血統情報セクションが見つかりませんでした")
            
            try:
                # 血統情報を抽出するためのパターン
                # 1. まず「父：XXX 母：YYY 母の父：ZZZ」の形式で一度に抽出を試みる
                full_pattern = r'父[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*母[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*(?:母の?父|母父)[：:]([^\n\r\s][^\n\r：:]*)'
                full_match = re.search(full_pattern, page_text)
                
                if full_match:
                    # 完全な形式でマッチした場合
                    result['sire'] = self._clean_horse_name(full_match.group(1).strip())
                    result['dam'] = self._clean_horse_name(full_match.group(2).strip())
                    result['damsire'] = self._clean_horse_name(full_match.group(3).strip())
                    print(f"[デバッグ] 完全な形式で血統情報を抽出: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
                else:
                    # 個別に抽出するパターン
                    patterns = [
                        # 父を抽出
                        (r'父[：:]([^\n\r\s][^\n\r：:]*)', 'sire'),
                        # 母を抽出
                        (r'母[：:]([^\n\r\s][^\n\r：:]*)', 'dam'),
                        # 母の父を抽出（「母の父：」または「母父：」の形式）
                        (r'(?:母の?父|母父)[：:]([^\n\r\s][^\n\r：:]*)', 'damsire')
                    ]
                    
                    for pattern, key in patterns:
                        match = re.search(pattern, page_text)
                        if match and not result.get(key):
                            result[key] = self._clean_horse_name(match.group(1).strip())
                            print(f"[デバッグ] {key} を抽出: {result[key]}")
                    
                    # 母の父がまだ見つからず、母が抽出できている場合は、母の情報から抽出を試みる
                    if not result.get('damsire') and result.get('dam'):
                        # 母の情報に「母の父」が含まれている場合（例：「母：ソリフロール 母の父」）
                        if '母の父' in result['dam']:
                            parts = result['dam'].split('母の父')
                            result['dam'] = self._clean_horse_name(parts[0].strip())
                            if len(parts) > 1:
                                result['damsire'] = self._clean_horse_name(parts[1].strip())
                                print(f"[デバッグ] 母の情報からdamsireを抽出: {result['damsire']}")
                        # 母の情報に「（母父：XXX）」が含まれている場合
                        elif '（母父：' in result['dam'] or '(母父：' in result['dam']:
                            dam_parts = re.split(r'[（(]母父[：:]', result['dam'])
                            if len(dam_parts) > 1:
                                result['dam'] = self._clean_horse_name(dam_parts[0].strip())
                                damsire_part = dam_parts[1].replace('）', '').replace(')', '').strip()
                                result['damsire'] = self._clean_horse_name(damsire_part)
                                print(f"[デバッグ] 母の情報からdamsireを抽出: {result['damsire']}")
            except Exception as e:
                print(f"[警告] 血統情報の抽出中にエラーが発生しました: {str(e)}")
            
            # 互換性のため dam_sire にも damsire と同じ値を設定
            if result['damsire'] and not result['dam_sire']:
                result['dam_sire'] = result['damsire']
            
            # 結果をログに出力
            print(f"[デバッグ] 抽出結果 - sire: '{result['sire']}'")
            print(f"[デバッグ] 抽出結果 - dam: '{result['dam']}'")
            print(f"[デバッグ] 抽出結果 - damsire: '{result['damsire']}'")
            
            # 必須フィールドの検証
            if not any([result['sire'], result['dam'], result['damsire']]):
                print("[警告] 血統情報を抽出できませんでした")
                print(f"[デバッグ] ページテキストの先頭500文字: {page_text[:500]}...")
            
            return result
            
        except Exception as e:
            print(f"[エラー] 血統情報の抽出中にエラーが発生しました: {str(e)}")
            return result
            
        # パターン2: 個別に抽出（フォールバック）
        patterns = {
            'sire': [
                r'父[：:]([^\n\r]+?)(?=\s*(?:母|$))',  # 母または行末まで
                r'父[：:]([^\n\r]+)'  # フォールバック
            ],
            'dam': [
                r'母[：:]([^\n\r]+?)(?=\s*(?:母の?父|母父|$))',  # 母の父または行末まで
                r'母[：:]([^\n\r]+)'  # フォールバック
            ],
            'damsire': [
                r'(?:母の?父|母父)[：:]([^\n\r]+?)(?=[\s\n\r]|$)',  # 空白か改行まで
                r'(?:母の?父|母父)[：:]([^\n\r]+)'  # フォールバック
            ]
        }
        
        # 各フィールドに対してパターンマッチングを試みる
        for field, pattern_list in patterns.items():
            for pattern in pattern_list:
                match = re.search(pattern, page_text, re.DOTALL)
                if match:
                    raw_value = match.group(1).strip()
                    value = self._clean_horse_name(raw_value)
                    if value:  # 空でないことを確認
                        result[field] = value
                        # dam_sire も damsire として設定（互換性のため）
                        if field == 'damsire':
                            result['dam_sire'] = value
                        print(f"[デバッグ] {field} を抽出: 生値='{raw_value}', 正規化後='{value}'")
                        break  # マッチしたら次のフィールドへ
        
        # damsireが見つからない場合のフォールバック
        if not result['damsire'] and (result['sire'] or result['dam']):
            print(f"[デバッグ] damsireが見つからないため、空文字を設定します")
            result['damsire'] = ''  # 空文字を設定
            result['dam_sire'] = ''  # 互換性のため
        
        print(f"[デバッグ] 最終的な血統情報: sire='{result['sire']}', dam='{result['dam']}', damsire='{result['damsire']}'")
        print("========================================")
        return result
    
    def _extract_weight(self, page_text: str) -> Optional[int]:
        """馬体重を抽出"""
        # "最終出走馬体重：XXXkg" を探す
        match = re.search(r'最終出走馬体重[：:]\s*(\d+)kg', page_text)
        if match:
            return int(match.group(1))
        return None
    
    def _extract_race_record(self, page_text: str) -> str:
        """成績を抽出"""
        # "通算成績：24戦4勝［4-6-2-12］" を探す
        match = re.search(r'通算成績[：:]\s*(\d+戦\d+勝［\d+-\d+-\d+-\d+］)', page_text)
        if match:
            return match.group(1).strip()
        return ""
    
    def _extract_jbis_prize_money(self, jbis_url: str) -> float:
        """JBISから現在の賞金情報を取得"""
        if not jbis_url:
            print("JBIS URLが指定されていないため、賞金情報を取得できません")
            return 0.0
            
        try:
            # JBISページにリクエスト
            response = self._make_request(jbis_url, method='GET')
            if not response or not response.ok:
                print(f"JBISページの取得に失敗しました: {jbis_url}")
                return 0.0
                
            # 基本情報ページから賞金情報を抽出
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # 総賞金を探す（複数のパターンを試す）
            prize_patterns = [
                r'総賞金[\s\S]*?([\d,]+)\\s*万円',  # 正規表現パターン1
                r'総賞金[\s\S]*?(\d+(?:,\d+)*)\\s*万円',  # 正規表現パターン2
                r'総賞金[\s\S]*?(\d+(?:,\d+)*)\\s*円'  # 正規表現パターン3
            ]
            
            for pattern in prize_patterns:
                match = re.search(pattern, str(soup))
                if match:
                    prize_str = match.group(1).replace(',', '')
                    try:
                        return float(prize_str) / 10000.0  # 万円に変換
                    except (ValueError, TypeError):
                        continue
            
            print(f"JBISから賞金情報を抽出できませんでした: {jbis_url}")
            return 0.0
            
        except Exception as e:
            print(f"JBISからの賞金取得中にエラーが発生しました: {str(e)}")
            return 0.0

    def _extract_prize_money(self, page_text: str, jbis_url: str = None) -> Dict:
        """賞金情報を抽出
        
        Args:
            page_text: ページのテキスト
            jbis_url: JBISのURL（オプション、指定すると最新の賞金情報を取得）
            
        Returns:
            Dict: 賞金情報（total_prize_start, total_prize_latest）
        """
        result = {
            'total_prize_start': 0.0,
            'total_prize_latest': 0.0
        }
        
        # オークション時点の賞金を抽出
        try:
            # 中央・地方・総獲得賞金の全パターンをカバー
            central_prize_match = re.search(r'中央獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
            local_prize_match = re.search(r'地方獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
            total_prize_match = re.search(r'総獲得賞金[：:]\s*([\d,.]+)万?円', page_text)
            
            if total_prize_match:
                result['total_prize_start'] = float(total_prize_match.group(1).replace(',', ''))
            else:
                central = float(central_prize_match.group(1).replace(',', '')) if central_prize_match else 0.0
                local = float(local_prize_match.group(1).replace(',', '')) if local_prize_match else 0.0
                result['total_prize_start'] = central + local
                
            # 最新の賞金情報をJBISから取得
            if jbis_url:
                latest_prize = self._extract_jbis_prize_money(jbis_url)
                result['total_prize_latest'] = latest_prize if latest_prize > 0 else result['total_prize_start']
            else:
                result['total_prize_latest'] = result['total_prize_start']
                
            print(f"[デバッグ] 賞金情報 - オークション時: {result['total_prize_start']}万円, 最新: {result['total_prize_latest']}万円")
                
        except (ValueError, TypeError, AttributeError) as e:
            print(f"賞金情報の抽出に失敗: {e}")
            result['total_prize_start'] = 0.0
            result['total_prize_latest'] = 0.0
            
        return result
    
    def _extract_comment(self, page_text: str) -> str:
        """コメントを抽出"""
        # "本馬について" の後のテキストを探す
        comment_match = re.search(r'本馬について(.+?)(?=\n\n|\n販売申込者|$)', page_text, re.DOTALL)
        if comment_match:
            return comment_match.group(1).strip()
        return ""
    
    def _extract_disease_tags(self, comment: str) -> str:
        """疾病タグを抽出"""
        disease_keywords = [
            '喉頭片麻痺', '喘鳴症', '脚部不安', '関節炎', '腱炎',
            '骨折', '脱臼', '筋肉痛', '腰痛', '腹痛', '球節炎', 'さく癖'
        ]
        
        found_diseases = []
        for disease in disease_keywords:
            if disease in comment:
                found_diseases.append(disease)
        
        return ','.join(found_diseases) if found_diseases else "なし"
    
    def _extract_primary_image(self, soup) -> str:
        """馬体画像のURLを抽出"""
        try:
            # 画像要素を探す
            image_elements = soup.find_all('img')
            for img in image_elements:
                src = img.get('src', '')
                if src and isinstance(src, str) and 'horse' in src.lower() and ('jpg' in src.lower() or 'jpeg' in src.lower() or 'png' in src.lower()):
                    return src
            
            return ""
        except Exception as e:
            print(f"馬体画像の抽出に失敗: {e}")
            return ""
    
    def _extract_seller(self, page_text: str) -> str:
        """販売申込者を抽出
        
        Returns:
            str: 販売者名（「インボイス登録あり」のテキストは削除）
        """
        seller_match = re.search(r'販売申込者[：:]\s*([^\n]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            # 「（インボイス登録あり）」を削除
            seller = re.sub(r'\s*[(（]インボイス登録あり[)）]', '', seller)
            return seller.strip()
        return ""
    
    def _extract_jbis_url(self, soup) -> str:
        """JBIS URLを抽出し、基本情報ページのURLに正規化して返す"""
        try:
            # 1. まず「基本情報」というテキストを含むリンクを探す
            info_links = []
            for link in soup.find_all('a', href=True):
                if '基本情報' in link.get_text():
                    info_links.append(link.get('href', ''))
            
            # 2. 基本情報リンクからJBISのURLを抽出
            for href in info_links:
                if 'jbis.or.jp' in href and 'horse' in href:
                    normalized_url = self._normalize_jbis_url(href)
                    print(f"基本情報ページからJBIS URLを抽出: {normalized_url}")
                    return normalized_url
            
            # 3. 基本情報リンクが見つからない場合は、直接JBISリンクを探す
            for link in soup.find_all('a', href=True):
                href = link.get('href', '')
                if 'jbis.or.jp' in href and 'horse' in href:
                    normalized_url = self._normalize_jbis_url(href)
                    print(f"直接JBISリンクから抽出: {normalized_url}")
                    return normalized_url
            
            print("警告: JBISの基本情報ページへのリンクが見つかりませんでした")
            return ""
            
        except Exception as e:
            print(f"JBIS URLの抽出に失敗: {e}")
            return ""

    def _normalize_jbis_url(self, jbis_url: str) -> str:
        """
        JBIS URLを基本情報ページのURLに正規化する
        
        Args:
            jbis_url: 正規化するJBISのURL
            
        Returns:
            str: 正規化された基本情報ページのURL（例: https://www.jbis.or.jp/horse/0001378353/）
        """
        if not jbis_url:
            return ""
            
        # 相対URLの場合はベースURLを追加
        if jbis_url.startswith('//'):
            jbis_url = 'https:' + jbis_url
        elif not jbis_url.startswith('http'):
            jbis_url = 'https://www.jbis.or.jp' + ('' if jbis_url.startswith('/') else '/') + jbis_url
        
        # クエリパラメータを除去
        jbis_url = jbis_url.split('?')[0]
        
        # 馬IDを抽出（例: /horse/0001378353/ から 0001378353 を抽出）
        horse_id_match = re.search(r'/horse/(\d+)', jbis_url)
        if not horse_id_match:
            return ""
            
        horse_id = horse_id_match.group(1)
        
        # 基本情報ページのURLを構築
        return f"https://www.jbis.or.jp/horse/{horse_id}/"

    def scrape_all_horses(self, auction_date: str = None) -> List[Dict]:
        """全馬の情報を取得"""
        if not auction_date:
            auction_date = self.get_auction_date()
        
        print(f"オークション日: {auction_date}")
        
        # 馬のリストを取得
        horses = self.scrape_horse_list()
        print(f"{len(horses)}頭の馬を発見しました。")
        
        # オークション日を追加
        for horse in horses:
            horse['auction_date'] = auction_date
        
        return horses

def save_scraped_data(horse_data: Dict[str, Any], data_dir: str = 'static-frontend/public/data') -> Tuple[bool, str]:
    """スクレイピングしたデータをhorses.jsonとauction_history.jsonに保存
    
    Args:
        horse_data: スクレイピングした馬のデータ
        data_dir: データを保存するディレクトリ
        
    Returns:
        Tuple[bool, str]: (成功可否, メッセージ)
    """
    try:
        # 必須フィールドのバリデーション
        print("\n[デバッグ] 必須フィールドのバリデーションを開始します...")
        required_fields = ['name', 'sex', 'age', 'sire', 'dam', 'seller', 'auction_date']
        missing_fields = [field for field in required_fields if not horse_data.get(field)]
        
        # 各フィールドの値をデバッグ出力
        print("[デバッグ] 現在のフィールド値:")
        for field in required_fields + ['damsire']:
            print(f"  - {field}: '{horse_data.get(field, 'N/A')}' (型: {type(horse_data.get(field))})")
        
        if missing_fields:
            return False, f"必須フィールドが不足しています: {', '.join(missing_fields)}"
            
        # damsireが存在しない場合は空文字を設定
        if 'damsire' not in horse_data or not horse_data['damsire']:
            horse_data['damsire'] = ''
            horse_data['dam_sire'] = ''  # 互換性のため

        # 馬情報を準備
        print(f"\n[デバッグ] 馬情報を準備中: {horse_data.get('name', 'N/A')}")
        print(f"[デバッグ] disease_tags の型: {type(horse_data.get('disease_tags'))}, 値: {horse_data.get('disease_tags')}")
        
        # disease_tags が文字列の場合はリストに変換
        disease_tags = horse_data.get('disease_tags', [])
        if isinstance(disease_tags, str):
            print(f"[警告] disease_tags が文字列です。リストに変換します: {disease_tags}")
            # カンマ区切りの文字列をリストに変換
            disease_tags = [tag.strip() for tag in disease_tags.split(',') if tag.strip()]
        
        # 馬の基本情報を準備
        horse_info = {
            'name': horse_data['name'],
            'sex': horse_data['sex'],
            'age': int(horse_data['age']),
            'sire': horse_data['sire'],
            'dam': horse_data['dam'],
            'damsire': horse_data['damsire'],
            'image_url': horse_data.get('primary_image', ''),
            'jbis_url': horse_data.get('jbis_url', ''),
            'auction_url': horse_data.get('detail_url', ''),
            'disease_tags': disease_tags,
            'weight': horse_data.get('weight', ''),
            'race_record': horse_data.get('race_record', ''),
            'comment': horse_data.get('comment', ''),
            'seller': horse_data.get('seller', ''),
            'auction_date': horse_data.get('auction_date', ''),
            'total_prize_start': float(horse_data.get('total_prize_start', 0)) if horse_data.get('total_prize_start') else 0.0,
            'total_prize_latest': float(horse_data.get('total_prize_latest', 0)) if horse_data.get('total_prize_latest') else 0.0,
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat()
        }
        print(f"[デバッグ] 保存する馬情報: {json.dumps(horse_info, ensure_ascii=False, indent=2)}")

        # 馬情報を保存
        horse_id = save_horse(horse_info, data_dir)

        # オークション履歴を準備
        auction_info = {
            'horse_id': horse_id,
            'auction_date': horse_data['auction_date'],
            'sold_price': float(horse_data.get('sold_price', 0)) if horse_data.get('sold_price') else None,
            'total_prize_start': float(horse_data.get('total_prize_start', 0)) if horse_data.get('total_prize_start') else 0.0,
            'total_prize_latest': float(horse_data.get('total_prize_latest', 0)) if horse_data.get('total_prize_latest') else 0.0,
            'weight': float(horse_data.get('weight', 0)) if horse_data.get('weight') else None,
            'seller': horse_data['seller'],
            'is_unsold': bool(horse_data.get('is_unsold', False)),
            'comment': horse_data.get('comment', '')
        }

        # オークション履歴を保存
        save_auction_history(auction_info, data_dir)

        return True, f"{horse_data['name']} のデータを保存しました"
    except Exception as e:
        return False, f"データの保存中にエラーが発生しました: {str(e)}"

def scrape_from_history_urls():
    """horses_history.jsonのURLリストからスクレイピングし、horses.jsonとauction_history.jsonに保存する"""
    print("スクレイピングを開始します...")
    
    # データディレクトリのパスを設定
    data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'static-frontend', 'public', 'data')
    input_file = os.path.join(data_dir, 'horses_history.json')
    
    if not os.path.exists(input_file):
        print(f"エラー: {input_file} が見つかりません")
        return

    # データを読み込み
    try:
        with open(input_file, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as e:
        print(f"エラー: ファイルの読み込みに失敗しました: {e}")
        return

    if not data:
        print("エラー: データが空です")
        return

    # 馬のリストを取得
    horses_list = data.get("horses", [])
    if not horses_list:
        print("エラー: 馬のデータが見つかりません")
        return

    # URLの収集と重複除去
    url_list = []
    missing_url_horses = []
    
    for horse_data in horses_list:
        top_level_url = horse_data.get("detail_url")
        history_url = None
        
        if horse_data.get("history"):
            history_entry = horse_data["history"][0] if horse_data["history"] else {}
            history_url = history_entry.get("detail_url")

        final_url = top_level_url or history_url

        if final_url:
            url_list.append(final_url)
        else:
            horse_name = horse_data.get("name", "名前不明")
            missing_url_horses.append(horse_name)

    # 重複を除去
    url_list = sorted(list(set(url_list)))

    print(f"履歴ファイルから{len(url_list)}件のURLを再取得します")
    if missing_url_horses:
        print(f"--- URL欠損データ ({len(missing_url_horses)}件) ---")
        for name in sorted(list(set(missing_url_horses))):
            print(f"- {name}")
        print("------------------------------------")

    # スクレイピングの実行
    scraper = ImprovedRakutenScraper()
    success_count = 0
    failed_count = 0
    
    for i, url in enumerate(url_list, 1):
        print(f"({i}/{len(url_list)}) {url}")
        try:
            # 馬の詳細情報をスクレイピング
            horse = scraper.scrape_horse_detail(url)
            if not horse:
                print(f"  → エラー: データを取得できませんでした")
                failed_count += 1
                continue
                
            # 詳細URLを設定
            horse["detail_url"] = url
            
            # オークション日を設定（デフォルトは現在日時）
            if "auction_date" not in horse:
                horse["auction_date"] = datetime.now().strftime("%Y-%m-%d")
            
            # データを保存
            success, message = save_scraped_data(horse, data_dir)
            if success:
                print(f"  → 成功: {message}")
                success_count += 1
            else:
                print(f"  → エラー: {message}")
                failed_count += 1
                
        except Exception as e:
            print(f"  → 例外が発生しました: {str(e)}")
            failed_count += 1
            
        time.sleep(1)  # サーバーに負荷をかけないように1秒待機
    
    # 結果を表示
    print("\n===== スクレイピング結果 =====")
    print(f"成功: {success_count}件")
    print(f"失敗: {failed_count}件")
    print("===========================\n")

def main():
    """メイン実行関数"""
    scraper = None
    exit_code = 1  # デフォルトはエラー終了
    
    try:
        logger.info("楽天競馬オークション スクレイピングを開始します...")
        
        # データディレクトリのパスを設定
        data_dir = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 
                              'static-frontend', 'public', 'data')
        os.makedirs(data_dir, exist_ok=True)
        
        # スクレイパーを初期化（タイムアウト30秒、最大3回リトライ）
        scraper = ImprovedRakutenScraper(timeout=30, max_retries=3)
        
        # オークション日を取得
        logger.info("オークション情報を取得中...")
        auction_date = scraper.get_auction_date()
        if not auction_date:
            logger.error("オークション日を取得できませんでした")
            return 1
            
        logger.info(f"オークション日: {auction_date}")
        
        # 全馬の情報を取得
        logger.info("馬の情報を取得中...")
        horses = scraper.scrape_all_horses(auction_date)
        
        if not horses:
            logger.error("馬の情報を取得できませんでした")
            return 1
            
        logger.info(f"\n===== スクレイピング結果 =====")
        logger.info(f"取得した馬の数: {len(horses)}")
        
        success_count = 0
        fail_count = 0
        
        # 各馬の情報を保存（進捗表示付き）
        for horse in tqdm(horses, desc="データを保存中", unit="件"):
            horse_name = horse.get('name', 'N/A')
            logger.debug(f"処理中: {horse_name}")
            
            try:
                success, message = save_scraped_data(horse, data_dir)
                if success:
                    success_count += 1
                    logger.debug(f"保存成功: {horse_name}")
                else:
                    fail_count += 1
                    logger.warning(f"保存失敗: {horse_name} - {message}")
                
                # サーバーに優しくするために少し待機
                time.sleep(0.5)
                
            except Exception as e:
                fail_count += 1
                logger.error(f"保存中にエラーが発生しました ({horse_name}): {str(e)}")
                continue
        
        # 結果をログに記録
        logger.info("\n===== 処理完了 =====")
        logger.info(f"成功: {success_count}件")
        logger.info(f"失敗: {fail_count}件")
        
        # 成功した場合のみ0を返す
        exit_code = 0 if success_count > 0 else 1
        
    except KeyboardInterrupt:
        logger.warning("\nユーザーによって処理が中断されました")
        exit_code = 130  # SIGINTの終了コード
    except Exception as e:
        logger.error(f"\n予期しないエラーが発生しました: {str(e)}", exc_info=True)
        exit_code = 1
    finally:
        # リソースのクリーンアップ
        if scraper and hasattr(scraper, 'session'):
            try:
                scraper.session.close()
                logger.info("セッションをクローズしました")
            except Exception as e:
                logger.error(f"セッションのクローズ中にエラーが発生しました: {str(e)}")
        
        logger.info("スクリプトを終了します")
        return exit_code

if __name__ == "__main__":
    import sys
    sys.exit(main())