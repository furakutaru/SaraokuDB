#!/usr/bin/env python3
"""
_process_horse_info メソッドのテストスクリプト
"""
import sys
import os
import logging
from bs4 import BeautifulSoup
from improved_scraper import ImprovedRakutenScraper

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def test_process_horse_info():
    """_process_horse_info メソッドのテストを実行"""
    try:
        logger.info("===== _process_horse_info メソッドのテストを開始 =====")
        
        # テスト用のHTMLサンプル - 実際の構造に合わせて修正
        html_content = """
        <div class="auctionTableCard">
            <div class="auctionTableCard__name">テスト馬</div>
            <div class="horseLabelWrapper">
                <div class="horseLabelWrapper__horseSex">牡</div>
                <div class="horseLabelWrapper__horseAge">3</div>
            </div>
            <div class="auctionTableCard__price">1,234万円</div>
            <div class="auctionTableCard__comment">テストコメント</div>
        </div>
        """
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        card = soup.select_one('.auctionTableCard')
        
        if not card:
            logger.error("テスト用のHTMLからカード要素を抽出できませんでした")
            return False
        
        # スクレイパーを初期化
        scraper = ImprovedRakutenScraper(test_mode=True)
        
        # メソッドを実行
        horse_info = scraper._process_horse_info(card, index=1, total=1)
        
        if not horse_info:
            logger.error("馬情報の抽出に失敗しました")
            return False
            
        # 結果を表示
        logger.info("抽出された馬情報:")
        for key, value in horse_info.items():
            logger.info(f"  {key}: {value}")
            
        # 必須フィールドの確認
        required_fields = ['name', 'sex', 'age']
        missing_fields = [field for field in required_fields if field not in horse_info or not horse_info[field]]
        
        if missing_fields:
            logger.error(f"以下の必須フィールドが不足しています: {missing_fields}")
            return False
            
        logger.info("テストが正常に完了しました")
        return True
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)
        return False

if __name__ == "__main__":
    if test_process_horse_info():
        logger.info("===== テスト成功 =====")
        sys.exit(0)
    else:
        logger.error("===== テスト失敗 =====")
        sys.exit(1)
