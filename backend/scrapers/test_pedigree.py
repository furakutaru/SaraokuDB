from bs4 import BeautifulSoup
from rakuten_scraper import RakutenAuctionScraper

def test_extract_pedigree():
    # テスト用のHTMLを読み込む
    with open('test_pedigree.html', 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # スクレイパーインスタンスを作成
    scraper = RakutenAuctionScraper()
    
    # 血統情報を抽出
    result = scraper._extract_pedigree_from_page(soup)
    
    # 結果を表示
    print("=== テスト結果 ===")
    print(f"父: {result.get('sire')}")
    print(f"母: {result.get('dam')}")
    print(f"母父: {result.get('dam_sire')}")
    
    # 期待値との比較
    expected = {
        'sire': 'テスト父馬',
        'dam': 'テスト母馬',
        'dam_sire': 'テスト母父馬'
    }
    
    if (result.get('sire') == expected['sire'] and 
        result.get('dam') == expected['dam'] and 
        result.get('dam_sire') == expected['dam_sire']):
        print("✅ テスト成功: 期待通りの結果が得られました")
    else:
        print("❌ テスト失敗: 期待値と異なります")
        print(f"期待値: {expected}")
        print(f"実際の値: {result}")

if __name__ == "__main__":
    test_extract_pedigree()
