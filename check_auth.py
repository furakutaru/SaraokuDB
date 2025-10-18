import os
import requests
from dotenv import load_dotenv
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# .envファイルから環境変数を読み込む
def load_environment():
    """環境変数を読み込む"""
    env_path = os.path.join(os.path.dirname(__file__), '.env')
    if os.path.exists(env_path):
        load_dotenv(env_path)
        logger.info(".envファイルを読み込みました")
    else:
        logger.warning(".envファイルが見つかりません。環境変数から読み込みます。")
    
    required_vars = ['PROD_API_BASE_URL', 'PROD_API_USERNAME', 'PROD_API_PASSWORD']
    missing_vars = [var for var in required_vars if not os.getenv(var)]
    
    if missing_vars:
        logger.error(f"以下の必須環境変数が設定されていません: {', '.join(missing_vars)}")
        return False
    
    return True

def check_auth():
    """認証チェックを実行する"""
    if not load_environment():
        return False
    
    base_url = os.getenv('PROD_API_BASE_URL')
    username = os.getenv('PROD_API_USERNAME')
    password = os.getenv('PROD_API_PASSWORD')
    
    # 環境変数のログ出力（パスワードはマスク）
    logger.info(f"API Base URL: {base_url}")
    logger.info(f"Username: {username}")
    logger.info("Password: ********")
    
    try:
        # 認証トークンを取得
        logger.info("認証トークンを取得中...")
        auth_url = f"{base_url.rstrip('/')}/api/auth/token"
        
        logger.debug(f"リクエストURL: {auth_url}")
        logger.debug(f"リクエストボディ: username={username}&password=******")
        
        response = requests.post(
            auth_url,
            data={
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10  # 10秒でタイムアウト
        )
        
        # レスポンスのログ出力
        logger.info(f"ステータスコード: {response.status_code}")
        logger.debug("レスポンスヘッダー:")
        for key, value in response.headers.items():
            logger.debug(f"  {key}: {value}")
        
        try:
            json_response = response.json()
            logger.debug("レスポンスボディ:")
            logger.debug(json_response)
            
            if response.status_code == 200 and 'access_token' in json_response:
                # トークンの一部のみ表示（セキュリティのため）
                token_preview = f"{json_response['access_token'][:10]}..." if json_response['access_token'] else "(空)"
                logger.info(f"✅ 認証に成功しました！")
                logger.info(f"トークン: {token_preview}")
                
                # トークンの有効期限を表示（もしあれば）
                if 'expires_in' in json_response:
                    from datetime import datetime, timedelta
                    expires_in = int(json_response['expires_in'])
                    expiry_time = datetime.now() + timedelta(seconds=expires_in)
                    logger.info(f"トークン有効期限: {expiry_time.strftime('%Y-%m-%d %H:%M:%S')} (あと{expires_in//3600}時間{expires_in%3600//60}分)")
                
                return True
                
            else:
                error_msg = json_response.get('detail', '不明なエラー')
                logger.error(f"❌ 認証に失敗しました: {error_msg}")
                return False
                
        except ValueError:
            logger.error("❌ レスポンスがJSON形式ではありません。")
            logger.debug(f"レスポンス本文: {response.text[:500]}")  # 最初の500文字のみ表示
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ リクエスト中にエラーが発生しました: {e}")
        return False

def main():
    """メイン関数"""
    print("=" * 50)
    print("認証チェックを開始します")
    print("=" * 50)
    
    if check_auth():
        print("\n✅ 認証チェックが正常に完了しました")
        return 0
    else:
        print("\n❌ 認証チェックに失敗しました")
        return 1

if __name__ == "__main__":
    # デバッグ用にHTTPリクエスト/レスポンスの詳細を表示
    # コメントアウトを外すと詳細なデバッグ情報が表示されます
    # import http.client
    # http.client.HTTPConnection.debuglevel = 1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True
    
    exit_code = main()
    exit(exit_code)
