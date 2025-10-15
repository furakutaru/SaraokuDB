#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import json
import logging
from bs4 import BeautifulSoup
from improved_scraper import ImprovedRakutenScraper

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_prize_money_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

def load_test_data():
    """テスト用のHTMLデータを読み込む"""
    test_data = [
        {
            "name": "通常の賞金表記",
            "html": """
            <div class="price">
                <div class="label">賞金</div>
                <div class="value">1,234万円</div>
            </div>
            """,
            "expected": 1234.0
        },
        {
            "name": "カンマなしの賞金表記",
            "html": """
            <div class="price">
                <div class="value">9876万円</div>
            </div>
            """,
            "expected": 9876.0
        },
        {
            "name": "未出走馬",
            "html": "<div class='record'>未出走</div>",
            "expected": 0.0,
            "race_record": "未出走"
        },
        {
            "name": "賞金情報なし",
            "html": "<div class='horse-info'>他の情報</div>",
            "expected": 0.0
        },
        {
            "name": "複数回のレース賞金表記",
            "html": """
            <div class="horse-info">
                <div class="price">
                    <div class="label">獲得賞金</div>
                    <div class="value">5,678万円</div>
                </div>
                <div class="price">
                    <div class="label">総賞金</div>
                    <div class="value">9,876万円</div>
                </div>
            </div>
            """,
            "expected": 9876.0  # 大きい方の値を取得する想定
        }
    ]
    return test_data

def run_tests():
    """賞金抽出のテストを実行"""
    test_data = load_test_data()
    scraper = ImprovedRakutenScraper(test_mode=True)
    
    results = {
        "total": 0,
        "passed": 0,
        "failed": 0,
        "details": []
    }
    
    for test in test_data:
        results["total"] += 1
        test_name = test["name"]
        html = test["html"]
        expected = test["expected"]
        race_record = test.get("race_record", "1戦1勝")
        
        logger.info(f"\n{'='*50}")
        logger.info(f"テストケース: {test_name}")
        logger.info(f"期待値: {expected}")
        
        try:
            # テスト用のBeautifulSoupオブジェクトを作成
            soup = BeautifulSoup(html, 'html.parser')
            
            # 賞金情報を抽出
            result = scraper._extract_prize_money(
                page_text=str(soup),
                jbis_url="https://www.jbis.or.jp/test/1234567/",
                race_record=race_record
            )
            
            # 結果を検証
            actual = result.get('total_prize_latest', 0)
            
            # 浮動小数点数の比較（誤差を考慮）
            is_passed = abs(actual - expected) < 0.01
            
            if is_passed:
                logger.info(f"✅ 成功: 期待値 {expected} 万円, 実際の値 {actual} 万円")
                results["passed"] += 1
            else:
                logger.error(f"❌ 失敗: 期待値 {expected} 万円, 実際の値 {actual} 万円")
                results["failed"] += 1
                
            # 詳細を保存
            results["details"].append({
                "test_name": test_name,
                "expected": expected,
                "actual": actual,
                "passed": is_passed,
                "html": html
            })
            
        except Exception as e:
            logger.error(f"❌ エラーが発生しました: {str(e)}")
            results["failed"] += 1
            results["details"].append({
                "test_name": test_name,
                "error": str(e),
                "html": html
            })
    
    # テスト結果を表示
    logger.info("\n" + "="*50)
    logger.info("テスト結果のサマリー:")
    logger.info(f"総テストケース数: {results['total']}")
    logger.info(f"成功: {results['passed']}")
    logger.info(f"失敗: {results['failed']}")
    
    # 失敗したテストケースの詳細を表示
    if results["failed"] > 0:
        logger.info("\n失敗したテストケースの詳細:")
        for detail in results["details"]:
            if not detail.get("passed", False):
                logger.info(f"\n- {detail['test_name']}")
                if "error" in detail:
                    logger.info(f"  エラー: {detail['error']}")
                else:
                    logger.info(f"  期待値: {detail['expected']} 万円")
                    logger.info(f"  実際の値: {detail['actual']} 万円")
                logger.info(f"  HTML: {detail['html'][:200]}...")
    
    # 結果をJSONファイルに保存
    with open("test_prize_money_results.json", "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    return results["failed"] == 0

if __name__ == "__main__":
    success = run_tests()
    if not success:
        sys.exit(1)
    sys.exit(0)
