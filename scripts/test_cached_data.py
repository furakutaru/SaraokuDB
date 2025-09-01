#!/usr/bin/env python3
"""
キャッシュされたデータを使用して_process_horse_infoメソッドをテストするスクリプト
"""
import sys
import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from improved_scraper import ImprovedRakutenScraper

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_cached_data.log')
    ]
)
logger = logging.getLogger(__name__)

def load_and_test_cached_html(html_file: Path):
    """キャッシュされたHTMLファイルを読み込んでテストを実行"""
    try:
        logger.info(f"\n{'='*80}")
        logger.info(f"テストファイル: {html_file}")
        
        # HTMLファイルを読み込む
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 馬の基本情報を含むテーブルを取得
        horse_tables = soup.select('table[cellpadding="10"]')
        if not horse_tables:
            logger.warning("馬情報のテーブルが見つかりませんでした")
            return False
            
        # テーブルから馬情報を抽出
        horse_info_list = []
        for table in horse_tables:
            # 馬名と基本情報を含む行を取得
            name_row = table.find('b')
            if name_row:
                horse_info_list.append(table)
                
        if not horse_info_list:
            logger.warning("馬の基本情報が見つかりませんでした")
            return False
            
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(test_mode=True)
        
        # 各馬情報に対してテストを実行
        for i, table in enumerate(horse_info_list, 1):
            logger.info(f"\n--- 馬 {i} ---")
            
            # メソッドを実行
            horse_info = scraper._process_horse_info(table, index=i, total=len(horse_info_list))
            
            if not horse_info:
                logger.warning(f"馬 {i} の情報抽出に失敗しました")
                continue
                
            # 結果を表示
            logger.info("抽出された馬情報:")
            for key, value in horse_info.items():
                logger.info(f"  {key}: {value}")
                
            # 必須フィールドの確認
            required_fields = ['name', 'sex', 'age']
            missing_fields = [field for field in required_fields 
                            if field not in horse_info or horse_info[field] is None]
            
            if missing_fields:
                logger.warning(f"以下の必須フィールドが不足しています: {missing_fields}")
            else:
                logger.info("必須フィールドはすべて抽出されました")
                
        return True
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    # キャッシュディレクトリを指定
    cache_dir = Path("html_dump/details/")
    
    if not cache_dir.exists():
        logger.error(f"キャッシュディレクトリが見つかりません: {cache_dir}")
        sys.exit(1)
        
    # キャッシュされたHTMLファイルを取得
    html_files = list(cache_dir.glob("*.html"))
    
    if not html_files:
        logger.warning("テストするHTMLファイルが見つかりませんでした")
        sys.exit(0)
        
    logger.info(f"{len(html_files)}個のHTMLファイルが見つかりました")
    
    # 各HTMLファイルに対してテストを実行
    success_count = 0
    for html_file in html_files:
        if load_and_test_cached_html(html_file):
            success_count += 1
    
    # 結果を表示
    logger.info(f"\nテスト結果: {success_count}/{len(html_files)} ファイルでテストが完了しました")
    
    if success_count == len(html_files):
        logger.info("すべてのテストが正常に完了しました")
        sys.exit(0)
    else:
        logger.error(f"{len(html_files) - success_count} ファイルで問題が発生しました")
        sys.exit(1)
