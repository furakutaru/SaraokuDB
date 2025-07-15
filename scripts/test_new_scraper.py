#!/usr/bin/env python3
"""
新しいスクレイピングスクリプトをテストするスクリプト
"""

import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend'))

from scrapers.rakuten_scraper import RakutenAuctionScraper
import json

def test_scraper():
    """スクレイピングスクリプトをテスト"""
    print("=== 新しいスクレイピングスクリプトのテスト ===")
    
    scraper = RakutenAuctionScraper()
    
    try:
        # 全馬のデータを取得
        horses = scraper.scrape_all_horses()
        
        if horses:
            print(f"\n取得した馬データ: {len(horses)}頭")
            
            # 最初の馬のデータを表示
            if horses:
                first_horse = horses[0]
                print(f"\n最初の馬のデータ:")
                print(f"  名前: {first_horse.get('name', 'N/A')}")
                print(f"  性別: {first_horse.get('sex', 'N/A')}")
                print(f"  年齢: {first_horse.get('age', 'N/A')}")
                print(f"  賞金: {first_horse.get('total_prize_start', 'N/A')}円")
                print(f"  落札価格: {first_horse.get('sold_price', 'N/A')}円")
                print(f"  販売者: {first_horse.get('seller', 'N/A')}")
                print(f"  父: {first_horse.get('sire', 'N/A')}")
                print(f"  母: {first_horse.get('dam', 'N/A')}")
                print(f"  成績: {first_horse.get('race_record', 'N/A')}")
            
            # 結果をJSONファイルに保存
            with open('test_scraping_result.json', 'w', encoding='utf-8') as f:
                json.dump(horses, f, ensure_ascii=False, indent=2)
            
            print(f"\n結果を test_scraping_result.json に保存しました")
            
        else:
            print("馬データを取得できませんでした")
            
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_scraper() 