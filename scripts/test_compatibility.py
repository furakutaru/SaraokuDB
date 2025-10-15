#!/usr/bin/env python3
"""
RakutenAuctionScraper の互換性テストスクリプト

このスクリプトは、新しい RakutenAuctionScraper クラスが
古いコードと互換性があることを確認するためのテストを実行します。
"""
import sys
import os
import logging
from pathlib import Path
from unittest.mock import patch, MagicMock

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# デバッグ用にモジュールのロード情報を表示
logger.debug("Python version: %s", sys.version)
logger.debug("Python executable: %s", sys.executable)
logger.debug("Current working directory: %s", os.getcwd())
logger.debug("sys.path: %s", sys.path)

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent  # 1つ上のディレクトリがプロジェクトルート
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))  # 優先的に検索されるように先頭に追加

# テスト用のモックデータ
MOCK_HORSE_DATA = [{
    'name': 'テスト馬',
    'price': 1000,
    'detail_url': 'https://example.com/horse/1',
    'scraped_at': '2023-01-01T00:00:00',
    'auction_date': '2023-01-01'
}]

def test_scraper_initialization():
    """スクレイパーの初期化テスト"""
    from improved_scraper import RakutenAuctionScraper
    
    try:
        # デフォルト設定で初期化
        scraper = RakutenAuctionScraper()
        print("✓ RakutenAuctionScraper の初期化に成功しました")
        
        # データディレクトリが存在することを確認
        data_dir = Path('static-frontend/public/data')
        assert data_dir.exists(), f"データディレクトリが存在しません: {data_dir}"
        print(f"✓ データディレクトリ: {data_dir}")
        
        # ベースURLが正しいことを確認
        assert hasattr(scraper, 'base_url'), "base_url 属性が存在しません"
        print(f"✓ ベースURL: {scraper.base_url}")
        
        return True
    except Exception as e:
        print(f"✗ テストが失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_scrape_all_horses():
    """scrape_all_horses メソッドのテスト"""
    from improved_scraper import RakutenAuctionScraper, ImprovedRakutenScraper
    
    try:
        # テスト用のモックデータ
        mock_data = MOCK_HORSE_DATA
        
        # 親クラスの scrape_horses メソッドをモック
        with patch.object(ImprovedRakutenScraper, 'scrape_horses') as mock_scrape:
            # モックの戻り値を設定
            mock_scrape.return_value = mock_data
            
            # テスト対象のインスタンスを作成
            scraper = RakutenAuctionScraper()
            print("\n馬一覧のスクレイピングをテスト中...")
            
            # scrape_all_horses メソッドを呼び出し
            result = scraper.scrape_all_horses()
            
            # 結果を検証
            assert isinstance(result, list), "戻り値がリストではありません"
            print(f"✓ 馬のデータを {len(result)} 件取得しました")
            
            if result:
                print(f"  例: {result[0]}")
            
            # モックが1回呼び出されたことを確認
            mock_scrape.assert_called_once()
            
            return True
    except Exception as e:
        print(f"✗ テストが失敗しました: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """メインのテスト実行関数"""
    print("=== RakutenAuctionScraper 互換性テスト開始 ===\n")
    
    # テストを実行
    tests = [
        ("スクレイパーの初期化テスト", test_scraper_initialization),
        ("馬一覧スクレイピングテスト", test_scrape_all_horses),
    ]
    
    all_passed = True
    for name, test_func in tests:
        print(f"\n{name} を実行中...")
        if not test_func():
            all_passed = False
    
    # テスト結果を表示
    if all_passed:
        print("\n✓ すべてのテストが正常に完了しました！")
    else:
        print("\n✗ 一部のテストが失敗しました")
    
    print("\n=== テスト終了 ===")
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    sys.exit(main())
