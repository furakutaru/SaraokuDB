import sys
import os
from rakuten_scraper import RakutenAuctionScraper

def main():
    print("=== 楽天オークションスクレイパーテスト開始 ===")
    
    # スクレイパーインスタンスの作成
    try:
        scraper = RakutenAuctionScraper()
        print("スクレイパーの初期化に成功しました。")
    except Exception as e:
        print(f"スクレイパーの初期化中にエラーが発生しました: {e}")
        return 1
    
    # 馬リストの取得テスト（最大5頭）
    try:
        print("\n=== 馬リストの取得を開始します ===")
        horses = scraper.scrape_horse_list(max_horses=5)
        
        if not horses:
            print("警告: 馬のリストを取得できませんでした。")
            return 1
            
        print(f"\n=== 取得した馬のリスト（{len(horses)}頭）===")
        for i, horse in enumerate(horses, 1):
            print(f"{i}. {horse.get('name', '名前不明')}")
            print(f"   URL: {horse.get('detail_url', 'URLなし')}")
            
    except Exception as e:
        print(f"\n!!! エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()
        return 1
        
    print("\n=== テストが正常に完了しました ===")
    return 0

if __name__ == "__main__":
    sys.exit(main())
