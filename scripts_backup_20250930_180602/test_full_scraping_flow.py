#!/usr/bin/env python3
"""
本番環境と同じフローでスクレイピングをテストするスクリプト
1. トップページから馬リストを取得
2. 各馬の詳細ページにアクセス
3. 詳細情報を抽出
4. 結果を表示・保存
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# スクレイパークラスをインポート
from scripts.improved_scraper import ImprovedRakutenScraper

# ログ設定
import logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_scraping_flow.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class ScrapingFlowTester:
    def __init__(self, test_mode: bool = True, max_horses: int = 3):
        """
        スクレイピングフローテスターを初期化
        
        Args:
            test_mode: テストモード（True: キャッシュを使用、False: 実際にリクエスト）
            max_horses: テスト対象の最大馬数
        """
        self.test_mode = test_mode
        self.max_horses = max_horses
        self.scraper = ImprovedRakutenScraper()
        self.output_dir = Path('test_output')
        self.output_dir.mkdir(exist_ok=True)
    
    def run(self):
        """スクレイピングフローを実行"""
        try:
            logger.info("=== スクレイピングフローテストを開始します ===")
            
            # 1. トップページから馬リストを取得
            logger.info("1. トップページから馬リストを取得中...")
            horses = self.scraper.scrape_horse_list()
            
            if not horses:
                logger.error("馬リストの取得に失敗しました")
                return False
            
            logger.info(f"馬リストを {len(horses)} 件取得しました")
            
            # テスト用に馬リストを制限
            if self.max_horses > 0:
                horses = horses[:self.max_horses]
            
            # 2. 各馬の詳細情報を取得
            results = []
            for i, horse in enumerate(horses, 1):
                logger.info(f"\n[{i}/{len(horses)}] 馬の詳細情報を取得中: {horse.get('name', '不明')}")
                
                # 詳細ページのURLを取得
                detail_url = horse.get('detail_url')
                if not detail_url:
                    logger.warning(f"詳細ページのURLが取得できませんでした: {horse}")
                    continue
                
                # 詳細ページをスクレイピング
                try:
                    logger.info(f"詳細ページにアクセス: {detail_url}")
                    horse_data = self.scraper.scrape_horse_detail(detail_url)
                    
                    if horse_data:
                        # 基本情報をマージ
                        horse_data.update({
                            'name': horse.get('name', ''),
                            'sex': horse.get('sex', ''),
                            'age': horse.get('age'),
                            'seller': horse.get('seller', '')
                        })
                        results.append(horse_data)
                        logger.info(f"詳細情報を取得しました: {json.dumps(horse_data, ensure_ascii=False, indent=2)}")
                    else:
                        logger.warning(f"詳細情報の取得に失敗しました: {detail_url}")
                
                except Exception as e:
                    logger.error(f"詳細情報の取得中にエラーが発生しました: {e}", exc_info=True)
            
            # 3. 結果を保存
            self._save_results(results)
            logger.info(f"\n=== テスト完了: {len(results)}/{len(horses)} 件の詳細情報を取得しました ===")
            return True
            
        except Exception as e:
            logger.error(f"スクレイピングフローでエラーが発生しました: {e}", exc_info=True)
            return False
    
    def _save_results(self, results: List[Dict[str, Any]]):
        """結果をJSONファイルに保存"""
        if not results:
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_file = self.output_dir / f'scraping_results_{timestamp}.json'
        
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"結果を保存しました: {output_file}")


def main():
    """メイン関数"""
    # テストモードで実行（キャッシュを使用）
    tester = ScrapingFlowTester(test_mode=True, max_horses=3)
    success = tester.run()
    
    if success:
        print("\nテストが正常に完了しました。結果はログファイルを確認してください。")
    else:
        print("\nテスト中にエラーが発生しました。ログを確認してください。")


if __name__ == "__main__":
    main()
