#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
デバッグ用スクリプト: 賞金情報抽出のデバッグ用
"""
import os
import sys
import logging
import json
import re
from pathlib import Path
from typing import Dict, Any, Optional, Tuple
from bs4 import BeautifulSoup

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_prize_extractor.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

# テスト用のHTMLサンプル
TEST_HTML_SAMPLES = {
    'basic': """
    <div class="auctionTableCard">
        <div class="auctionTableCard__price">総賞金 1,234.5万円</div>
        <a href="/item/12345">詳細を見る</a>
    </div>
    """,
    'no_yen': """
    <div class="price">
        賞金: 5,678,900円
    </div>
    """,
    'with_text': """
    <div class="item-details">
        <p>獲得賞金は3,210,000円です</p>
    </div>
    """,
    'japanese_format': """
    <div class="prize-info">
        <span>総賞金：987万6,543円</span>
    </div>
    """,
    'no_prize': """
    <div class="no-prize">
        賞金情報はありません
    </div>
    """
}

# テスト用のユーティリティ関数
def setup_import_paths() -> None:
    """プロジェクトのルートをPythonパスに追加"""
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)
    logger.debug(f'Python path: {sys.path}')

class TestResult:
    """テスト結果を保持するクラス"""
    def __init__(self):
        self.total = 0
        self.passed = 0
        self.failed = 0
        self.errors = []
    
    def add_success(self, test_name: str) -> None:
        """成功ケースを追加"""
        self.total += 1
        self.passed += 1
        logger.info(f"✅ {test_name}: 成功")
    
    def add_failure(self, test_name: str, reason: str = '') -> None:
        """失敗ケースを追加"""
        self.total += 1
        self.failed += 1
        error_msg = f"❌ {test_name}: 失敗"
        if reason:
            error_msg += f" - {reason}"
        logger.error(error_msg)
        self.errors.append(error_msg)
    
    def add_error(self, test_name: str, error: Exception) -> None:
        """エラーケースを追加"""
        self.total += 1
        self.failed += 1
        error_msg = f"❌ {test_name}: エラー - {str(error)}"
        logger.error(error_msg, exc_info=True)
        self.errors.append(error_msg)
    
    def summary(self) -> str:
        """テスト結果のサマリーを返す"""
        return (
            f"\nテスト結果: {self.passed}/{self.total} 成功\n"
            f"成功: {self.passed}, 失敗: {self.failed}\n"
        )

def setup_import_paths():
    """プロジェクトのルートをPythonパスに追加"""
    project_root = str(Path(__file__).parent.absolute())
    if project_root not in sys.path:
        sys.path.insert(0, project_root)

def test_extract_from_html(html_content: str, test_name: str = "Test", 
                         expected_result: Optional[Dict] = None) -> Tuple[bool, Optional[Dict]]:
    """
    HTMLから賞金情報を抽出するテスト
    
    Args:
        html_content: テスト用のHTML文字列
        test_name: テスト名
        expected_result: 期待する結果（オプション）
        
    Returns:
        Tuple[bool, Optional[Dict]]: (成功したかどうか, 抽出結果)
    """
    from components.prize_info_extractor import PrizeInfoExtractor
    
    logger.info("\n" + "="*80)
    logger.info(f"🏁 テスト開始: {test_name}")
    logger.debug(f"HTML コンテンツ: {html_content[:200]}...")
    
    try:
        # HTMLをパース
        soup = BeautifulSoup(html_content, 'html.parser')
        logger.debug("HTMLのパースに成功しました")
        
        # 抽出器を初期化
        extractor = PrizeInfoExtractor(logger)
        
        # 賞金情報を抽出
        logger.debug("賞金情報の抽出を開始します...")
        result, success = extractor.extract(soup)
        
        # 結果を検証
        if success:
            logger.info(f"✅ 抽出に成功: {json.dumps(result, ensure_ascii=False, indent=2)}")
            
            # 期待値がある場合は検証
            if expected_result:
                is_match = True
                for key, value in expected_result.items():
                    if key not in result or result[key] != value:
                        logger.warning(f"期待値と一致しません: {key} (期待: {value}, 実際: {result.get(key)})")
                        is_match = False
                
                if is_match:
                    logger.info("✅ 期待値と一致しました")
                else:
                    logger.warning("⚠️ 期待値と一部が一致しませんでした")
                    success = False
        else:
            logger.warning("❌ 抽出に失敗しました")
            
        return success, result
        
    except Exception as e:
        logger.error(f"❌ テスト中にエラーが発生しました: {e}", exc_info=True)
        return False, None

def run_test_suite() -> TestResult:
    """テストスイートを実行"""
    result = TestResult()
    
    # 基本テストケース
    success, _ = test_extract_from_html(
        TEST_HTML_SAMPLES['basic'],
        "基本テスト（総賞金 1,234.5万円）",
        expected_result={'total_prize': 12345000}
    )
    if success:
        result.add_success("基本テスト")
    else:
        result.add_failure("基本テスト", "賞金の抽出に失敗")
    
    # 円表記のみのテスト
    success, _ = test_extract_from_html(
        TEST_HTML_SAMPLES['no_yen'],
        "円表記テスト（5,678,900円）",
        expected_result={'total_prize': 5678900}
    )
    if success:
        result.add_success("円表記テスト")
    else:
        result.add_failure("円表記テスト", "円表記の抽出に失敗")
    
    # テキスト内の賞金テスト
    success, _ = test_extract_from_html(
        TEST_HTML_SAMPLES['with_text'],
        "テキスト内賞金テスト（3,210,000円）",
        expected_result={'total_prize': 3210000}
    )
    if success:
        result.add_success("テキスト内賞金テスト")
    else:
        result.add_failure("テキスト内賞金テスト", "テキスト内の賞金抽出に失敗")
    
    # 日本語フォーマットテスト
    success, _ = test_extract_from_html(
        TEST_HTML_SAMPLES['japanese_format'],
        "日本語フォーマットテスト（987万6,543円）",
        expected_result={'total_prize': 9876543}
    )
    if success:
        result.add_success("日本語フォーマットテスト")
    else:
        result.add_failure("日本語フォーマットテスト", "日本語フォーマットの抽出に失敗")
    
    # 賞金なしテスト
    success, _ = test_extract_from_html(
        TEST_HTML_SAMPLES['no_prize'],
        "賞金なしテスト",
        expected_result=None
    )
    if not success:  # 賞金がない場合は抽出に失敗するのが正しい
        result.add_success("賞金なしテスト")
    else:
        result.add_failure("賞金なしテスト", "賞金がない場合に誤って抽出")
    
    return result

def test_real_data() -> None:
    """実際のデータでテスト"""
    logger.info("\n" + "="*80)
    logger.info("📂 実際のデータでのテストを開始します")
    
    # 実際のHTMLファイルを読み込む場合はここにパスを指定
    real_data_dir = Path('data/html_samples')
    if real_data_dir.exists():
        for html_file in real_data_dir.glob('*.html'):
            try:
                with open(html_file, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                test_name = f"実データテスト: {html_file.name}"
                logger.info(f"\n📄 {test_name}")
                
                success, result = test_extract_from_html(html_content, test_name)
                
                if success:
                    logger.info(f"✅ 抽出成功: {result}")
                else:
                    logger.warning(f"❌ 抽出失敗")
                    
            except Exception as e:
                logger.error(f"❌ ファイル処理中にエラーが発生しました: {html_file}", exc_info=True)
    else:
        logger.warning(f"実データディレクトリが見つかりません: {real_data_dir}")

def main():
    """メイン処理"""
    logger.info("🏁 賞金情報抽出デバッガーを開始します")
    
    # インポートパスの設定
    setup_import_paths()
    
    # テストスイートを実行
    test_result = run_test_suite()
    
    # 実際のデータでのテスト（オプション）
    # test_real_data()
    
    # サマリーを表示
    logger.info("\n" + "="*80)
    logger.info("📊 テスト結果サマリー")
    logger.info(test_result.summary())
    
    if test_result.errors:
        logger.warning("\n以下のエラーが発生しました:")
        for error in test_result.errors:
            logger.warning(f"- {error}")
    
    logger.info("\n✨ デバッグを完了しました")
    
    # テストが全て成功したかどうかで終了コードを返す
    return 0 if test_result.failed == 0 else 1

if __name__ == "__main__":
    try:
        setup_import_paths()
        sys.exit(main())
    except KeyboardInterrupt:
        logger.warning("\nユーザーによって中断されました")
        sys.exit(1)
    except Exception as e:
        logger.critical(f"予期せぬエラーが発生しました: {e}", exc_info=True)
        sys.exit(1)
