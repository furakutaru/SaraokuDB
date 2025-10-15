#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
import sys

# ロギング設定（詳細なログ出力）
logging.basicConfig(
    level=logging.DEBUG,  # すべてのログを表示
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(stream=sys.stdout),  # 標準出力にログを出力
    ]
)
logger = logging.getLogger(__name__)

class MockScraper:
    def __init__(self):
        self.logger = logger
    
    def _clean_horse_name(self, name_elem):
        """馬名をクリーンアップするメソッドのコピー"""
        if not name_elem:
            self.logger.warning("馬名要素が見つかりませんでした")
            return "不明な馬"
        try:
            name = name_elem.get_text(' ', strip=True)
            self.logger.debug(f"元の馬名: {name}")
            name = re.sub(r'\s*[（(][^）)]*[）)]\s*|※.*$', '', name)
            name = name.strip()
            name = re.sub(r'\s+', ' ', name)
            if not name:
                self.logger.warning("馬名が空でした")
                return "不明な馬"
            self.logger.debug(f"処理後の馬名: {name} (長さ: {len(name)}文字)")
            return name
        except Exception as e:
            self.logger.error(f"馬名のクリーンアップ中にエラーが発生しました: {str(e)}")
            return "不明な馬"

def test_clean_horse_name():
    """_clean_horse_name メソッドのテストを実行"""
    from bs4 import BeautifulSoup
    
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
    
    print("\n=== 馬名クリーニングのテストを開始します ===\n")
    logger.info("テストを開始します")
    
    for i, test_case in enumerate(test_cases, 1):
        try:
            # BeautifulSoup要素を作成
            name_elem = None
            if test_case["input"]:
                soup = BeautifulSoup(test_case["input"], 'html.parser')
                name_elem = soup.span  # 最初のspan要素を取得
            
            # メソッドを実行
            result = scraper._clean_horse_name(name_elem)
            
            # 結果を検証
            status = "✓ 成功" if result == test_case["expected"] else f"✗ 失敗: 期待値 '{test_case['expected']}' に対して実際の結果は '{result}' でした"
            
            logger.info(f"テスト {i}: {status}")
            logger.info(f"  入力: {test_case['input']}")
            logger.info(f"  出力: {result}")
            logger.info("")
            
        except Exception as e:
            logger.error(f"テスト {i}: ✗ 例外が発生しました - {str(e)}")
            logger.error(f"  入力: {test_case['input']}")
            logger.error("")
    
    logger.info("\n=== テスト完了 ===\n")

if __name__ == "__main__":
    test_clean_horse_name()
