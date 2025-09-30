#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬名クリーニング機能のテストスクリプト

このスクリプトは、ImprovedRakutenScraper クラスの _clean_horse_name メソッドを
テストするためのものです。
"""

import sys
import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.improved_scraper import ImprovedRakutenScraper, ScraperConfig

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_clean_horse_name.log')
    ]
)
logger = logging.getLogger(__name__)

def test_clean_horse_name():
    """_clean_horse_name メソッドのテストを実行"""
    # テスト用のスクレイパーインスタンスを作成（テストモードで初期化）
    config = ScraperConfig(use_cache=False)
    scraper = ImprovedRakutenScraper(config=config)
    
    # テストケースの定義
    test_cases = [
        {
            "input": "サトノダイヤモンド",
            "expected": "サトノダイヤモンド"
        },
        {
            "input": " サトノダイヤモンド ",  # 前後のスペース
            "expected": "サトノダイヤモンド"
        },
        {
            "input": "サトノダイヤモンド※",  # コメント記号
            "expected": "サトノダイヤモンド"
        },
        {
            "input": "サトノダイヤモンド（牡3）",  # 括弧内の情報
            "expected": "サトノダイヤモンド"
        },
        {
            "input": "サトノ ダイヤモンド",  # 全角スペース
            "expected": "サトノ ダイヤモンド"
        },
        {
            "input": "サトノ　ダイヤモンド",  # 半角スペース
            "expected": "サトノ ダイヤモンド"
        },
        {
            "input": "",  # 空文字列
            "expected": "不明な馬"
        },
        {
            "input": None,  # None
            "expected": "不明な馬"
        },
        {
            "input": "A very long horse name that exceeds the maximum length limitation that we want to test",
            "expected": "A very long horse name that exceeds the maximum length limitation that we want to test"
        }
    ]
    
    # テストの実行
    print("\n=== 馬名クリーニングのテストを開始します ===\n")
    
    for i, test_case in enumerate(test_cases, 1):
        # BeautifulSoup要素を作成
        name_elem = None
        if test_case["input"] is not None:
            # テスト用のHTML要素を作成
            html = f'<span class="horse-name">{test_case["input"]}</span>'
            soup = BeautifulSoup(html, 'html.parser')
            name_elem = soup.select_one('.horse-name')
        
        # メソッドを実行
        try:
            result = scraper._clean_horse_name(name_elem)
            
            # 結果を検証
            if result == test_case["expected"]:
                status = "✓ 成功"
            else:
                status = f"✗ 失敗: 期待値 '{test_case['expected']}' に対して実際の結果は '{result}' でした"
                
            print(f"テスト {i}: {status}")
            print(f"  入力: {repr(test_case['input'])}")
            print(f"  出力: {repr(result)}")
            print()
            
        except Exception as e:
            print(f"テスト {i}: ✗ 例外が発生しました - {str(e)}")
            print(f"  入力: {repr(test_case['input'])}")
            print()
            logger.exception("テスト中に例外が発生しました")
    
    print("\n=== テスト完了 ===\n")

if __name__ == "__main__":
    try:
        test_clean_horse_name()
    except Exception as e:
        logger.error("テストの実行中にエラーが発生しました:", exc_info=True)
        print(f"\nエラーが発生しました: {str(e)}")
        sys.exit(1)
