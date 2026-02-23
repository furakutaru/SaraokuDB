#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import sys
import traceback
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# スクリプトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

# カスタムスクレイパーから必要なクラスをインポート
from improved_scraper import ImprovedRakutenScraper, ScraperConfig

# ロギングの設定
def setup_logging():
    """ロギングの設定を行う"""
    log_level = os.getenv('LOG_LEVEL', 'INFO').upper()
    log_level = getattr(logging, log_level, logging.INFO)
    
    # ログフォーマット
    log_format = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    formatter = logging.Formatter(log_format)
    
    # ルートロガーの設定
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # コンソールハンドラ
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラ
    file_handler = logging.FileHandler('scraper.log', encoding='utf-8')
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # 不要なライブラリのログを無効化
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('requests').setLevel(logging.WARNING)
    
    return logging.getLogger(__name__)

# ロガーの初期化
logger = setup_logging()

# リクエストのロギング用アダプタ
class RequestIdAdapter(logging.LoggerAdapter):
    def process(self, msg, kwargs):
        request_id = getattr(self.extra, 'request_id', 'NO_REQUEST_ID')
        return f'[{request_id}] {msg}', kwargs

# 環境変数の読み込み
env_path = Path(__file__).parent.parent / 'backend' / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)

# デバッグ用: 環境変数の確認
logger.info("=== 環境変数の確認 ===")
logger.info(f"PROD_API_BASE_URL: {'***' if os.getenv('PROD_API_BASE_URL') else 'Not Set'}")
logger.info(f"PROD_API_USERNAME: {'***' if os.getenv('PROD_API_USERNAME') else 'Not Set'}")
logger.info(f"PROD_API_PASSWORD: {'***' if os.getenv('PROD_API_PASSWORD') else 'Not Set'}")
logger.info(f"GITHUB_ACTIONS: {os.getenv('GITHUB_ACTIONS')}")
logger.info("=====================")

def _normalize_horse_name(name: str) -> str:
    """末尾の年齢/性別+年齢を除去し、空白を畳んだ正規化馬名を返す"""
    try:
        import re, unicodedata
        if not name:
            return ""
        s = unicodedata.normalize("NFKC", str(name))
        s = s.replace("　", " ")
        # 末尾の [性別(任意)] 年齢『歳』 を除去（例: " リケア 牝３歳" / " ４歳"）
        s = re.sub(r"\s*(?:牡|牝|セ)?\s*\d+\s*歳\s*$", "", s)
        # 連続空白を1つに
        s = re.sub(r"\s+", " ", s).strip()
        return s
    except Exception:
        return name or ""


