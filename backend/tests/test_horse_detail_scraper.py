import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.rakuten_scraper import RakutenAuctionScraper

def test_scrape_horse_detail():
    """馬の詳細ページのスクレイピングテスト"""
    try:
        # スクレイパーを初期化
        print("スクレイパーを初期化しています...")
        scraper = RakutenAuctionScraper()
        
        # テスト用の馬詳細ページURL（前回のテストで取得したURLを使用）
        test_url = "https://keiba.r10s.jp/auction/data/item/1/250803_horse_01/250803_horse_01_bt.pdf"
        
        print(f"テスト用URL: {test_url} から詳細情報を取得します...")
        
        # スクレイピング実行
        horse_data = scraper.scrape_horse_detail(test_url)
        
        if horse_data:
            print("✅ 詳細情報の取得に成功しました。")
            print("\n=== 取得した馬の詳細情報 ===")
            for key, value in horse_data.items():
                print(f"{key}: {value}")
            return True
        else:
            print("⚠️ 詳細情報の取得に失敗しました。")
            return False
            
    except Exception as e:
        print(f"❌ スクレイピング中にエラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_scrape_horse_detail()
