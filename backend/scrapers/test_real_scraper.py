from rakuten_scraper import RakutenAuctionScraper

def main():
    # スクレイパーを初期化
    scraper = RakutenAuctionScraper()
    
    try:
        # 馬の一覧を取得
        print("馬の一覧を取得中...")
        horses = scraper.scrape_horse_list()
        
        if not horses:
            print("馬の一覧を取得できませんでした")
            return
            
        print(f"{len(horses)}頭の馬を発見しました。")
        
        # 最初の馬の詳細を取得
        first_horse = horses[0]
        print(f"\n馬名: {first_horse.get('name')}")
        print(f"詳細URL: {first_horse.get('detail_url')}")
        
        # 詳細情報を取得
        print("\n詳細情報を取得中...")
        detail = scraper.scrape_horse_detail(first_horse['detail_url'])
        
        if not detail:
            print("詳細情報を取得できませんでした")
            return
            
        # 血統情報を表示
        print("\n=== 取得した血統情報 ===")
        print(f"父: {detail.get('sire', '取得できませんでした')}")
        print(f"母: {detail.get('dam', '取得できませんでした')}")
        print(f"母父: {detail.get('dam_sire', '取得できませんでした')}")
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()
