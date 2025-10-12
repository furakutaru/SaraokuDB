#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
from bs4 import BeautifulSoup

class MockScraper:
    def __init__(self):
        self.logger = self  # Simple logger replacement
        
    def debug(self, msg):
        print(f"[DEBUG] {msg}")
        
    def warning(self, msg):
        print(f"[WARNING] {msg}")
        
    def error(self, msg):
        print(f"[ERROR] {msg}")
    
    def _clean_horse_name(self, name_elem):
        """馬名をクリーンアップするメソッドのコピー"""
        if not name_elem:
            self.warning("馬名要素が見つかりませんでした")
            return "不明な馬"
        try:
            name = name_elem.get_text(' ', strip=True)
            self.debug(f"元の馬名: {name}")
            name = re.sub(r'\s*[（(][^）)]*[）)]\s*|※.*$', '', name)
            name = name.strip()
            name = re.sub(r'\s+', ' ', name)
            if not name:
                self.warning("馬名が空でした")
                return "不明な馬"
            self.debug(f"処理後の馬名: {name} (長さ: {len(name)}文字)")
            return name
        except Exception as e:
            self.error(f"馬名のクリーンアップ中にエラーが発生しました: {str(e)}")
            return "不明な馬"

def run_tests():
    print("\n=== 馬名クリーニングのテストを開始します ===\n")
    
    # テスト用のスクレイパーインスタンスを作成
    scraper = MockScraper()
    
    # テストケースの定義
    test_cases = [
        {"input": "<span>サトノダイヤモンド</span>", "expected": "サトノダイヤモンド"},
        {"input": "<span> サトノダイヤモンド </span>", "expected": "サトノダイヤモンド"},
        {"input": "<span>サトノダイヤモンド※</span>", "expected": "サトノダイヤモンド"},
        {"input": "<span>サトノダイヤモンド（牡3）</span>", "expected": "サトノダイヤモンド"},
        {"input": "<span>サトノ ダイヤモンド</span>", "expected": "サトノ ダイヤモンド"},
        {"input": "<span>サトノ　ダイヤモンド</span>", "expected": "サトノ ダイヤモンド"},
        {"input": "<span></span>", "expected": "不明な馬"},
        {"input": "", "expected": "不明な馬"},
        {"input": None, "expected": "不明な馬"},
        {
            "input": f"<span>{'A' * 100}</span>", 
            "expected": 'A' * 100
        }
    ]
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nテスト {i}:")
        print(f"  入力: {test_case['input']}")
        
        # BeautifulSoup要素を作成
        name_elem = None
        if test_case["input"]:
            soup = BeautifulSoup(test_case["input"], 'html.parser')
            name_elem = soup.span  # 最初のspan要素を取得
        
        # メソッドを実行
        result = scraper._clean_horse_name(name_elem)
        
        # 結果を検証して表示
        status = "✓ 成功" if result == test_case["expected"] else f"✗ 失敗: 期待値 '{test_case['expected']}' に対して実際の結果は '{result}' でした"
        print(f"  結果: {status}")
    
    print("\n=== テスト完了 ===\n")

if __name__ == "__main__":
    run_tests()
