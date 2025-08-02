import sys
import os
import json
from bs4 import BeautifulSoup

# Add the parent directory to the path so we can import the scraper
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from scrapers.rakuten_scraper import RakutenAuctionScraper

def test_extract_seller():
    # Initialize the scraper
    scraper = RakutenAuctionScraper()
    
    # Test case 1: Direct regex match
    test_html_1 = """
    <html>
    <body>
        <div>販売申込者：テスト牧場（北海道）</div>
    </body>
    </html>
    """
    
    # Test case 2: Table-based match
    test_html_2 = """
    <html>
    <body>
        <table>
            <tr>
                <th>販売申込者</th>
                <td>テスト牧場（北海道）</td>
            </tr>
        </table>
    </body>
    </html>
    """
    
    # Test case 3: No seller information
    test_html_3 = """
    <html>
    <body>
        <div>No seller information here</div>
    </body>
    </html>
    """
    
    # Run tests
    print("=== Test 1: Direct regex match ===")
    result1 = scraper._extract_seller(test_html_1)
    print(f"Expected: テスト牧場, Got: {result1}")
    
    print("\n=== Test 2: Table-based match ===")
    result2 = scraper._extract_seller(test_html_2)
    print(f"Expected: テスト牧場, Got: {result2}")
    
    print("\n=== Test 3: No seller information ===")
    result3 = scraper._extract_seller(test_html_3)
    print(f"Expected: (empty string), Got: '{result3}'")

if __name__ == "__main__":
    test_extract_seller()