class ScraperClient:
    def __init__(self):
        # 本番環境の認証情報を優先的に使用
        self.api_base_url = os.getenv('PROD_API_BASE_URL')
        self.api_username = os.getenv('PROD_API_USERNAME')
        self.api_password = os.getenv('PROD_API_PASSWORD')
        
        # デバッグ用ログ
        logger.info(f"API Base URL: {self.api_base_url}")
        logger.info(f"API Username: {'*' * len(self.api_username) if self.api_username else 'Not Set'}")
        
        if not all([self.api_base_url, self.api_username, self.api_password]):
            raise ValueError("API認証情報が正しく設定されていません")
            
        self.api_base_url = self.api_base_url.rstrip('/')
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'SaraokuDB-Scraper/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
        self.authenticate()
    
    def authenticate(self):
        """API認証を行いトークンを取得"""
        try:
            # 認証URLを正しく設定（/api/auth/token/）
            auth_url = f"{self.api_base_url}/api/auth/token/"
            logger.info(f"認証URL: {auth_url}")
            
            # 認証リクエストを送信（x-www-form-urlencoded形式で送信）
            response = self.session.post(
                auth_url,
                data={
                    'username': self.api_username,
                    'password': self.api_password,
                },
                headers={
                    'Content-Type': 'application/x-www-form-urlencoded',
                    'Accept': 'application/json'
                }
            )
            
            # レスポンスのステータスコードを確認
            response.raise_for_status()
            
            # トークンを取得
            token_data = response.json()
            self.token = token_data.get('access_token')
            
            if not self.token:
                raise ValueError("認証トークンを取得できませんでした")
            
            # 認証ヘッダーを更新
            self.session.headers.update({
                'Authorization': f'Bearer {self.token}'
            })
            
            logger.info("認証に成功しました")
            return True
            
        except Exception as e:
            logger.error(f"認証に失敗しました: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"レスポンス: {e.response.text}")
            raise
    
    def save_horse(self, horse_data, *, update_only: bool = False):
        """馬データをAPIに保存し、必要に応じてオークション履歴も保存する"""
        try:
            # URLを正規化（末尾のスラッシュを削除）
            base_url = self.api_base_url.rstrip('/')
            # VercelのAPIエンドポイントを直接指定
            save_url = f"{base_url}/api/horses"  # Vercelの設定に合わせて /api を含める
            
            logger.info(f"API ベースURL: {self.api_base_url}")
            logger.info(f"保存URL: {save_url}")
            logger.info(f"リクエストヘッダー: {self.session.headers}")
            
            # データのコピーを作成（元データを変更しないため）
            data_to_send = horse_data.copy()

            # 馬名を正規化（末尾の「 ４歳」等を除去）
            if 'name' in data_to_send and data_to_send['name']:
                data_to_send['name'] = _normalize_horse_name(data_to_send['name'])
            elif 'raw_name' in data_to_send and data_to_send['raw_name']:
                data_to_send['name'] = _normalize_horse_name(data_to_send['raw_name'])
            
            # race_records を race_record に変換
            if 'race_records' in data_to_send:
                if data_to_send['race_records'] is not None:
                    if isinstance(data_to_send['race_records'], (dict, list)):
                        # 辞書やリストの場合はJSON文字列に変換
                        data_to_send['race_record'] = json.dumps(data_to_send['race_records'], ensure_ascii=False)
                    else:
                        data_to_send['race_record'] = data_to_send['race_records']
                # 元の race_records は削除
                del data_to_send['race_records']
            # race_record が存在しない場合は空のJSONオブジェクトを設定
            elif 'race_record' not in data_to_send or data_to_send.get('race_record') is None:
                data_to_send['race_record'] = '{}'  # 空のJSONオブジェクトを表す文字列
            
            # 必須フィールドのバリデーションと型変換
            if 'image_url' not in data_to_send or data_to_send['image_url'] is None:
                data_to_send['image_url'] = ""
            
            # disease_tagsがリストの場合はカンマ区切りの文字列に変換
            if 'disease_tags' in data_to_send and isinstance(data_to_send['disease_tags'], list):
                data_to_send['disease_tags'] = ", ".join(data_to_send['disease_tags'])
            elif 'disease_tags' not in data_to_send or data_to_send['disease_tags'] is None:
                data_to_send['disease_tags'] = ""
            
            # race_record の初期化
            try:
                # race_record が既に設定されている場合はそのまま使用
                if 'race_record' not in data_to_send or not data_to_send['race_record']:
                    # race_record が存在しない場合はデフォルト値を設定
                    data_to_send['race_record'] = {
                        'total_races': 0,
                        'wins': 0,
                        'record_format': 'simple',
                        'formatted_record': '0戦0勝',
                        'records': []  # 空のリストを追加
                    }
                else:
                    # race_record が文字列の場合はパース
                    if isinstance(data_to_send['race_record'], str):
                        try:
                            data_to_send['race_record'] = json.loads(data_to_send['race_record'])
                        except json.JSONDecodeError:
                            data_to_send['race_record'] = {
                                'total_races': 0,
                                'wins': 0,
                                'record_format': 'simple',
                                'formatted_record': '0戦0勝',
                                'records': []
                            }
                    
                    # records フィールドが存在しない場合は追加
                    if not isinstance(data_to_send['race_record'], dict):
                        data_to_send['race_record'] = {
                            'total_races': 0,
                            'wins': 0,
                            'record_format': 'simple',
                            'formatted_record': '0戦0勝',
                            'records': []
                        }
                    elif 'records' not in data_to_send['race_record']:
                        data_to_send['race_record']['records'] = []
                
                # レース記録が正しく設定されているか確認
                if not isinstance(data_to_send['race_record'].get('total_races'), int) or \
                   not isinstance(data_to_send['race_record'].get('wins'), int):
                    logger.warning(f"レース記録の形式が不正です: {data_to_send['race_record']}")
                    data_to_send['race_record'] = {
                        'total_races': 0,
                        'wins': 0,
                        'record_format': 'simple',
                        'formatted_record': '0戦0勝',
                        'records': []
                    }
                
                logger.info(f"レコードを処理しました: {data_to_send['race_record']}")
                
            except Exception as e:
                logger.error(f"レコードの処理中にエラーが発生しました: {str(e)}")
                logger.error(traceback.format_exc())
                
                # エラーが発生した場合はデフォルト値を設定
                data_to_send['race_record'] = {
                    'total_races': 0,
                    'wins': 0,
                    'record_format': 'simple',
                    'formatted_record': '0戦0勝',
                    'records': []
                }
            
            # 常にJSON文字列に変換
            data_to_send['race_record'] = json.dumps(data_to_send['race_record'], ensure_ascii=False)
            
            # prize_money が辞書型の場合は数値に変換
            if 'prize_money' in data_to_send and isinstance(data_to_send['prize_money'], dict):
                prize_money = data_to_send['prize_money']
                if 'total_prize' in prize_money and prize_money['total_prize'] is not None:
                    data_to_send['prize_money'] = prize_money['total_prize']
                    logger.debug(f"prize_money を数値に変換: {data_to_send['prize_money']}")
                else:
                    data_to_send['prize_money'] = 0  # デフォルト値
                    logger.debug("prize_money が None のため 0 を設定")
            
            # update-only 指定時は履歴を汚し得るフィールドを送らない
            if update_only:
                for k in [
                    "auction_date",  # 履歴扱い
                    "sold_price",    # 価格履歴
                    "is_unsold",     # 主取り判定履歴
                    "unsold_count",
                    "seller",        # 出品者履歴
                    "comment",       # コメント履歴
                    "sex",           # 性別履歴
                    "age",           # 年齢履歴
                ]:
                    if k in data_to_send:
                        data_to_send.pop(k, None)

            # デバッグ用に送信データをログに出力
            logger.debug(f"送信データ: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
            
            # リクエストを送信
            save_url = f"{self.api_base_url}/api/horses/"  # 明示的にURLを設定
            logger.info(f"送信先URL: {save_url}")
            logger.info(f"リクエストヘッダー: {self.session.headers}")
            logger.info(f"リクエストボディ: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
            
            # 馬データを保存（常に新しいレコードとして挿入）
            try:
                # 既存の馬をチェック
                existing_horse = None
                if 'name' in data_to_send:
                    try:
                        # 名前で既存の馬を検索
                        search_url = f"{self.api_base_url}/api/horses"
                        search_params = {'name': data_to_send['name']}
                        search_headers = {
                            'Authorization': f'Bearer {self.token}'
                        }
                        search_response = self.session.get(
                            search_url, 
                            params=search_params, 
                            headers=search_headers,
                            timeout=30
                        )
                        
                        if search_response.status_code == 200:
                            search_result = search_response.json()
                            # 検索結果がリストで、かつ要素が存在する場合
                            if isinstance(search_result, list) and len(search_result) > 0:
                                existing_horse = search_result[0]
                            # 検索結果が辞書で、'items'キーが存在する場合
                            elif isinstance(search_result, dict) and 'items' in search_result and len(search_result['items']) > 0:
                                existing_horse = search_result['items'][0]
                    except Exception as e:
                        logger.warning(f"既存の馬の検索中にエラーが発生しました: {str(e)}")
                        logger.debug(f"検索URL: {search_url}")
                        logger.debug(f"検索パラメータ: {search_params}")
                        logger.debug(f"レスポンス: {search_response.text if hasattr(search_response, 'text') else 'No response text'}")
                
                # オークションIDを保存（元のIDをauction_idとして使用）
                if 'id' in data_to_send:
                    data_to_send['auction_id'] = data_to_send['id']
                    del data_to_send['id']  # IDを削除して新しいレコードを作成
                
                # 必須フィールドの確認と検証
                required_fields = [
                    ('name', str, '文字列'),
                    ('sire', str, '文字列'),
                    ('dam', str, '文字列'),
                    ('damsire', str, '文字列')
                ]
                
                # 不足しているフィールドをチェック
                missing_fields = [field for field, _, _ in required_fields if field not in data_to_send or data_to_send[field] is None]
                if missing_fields:
                    error_msg = f"必須フィールドが不足しています: {', '.join(missing_fields)}"
                    logger.error(error_msg)
                    logger.error(f"データ内容: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
                    return None
                
                # フィールドの型を検証
                validation_errors = []
                for field, expected_type, type_name in required_fields:
                    if field in data_to_send and not isinstance(data_to_send[field], expected_type):
                        actual_type = type(data_to_send[field]).__name__
                        validation_errors.append(f"'{field}' は {type_name} である必要があります (実際の型: {actual_type})")
                
                if validation_errors:
                    error_msg = "フィールドの型が正しくありません: " + "; ".join(validation_errors)
                    logger.error(error_msg)
                    logger.error(f"データ内容: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
                    return None
                
                # リクエストボディのログ出力
                logger.debug(f"送信データ: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
                
                # リクエストヘッダーを設定
                headers = {
                    'Content-Type': 'application/json',
                    'Accept': 'application/json',
                    'Authorization': f'Bearer {self.token}'
                }
                
                # 新しい馬データを送信
                try:
                    # デバッグ用にリクエスト内容をログに出力
                    logger.info(f"送信先URL: {save_url}")
                    logger.info(f"リクエストヘッダー: {headers}")
                    logger.info(f"リクエストボディ: {json.dumps(data_to_send, ensure_ascii=False, indent=2)}")
                    
                    # リクエスト送信
                    response = self.session.post(
                        save_url,
                        json=data_to_send,
                        headers=headers,
                        timeout=60,  # タイムアウトを60秒に延長
                        verify=True  # SSL証明書の検証を有効化
                    )
                    
                    # レスポンスの詳細をログに出力
                    logger.info(f"レスポンスステータス: {response.status_code}")
                    logger.info(f"レスポンスヘッダー: {dict(response.headers)}")
                    logger.info(f"レスポンスボディ: {response.text}")
                    
                    # レスポンスのステータスコードを確認
                    response.raise_for_status()
                    
                    result = response.json()
                    horse_id = result.get('id')
                    logger.info(f"馬データを保存しました: {data_to_send.get('name')} (ID: {horse_id})")
                    
                    # オークション履歴を保存（update-only時はスキップ）
                    if (not update_only) and ('auction_info' in data_to_send):
                        self._save_auction_history(horse_id, data_to_send)
                    
                    return result
                    
                except requests.exceptions.RequestException as e:
                    # エラーの詳細をログに出力
                    logger.error(f"馬データの保存中にエラーが発生しました: {str(e)}")
                    if hasattr(e, 'response') and e.response is not None:
                        logger.error(f"レスポンスステータス: {e.response.status_code if hasattr(e.response, 'status_code') else 'N/A'}")
                        logger.error(f"レスポンスヘッダー: {dict(e.response.headers) if hasattr(e.response, 'headers') else 'N/A'}")
                        logger.error(f"レスポンスボディ: {e.response.text if hasattr(e.response, 'text') else 'N/A'}")
                    else:
                        logger.error("レスポンスがありません。ネットワーク接続を確認してください。")
                    return None
                    
            except Exception as e:
                logger.error(f"馬データの処理中に予期しないエラーが発生しました: {str(e)}")
                logger.error(traceback.format_exc())
                return None
                
        except requests.exceptions.RequestException as e:
            logger.error(f"馬データの処理中にエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
        except Exception as e:
            logger.error(f"馬データの処理中に予期しないエラーが発生しました: {str(e)}")
            logger.error(traceback.format_exc())
            return None
            
    def _save_auction_history(self, horse_id: int, horse_data: dict):
        """オークション履歴を保存する
        
        Args:
            horse_id: 馬のID
            horse_data: 馬のデータ（名前、血統情報、オークション情報を含む）
        """
        try:
            # オークション情報が不足している場合はスキップ
            if not all(key in horse_data for key in ['sold_price', 'auction_date']):
                logger.warning(f"オークション情報が不足しているため、履歴を保存しません: {horse_data.get('name')}")
                return None

            # 血統情報を取得
            horse_name = horse_data.get('name')
            sire_name = horse_data.get('sire')
            dam_name = horse_data.get('dam')
            damsire_name = horse_data.get('damsire')
            
            if not all([horse_name, sire_name, dam_name, damsire_name]):
                logger.warning(f"血統情報が不足しているため、履歴を保存しません: {horse_name}")
                return None

            # オークション履歴のデータを準備
            auction_data = {
                'horse_id': horse_id,
                'horse_name': horse_name,
                'sire_name': sire_name,
                'dam_name': dam_name,
                'damsire_name': damsire_name,
                'auction_date': horse_data['auction_date'],
                'price': horse_data['sold_price'],
                'seller': horse_data.get('seller'),
                'buyer': None,  # 落札者情報は別途取得する必要がある場合がある
                'auction_house': horse_data.get('auction_house', '不明'),
                'auction_name': horse_data.get('auction_name', '不明'),
                'lot_number': horse_data.get('lot_number'),
                'auction_url': horse_data.get('detail_url')
            }
            
            # APIエンドポイント
            base_url = self.api_base_url.rstrip('/')
            
            # オークション履歴を保存
            save_url = f"{base_url}/api/auction_histories"
            logger.info(f"オークション履歴を保存します: {save_url}")
            logger.debug(f"オークション履歴データ: {json.dumps(auction_data, ensure_ascii=False, indent=2)}")
            
            response = self.session.post(
                save_url,
                json=auction_data,
                timeout=30
            )
            
            # レスポンスの確認
            response.raise_for_status()
            result = response.json()
            logger.info(f"オークション履歴を保存しました: {horse_name}, 日付 {auction_data['auction_date']}, 価格 {auction_data['price']}万円")
            return result
            
        except requests.exceptions.RequestException as e:
            error_msg = str(e)
            if hasattr(e, 'response') and e.response is not None:
                error_msg = f"{e.response.status_code} - {e.response.text}"
            logger.error(f"オークション履歴の保存中にエラーが発生しました: {error_msg}")
            return None
        except Exception as e:
            logger.error(f"オークション履歴の保存中に予期しないエラーが発生しました: {str(e)}")
            return None

def main():
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングを実行します')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='出力ディレクトリのパス')
    parser.add_argument('--write-json', action='store_true', default=False,
                      help='JSONファイルを書き出す（デフォルトは書き出さない）')
    parser.add_argument('--update-only', action='store_true', default=False,
                      help='履歴カラム（auction_date/price/seller/sex/age/comment）を更新せず、通常項目のみ更新する')
    args = parser.parse_args()
    
    # クライアントの初期化
    client = ScraperClient()
    
    # 認証
    if not client.authenticate():
        logger.error("認証に失敗したため、スクリプトを終了します")
        return
    
    # スクレイパーの初期化
    config = ScraperConfig(
        use_cache=True,
        max_workers=5,
        max_retries=0,  # リトライを無効化
    )
    # HTML保存を無効化してスクレイパーを初期化
    scraper = ImprovedRakutenScraper(config, save_html=False)
    
    # 出力ディレクトリのパス
    if args.output_dir:
        output_dir = Path(args.output_dir)
    else:
        output_dir = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'horses.json'
    
    try:
        # 馬一覧をスクレイピング
        logger.info("馬一覧のスクレイピングを開始します")
        horses = scraper.scrape_horse_list(max_pages=0)  # 0は全ページ取得
        
        if not horses:
            # 抽出失敗があったか確認
            if hasattr(scraper, 'failed_horses') and scraper.failed_horses:
                logger.error(f"抽出失敗が発生しました。失敗件数: {len(scraper.failed_horses)}")
                logger.error("スクレイピング対象のページ構造が変更されている可能性があります。")
            else:
                logger.error("スクレイピング結果が0件です（全馬保存方針により失敗扱い）。")
                logger.error("1. オークションが開催されていない / 2. 準備中 / 3. ページ構造変更 の可能性")
            sys.exit(1)
            
        logger.info(f"合計 {len(horses)} 件の馬データを取得しました")
        
        # 既存のデータを読み込む
        existing_horses = []
        if output_file.exists():
            try:
                with open(output_file, 'r', encoding='utf-8') as f:
                    existing_horses = json.load(f)
                logger.info(f"既存の{len(existing_horses)}件の馬データを読み込みました")
            except (json.JSONDecodeError, FileNotFoundError) as e:
                logger.warning(f"既存のJSONファイルの読み込みに失敗しました: {str(e)}。新規作成します。")
                existing_horses = []
        
        # 既存の馬データをIDをキーとする辞書に変換
        existing_horses_dict = {str(h.get('id')): h for h in existing_horses if h.get('id') is not None}
        
        # 更新・追加処理
        updated_count = 0
        added_count = 0
        failed_count = 0
        
        for i, horse in enumerate(horses, 1):
            try:
                horse_id = str(horse.get('id'))
                if not horse_id:
                    logger.warning(f"[{i}/{len(horses)}] 馬IDが存在しないためスキップします: {horse.get('name')}")
                    continue
                
                # APIで保存
                response = client.save_horse(horse, update_only=args.update_only)
                
                if response:
                    # 既存の馬データを更新または追加
                    if horse_id in existing_horses_dict:
                        # 既存データを更新
                        existing_horses_dict[horse_id].update(horse)
                        updated_count += 1
                        logger.info(f"[{i}/{len(horses)}] 馬データを更新しました: {horse.get('name')}")
                    else:
                        # 新しいデータを追加
                        existing_horses_dict[horse_id] = horse
                        added_count += 1
                        logger.info(f"[{i}/{len(horses)}] 新しい馬データを追加しました: {horse.get('name')}")
                else:
                    logger.warning(f"[{i}/{len(horses)}] 馬データの保存に失敗しました: {horse.get('name')}")
                    failed_count += 1 # Increment failed_count even if save_horse returns None
                    # Populate scraper.failed_horses for API save failures
                    if not hasattr(scraper, 'failed_horses'):
                        scraper.failed_horses = []
                    scraper.failed_horses.append({
                        'index': i,
                        'horse_name': horse.get('name'),
                        'error': "API保存失敗",
                        'timestamp': datetime.now().isoformat()
                    })
                    
            except Exception as e:
                failed_count += 1
                logger.error(f"馬データの処理中にエラーが発生しました (馬 {i}/{len(horses)}): {str(e)}", exc_info=True)
                # Populate scraper.failed_horses for unexpected errors during processing
                if not hasattr(scraper, 'failed_horses'):
                    scraper.failed_horses = []
                scraper.failed_horses.append({
                    'index': i,
                    'horse_name': horse.get('name'),
                    'error': str(e),
                    'timestamp': datetime.now().isoformat()
                })
                continue
        
        # 更新・追加後のデータをリストに変換
        all_horses = list(existing_horses_dict.values())
        
        # 成否判定（全馬保存が前提）
        total = len(horses)
        success = added_count + updated_count
        failed = failed_count + max(0, total - (added_count + updated_count))

        logger.info(f"SUMMARY: total={total} success={success} failed={failed}")

        # JSON出力はオプション
        if args.write_json and all_horses:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_horses, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"horses.json を出力しました: {output_file}")

        if total == 0 or failed > 0 or success != total:
            logger.error("全馬保存に失敗しました（失敗あり／件数不一致）")
            sys.exit(1)

        logger.info("全馬保存に成功しました")
        
    except Exception as e:
        logger.error(f"スクレイピング中にエラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
