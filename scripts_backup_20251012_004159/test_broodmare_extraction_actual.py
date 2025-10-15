#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from bs4 import BeautifulSoup

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from scripts.components.horse_info_extractor import HorseInfoExtractor

def setup_logging():
    """ロギングの設定"""
    logging.basicConfig(
        level=logging.DEBUG,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )
    return logging.getLogger(__name__)

def test_broodmare_extraction():
    """繁殖牝馬の性別・年齢抽出を実際のHTMLでテスト"""
    logger = setup_logging()
    extractor = HorseInfoExtractor()
    
    # 実際の繁殖牝馬のHTML例（簡略化）
    html_content = """
    <div class="horse-info">
        <h2 class="horse-name">サクラメイワン</h2>
        <div class="horse-details">
            <span class="sex">牝</span>
            <span class="age">5歳</span>
            <span class="broodmare">※繁殖牝馬（受胎）</span>
        </div>
    </div>
    """
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 性別と年齢を抽出
    result = extractor._extract_sex_and_age(soup)
    
    # 結果を表示
    logger.info("抽出結果:")
    logger.info(f"性別: {result.get('sex', '抽出失敗')}")
    logger.info(f"年齢: {result.get('age', '抽出失敗')}歳")
    
    # 期待される結果と比較
    expected_sex = '牝'
    expected_age = 5
    
    if result.get('sex') == expected_sex and result.get('age') == expected_age:
        logger.info("✅ テスト成功: 性別と年齢が正しく抽出されました")
        return True
    else:
        logger.error("❌ テスト失敗: 期待される結果と一致しません")
        logger.info(f"期待される結果: 性別='{expected_sex}', 年齢={expected_age}歳")
        return False

if __name__ == "__main__":
    test_broodmare_extraction()
