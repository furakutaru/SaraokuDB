import sys
import os
from bs4 import BeautifulSoup

# Add the parent directory to the path so we can import the scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.rakuten_scraper import RakutenAuctionScraper

def test_pedigree_extraction():
    """Test pedigree extraction from a sample horse detail page"""
    print("=== 血統情報抽出テストを開始 ===")
    
    # Initialize the scraper
    scraper = RakutenAuctionScraper()
    
    # Test with a sample URL or HTML file
    test_url = "https://example.com/horse/detail/123"  # Replace with actual test URL
    
    # Alternatively, load from a saved HTML file for testing
    html_file = os.path.join(os.path.dirname(__file__), 'test_data/horse_detail.html')
    
    try:
        # Try to load from file first
        if os.path.exists(html_file):
            print(f"HTMLファイルから読み込み中: {html_file}")
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            soup = BeautifulSoup(html_content, 'html.parser')
        else:
            # If no test file, try to fetch from URL
            print(f"URLからデータを取得中: {test_url}")
            response = scraper.session.get(test_url)
            response.raise_for_status()
            soup = BeautifulSoup(response.text, 'html.parser')
        
        # Call the pedigree extraction method
        print("\n=== 血統情報抽出を実行中 ===")
        pedigree = scraper._extract_pedigree_from_page(soup)
        
        # Print results
        print("\n=== 抽出結果 ===")
        print(f"父: {pedigree.get('sire', 'N/A')}")
        print(f"母: {pedigree.get('dam', 'N/A')}")
        print(f"母父: {pedigree.get('damsire', 'N/A')}")
        
        # Check if all required fields are present
        required_fields = ['sire', 'dam', 'damsire']
        missing = [field for field in required_fields if not pedigree.get(field) or pedigree[field] == '不明']
        
        if missing:
            print(f"\n警告: 以下の必須フィールドが抽出できませんでした: {', '.join(missing)}")
        else:
            print("\n✅ すべての血統情報が正常に抽出されました")
            
    except Exception as e:
        print(f"\n❌ エラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    test_pedigree_extraction()
