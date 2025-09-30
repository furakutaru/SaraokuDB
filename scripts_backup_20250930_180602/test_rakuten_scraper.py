import requests
from bs4 import BeautifulSoup
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_rakuten_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

def main():
    # 楽天競馬オークションのURL
    url = "https://auction.keiba.rakuten.co.jp/"
    
    try:
        # ユーザーエージェントを設定（PC向け）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        logger.info(f"{url} にアクセス中...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()  # ステータスコードが200以外の場合は例外を発生
        
        # 文字コードを設定
        response.encoding = response.apparent_encoding
        
        # HTMLをパース
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ページのタイトルを取得
        title = soup.title.string if soup.title else 'タイトルが見つかりません'
        logger.info(f"ページタイトル: {title}")
        
        # 馬の情報を探す（実際のHTML構造に合わせて修正が必要）
        horse_elements = soup.select('.horse-info')  # このセレクタは仮のものです
        
        if horse_elements:
            logger.info(f"馬の要素を {len(horse_elements)} 件見つけました。")
            
            # 最初の数件の馬名を表示
            for i, horse in enumerate(horse_elements[:5], 1):
                name = horse.select_one('.horse-name')  # このセレクタは仮のものです
                if name:
                    logger.info(f"{i}. {name.text.strip()}")
                else:
                    logger.warning(f"{i}件目の馬名を抽出できませんでした。")
        else:
            logger.warning("馬の要素が見つかりませんでした。")
            
            # HTMLの一部をデバッグ出力（最初の1000文字）
            logger.debug(f"HTMLの先頭1000文字: {response.text[:1000]}")
        
    except requests.RequestException as e:
        logger.error(f"リクエスト中にエラーが発生しました: {e}")
    except Exception as e:
        logger.error(f"予期しないエラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
