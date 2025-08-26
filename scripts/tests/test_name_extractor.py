"""
NameExtractor のテストモジュール
"""

import unittest
from unittest.mock import MagicMock, patch
from bs4 import BeautifulSoup
from components.extractors.name_extractor import NameExtractor

class TestNameExtractor(unittest.TestCase):    
    def setUp(self):
        """テストの前処理"""
        self.logger = MagicMock()
        self.extractor = NameExtractor(logger=self.logger)
    
    def test_from_list_page(self):
        """リストページからの馬名抽出テスト"""
        # テスト用のHTMLを作成
        html = '''
        <div class="horse-card">
            <div class="horse-name">サラブレッド</div>
            <div class="horse-info">牡3</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.from_list_page(soup)
        
        # 検証
        self.assertEqual(result, 'サラブレッド')
    
    def test_from_list_page_with_extra_text(self):
        """リストページ（追加テキスト付き）からの馬名抽出テスト"""
        # テスト用のHTMLを作成
        html = '''
        <div class="horse-card">
            <div class="horse-name">サラブレッド ※登録抹消</div>
            <div class="horse-info">牡3</div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.from_list_page(soup)
        
        # 検証
        self.assertEqual(result, 'サラブレッド')
    
    def test_from_detail_title(self):
        """詳細ページタイトルからの馬名抽出テスト"""
        # テストデータ
        title = "サラブレッド 牡3歳 2023年5月1日 サラブレッドオークション"
        
        # テスト実行
        result = self.extractor.from_detail_title(title)
        
        # 検証
        self.assertEqual(result, 'サラブレッド')
    
    def test_from_item_title(self):
        """詳細ページのitemTitle要素からの馬名抽出テスト"""
        # テスト用のHTMLを作成
        html = '''
        <div id="itemTitle">
            <div><h1><span itemprop="name">サラブレッド　　牡3歳　　※中央競馬　登録抹消</span></h1></div>
        </div>
        '''
        soup = BeautifulSoup(html, 'html.parser')
        
        # テスト実行
        result = self.extractor.from_item_title(soup)
        
        # 検証
        self.assertEqual(result, 'サラブレッド')
    
    def test_extract_auto_detection(self):
        """自動検出機能のテスト"""
        # リストページの要素
        list_html = '''
        <div class="horse-card">
            <div class="horse-name">サラブレッド</div>
            <div class="horse-info">牡3</div>
        </div>
        '''
        list_soup = BeautifulSoup(list_html, 'html.parser')
        
        # 詳細ページのitemTitle要素
        detail_html = '''
        <div id="itemTitle">
            <div><h1><span itemprop="name">サラブレッド　　牡3歳　　※中央競馬　登録抹消</span></h1></div>
        </div>
        '''
        detail_soup = BeautifulSoup(detail_html, 'html.parser')
        
        # テストケース
        test_cases = [
            # (source, expected)
            (list_soup, 'サラブレッド'),  # リストページの要素
            (detail_soup, 'サラブレッド'),  # 詳細ページの要素
            ("サラブレッド 牡3歳 2023年5月1日 サラブレッドオークション", 'サラブレッド')  # 詳細ページタイトル
        ]
        
        for source, expected in test_cases:
            with self.subTest(source=type(source).__name__):
                result = self.extractor.extract(source, 'auto')
                self.assertEqual(result, expected)
    
    def test_clean_name(self):
        """馬名のクリーンアップテスト"""
        test_cases = [
            ('サラブレッド', 'サラブレッド'),
            ('サラブレッド 登録抹消', 'サラブレッド'),
            ('サラブレッド※', 'サラブレッド'),
            ('サラブレッド 新馬', 'サラブレッド'),
            (' サラブレッド ', 'サラブレッド'),
            ('', None),
            ('サラブレッド　', 'サラブレッド'),  # 全角スペース
            ('サラブレッド　　※', 'サラブレッド'),  # 全角スペースと記号
            ('サラブレッド 未出走', 'サラブレッド')
        ]
        
        for input_name, expected in test_cases:
            with self.subTest(input_name=input_name):
                result = self.extractor._clean_name(input_name, 'list_page')
                self.assertEqual(result, expected)

if __name__ == '__main__':
    unittest.main()
