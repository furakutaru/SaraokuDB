#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
修正版の血統情報抽出をテスト
"""

import sys
import os
import logging
from bs4 import BeautifulSoup

# 親ディレクトリをパスに追加
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '.')))
from components.horse_info_extractor_fixed import HorseInfoExtractor

# ロガーの設定
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_pedigree_extraction():
    """血統情報の抽出をテスト"""
    # テスト用のHTML
    test_html = """
    <html>
    <body>
        <div id="itemDetails">
            <table>
                <tr>
                    <td>
                        <pre>
                            父：テスト父馬　母：テスト母馬　母の父：テスト母父馬
                            通算成績：4戦0勝［0-0-0-4］　　　　最終出走馬体重：496kg
                        </pre>
                    </td>
                </tr>
            </table>
        </div>
    </body>
    </html>
    """
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(test_html, 'html.parser')
    
    # テスト対象の要素を取得
    pre_elem = soup.select_one('pre')
    
    # 抽出クラスのインスタンスを作成
    extractor = HorseInfoExtractor(logger=logger)
    
    # 血統情報を抽出
    result = extractor._extract_pedigree(pre_elem)
    
    # 結果を表示
    print("\n抽出結果:")
    print(f"父: {result.get('sire', '抽出失敗')}")
    print(f"母: {result.get('dam', '抽出失敗')}")
    print(f"母の父: {result.get('damsire', '抽出失敗')}")
    
    # 期待値との比較
    expected = {
        'sire': 'テスト父馬',
        'dam': 'テスト母馬',
        'damsire': 'テスト母父馬'
    }
    
    # 検証
    success = True
    for key, value in expected.items():
        if result.get(key) != value:
            print(f"エラー: {key} の値が一致しません。期待: {value}, 実際: {result.get(key)}")
            success = False
    
    if success:
        print("\nテストは成功しました！")
    else:
        print("\nテストは失敗しました。")

if __name__ == '__main__':
    test_pedigree_extraction()
