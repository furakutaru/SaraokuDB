#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
本番環境用スクレイパー実行スクリプト
"""
import os
import sys
import json
from pathlib import Path
from datetime import datetime
from improved_scraper import ImprovedRakutenScraper, ScraperConfig

def setup_logging():
    """ログ設定"""
    import logging
    
    # ログディレクトリの作成
    log_dir = Path('logs')
    log_dir.mkdir(exist_ok=True)
    
    # ログファイル名（日時ベース）
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    log_file = log_dir / f'scraper_production_{timestamp}.log'
    
    # ログ設定
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(log_file, encoding='utf-8'),
            logging.StreamHandler(sys.stdout)
        ]
    )
    
    return logging.getLogger(__name__)

def save_results(horses, output_dir=None):
    """結果をJSONファイルに保存"""
    # 出力ディレクトリのパスを設定
    if output_dir is None:
        # スクリプトと同じディレクトリのoutputフォルダを使用
        output_path = Path(__file__).parent / 'output'
    else:
        output_path = Path(output_dir)
    
    # 出力ディレクトリの作成
    output_path.mkdir(parents=True, exist_ok=True)
    
    # タイムスタンプ付きのファイル名
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    output_file = output_path / f'horses_{timestamp}.json'
    
    # JSONとして保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(horses, f, ensure_ascii=False, indent=2)
    
    return output_file

def main():
    """メイン処理"""
    logger = setup_logging()
    logger.info("スクレイパーを開始します")
    
    try:
        # 設定（本番環境向け）
        config = ScraperConfig(
            use_cache=False,  # 本番環境ではキャッシュを無効化
            max_workers=5,    # 並列処理数
            timeout=30,       # タイムアウト（秒）
            max_retries=3,    # 最大リトライ回数
            use_mobile=True   # モバイル版のUser-Agentを使用（馬名の省略を防ぐ）
        )
        
        # スクレイパーの初期化
        logger.info("スクレイパーを初期化しています...")
        scraper = ImprovedRakutenScraper(config=config)
        
        # 馬一覧のスクレイピング
        logger.info("馬一覧のスクレイピングを開始します...")
        horses = scraper.scrape_horse_list()
        
        if not horses:
            logger.error("馬の情報を取得できませんでした")
            return 1
        
        # 結果の保存
        output_file = save_results(horses)
        logger.info(f"{len(horses)}件の馬情報を {output_file} に保存しました")
        
        # 必須フィールドのチェック
        required_fields = ['name', 'age', 'sex']
        missing_fields = []
        
        for horse in horses:
            for field in required_fields:
                if field not in horse or horse[field] is None:
                    missing_fields.append((horse.get('name', '名前不明'), field))
        
        if missing_fields:
            logger.warning(f"以下の馬で必須フィールドが不足しています（{len(missing_fields)}件）:")
            for name, field in missing_fields[:10]:  # 最初の10件のみ表示
                logger.warning(f"  - {name}: {field} が不足")
            if len(missing_fields) > 10:
                logger.warning(f"  ... 他 {len(missing_fields) - 10}件")
        else:
            logger.info("すべての馬で必須フィールドが正しく取得されました")
        
        return 0
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
