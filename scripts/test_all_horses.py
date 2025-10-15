#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import logging
from pathlib import Path
from datetime import datetime

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.improved_scraper import ScraperConfig, ImprovedRakutenScraper

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

def test_all_horses():
    """全ての馬の情報をスクレイピングして確認するテスト"""
    logger = setup_logger()
    
    try:
        # 本番環境用の設定でスクレイパーを初期化
        config = ScraperConfig(
            use_cache=True,  # キャッシュを有効に
            cache_dir='cache',  # 本番用キャッシュディレクトリ
            max_workers=5  # 並列処理のワーカー数
        )
        
        # スクレイパーの初期化
        scraper = ImprovedRakutenScraper(config)
        
        # スクレイピング実行
        logger.info("スクレイピングを開始します...")
        horses = scraper.scrape_horse_list()
        
        if not horses:
            logger.error("馬の情報を取得できませんでした")
            return
        
        # 結果の確認
        logger.info(f"合計 {len(horses)} 頭の馬の情報を取得しました")
        
        # 性別と年齢が正しく取得できているか確認
        missing_info = []
        for i, horse in enumerate(horses, 1):
            name = horse.get('name', '名前不明')
            sex = horse.get('sex')
            age = horse.get('age')
            
            if not sex or not age:
                missing_info.append({
                    'id': horse.get('id'),
                    'name': name,
                    'sex': sex,
                    'age': age,
                    'detail_url': horse.get('detail_url')
                })
            
            logger.info(f"[{i}/{len(horses)}] {name}: 性別={sex}, 年齢={age}")
        
        # 結果のサマリーを表示
        if missing_info:
            logger.warning(f"\n情報が不足している馬が {len(missing_info)} 頭見つかりました:")
            for horse in missing_info:
                logger.warning(f"- {horse['name']} (ID: {horse['id']}): 性別={horse['sex']}, 年齢={horse['age']}")
                if horse['detail_url']:
                    logger.warning(f"  詳細URL: {horse['detail_url']}")
        else:
            logger.info("\n全ての馬の性別と年齢が正しく取得できました！")
        
        # 結果をファイルに保存
        output_file = Path('scraping_results.json')
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(horses, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\nスクレイピング結果を {output_file} に保存しました")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)

if __name__ == "__main__":
    test_all_horses()
