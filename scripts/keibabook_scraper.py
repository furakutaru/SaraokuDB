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
        if hasattr(self, 'session'):
            await self.session.close()
            
    async def close(self):
        """セッションをクローズします"""
        if hasattr(self, 'session'):
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
        
        # 検索パラメータを設定
        data = {
            "_token": token,
            "bamei": name,  # 馬名
            "search": "1",  # 1: 部分一致
            "sire": father,  # 父馬名
            "sirecd": "",  # 父馬CD（空でOK）
            "search_sire": "1",  # 父馬名で検索する場合は1
            "brood": "",  # 母馬名（空文字）
            "broodcd": "",  # 母馬CD（空でOK）
            "search_brood": "0",  # 母馬名で検索しない
            "nenrei1": "",  # 年齢（空で全件）
            "nenrei2": "",  # 年齢（空で全件）
            "seibet[]": ["0", "1", "2"],  # 性別（牡・牝・セン）
            "masyof[]": ["1"],  # 中央現役以外も含む
            "sort": "kbamei",  # 馬名順
            "group": "50",  # 1ページあたりの表示件数を拡大
            "page": "0",  # ページ番号
            "sort_type": "asc"  # 昇順
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

            # テーブル未検出や0件の場合はフォールバック: 少し待ってから再試行 or 前方一致に切替
            if not results:
                try:
                    await asyncio.sleep(1.0)
                except Exception:
                    pass
                # 直近の問題: テーブル未検出や0件 → 前方一致に切り替えて再検索
                data_fallback = data.copy()
                data_fallback["search"] = "0"  # 0: で始まる
                encoded_data_fb = urllib.parse.urlencode(data_fallback, doseq=True)
                headers_fb = self.HEADERS.copy()
                headers_fb["Content-Length"] = str(len(encoded_data_fb))
                logger.info("フォールバック検索を実行します（前方一致, group=50）")

                response_fb = await self._request_with_retry(
                    "POST",
                    self.BASE_URL,
                    data=data_fallback,
                    headers=headers_fb,
                    timeout=30
                )
                html_fb = await response_fb.text()
                timestamp_fb = datetime.now().strftime('%Y%m%d_%H%M%S')
                filename_fb = f'keibabook_response_{timestamp_fb}.html'
                with open(filename_fb, 'w', encoding='utf-8') as f:
                    f.write(html_fb)
                logger.info(f"フォールバックレスポンスを {filename_fb} に保存しました")
                results = await self._parse_search_results(html_fb)
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
        debug_filename = f"debug_search_results_{timestamp}.html"
        with open(debug_filename, "w", encoding="utf-8") as f:
            f.write(html)
        logger.debug(f"デバッグ用HTMLを保存しました: {debug_filename}")
        
        # 検索結果のテーブルを特定（ヘッダーの default テーブルではなく、結果の default search テーブル）
        table = soup.select_one('table.default.search')
        if not table:
            # フォールバック: 獲得総賞金 のヘッダーを持つ default テーブルを探す
            for cand in soup.select('table.default'):
                thead = cand.find('thead')
                if not thead:
                    continue
                headers = [th.get_text(strip=True) for th in thead.find_all('th')]
                if any('獲得総賞金' in h for h in headers):
                    table = cand
                    break
        
        if not table:
            logger.warning("検索結果テーブルが見つかりませんでした")
            # エラーページの内容を確認
            error_div = soup.find('div', class_='error')
            if error_div:
                error_msg = error_div.get_text(strip=True)
                logger.error(f"エラーメッセージ: {error_msg}")
            return results
        
        # tbody 内の行を取得（ヘッダーは thead にある）
        tbody = table.find('tbody') or table
        rows = tbody.find_all('tr')
        
        for row in rows:
            try:
                cols = row.find_all('td')
                if len(cols) < 2:  # 有効な列が少なすぎる場合はスキップ
                    continue
                    
                # 馬名と詳細URLを取得
                name_link = cols[0].find('a', class_='umalink_click')
                name = name_link.get_text(strip=True) if name_link else cols[0].get_text(strip=True)
                detail_url = name_link['href'] if name_link and 'href' in name_link.attrs else ''
                
                # 生年/年齢/性別（列位置がレイアウトで変わることがあるため安全に参照）
                age = None
                gender = ''
                try:
                    if len(cols) >= 5:
                        # 年齢はだいたい index 3
                        age_text = cols[3].get_text(strip=True)
                        age = int(age_text) if age_text and age_text.isdigit() else None
                        # 性別はだいたい index 4
                        gender_cell = cols[4].get_text(strip=True)
                        gender = gender_cell[0] if gender_cell else ''
                except Exception:
                    pass
                
                # 父と母
                father = ''
                mother = ''
                # 父母はだいたい index 6 のセル内リンク
                parent_cell_idx = 6 if len(cols) > 6 else 2
                parents = cols[parent_cell_idx].find_all('a', class_='umalink_click')
                if len(parents) >= 2:
                    father = parents[0].get_text(strip=True)
                    mother = parents[1].get_text(strip=True)
                
                # 賞金は最終列（獲得総賞金）を参照
                prize = 0
                if len(cols) > 0:
                    prize_text = cols[-1].get_text(strip=True)
                    try:
                        if prize_text and prize_text != '-':
                            txt = prize_text.replace('円', '').strip()
                            if '万' in txt:
                                # 例: "3,662.4万" や "1,234万5,678"
                                if txt.endswith('万'):
                                    value = txt[:-1].replace(',', '')  # 末尾の万を除去
                                    prize = int(float(value) * 10000)
                                else:
                                    parts = txt.split('万')
                                    head = parts[0].replace(',', '')
                                    tail = parts[1].replace(',', '') if len(parts) > 1 else '0'
                                    prize = int(float(head) * 10000 + float(tail))
                            else:
                                prize = int(txt.replace(',', ''))
                    except (ValueError, AttributeError) as e:
                        logger.warning(f"賞金のパースに失敗しました: {prize_text}, エラー: {str(e)}")
                
                # 馬の情報を追加
                horse_info = {
                    'name': name,
                    'gender': gender,
                    'age': age,
                    'father': father,
                    'mother': mother,
                    'prize': prize,
                    'detail_url': detail_url
                }
                
                results.append(horse_info)
                logger.debug(f"抽出した馬情報: {horse_info}")
                
            except Exception as e:
                logger.warning(f"行の処理中にエラーが発生しました: {str(e)}")
                logger.debug(f"エラーが発生した行: {row}")
                continue
                
        return results
        
        if not results:
            logger.info("検索結果: 0件見つかりました")
        else:
            logger.info(f"検索結果: {len(results)}件見つかりました")
        
        return results

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

    async def get_horse_prize(self, detail_path_or_url: str) -> Optional[int]:
        """詳細ページから獲得総賞金を取得

        Args:
            detail_path_or_url: '/db/uma/xxxxx' などの相対パス、または絶対URL

        Returns:
            int または None
        """
        try:
            if not detail_path_or_url:
                return None

            if detail_path_or_url.startswith('http'):
                url = detail_path_or_url
            else:
                url = f"https://p.keibabook.co.jp{detail_path_or_url}"

            # 取得
            resp = await self._request_with_retry("GET", url, headers=self.HEADERS)
            html = await resp.text()
            soup = BeautifulSoup(html, 'html.parser')

            # ラベルに "獲得総賞金" が含まれる行を探す
            prize_text = None
            # テーブル内のth/td構造を探索
            for th in soup.find_all(['th','dt']):
                label = th.get_text(strip=True)
                if not label:
                    continue
                if '獲得総賞金' in label or '総賞金' in label:
                    # 兄弟のtd/ddを取得
                    td = th.find_next_sibling(['td','dd'])
                    if td:
                        prize_text = td.get_text(strip=True)
                        break

            # 代替: 『獲得総賞金』の語を含む任意要素から後続値を拾う
            if not prize_text:
                text_nodes = soup.find_all(text=True)
                for t in text_nodes:
                    if isinstance(t, str) and ('獲得総賞金' in t or '総賞金' in t):
                        # 近傍の数字を探す
                        parent = soup
                        try:
                            parent = t.parent
                            # 次の要素のテキスト
                            nxt = parent.find_next(string=True)
                            if nxt and nxt != t:
                                prize_text = nxt.strip()
                                break
                        except Exception:
                            continue

            if not prize_text:
                return None

            txt = prize_text.replace('円', '').strip()
            if not txt or txt == '-':
                return None

            # 例: "3,662.4万" や "1,234万5,678"
            if '万' in txt:
                if txt.endswith('万'):
                    value = txt[:-1].replace(',', '')
                    return int(float(value) * 10000)
                else:
                    parts = txt.split('万')
                    head = parts[0].replace(',', '')
                    tail = parts[1].replace(',', '') if len(parts) > 1 else '0'
                    return int(float(head) * 10000 + float(tail))
            else:
                return int(txt.replace(',', ''))

        except Exception as e:
            logger.warning(f"詳細ページから賞金取得に失敗: {str(e)}")
            return None

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
