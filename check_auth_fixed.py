import os
import requests
from dotenv import load_dotenv
import logging
from urllib.parse import urljoin

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

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
    
    base_url = os.getenv('PROD_API_BASE_URL').rstrip('/')
    username = os.getenv('PROD_API_USERNAME')
    password = os.getenv('PROD_API_PASSWORD')
    
    # 環境変数のログ出力（パスワードはマスク）
    logger.info(f"API Base URL: {base_url}")
    logger.info(f"Username: {username}")
    logger.info("Password: ********")
    
    try:
        # 認証トークンを取得
        logger.info("認証トークンを取得中...")
        auth_url = f"{base_url}/api/auth/token"
        
        logger.debug(f"リクエストURL: {auth_url}")
        logger.debug(f"ユーザー名: {username}")
        
        # フォームデータとして送信
        response = requests.post(
            auth_url,
            data={
                "username": username,
                "password": password
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"},
            timeout=10
        )
        
        # レスポンスのログ出力
        logger.info(f"ステータスコード: {response.status_code}")
        logger.debug("レスポンスヘッダー:")
        for key, value in response.headers.items():
            logger.debug(f"  {key}: {value}")
        
        # レスポンスの処理
        try:
            json_response = response.json()
            logger.debug("レスポンスボディ:")
            logger.debug(json_response)
            
            if response.status_code == 200 and 'access_token' in json_response:
                token_preview = f"{json_response['access_token'][:10]}..." if json_response['access_token'] else "(空)"
                logger.info("✅ 認証に成功しました！")
                logger.info(f"トークン: {token_preview}")
                logger.info(f"トークンタイプ: {json_response.get('token_type', 'N/A')}")
                
                # トークンを使って保護されたエンドポイントにアクセス
                logger.info("\n保護されたエンドポイントにアクセス中...")
                protected_url = f"{base_url}/api/horses/"
                headers = {"Authorization": f"Bearer {json_response['access_token']}"}
                
                protected_response = requests.get(protected_url, headers=headers, timeout=10)
                logger.info(f"保護されたエンドポイントのステータスコード: {protected_response.status_code}")
                
                if protected_response.status_code == 200:
                    logger.info("✅ 保護されたエンドポイントへのアクセスに成功しました！")
                else:
                    logger.error(f"❌ 保護されたエンドポイントへのアクセスに失敗しました: {protected_response.text}")
                
                return True
            else:
                error_msg = json_response.get('detail', '不明なエラー')
                logger.error(f"❌ 認証に失敗しました: {error_msg}")
                return False
                
        except ValueError:
            logger.error("❌ レスポンスがJSON形式ではありません。")
            logger.debug(f"レスポンス本文: {response.text[:500]}")
            return False
            
    except requests.exceptions.RequestException as e:
        logger.error(f"❌ リクエスト中にエラーが発生しました: {e}")
        if hasattr(e, 'response') and e.response is not None:
            logger.error(f"レスポンス: {e.response.text}")
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
    # 必要に応じてコメントを外してください
    # import http.client
    # http.client.HTTPConnection.debuglevel = 1
    # logging.basicConfig()
    # logging.getLogger().setLevel(logging.DEBUG)
    # requests_log = logging.getLogger("urllib3")
    # requests_log.setLevel(logging.DEBUG)
    # requests_log.propagate = True
    
    exit_code = main()
    exit(exit_code)
