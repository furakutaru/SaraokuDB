import sys
import os
from bs4 import BeautifulSoup

# Add the parent directory to the Python path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

def test_pedigree_extraction():
    # Create an instance of the scraper
    scraper = RakutenAuctionScraper()
    
    # Test cases with various formats
    test_cases = [
        {
            "name": "通常のケース",
            "html": """
            <html><body>
                <div>父：ディープインパクト 母：ウインドインハーヘア 母の父：サンデーサイレンス</div>
            </body></html>
            """,
            "expected": {
                "sire": "ディープインパクト",
                "dam": "ウインドインハーヘア",
                "damsire": "サンデーサイレンス"
            }
        },
        {
            "name": "スペース区切りの母父情報",
            "html": """
            <html><body>
                <div>父：ゴールドシップ 母：トーセンダンス 母の父 ディープインパクト</div>
            </body></html>
            """,
            "expected": {
                "sire": "ゴールドシップ",
                "dam": "トーセンダンス",
                "damsire": "ディープインパクト"
            }
        },
        {
            "name": "括弧表記の母父",
            "html": """
            <html><body>
                <div>父：ロードカナロア 母：アパパネ（母父：ハーツクライ）</div>
            </body></html>
            """,
            "expected": {
                "sire": "ロードカナロア",
                "dam": "アパパネ",
                "damsire": "ハーツクライ"
            }
        }
    ]
    
    # Run tests
    for test in test_cases:
        print(f"\n=== {test['name']} ===")
        soup = BeautifulSoup(test['html'], 'html.parser')
        result = scraper._extract_pedigree_from_page(soup)
        
        # Print results
        print(f"抽出結果: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
        
        # Verify results
        success = True
        for key in test['expected']:
            if result.get(key) != test['expected'][key]:
                print(f"  ✗ {key}: 期待値='{test['expected'][key]}', 実際='{result.get(key)}'")
                success = False
            else:
                print(f"  ✓ {key}: {result.get(key)}")
        
        if success:
            print("  ✅ テスト成功")
        else:
            print("  ❌ テスト失敗")

if __name__ == "__main__":
    test_pedigree_extraction()
