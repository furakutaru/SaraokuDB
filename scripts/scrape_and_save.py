#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import json
import logging
import requests
from datetime import datetime
from dotenv import load_dotenv
from pathlib import Path

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
        self.api_base_url = os.getenv('API_BASE_URL', 'http://localhost:8001/api')
        self.api_username = os.getenv('API_USERNAME', 'admin')
        self.api_password = os.getenv('API_PASSWORD', 'secret')
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
            auth_url = f"{self.api_base_url}/token"
            if self.api_base_url.endswith('/api'):
                auth_url = f"{self.api_base_url}/token"
            elif not self.api_base_url.endswith('/'):
                auth_url = f"{self.api_base_url}/token"
            
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
        except Exception as e:
            logger.error(f"認証に失敗しました: {e}")
            if hasattr(e, 'response') and hasattr(e.response, 'text'):
                logger.error(f"エラーレスポンス: {e.response.text}")
            return False
    
    def save_horse(self, horse_data):
        """馬データをAPI経由で保存"""
        if not self.token and not self.authenticate():
            logger.error('認証に失敗したため、データを保存できません')
            return False
        
        try:
            # データのコピーを作成（元データを変更しないため）
            data_to_send = horse_data.copy()
            
            # race_recordsをrace_recordにマッピング
            if 'race_records' in data_to_send:
                data_to_send['race_record'] = data_to_send.pop('race_records')
            
            response = self.session.post(
                f"{self.api_base_url}/horses",
                json=data_to_send
            )
            response.raise_for_status()
            logger.info(f"馬データを保存しました: {data_to_send.get('name')}")
            return True
        except requests.exceptions.HTTPError as e:
            logger.error(f"APIリクエストエラー: {e.response.status_code} - {e.response.text}")
            return False
        except Exception as e:
            logger.error(f"データ保存中にエラーが発生しました: {str(e)}")
            return False

def main():
    # クライアントの初期化
    client = ScraperClient()
    
    # 認証
    if not client.authenticate():
        logger.error("認証に失敗したため、スクリプトを終了します")
        return
    
    # スクレイピングの実行（モックデータを使用）
    # 実際のスクレイピング処理は別のスクリプトで実装
    current_date = datetime.now().strftime("%Y%m%d")
    mock_horse = {
        "name": "テスト馬",
        "auction_id": f"TEST-{current_date}-001",  # 必須フィールドを追加
        "sex": "牡",
        "age": 3,
        "sire": "テスト父",
        "dam": "テスト母",
        "auction_date": datetime.now().strftime("%Y-%m-%d"),
        "sold_price": 10000000,
        "seller": "テストセラー",
        "comment": "スクリプトからのテストデータ"
    }
    
    # データの保存
    client.save_horse(mock_horse)
    logger.info("スクリプトが正常に完了しました")

if __name__ == "__main__":
    main()
