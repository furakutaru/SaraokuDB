#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
import requests
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('api_test.log')
    ]
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
from dotenv import load_dotenv
load_dotenv(Path(__file__).parent / 'backend' / '.env')

def test_health_check(base_url):
    """ヘルスチェックエンドポイントのテスト"""
    try:
        url = f"{base_url}/api/health"
        logger.info(f"Testing health check: {url}")
        
        response = requests.get(url, timeout=10)
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response: {response.text}")
        
        if response.status_code == 200:
            logger.info("✅ Health check passed")
            return True
        else:
            logger.error(f"❌ Health check failed with status {response.status_code}")
            return False
            
    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return False

def test_authentication(base_url, username, password):
    """認証エンドポイントのテスト"""
    try:
        url = f"{base_url}/api/token"
        logger.info(f"Testing authentication: {url}")
        
        # 認証リクエスト
        auth_data = {
            "username": username,
            "password": password
        }
        
        headers = {
            "Content-Type": "application/x-www-form-urlencoded",
            "Accept": "application/json"
        }
        
        logger.info(f"Sending auth request to {url}")
        logger.info(f"Headers: {headers}")
        logger.info(f"Data: {auth_data}")
        
        response = requests.post(
            url,
            data=auth_data,
            headers=headers,
            timeout=30
        )
        
        logger.info(f"Status Code: {response.status_code}")
        logger.info(f"Response Headers: {dict(response.headers)}")
        logger.info(f"Response Body: {response.text}")
        
        if response.status_code == 200:
            token = response.json().get("access_token")
            if token:
                logger.info("✅ Authentication successful")
                logger.info(f"Access Token: {token[:20]}...")
                return token
            else:
                logger.error("❌ No access token in response")
                return None
        else:
            logger.error(f"❌ Authentication failed with status {response.status_code}")
            return None
            
    except Exception as e:
        logger.error(f"Authentication error: {str(e)}", exc_info=True)
        return None

def main():
    # 環境変数から設定を読み込む
    base_url = os.getenv("PROD_API_BASE_URL", "http://localhost:8000")
    username = os.getenv("PROD_API_USERNAME")
    password = os.getenv("PROD_API_PASSWORD")
    
    logger.info("=" * 50)
    logger.info("Starting API Tests")
    logger.info(f"Base URL: {base_url}")
    logger.info(f"Username: {'*' * len(username) if username else 'Not set'}")
    logger.info("=" * 50)
    
    # ヘルスチェック
    logger.info("\n🔍 Testing Health Check")
    health_ok = test_health_check(base_url)
    
    # 認証テスト
    logger.info("\n🔑 Testing Authentication")
    if not username or not password:
        logger.warning("Skipping authentication test: Username or password not set")
    else:
        token = test_authentication(base_url, username, password)
    
    logger.info("\n" + "=" * 50)
    logger.info("API Tests Completed")
    logger.info("=" * 50)

if __name__ == "__main__":
    main()
