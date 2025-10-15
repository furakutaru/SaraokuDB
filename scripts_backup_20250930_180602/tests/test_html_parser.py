"""
HTMLパーサーユーティリティのユニットテスト
"""
import unittest
from bs4 import BeautifulSoup

from core.utils.html_parser import HTMLParser

class TestHTMLParser(unittest.TestCase):
    """HTMLParserクラスのテスト"""
    
    def setUp(self):
        """テスト用のHTMLをセットアップ"""
        self.html = """
        <html>
            <head><title>Test Page</title></head>
            <body>
                <div class="container">
                    <h1>Test Heading</h1>
                    <div class="content">
                        <p class="text">Paragraph 1</p>
                        <p class="text">Paragraph 2</p>
                        <p class="special">Special Text</p>
                    </div>
                    <div class="info" data-id="123">
                        <span class="label">Name:</span>
                        <span class="value">Test Name</span>
                    </div>
                    <ul class="list">
                        <li>Item 1</li>
                        <li>Item 2</li>
                        <li>Item 3</li>
                    </ul>
                    <div class="hidden" style="display: none;">Hidden Content</div>
                </div>
            </body>
        </html>
        """
        self.parser = HTMLParser(self.html)
    
    def test_find_element(self):
        """単一要素の検索テスト"""
        # タグ名で検索
        h1 = self.parser.find('h1')
        self.assertIsNotNone(h1)
        self.assertEqual(h1.get_text(strip=True), "Test Heading")
        
        # クラス名で検索
        content = self.parser.find(class_='content')
        self.assertIsNotNone(content)
        
        # 存在しない要素
        non_existent = self.parser.find('non-existent')
        self.assertIsNone(non_existent)
    
    def test_find_all_elements(self):
        """複数要素の検索テスト"""
        # クラス名で複数要素を検索
        paragraphs = self.parser.find_all('p', class_='text')
        self.assertEqual(len(paragraphs), 2)
        self.assertEqual(paragraphs[0].get_text(strip=True), "Paragraph 1")
        self.assertEqual(paragraphs[1].get_text(strip=True), "Paragraph 2")
        
        # 存在しない要素
        non_existent = self.parser.find_all('non-existent')
        self.assertEqual(len(non_existent), 0)
    
    def test_get_text(self):
        """テキスト取得のテスト"""
        # 単一要素のテキスト取得
        text = self.parser.get_text('h1')
        self.assertEqual(text, "Test Heading")
        
        # デフォルト値のテスト
        text = self.parser.get_text('non-existent', default="Default Text")
        self.assertEqual(text, "Default Text")
        
        # 複数要素の最初のテキスト取得
        text = self.parser.get_text('p', first_only=True)
        self.assertEqual(text, "Paragraph 1")
    
    def test_get_attribute(self):
        """属性値取得のテスト"""
        # データ属性の取得
        data_id = self.parser.get_attribute('div.info', 'data-id')
        self.assertEqual(data_id, "123")
        
        # 存在しない属性
        non_existent = self.parser.get_attribute('div.info', 'non-existent')
        self.assertIsNone(non_existent)
        
        # デフォルト値のテスト
        non_existent = self.parser.get_attribute('div.info', 'non-existent', default="default")
        self.assertEqual(non_existent, "default")
    
    def test_extract_text_with_regex(self):
        """正規表現によるテキスト抽出のテスト"""
        # 正規表現に一致するテキストを抽出
        pattern = r'Item (\d+)'
        matches = self.parser.extract_text_with_regex('li', pattern)
        self.assertEqual(matches, ['1', '2', '3'])
        
        # 一致しないパターン
        matches = self.parser.extract_text_with_regex('p', r'No Match')
        self.assertEqual(matches, [])
    
    def test_extract_first_match(self):
        """最初に一致するテキスト抽出のテスト"""
        # 正規表現に一致する最初のテキストを抽出
        pattern = r'Item (\d+)'
        match = self.parser.extract_first_match('li', pattern)
        self.assertEqual(match, '1'
        
        # 一致しないパターン
        match = self.parser.extract_first_match('p', r'No Match')
        self.assertIsNone(match)
        
        # デフォルト値のテスト
        match = self.parser.extract_first_match('p', r'No Match', default="Not Found")
        self.assertEqual(match, "Not Found")
    
    def test_extract_json_ld(self):
        """JSON-LDデータ抽出のテスト"""
        # テスト用のJSON-LDデータを含むHTML
        json_ld_html = """
        <html>
            <head>
                <script type="application/ld+json">
                {
                    "@context": "https://schema.org",
                    "@type": "Product",
                    "name": "Test Product",
                    "description": "A test product"
                }
                </script>
            </head>
            <body></body>
        </html>
        """
        parser = HTMLParser(json_ld_html)
        
        # JSON-LDデータを抽出
        json_data = parser.extract_json_ld()
        
        # 検証
        self.assertEqual(len(json_data), 1)
        self.assertEqual(json_data[0]['@type'], 'Product')
        self.assertEqual(json_data[0]['name'], 'Test Product')
    
    def test_select_element(self):
        """CSSセレクタを使用した要素選択のテスト"""
        # CSSセレクタで要素を選択
        elements = self.parser.select('.content p')
        self.assertEqual(len(elements), 3)
        self.assertEqual(elements[0].get_text(strip=True), "Paragraph 1")
        
        # 存在しない要素
        elements = self.parser.select('.non-existent')
        self.assertEqual(len(elements), 0)
    
    def test_select_one_element(self):
        """CSSセレクタを使用した単一要素選択のテスト"""
        # CSSセレクタで単一要素を選択
        element = self.parser.select_one('.content .special')
        self.assertIsNotNone(element)
        self.assertEqual(element.get_text(strip=True), "Special Text")
        
        # 存在しない要素
        element = self.parser.select_one('.non-existent')
        self.assertIsNone(element)
    
    def test_is_visible(self):
        """要素の可視性チェックのテスト"""
        # 可視要素
        visible_element = self.parser.find('h1')
        self.assertTrue(self.parser.is_visible(visible_element))
        
        # 非表示要素
        hidden_element = self.parser.find('.hidden')
        self.assertFalse(self.parser.is_visible(hidden_element))
        
        # 親要素が非表示の場合
        parent = self.parser.find('.content')
        parent['style'] = 'display: none;'
        child = self.parser.find('.text')
        self.assertFalse(self.parser.is_visible(child))

if __name__ == '__main__':
    unittest.main()
