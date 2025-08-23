#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from improved_scraper import ImprovedRakutenScraper

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_prize_money.log')
    ]
)
logger = logging.getLogger(__name__)

def test_extract_prize_money():
    """_extract_prize_money メソッドのテストを実行"""
    try:
        # テスト用のHTMLファイルを読み込む
        test_html_dir = os.path.join(os.path.dirname(__file__), 'test_data')
        test_file = os.path.join(test_html_dir, 'test_horse_detail.html')
        
        if not os.path.exists(test_file):
            logger.error(f"テスト用のHTMLファイルが見つかりません: {test_file}")
            logger.info("テスト用のHTMLファイルを作成しますか？ (y/n): ")
            if input().strip().lower() == 'y':
                create_test_file(test_file)
            else:
                return False
        
        with open(test_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(test_mode=True)
        
        # 賞金情報を抽出
        jbis_url = "https://www.jbis.or.jp/horse/0001313610/"  # テスト用のJBIS URL
        result = scraper._extract_prize_money(
            page_text=html_content,
            jbis_url=jbis_url,
            race_record="未出走"
        )
        
        logger.info(f"賞金情報の抽出結果: {result}")
        
        # 未出走馬のテスト
        assert result['prize_source'] == 'unraced', "未出走馬の判定に失敗しました"
        assert result['total_prize_start'] == 0.0, "未出走馬の賞金が0ではありません"
        
        # 通常の馬のテスト
        result = scraper._extract_prize_money(
            page_text=html_content,
            jbis_url=jbis_url,
            race_record="1-1-1-3"
        )
        
        logger.info(f"賞金情報の抽出結果: {result}")
        
        if result['prize_source'] != 'not_found':
            logger.info("賞金情報の抽出に成功しました")
            return True
        else:
            logger.warning("賞金情報が見つかりませんでした")
            return False
            
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def create_test_file(file_path):
    """テスト用のHTMLファイルを作成"""
    os.makedirs(os.path.dirname(file_path), exist_ok=True)
    
    # テスト用のHTMLコンテンツ
    html_content = """
    <!DOCTYPE html>
    <html>
    <head>
        <title>テスト用馬詳細ページ</title>
    </head>
    <body>
        <div class="horse-detail">
            <h1>テスト用馬名</h1>
            <div class="horse-info">
                <div class="info-row">
                    <div class="info-label">総賞金</div>
                    <div class="info-value">1,234.5万円</div>
                </div>
                <div class="info-row">
                    <div class="info-label">賞金</div>
                    <div class="info-value">1,234.5万円</div>
                </div>
                <div class="info-row">
                    <div class="info-label">JBIS</div>
                    <div class="info-value">
                        <a href="https://www.jbis.or.jp/horse/0001313610/" target="_blank">JBIS</a>
                    </div>
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(html_content)
    
    logger.info(f"テスト用のHTMLファイルを作成しました: {file_path}")

if __name__ == "__main__":
    if test_extract_prize_money():
        logger.info("テストが正常に完了しました")
        sys.exit(0)
    else:
        logger.error("テストが失敗しました")
        sys.exit(1)
