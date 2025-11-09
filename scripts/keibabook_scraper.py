import asyncio
import aiohttp
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Any, Union, Tuple
import logging
from datetime import datetime, timedelta
import random
import time
import json

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルでより詳細なログを出力
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('keibabook_scraper.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class RetryableError(Exception):
    """リトライ可能なエラーを表す例外クラス"""
    pass

class KeibaBookScraper:
    """競馬ブックのスクレイピング用クラス（リトライ機能付き）"""
    
    BASE_URL = "https://p.keibabook.co.jp/db/search/horse"
    HEADERS = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/avif,image/webp,image/apng,*/*;q=0.8,application/signed-exchange;v=b3;q=0.7",
        "Accept-Language": "ja,en-US;q=0.9,en;q=0.8,ja-JP;q=0.7",
        "Accept-Encoding": "gzip, deflate, br",
        "Connection": "keep-alive",
        "Referer": "https://p.keibabook.co.jp/db/search/horse",
        "Content-Type": "application/x-www-form-urlencoded; charset=UTF-8",
        "Origin": "https://p.keibabook.co.jp",
        "DNT": "1",
        "Sec-Fetch-Dest": "document",
        "Sec-Fetch-Mode": "navigate",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1",
        "Cache-Control": "max-age=0",
        "TE": "trailers",
        "Sec-Fetch-Site": "same-origin",
        "Sec-Fetch-User": "?1",
        "Upgrade-Insecure-Requests": "1"
    }
    
    def __init__(
        self,
        session: Optional[aiohttp.ClientSession] = None,
        max_retries: int = 3,
        base_delay: float = 2.0,
        max_delay: float = 60.0,
        jitter: bool = True,
        verify_ssl: bool = False
    ):
        """初期化
        
        Args:
            session: aiohttpのセッション
            max_retries: 最大リトライ回数
            base_delay: リトライ間の基本待機時間（秒）
            max_delay: リトライ間の最大待機時間（秒）
            jitter: ジッター（ランダムな遅延）を有効にするか
            verify_ssl: SSL証明書の検証を行うか
        """
        self.max_retries = max_retries
        self.base_delay = base_delay
        self.max_delay = max_delay
        self.jitter = jitter
        self.request_count = 0
        self.last_request_time = None
        
        # セッションの設定をカスタマイズ
        connector = aiohttp.TCPConnector(ssl=verify_ssl)
        self.session = session or aiohttp.ClientSession(
            connector=connector,
            headers=self.HEADERS
        )
    
    async def __aenter__(self):
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.session.close()

    def _should_retry(self, error: Exception) -> bool:
        """リトライすべきエラーかどうかを判定"""
        if isinstance(error, (aiohttp.ClientError, asyncio.TimeoutError, RetryableError)):
            return True
        return False

    def _get_retry_delay(self, attempt: int) -> float:
        """リトライ間の遅延時間を計算（指数バックオフ + ジッター）"""
        delay = min(self.base_delay * (2 ** (attempt - 1)), self.max_delay)
        if self.jitter:
            delay = random.uniform(0, delay)
        return delay

    async def _respect_rate_limit(self):
        """レートリミットを考慮してリクエスト間隔を調整"""
        if self.last_request_time:
            elapsed = (datetime.now() - self.last_request_time).total_seconds()
            min_interval = 1.0  # 最低1秒間隔を空ける
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)

    async def _request_with_retry(
        self,
        method: str,
        url: str,
        **kwargs
    ) -> aiohttp.ClientResponse:
        """リトライ機能付きのHTTPリクエスト"""
        last_error = None
        
        # デフォルトのタイムアウト設定を追加
        if 'timeout' not in kwargs:
            kwargs['timeout'] = aiohttp.ClientTimeout(total=30)
        
        for attempt in range(1, self.max_retries + 1):
            try:
                # レートリミット対策の遅延
                await self._respect_rate_limit()
                
                logger.debug(f"リクエスト送信: {method} {url}")
                
                # リクエスト実行
                async with self.session.request(
                    method,
                    url,
                    **kwargs
                ) as response:
                    self.request_count += 1
                    self.last_request_time = datetime.now()
                    
                    # レスポンスの内容を確認
                    content = await response.text()
                    
                    # エラーページのチェック
                    if "アクセスが集中しています" in content:
                        raise RetryableError("アクセスが集中しています")
                        
                    # ステータスコードチェック
                    if response.status == 200:
                        return response
                    
                    # レートリミットやサーバーエラーの場合
                    if response.status in [429, 500, 502, 503, 504]:
                        raise RetryableError(f"HTTP {response.status}: {content}")
                    
                    # その他のエラー
                    response.raise_for_status()
            
            except (aiohttp.ClientError, asyncio.TimeoutError) as e:
                last_error = e
                if attempt == self.max_retries or not self._should_retry(e):
                    logger.error(f"リクエストが失敗しました（最終試行）: {str(e)}")
                    raise
                
                # リトライ前の待機
                delay = self._get_retry_delay(attempt)
                logger.warning(
                    f"リクエストが失敗しました (試行 {attempt}/{self.max_retries}): "
                    f"{str(e)}. {delay:.2f}秒後に再試行します..."
                )
                await asyncio.sleep(delay)
        
        # すべてのリトライが失敗した場合
        raise last_error or Exception("リクエストが失敗しました")

    async def search_horse(self, name: str, father: str, mother: str, age: Optional[int] = None, gender: Optional[str] = None) -> List[Dict[str, Any]]:
        """馬を検索する"""
        try:
            # トークンを取得するためにトップページにアクセス
            token = 'dummy_token'
            logger.info("トークンを取得するためにトップページにアクセスします...")
            
            # セッションクッキーを取得するために一度GETリクエストを送信
            await self.session.get(self.BASE_URL, headers=self.HEADERS)
            
            # 検索ページにアクセスしてトークンを取得
            async with self.session.get(self.BASE_URL, headers=self.HEADERS) as response:
                if response.status == 200:
                    html = await response.text()
                    # デバッグ用にHTMLを保存
                    with open(f"debug_search_page_{int(time.time())}.html", "w", encoding="utf-8") as f:
                        f.write(html)
                    
                    soup = BeautifulSoup(html, 'html.parser')
                    token = soup.find('input', {'name': '_token'})
                    if token and 'value' in token.attrs:
                        token = token['value']
                        logger.debug(f"トークンを取得しました: {token}")
                    else:
                        logger.warning("トークンが見つかりませんでした")
                        # フォールバックとして、ページ内の最初のトークンを探す
                        for meta in soup.find_all('meta', {'name': 'csrf-token'}):
                            if 'content' in meta.attrs:
                                token = meta['content']
                                logger.debug(f"メタタグからトークンを取得: {token}")
                                break
        except Exception as e:
            logger.warning(f"トークンの取得に失敗しました: {str(e)}")
            token = 'dummy_token'
        
        data = {
            "_token": token,
            "bamei": name,
            "search": "1",  # 1: 部分一致
            "sire": father,
            # 母名はコメントアウト（同名の馬が複数いる場合に問題が発生するため）
            # "brood": mother,
            "masyof[]": "1",  # 中央現役以外も含む
            "sort": "kbamei",
            "group": "10",
            "page": "0",
            "sort_type": "asc"
        }

        # 年齢の条件をコメントアウト（検索条件を緩和）
        # if age:
        #     data["nenrei1"] = str(age) if age else "0"
        #     data["nenrei2"] = str(age) if age else "0"
            
        if gender:
            gender_map = {"牡": "0", "牝": "1", "セン": "2"}
            data["seibet[]"] = ["1"] if gender == "牝" else ["0"] if gender == "牡" else ["0", "1", "2"]  # 性別が不明な場合は全選択

        try:
            # デバッグ用にURLエンコードされたデータをログに出力
            import urllib.parse
            encoded_data = urllib.parse.urlencode(data, doseq=True)
            logger.info(f"検索リクエストを送信: {self.BASE_URL}")
            logger.debug(f"リクエストデータ: {encoded_data}")
            
            # カスタムヘッダーを追加
            headers = self.HEADERS.copy()
            headers["Content-Length"] = str(len(encoded_data))
            
            response = await self._request_with_retry(
                "POST",
                self.BASE_URL,
                data=data,
                headers=headers,
                timeout=30
            )
            
            html = await response.text()
            
            # レスポンスの内容をログに出力（デバッグ用）
            logger.debug(f"レスポンス: {html[:500]}...")  # 最初の500文字を出力
            
            # レスポンスをファイルに保存（デバッグ用）
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f'keibabook_response_{timestamp}.html'
            with open(filename, 'w', encoding='utf-8') as f:
                f.write(html)
            logger.info(f"レスポンスを {filename} に保存しました")
            
            results = await self._parse_search_results(html)
            logger.info(f"検索結果: {len(results)}件見つかりました")
            return results

        except Exception as e:
            logger.error(f"馬の検索中にエラーが発生しました: {str(e)}", exc_info=True)
            return []

    async def _parse_search_results(self, html: str) -> List[Dict[str, Any]]:
        """検索結果のHTMLをパースして、馬の情報を抽出する"""
        soup = BeautifulSoup(html, 'html.parser')
        results = []
        
        # デバッグ用にHTMLを保存
        timestamp = int(time.time())
        with open(f"debug_search_results_{timestamp}.html", "w", encoding="utf-8") as f:
            f.write(html)
        
        # 検索結果のテーブルを探す
        table = soup.find('table', class_='default search')
        
        if not table:
            logger.warning("検索結果テーブルが見つかりませんでした")
            # デバッグ用にHTMLを保存
            with open(f'debug_no_table_{timestamp}.html', 'w', encoding='utf-8') as f:
                f.write(html)
            return results
        
        # テーブルのヘッダーを取得
        thead = table.find('thead')
        if not thead:
            logger.warning("テーブルのヘッダーが見つかりませんでした")
            return results
            
        # ヘッダーから各カラムのインデックスを取得
        headers = [th.get_text(strip=True) for th in thead.find_all('th')]
        logger.debug(f"見つかったヘッダー: {headers}")
        
        try:
            name_idx = headers.index('馬名')
            birth_year_idx = headers.index('生年')
            age_idx = headers.index('年齢')
            gender_idx = headers.index('性別')
            
            # 「父母」が1つのカラムにまとまっている場合を想定
            parents_idx = headers.index('父母') if '父母' in headers else -1
            
            # 個別の「父」「母」カラムが存在するか確認
            father_idx = headers.index('父') if '父' in headers else parents_idx
            mother_idx = headers.index('母') if '母' in headers else parents_idx
        except ValueError as e:
            logger.warning(f"必要なカラムが見つかりません: {str(e)}")
            logger.debug(f"見つかったヘッダー: {headers}")
            return results
        
        # テーブルのボディを取得
        tbody = table.find('tbody')
        if not tbody:
            logger.warning("テーブルのボディが見つかりませんでした")
            return results
            
        # 各行を処理
        for row in tbody.find_all('tr'):
            cols = row.find_all('td')
            if len(cols) <= max(name_idx, birth_year_idx, age_idx, gender_idx, father_idx, mother_idx):
                logger.warning(f"列数が不足しています: 必要な列数={max(name_idx, birth_year_idx, age_idx, gender_idx, father_idx, mother_idx) + 1}, 実際の列数={len(cols)}")
                continue
                
            try:
                # 馬名と詳細URLを取得
                name_link = cols[name_idx].find('a')
                if not name_link:
                    continue
                    
                name = name_link.get_text(strip=True)
                detail_url = name_link.get('href', '')
                
                # 性別を取得
                gender = cols[gender_idx].get_text(strip=True)
                
                # 年齢を取得（生年から計算）
                birth_year = cols[birth_year_idx].get_text(strip=True)
                current_year = datetime.now().year
                age = current_year - int(birth_year) if birth_year.isdigit() else None
                
                # 賞金情報を取得（獲得総賞金から取得）
                try:
                    total_prize_idx = headers.index('獲得総賞金')
                    total_prize_text = cols[total_prize_idx].get_text(strip=True)
                    logger.debug(f"賞金テキスト: {total_prize_text}")
                    
                    # 不要な文字を削除
                    clean_text = total_prize_text.replace(',', '').replace('円', '').strip()
                    
                    # 空文字またはハイフンの場合は0を返す
                    if not clean_text or clean_text == '-':
                        total_prize = 0
                    # 「万」を含む場合
                    elif '万' in clean_text:
                        try:
                            value = clean_text.replace('万', '')
                            total_prize = int(float(value) * 10000)
                        except ValueError as e:
                            logger.warning(f"賞金の数値変換に失敗しました: {clean_text}, エラー: {str(e)}")
                            total_prize = 0
                    # 通常の数値の場合
                    else:
                        try:
                            total_prize = int(clean_text)
                        except ValueError as e:
                            logger.warning(f"賞金の数値変換に失敗しました: {clean_text}, エラー: {str(e)}")
                            total_prize = 0
                    
                    logger.debug(f"変換後の賞金: {total_prize}円")
                except (ValueError, IndexError) as e:
                    logger.warning(f"賞金情報の取得中にエラーが発生しました: {str(e)}")
                    logger.debug(f"ヘッダー: {headers}")
                    logger.debug(f"列数: {len(cols)}")
                    total_prize = 0
                
                # 父と母の情報を取得
                parents_text = cols[parents_idx].get_text(' ', strip=True) if parents_idx != -1 else ""
                
                # 父を取得（「父母」カラムから最初のリンクを取得）
                father_elem = cols[father_idx].find('a')
                father = father_elem.get_text(strip=True) if father_elem else ""
                
                # 母を取得（「父母」カラムから2番目のリンクを取得）
                mother_links = cols[mother_idx].find_all('a')
                mother = mother_links[1].get_text(strip=True) if len(mother_links) > 1 else ""
                
                # リンクが見つからない場合はテキストから抽出を試みる
                if not father and parents_text:
                    # 親の情報から「父」と「母」を分離するロジックを追加
                    parents_parts = [p.strip() for p in parents_text.split('\n') if p.strip()]
                    if len(parents_parts) >= 2:
                        father = parents_parts[0]
                        mother = parents_parts[1]
                    elif parents_text:
                        # 1行しかない場合は、最初の単語を父、2番目を母とする
                        parts = parents_text.split()
                        if len(parts) >= 2:
                            father = parts[0]
                            mother = parts[1]
                
                horse_info = {
                    'name': name,
                    'gender': gender,
                    'age': age,
                    'father': father,
                    'mother': mother,
                    'prize': total_prize,  # 合計賞金
                    'detail_url': f"https://p.keibabook.co.jp{detail_url}" if detail_url.startswith('/') else detail_url
                }
                
                results.append(horse_info)
                
            except Exception as e:
                logger.warning(f"馬情報のパース中にエラーが発生しました: {str(e)}")
                continue
        
        if not results:
            logger.info("検索結果: 0件見つかりました")
            # 検索フォームの内容を確認
            form = soup.find('form', {'method': 'POST'})
            if form:
                logger.info("検索フォームの内容を確認しました")
                # デバッグ用にフォームの内容をログに出力
                for input_tag in form.find_all('input'):
                    if input_tag.get('name') and input_tag.get('value'):
                        logger.debug(f"フォームパラメータ: {input_tag['name']} = {input_tag['value']}")
        else:
            logger.info(f"検索結果: {len(results)}件見つかりました")
            
        return results

    async def get_horse_prize(self, detail_url: str) -> Optional[int]:
        """馬の詳細ページから賞金情報を取得"""
        if not detail_url:
            return None

        if not detail_url.startswith('http'):
            detail_url = f"https://p.keibabook.co.jp{detail_url}"

        try:
            response = await self._request_with_retry(
                "GET",
                detail_url,
                headers=self.HEADERS,
                timeout=30
            )
            
            html = await response.text()
            soup = BeautifulSoup(html, 'html.parser')
            
            # 賞金情報を取得（実際のHTML構造に合わせて調整が必要）
            prize_text = soup.select_one('td:-soup-contains("賞金") + td')
            if prize_text:
                prize_str = prize_text.get_text(strip=True)
                # 数字とカンマのみを抽出
                import re
                prize_num = re.sub(r'[^0-9]', '', prize_str)
                return int(prize_num) if prize_num else None
            return None

        except Exception as e:
            logger.error(f"賞金情報の取得中にエラーが発生しました: {str(e)}")
            return None

    async def get_horse_info(
        self,
        name: str,
        father: str,
        mother: str,
        auction_date: Optional[str] = None,
        gender: Optional[str] = None
    ) -> Optional[Dict]:
        """馬の情報を取得（年齢を自動計算）"""
        age = None
        if auction_date:
            age = self._calculate_age(auction_date)
            logger.info(f"オークション日 {auction_date} から計算した年齢: {age}歳")

        # 検索を実行
        results = await self.search_horse(name, father, mother, age, gender)
        
        if not results:
            logger.warning("該当する馬が見つかりませんでした")
            return None

        # 最もマッチする馬を選択
        best_match = self._select_best_match(results, name, father, mother, age)
        
        # 賞金情報が検索結果に含まれている場合はそれを使用
        if 'prize' not in best_match or not best_match['prize']:
            # 検索結果に賞金情報がない場合のみ、詳細ページから取得を試みる
            if best_match.get('detail_url'):
                prize = await self.get_horse_prize(best_match['detail_url'])
                best_match['prize'] = prize
        
        # 賞金情報をログに出力（デバッグ用）
        logger.debug(f"最終的な賞金情報: {best_match.get('prize')}円")
            
        return best_match

    def _calculate_age(self, auction_date: str) -> int:
        """オークション日から現在の年齢を計算"""
        try:
            auction_dt = datetime.strptime(auction_date, '%Y-%m-%d')
            current_dt = datetime.now()
            
            # 馬の年齢計算（1月1日をまたぐと1歳加算）
            age = current_dt.year - auction_dt.year
            
            # 1月1日より前の場合は1歳引く
            if (current_dt.month, current_dt.day) < (1, 1):
                age -= 1
                
            return max(1, age)  # 最低1歳
            
        except ValueError as e:
            logger.error(f"日付のパースに失敗しました: {str(e)}")
            return 0

    def _select_best_match(
        self,
        horses: List[Dict],
        name: str,
        father: str,
        mother: str,
        target_age: Optional[int] = None
    ) -> Dict:
        """検索結果から最もマッチする馬を選択"""
        if len(horses) == 1:
            return horses[0]

        # スコアを計算して最もスコアの高い馬を選択
        best_score = -1
        best_match = horses[0]  # デフォルトで最初の馬を選択

        for horse in horses:
            score = 0
            
            # 馬名が完全一致
            if horse['name'] == name:
                score += 3
            # 馬名が含まれる
            elif name in horse['name']:
                score += 1
                
            # 父名が一致
            if horse['father'] == father:
                score += 2
                
            # 母名が一致
            if horse['mother'] == mother:
                score += 2
                
            # 年齢が一致
            if target_age and horse.get('age') == target_age:
                score += 1
                
            # 最高スコアを更新
            if score > best_score:
                best_score = score
                best_match = horse

        return best_match

# 使用例
async def main():
    """使用例"""
    # デバッグ用の設定
    import http.client as http_client
    http_client.HTTPConnection.debuglevel = 1
    
    # リクエスト/レスポンスのログを有効化
    logging.basicConfig()
    logging.getLogger().setLevel(logging.DEBUG)
    requests_log = logging.getLogger("requests.packages.urllib3")
    requests_log.setLevel(logging.DEBUG)
    requests_log.propagate = True
    
    try:
        # スクレイパーの初期化（SSL検証を無効化）
        async with KeibaBookScraper(verify_ssl=False) as scraper:
                # テスト用の馬情報
                test_horses = [
                    {
                        "name": "ミックファイア",
                        "father": "シニスターミニスター",
                        "mother": "マリアージュ",
                        "auction_date": "2020-01-01",  # 仮のオークション日
                        "gender": "牡"
                    },
                    # 他のテストケースを追加
                ]
                
                for test in test_horses:
                    print(f"\n{'='*50}")
                    print(f"検索中: {test['name']} (父: {test['father']})")
                    # 母名はコメントアウト中: 母: {test['mother']}
                    
                    try:
                        # 検索リクエストのデバッグ情報を強化
                        logger.debug(f"検索リクエスト: {scraper.search_horse.__name__}({test['name']}, {test['father']}, {test['mother']}, {test.get('auction_date')}, {test.get('gender')})")
                        
                        # リクエストヘッダーを調整
                        scraper.HEADERS['User-Agent'] = 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/74.0.3729.169 Safari/537.3'
                        
                        # 馬の情報を取得
                        horse_info = await scraper.get_horse_info(
                            name=test['name'],
                            father=test['father'],
                            mother=test['mother'],
                            auction_date=test.get('auction_date'),
                            gender=test.get('gender')
                        )
                        
                        if horse_info:
                            print("\n--- 検索結果 ---")
                            print(f"名前: {horse_info['name']}")
                            print(f"年齢: {horse_info.get('age', '不明')}歳")
                            print(f"性別: {horse_info.get('gender', '不明')}")
                            print(f"父: {horse_info.get('father', '不明')}")
                            print(f"母: {horse_info.get('mother', '不明')}")
                            if 'prize' in horse_info and horse_info['prize'] is not None:
                                print(f"賞金: {horse_info['prize']:,}円")
                            else:
                                print("賞金: 情報なし")
                            
                            # 詳細URLがある場合は表示
                            if 'detail_url' in horse_info and horse_info['detail_url']:
                                print(f"詳細URL: https://p.keibabook.co.jp{horse_info['detail_url']}")
                        else:
                            print("該当する馬が見つかりませんでした")
                        
                        # リクエスト間の遅延を入れる
                        await asyncio.sleep(2)
                        
                    except Exception as e:
                        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
                        continue
                    
    except Exception as e:
        logger.error(f"致命的なエラーが発生しました: {str(e)}", exc_info=True)
    finally:
        print("\nスクリプトを終了します")

if __name__ == "__main__":
    asyncio.run(main())
