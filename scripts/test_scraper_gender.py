import sys
import os
from improved_scraper import ImprovedRakutenScraper

def test_gender_extraction():
    print("テストモードでスクレイパーを初期化中...")
    scraper = ImprovedRakutenScraper(test_mode=True)
    
    print("\nテスト用の馬データを取得中...")
    horses = scraper.scrape_horse_list(use_cache=False)
    
    print(f"\n取得した馬の数: {len(horses)}")
    
    # センの馬をフィルタリング
    geldings = [h for h in horses if h.get('sex') in ['セ', 'セン']]
    print(f"\nセンの馬の数: {len(geldings)}")
    
    # センの馬の詳細を表示
    if geldings:
        print("\nセンの馬の詳細:")
        for i, horse in enumerate(geldings, 1):
            print(f"{i}. {horse.get('name')} - 性別: {horse.get('sex')}, 年齢: {horse.get('age')}")
    
    # すべての馬の性別を表示
    print("\nすべての馬の性別:")
    for i, horse in enumerate(horses, 1):
        print(f"{i}. {horse.get('name')} - 性別: {horse.get('sex')}, 年齢: {horse.get('age')}")

if __name__ == "__main__":
    test_gender_extraction()
