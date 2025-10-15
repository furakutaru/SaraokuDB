#!/usr/bin/env python3
"""
販売者情報の抽出をテストするスクリプト
"""
import os
import sys
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトのルートをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

def extract_seller(html_content: str) -> str:
    """HTMLから販売者情報を抽出する"""
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # まず「販売申込者」を直接検索
        seller_text = soup.find(string=lambda text: '販売申込者' in str(text))
        if seller_text:
            # テキストノードの親要素を取得
            parent = seller_text.parent
            # テキスト全体を取得
            full_text = parent.get_text(strip=True)
            # 「販売申込者：」の後のテキストを抽出（括弧前まで）
            if '販売申込者：' in full_text:
                seller = full_text.split('販売申込者：', 1)[1].split('（')[0].strip()
                if seller:
                    logger.debug(f"販売申込者から抽出: {seller}")
                    return seller
        
        # テーブル内の販売者情報を検索
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
                
                # 「販売者」または「出品者」を含む行を探す
                for i, cell in enumerate(cells):
                    if any(keyword in cell for keyword in ['販売者', '出品者']):
                        if i + 1 < len(cells):
                            seller = cells[i+1].split('（')[0].strip()
                            if seller:
                                logger.debug(f"テーブルから抽出: {seller}")
                                return seller
                        
                        # セルのテキスト内に「：」で区切られている場合
                        if '：' in cell:
                            seller = cell.split('：', 1)[1].split('（')[0].strip()
                            if seller:
                                return seller
        
        # 見つからなかった場合は空文字を返す
        logger.warning("販売者情報が見つかりませんでした")
        return ""
        
    except Exception as e:
        logger.error(f"販売者情報の抽出中にエラーが発生しました: {str(e)}")
        return ""

def test_seller_extraction(html_file_path: str):
    """指定されたHTMLファイルから販売者情報を抽出してテスト"""
    logger.info(f"Testing seller extraction for: {html_file_path}")
    
    # ファイルの存在確認
    if not os.path.exists(html_file_path):
        logger.error(f"File not found: {html_file_path}")
        return
    
    # HTMLファイルを読み込む
    with open(html_file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # 販売者を抽出
    seller = extract_seller(html_content)
    
    # 結果を表示
    if seller:
        logger.info(f"抽出された販売者: {seller}")
    else:
        logger.warning("販売者を抽出できませんでした")
    
    return seller

if __name__ == "__main__":
    # テストする馬のHTMLファイルパス
    test_file = "/Users/yum.ishii/SaraokuDB/cache/20250929/details/15058.html"
    
    logger.info(f"Starting seller extraction test for horse ID: 15058")
    seller = test_seller_extraction(test_file)
    
    if seller:
        logger.info(f"Successfully extracted seller: {seller}")
    else:
        logger.warning("Failed to extract seller")
    
    logger.info("Test completed")
