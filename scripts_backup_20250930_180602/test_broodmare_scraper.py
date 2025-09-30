#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.improved_scraper import TestConfig, ImprovedRakutenScraper

# ロギング設定
def setup_logger():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_broodmare_scraping():
    """繁殖牝馬の詳細ページをスクレイピングして性別と年齢を抽出するテスト"""
    logger = setup_logger()
    
    # テスト用の設定でスクレイパーを初期化
    config = TestConfig(
        use_cache=True,  # キャッシュを有効に
        cache_dir='test_cache'  # テスト用キャッシュディレクトリ
    )
    
    # スクレイパーの初期化（ロガーのみ使用）
    from scripts.components.horse_info_extractor import HorseInfoExtractor
    horse_info_extractor = HorseInfoExtractor()
    
    # テスト用の繁殖牝馬のHTMLファイルパス
    test_html_path = Path('scripts/html_dump/details/14850.html')
    
    if not test_html_path.exists():
        logger.error(f"テスト用のHTMLファイルが見つかりません: {test_html_path}")
        return
    
    try:
        logger.info(f"テスト用のHTMLファイルを読み込み中: {test_html_path}")
        
        # ファイルからHTMLを読み込む
        with open(test_html_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
            
        # BeautifulSoupでパース
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html_content, 'html.parser')
            
        # 性別と年齢を抽出
        result = horse_info_extractor._extract_sex_and_age(soup)
        
        if result:
            logger.info("抽出結果:")
            logger.info(f"性別: {result.get('sex', '不明')}")
            logger.info(f"年齢: {result.get('age', '不明')}歳")
        else:
            logger.error("性別・年齢の抽出に失敗しました")
                
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    test_broodmare_scraping()
