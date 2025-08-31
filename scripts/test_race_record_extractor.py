#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
import unittest
from bs4 import BeautifulSoup
from pathlib import Path

# カレントディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))

from race_record_extractor import RaceRecordExtractor

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

class TestRaceRecordExtractor(unittest.TestCase):    
    def setUp(self):
        """テストの前処理"""
        self.extractor = RaceRecordExtractor(logger=logger)
        
        # テスト用のHTMLファイルのパス
        self.test_data_dir = Path(__file__).parent / 'test_data' / 'race_records'
        
    def test_extract_race_records(self):
        """レース記録の抽出テスト（本番環境形式）"""
        # テスト用のHTMLを直接定義（本番環境の形式に合わせる）
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>テスト用レース記録</title>
        </head>
        <body>
            <div class="horse_info">
                <div class="record">
                    <h3>戦績</h3>
                    <p>23戦1勝［1-0-1-21］</p>
                </div>
                
                <table class="raceTable">
                    <thead>
                        <tr>
                            <th>日付</th>
                            <th>レース名</th>
                            <th>競馬場</th>
                            <th>距離</th>
                            <th>馬場</th>
                            <th>着順</th>
                            <th>タイム</th>
                            <th>騎手</th>
                        </tr>
                    </thead>
                    <tbody>
                        <tr>
                            <td>2023/10/15</td>
                            <td>第1回東京競馬 3歳未勝利</td>
                            <td>東京</td>
                            <td>芝2000m</td>
                            <td>良</td>
                            <td>5</td>
                            <td>2:02.5</td>
                            <td>武豊</td>
                        </tr>
                        <tr>
                            <td>2023/09/10</td>
                            <td>第2回新潟競馬 2歳新馬</td>
                            <td>新潟</td>
                            <td>芝1800m</td>
                            <td>稍重</td>
                            <td>3</td>
                            <td>1:48.9</td>
                            <td>ルメール</td>
                        </tr>
                    </tbody>
                </table>
            </div>
        </body>
        </html>
        """
            
        # レース記録を抽出
        result, success = self.extractor.extract(html_content)
        
        # 結果を検証
        self.assertTrue(success, "レース記録の抽出に失敗しました")
        self.assertIn('races', result, "結果に'races'キーが含まれていません")
        self.assertIn('summary', result, "結果に'summary'キーが含まれていません")
        self.assertGreater(len(result['races']), 0, "レース記録が1件も抽出されていません")
        
        # サマリー情報を検証（パースできていれば成功）
        if result['summary']:  # サマリーがあれば検証
            self.assertIn('races', result['summary'], "サマリーに'races'キーが含まれていません")
            self.assertIn('wins', result['summary'], "サマリーに'wins'キーが含まれていません")
        
        # 最初のレース記録を検証
        first_record = result['races'][0]
        self.assertIn('date', first_record, "日付が抽出されていません")
        self.assertIn('race_name', first_record, "レース名が抽出されていません")
        self.assertIn('track', first_record, "競馬場が抽出されていません")
        self.assertIn('distance', first_record, "距離が抽出されていません")
        self.assertIn('track_condition', first_record, "馬場状態が抽出されていません")
        self.assertIn('position', first_record, "着順が抽出されていません")
        self.assertIn('time', first_record, "タイムが抽出されていません")
        self.assertIn('jockey', first_record, "騎手が抽出されていません")
        
        logger.info(f"抽出されたレース記録: {result}")
        
    def test_extract_no_records(self):
        """レース記録がない場合のテスト"""
        html_content = """
        <html>
            <body>
                <div class="horse_info">
                    <h1>テスト用ページ</h1>
                    <div class="record">
                        <h3>戦績</h3>
                        <p>未出走</p>
                    </div>
                    <p>このページにはレース記録が含まれていません</p>
                </div>
            </body>
        </html>
        """
        
        result, success = self.extractor.extract(html_content)
        
        # レコードが0件でも成功とみなす（エラーではない）
        self.assertTrue(success, "空のレース記録は成功とみなすべきです")
        self.assertIn('races', result, "結果に'races'キーが含まれていません")
        self.assertIn('summary', result, "結果に'summary'キーが含まれていません")
        self.assertEqual(len(result['races']), 0, "レース記録が0件でないようです")
        
    def test_extract_invalid_html(self):
        """無効なHTMLを渡した場合のテスト"""
        result, success = self.extractor.extract("<invalid>html</invalid>")
        
        # 構文エラーでも空の結果を返す
        self.assertIn('races', result, "結果に'races'キーが含まれていません")
        self.assertIn('summary', result, "結果に'summary'キーが含まれていません")
        self.assertEqual(len(result['races']), 0, "無効なHTMLでは空のレース記録を返すべきです")

if __name__ == "__main__":
    unittest.main()
