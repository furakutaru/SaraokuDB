"""
improved_scraper.py のテストスクリプト
"""
import os
import sys
import logging
import unittest
from pathlib import Path
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup

# テスト対象のスクリプトがあるディレクトリをパスに追加
sys.path.insert(0, str(Path(__file__).parent.parent))
sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))

try:
    from scripts.improved_scraper import ImprovedRakutenScraper
except ImportError:
    sys.path.insert(0, str(Path(__file__).parent.parent / 'scripts'))
    from improved_scraper import ImprovedRakutenScraper

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_improved_scraper.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class TestImprovedScraper(unittest.TestCase):    
    @classmethod
    def setUpClass(cls):
        """テストクラス全体の前処理"""
        # テスト用のロガーを設定
        cls.logger = logging.getLogger('TestImprovedScraper')
        cls.logger.setLevel(logging.DEBUG)
        
        # テスト用のキャッシュディレクトリを設定
        cls.cache_dir = Path('test_cache')
        cls.cache_dir.mkdir(exist_ok=True)
        
        # テスト用のHTMLサンプルを読み込む
        cls.sample_dir = Path(__file__).parent / 'test_data'
        cls.sample_dir.mkdir(exist_ok=True)
        
        # テスト用のHTMLファイルパス
        cls.valid_horse_html = cls.sample_dir / 'valid_horse.html'
        cls.invalid_horse_html = cls.sample_dir / 'invalid_horse.html'
        
        # テスト用のHTMLが存在しない場合は作成
        if not cls.valid_horse_html.exists():
            cls._create_sample_html()
    
    @classmethod
    def _create_sample_html(cls):
        """テスト用のサンプルHTMLを作成"""
        # 有効な馬情報を含むHTML
        valid_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>テスト馬名　　牝３歳　　※地方競馬　在籍 | サラブレッドオークション</title>
        </head>
        <body>
            <div class="horse-info">
                <h1>テスト馬名</h1>
                <div class="pedigree">
                    <p>父: テスト父馬</p>
                    <p>母: テスト母馬</p>
                    <p>母の父: テスト母父</p>
                </div>
                <div class="weight">
                    <span>馬体重: 450kg</span>
                </div>
            </div>
        </body>
        </html>
        """
        
        # 無効な馬情報（必須フィールド不足）を含むHTML
        invalid_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>無効な馬情報 | サラブレッドオークション</title>
        </head>
        <body>
            <div class="horse-info">
                <h1>無効な馬情報</h1>
            </div>
        </body>
        </html>
        """
        
        # ファイルに保存
        with open(cls.valid_horse_html, 'w', encoding='utf-8') as f:
            f.write(valid_html)
            
        with open(cls.invalid_horse_html, 'w', encoding='utf-8') as f:
            f.write(invalid_html)
    
    def setUp(self):
        """各テストメソッドの前処理"""
        # キャッシュを使用しない設定でスクレイパーを初期化
        self.scraper = ImprovedRakutenScraper(use_cache=False)
    
    def test_extract_horse_info_valid(self):
        """有効な馬情報の抽出テスト"""
        # テスト用HTMLを読み込む
        with open(self.valid_horse_html, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, 'html.parser')
        
        # 馬情報を抽出（実際の実装に合わせてhorse_elementを渡す）
        horse_element = soup.find('div', class_='horse-info')
        self.assertIsNotNone(horse_element, '馬情報の要素が見つかりません')
        
        # 馬情報を抽出（実際のメソッドシグネチャに合わせて引数を渡す）
        horse_info = self.scraper._extract_horse_info(horse_element, index=1, total=1)
        
        # 必須フィールドが正しく抽出されているか確認
        self.assertIsNotNone(horse_info, '馬情報がNoneです')
        self.assertEqual(horse_info.get('name'), 'テスト馬名', '馬名が正しく抽出されていません')
        self.assertEqual(horse_info.get('sex'), '牝', '性別が正しく抽出されていません')
        self.assertEqual(horse_info.get('age'), 3, '年齢が正しく抽出されていません')
        self.assertEqual(horse_info.get('sire'), 'テスト父馬', '父馬名が正しく抽出されていません')
        self.assertEqual(horse_info.get('dam'), 'テスト母馬', '母馬名が正しく抽出されていません')
        self.assertEqual(horse_info.get('damsire'), 'テスト母父', '母父名が正しく抽出されていません')
        self.assertEqual(horse_info.get('weight'), 450, '馬体重が正しく抽出されていません')
    
    def test_extract_horse_info_invalid(self):
        """無効な馬情報の抽出テスト"""
        # テスト用HTMLを読み込む
        with open(self.invalid_horse_html, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, 'html.parser')
        
        # 馬情報を抽出（実際の実装に合わせてhorse_elementを渡す）
        horse_element = soup.find('div', class_='horse-info')
        self.assertIsNotNone(horse_element, '馬情報の要素が見つかりません')
        
        # 馬情報を抽出（実際のメソッドシグネチャに合わせて引数を渡す）
        with self.assertLogs(level='WARNING'):
            horse_info = self.scraper._extract_horse_info(horse_element, index=1, total=1)
        
        # 必須フィールドが不足しているためNoneが返ることを確認
        self.assertIsNone(horse_info, '無効な馬情報なのにNoneが返されませんでした')
    
    def test_extract_horse_info_missing_fields(self):
        """必須フィールドが不足している場合のテスト"""
        # テスト用HTMLを読み込む
        with open(self.valid_horse_html, 'r', encoding='utf-8') as f:
            html = f.read()
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html, 'html.parser')
        
        # タイトルを変更して性別と年齢を削除
        title = soup.find('title')
        if title:
            title.string = 'テスト馬名 | サラブレッドオークション'
        
        # 血統情報を削除
        pedigree = soup.find(class_='pedigree')
        if pedigree:
            pedigree.decompose()
        
        # 馬情報を抽出（実際の実装に合わせてhorse_elementを渡す）
        horse_element = soup.find('div', class_='horse-info')
        self.assertIsNotNone(horse_element, '馬情報の要素が見つかりません')
        
        # 馬情報を抽出（実際のメソッドシグネチャに合わせて引数を渡す）
        with self.assertLogs(level='WARNING'):
            horse_info = self.scraper._extract_horse_info(horse_element, index=1, total=1)
        
        # 必須フィールドが不足しているためNoneが返ることを確認
        self.assertIsNone(horse_info, '必須フィールドが不足しているのにNoneが返されませんでした')
    
    @classmethod
    def tearDownClass(cls):
        """テストクラス全体の後処理"""
        # テスト用のキャッシュディレクトリを削除
        if cls.cache_dir.exists():
            import shutil
            shutil.rmtree(cls.cache_dir)

if __name__ == '__main__':
    unittest.main(verbosity=2)
