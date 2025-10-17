#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
import sys
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

# スクリプトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

# カスタムスクレイパーから必要なクラスをインポート
from improved_scraper import ImprovedRakutenScraper, ScraperConfig

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
            # ベースURLの正規化
            base_url = self.api_base_url.rstrip('/')
            
            # APIエンドポイントの構築
            if not base_url.endswith('/api'):
                base_url = f"{base_url}/api"
            
            auth_url = f"{base_url}/token"
            logger.info(f"認証を試みます: {auth_url} (ユーザー: {self.api_username})")
            
            # 認証リクエストの送信 (form-data形式で送信)
            response = self.session.post(
                auth_url,
                data={
                    "username": self.api_username,
                    "password": self.api_password,
                    "grant_type": "password"
                },
                headers={"Content-Type": "application/x-www-form-urlencoded"}
            )
            
            # レスポンスの確認
            response.raise_for_status()
            token_data = response.json()
            
            # トークンの取得とヘッダーへの設定
            self.token = token_data.get("access_token")
            if self.token:
                self.session.headers.update({"Authorization": f"Bearer {self.token}"})
                logger.info("認証に成功しました")
                return True
            else:
                logger.error("トークンの取得に失敗しました")
                logger.error(f"レスポンス: {token_data}")
                return False
                
        except requests.exceptions.RequestException as e:
            logger.error(f"認証リクエストに失敗しました: {str(e)}")
            if hasattr(e, 'response') and e.response is not None:
                logger.error(f"ステータスコード: {e.response.status_code}")
                if hasattr(e.response, 'text') and e.response.text:
                    logger.error(f"エラーレスポンス: {e.response.text}")
            return False
        except json.JSONDecodeError as e:
            logger.error(f"レスポンスのJSON解析に失敗しました: {str(e)}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"生のレスポンス: {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"予期せぬエラーが発生しました: {str(e)}", exc_info=True)
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
    output_dir = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data'
    output_dir.mkdir(parents=True, exist_ok=True)
    output_file = output_dir / 'horses.json'
    
    try:
        # 馬一覧をスクレイピング
        logger.info("馬一覧のスクレイピングを開始します")
        horses = scraper.scrape_horse_list(max_pages=0)  # 0は全ページ取得
        
        if not horses:
            logger.warning("スクレイピング結果が0件です")
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
