import requests
from bs4 import BeautifulSoup
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extract_horse_names.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_horse_info(html_content):
    """HTMLから馬の情報を抽出する"""
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    
    # 馬のカード要素を取得
    horse_cards = soup.select('div.auctionTableCard')
    
    for card in horse_cards:
        try:
            # 馬名を抽出（実際のHTML構造に合わせて修正）
            name_elem = card.select_one('div.horseName')
            name = name_elem.text.strip() if name_elem else '不明な馬'
            
            # 性別を抽出
            sex_elem = card.select_one('div.horseLabelWrapper__horseSex')
            sex = sex_elem.text.strip() if sex_elem else '不明'
            
            # 年齢を抽出
            age_elem = card.select_one('div.horseLabelWrapper__horseAge')
            age = age_elem.text.strip() if age_elem else '不明'
            
            horses.append({
                'name': name,
                'sex': sex,
                'age': age,
                'raw_html': str(card)[:200] + '...'  # デバッグ用に一部のHTMLを保存
            })
            
        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました: {e}")
            logger.debug(f"エラーが発生した要素: {card}")
    
    return horses

def main():
    # 保存したHTMLファイルを読み込む
    html_file = "rakuten_auction_page.html"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"{html_file} から馬情報を抽出中...")
        horses = extract_horse_info(html_content)
        
        # 結果を表示
        print("\n=== 抽出された馬の情報 ===")
        for i, horse in enumerate(horses[:10], 1):  # 最初の10頭を表示
            print(f"\n{i}. 馬名: {horse['name']}")
            print(f"   性別: {horse['sex']}")
            print(f"   年齢: {horse['age']}")
        
        print(f"\n合計 {len(horses)} 頭の馬情報を抽出しました。")
        
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {html_file}")
        logger.info("先に debug_page_structure.py を実行してHTMLを保存してください。")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
