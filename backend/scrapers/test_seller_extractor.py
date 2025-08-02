import re
from bs4 import BeautifulSoup
from fixed_seller_extractor import _extract_seller

class TestSellerExtractor:
    def __init__(self):
        self.extractor = type('obj', (object,), {'_extract_seller': _extract_seller})()
    
    def test_direct_regex(self):
        """Test direct regex pattern matching"""
        test_text = """
        販売申込者：テスト牧場（北海道）
        その他の情報...
        """
        result = self.extractor._extract_seller(test_text)
        print(f"Test direct_regex: {result} (Expected: テスト牧場)")
        return result == "テスト牧場"
    
    def test_table_extraction(self):
        """Test extraction from HTML table"""
        test_html = """
        <table>
            <tr><th>販売申込者</th><td>テスト牧場</td></tr>
            <tr><th>その他</th><td>情報</td></tr>
        </table>
        """
        result = self.extractor._extract_seller(test_html)
        print(f"Test table_extraction: {result} (Expected: テスト牧場)")
        return result == "テスト牧場"
    
    def test_no_seller(self):
        """Test case when no seller info is found"""
        test_text = "このテキストには販売申込者情報が含まれていません"
        result = self.extractor._extract_seller(test_text)
        print(f"Test no_seller: {result} (Expected: 空文字列)")
        return result == ""

if __name__ == "__main__":
    tester = TestSellerExtractor()
    tests = [
        tester.test_direct_regex(),
        tester.test_table_extraction(),
        tester.test_no_seller()
    ]
    
    print(f"\nテスト結果: {sum(tests)}/{len(tests)} 成功")
    if all(tests):
        print("✅ すべてのテストが成功しました！")
    else:
        print("❌ 一部のテストが失敗しました")
