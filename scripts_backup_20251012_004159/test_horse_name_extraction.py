import sys
import os
import logging
from pathlib import Path
from bs4 import BeautifulSoup

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_horse_name_extraction.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_horse_names(html_content):
    """HTMLから馬名を抽出する関数"""
    soup = BeautifulSoup(html_content, 'html.parser')
    horse_names = []
    
    # 馬のカード要素を探す（実際のHTML構造に合わせて修正が必要）
    horse_cards = soup.select('div.horse-card')
    
    for card in horse_cards:
        try:
            # 馬名を抽出（実際のHTML構造に合わせて修正が必要）
            name_elem = card.select_one('span.horse-name')
            if name_elem:
                horse_names.append(name_elem.text.strip())
        except Exception as e:
            logger.error(f"馬名の抽出中にエラーが発生しました: {e}")
    
    return horse_names

def main():
    # テスト用のHTMLファイルを読み込む
    test_html = """
    <!DOCTYPE html>
    <html>
    <body>
        <div class="horse-card">
            <span class="horse-name">サトノダイヤモンド</span>
            <span class="age">4</span>
        </div>
        <div class="horse-card">
            <span class="horse-name">キタサンブラック</span>
            <span class="age">5</span>
        </div>
    </body>
    </html>
    """
    
    # 馬名を抽出
    horse_names = extract_horse_names(test_html)
    
    # 結果を表示
    print("\n抽出された馬名:")
    for i, name in enumerate(horse_names, 1):
        print(f"{i}. {name}")
    
    print(f"\n合計 {len(horse_names)} 頭の馬名を抽出しました。")

if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        logger.error("エラーが発生しました:", exc_info=True)
        print(f"\nエラーが発生しました: {str(e)}")
