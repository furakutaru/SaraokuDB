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
load_dotenv(Path(__file__).parent.parent / 'backend' / '.env')

class ScraperClient:
    def __init__(self):
        # 本番環境の認証情報を優先的に使用
        self.api_base_url = os.getenv('PROD_API_BASE_URL')
        self.api_username = os.getenv('PROD_API_USERNAME')
        self.api_password = os.getenv('PROD_API_PASSWORD')
        
        # ローカル開発環境の認証情報
        local_base_url = os.getenv('LOCAL_API_BASE_URL', 'http://localhost:8001')
        local_username = os.getenv('LOCAL_API_USERNAME', 'admin')
        local_password = os.getenv('LOCAL_API_PASSWORD', 'secret')
        
        # 環境の判定
        is_production = os.getenv('ENV') == 'production' or os.getenv('GITHUB_ACTIONS') == 'true'
        
        if not is_production and not all([self.api_base_url, self.api_username, self.api_password]):
            logger.warning("ローカル開発環境のため、ローカル用の認証情報を使用します")
            self.api_base_url = local_base_url
            self.api_username = local_username
            self.api_password = local_password
        elif not all([self.api_base_url, self.api_username, self.api_password]):
            raise ValueError("本番環境の認証情報が設定されていません。PROD_API_BASE_URL, PROD_API_USERNAME, PROD_API_PASSWORD を設定してください")
            
        self.api_base_url = self.api_base_url.rstrip('/')
        logger.info(f"API Base URL: {self.api_base_url} (ユーザー: {self.api_username})")
        
        self.token = None
        self.session = requests.Session()
        
        # セッションのヘッダーを設定
        self.session.headers.update({
            'User-Agent': 'SaraokuDB-Scraper/1.0',
            'Accept': 'application/json',
            'Content-Type': 'application/json'
        })
    
    def authenticate(self):
        """API認証を行いトークンを取得"""
        try:
            if not all([self.api_base_url, self.api_username, self.api_password]):
                logger.error("認証情報が不足しています。環境変数を確認してください。")
                logger.error(f"API_BASE_URL: {'設定済み' if self.api_base_url else '未設定'}")
                logger.error(f"API_USERNAME: {'設定済み' if self.api_username else '未設定'}")
                logger.error(f"API_PASSWORD: {'設定済み' if self.api_password else '未設定'}")
                return False

            # ベースURLの正規化
            base_url = self.api_base_url.rstrip('/')
            
            # APIエンドポイントの構築（/api/auth/token を使用）
            auth_url = f"{base_url}/api/auth/token"  # 認証エンドポイントを修正
            logger.info(f"認証を試みます: {auth_url} (ユーザー: {self.api_username})")
            
            # 認証リクエストの送信 (OAuth2互換形式)
            auth_data = {
                'username': self.api_username,
                'password': self.api_password
            }
            
            # デバッグ用ログ
            logger.debug(f"認証リクエストURL: {auth_url}")
            logger.debug(f"認証リクエストデータ: {auth_data}")
            
            # セッションを使用せずに直接リクエストを送信
            headers = {
                'Content-Type': 'application/x-www-form-urlencoded',
                'User-Agent': 'SaraokuDB-Scraper/1.0',
                'Accept': 'application/json'
            }
            
            logger.debug(f"リクエストヘッダー: {headers}")
            
            try:
                # リクエストデータをURLエンコードされた形式に変換
                import urllib.parse
                encoded_data = urllib.parse.urlencode({
                    'username': self.api_username,
                    'password': self.api_password
                })
                
                # リクエストを送信
                response = requests.post(
                    auth_url,
                    data=encoded_data,
                    headers=headers,
                    allow_redirects=True,
                    timeout=30  # 30秒のタイムアウトを設定
                )
                
                logger.debug(f"認証レスポンス: {response.status_code} - {response.text}")
                
                # レスポンスの検証
                response.raise_for_status()
                
                # トークンの抽出
                try:
                    token_data = response.json()
                    if not token_data.get('access_token'):
                        logger.error(f"トークンがレスポンスに含まれていません: {token_data}")
                        return False
                        
                    self.token = token_data['access_token']
                    
                    # セッションのヘッダーを更新
                    self.session.headers.update({
                        "Authorization": f"Bearer {self.token}",
                        "Content-Type": "application/json"
                    })
                    logger.info("認証に成功しました")
                    return True
                    
                except ValueError as e:
                    logger.error(f"レスポンスのJSON解析に失敗しました: {e}")
                    logger.error(f"レスポンス本文: {response.text}")
                    return False
            
            except requests.exceptions.Timeout:
                logger.error("認証リクエストがタイムアウトしました")
                return False
                
            except requests.exceptions.TooManyRedirects:
                logger.error("リダイレクトが多すぎます。URLを確認してください")
                return False
            
        except requests.exceptions.RequestException as e:
            logger.error(f"認証リクエストに失敗しました: {e}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"ステータスコード: {e.response.status_code}")
                try:
                    logger.error(f"レスポンスヘッダー: {dict(e.response.headers)}")
                    logger.error(f"レスポンス本文: {e.response.text}")
                except Exception as ex:
                    logger.error(f"レスポンスの解析中にエラーが発生しました: {ex}")
            return False
            
        except json.JSONDecodeError as e:
            logger.error(f"レスポンスのJSON解析に失敗しました: {e}")
            if 'response' in locals():
                logger.error(f"生のレスポンス: {response.text}")
            return False
            
        except Exception as e:
            logger.error(f"認証中に予期せぬエラーが発生しました: {str(e)}\n{traceback.format_exc()}")
            return False
    
    def save_horse(self, horse_data):
        """馬データをAPI経由で保存"""
        if not self.token and not self.authenticate():
            logger.error('認証に失敗したため、データを保存できません')
            return False
        
        try:
            # データのコピーを作成（元データを変更しないため）
            data_to_send = horse_data.copy()
            
            # 必須フィールドのバリデーションと型変換
            if 'image_url' not in data_to_send or data_to_send['image_url'] is None:
                data_to_send['image_url'] = ""  # 空文字をデフォルト値として設定
            
            # disease_tagsがリストの場合はカンマ区切りの文字列に変換
            if 'disease_tags' in data_to_send and isinstance(data_to_send['disease_tags'], list):
                data_to_send['disease_tags'] = ", ".join(data_to_send['disease_tags'])
            elif 'disease_tags' not in data_to_send or data_to_send['disease_tags'] is None:
                data_to_send['disease_tags'] = ""  # 空文字をデフォルト値として設定
            
            # race_recordsをrace_recordにマッピング
            if 'race_records' in data_to_send:
                data_to_send['race_record'] = data_to_send.pop('race_records')
            
            response = self.session.post(
                f"{self.api_base_url}/horses",
                json=data_to_send
            )
            response.raise_for_status()
            logger.info(f"馬データを保存しました: {data_to_send.get('name')}")
            return response.json()
        except requests.exceptions.HTTPError as e:
            if e.response is not None:
                logger.error(f"APIリクエストエラー: {e.response.status_code} - {e.response.text}")
            else:
                logger.error(f"APIリクエストエラー: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"馬データの保存中にエラーが発生しました: {str(e)}")
            return False

def main():
    import argparse
    
    # コマンドライン引数の解析
    parser = argparse.ArgumentParser(description='楽天競馬オークションのスクレイピングを実行します')
    parser.add_argument('--output-dir', type=str, default=None,
                      help='出力ディレクトリのパス')
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
        max_workers=5
    )
    scraper = ImprovedRakutenScraper(config)
    
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
            logger.warning("スクレイピング結果が0件です。以下のいずれかの可能性があります：")
            logger.warning("1. オークションが開催されていない")
            logger.warning("2. オークション準備中でデータが公開されていない")
            logger.warning("3. スクレイピング対象のページ構造が変更されている")
            logger.info("警告は出していますが、処理は正常終了とします。")
            # 0件でもエラー終了せずに正常終了する
            return
            
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
        
        for i, horse in enumerate(horses, 1):
            try:
                horse_id = str(horse.get('id'))
                if not horse_id:
                    logger.warning(f"[{i}/{len(horses)}] 馬IDが存在しないためスキップします: {horse.get('name')}")
                    continue
                
                # APIで保存
                response = client.save_horse(horse)
                
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
                    
            except Exception as e:
                logger.error(f"馬データの処理中にエラーが発生しました: {str(e)}", exc_info=True)
                continue
        
        # 更新・追加後のデータをリストに変換
        all_horses = list(existing_horses_dict.values())
        
        # データを保存
        if all_horses:
            with open(output_file, 'w', encoding='utf-8') as f:
                json.dump(all_horses, f, ensure_ascii=False, indent=2, default=str)
            logger.info(f"馬データを保存しました - 合計: {len(all_horses)}件 (新規: {added_count}件, 更新: {updated_count}件)")
        else:
            logger.warning("保存する馬データがありませんでした")
                
        logger.info("すべての処理が完了しました")
        
    except Exception as e:
        logger.error(f"スクレイピング中にエラーが発生しました: {str(e)}", exc_info=True)
        raise

if __name__ == "__main__":
    main()
