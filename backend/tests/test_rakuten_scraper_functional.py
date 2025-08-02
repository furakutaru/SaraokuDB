import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.rakuten_scraper import RakutenAuctionScraper

def test_scrape_horse_list():
    """馬リストのスクレイピングテスト"""
    try:
        # スクレイパーを初期化
        print("スクレイパーを初期化しています...")
        scraper = RakutenAuctionScraper()
        
        # スクレイピング実行（デフォルトのURLを使用）
        print("馬リストの取得を開始します...")
        result = scraper.scrape_horse_list()
        
        if result:
            print(f"✅ スクレイピングに成功しました。{len(result)}件の馬情報を取得しました。")
            print("取得した最初の馬情報:")
            print(result[0] if result else "データがありません")
            return True
        else:
            print("⚠️ スクレイピングは完了しましたが、データが取得できませんでした。")
            return False
            
    except Exception as e:
        print(f"❌ スクレイピング中にエラーが発生しました: {e}")
        return False

if __name__ == "__main__":
    test_scrape_horse_list()
