import json
from bs4 import BeautifulSoup
import logging
from pathlib import Path
from datetime import datetime

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('parse_horse_info.log')
    ]
)
logger = logging.getLogger(__name__)

def extract_horse_info(html_content):
    """HTMLから馬の情報を抽出する"""
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    
    # 馬のカード要素を取得
    horse_cards = soup.select('div.auctionTableCard')
    
    for i, card in enumerate(horse_cards, 1):
        try:
            # 馬名、性別、年齢を含む要素を抽出
            horse_info = {}
            
            # 馬名を抽出
            name_elem = card.select_one('div.horseName')
            if not name_elem:
                # 別のセレクタを試す
                name_elem = card.select_one('div[data-v-472c0de4]')
            
            horse_info['name'] = name_elem.text.strip() if name_elem else '不明な馬'
            
            # 性別を抽出
            sex_elem = card.select_one('div.horseLabelWrapper__horseSex')
            horse_info['sex'] = sex_elem.text.strip() if sex_elem else '不明'
            
            # 年齢を抽出
            age_elem = card.select_one('div.horseLabelWrapper__horseAge')
            horse_info['age'] = age_elem.text.strip() if age_elem else '不明'
            
            # その他の情報があれば追加
            info_elems = card.select('div.horseInfo')
            if info_elems:
                horse_info['info'] = [elem.text.strip() for elem in info_elems]
            
            # 画像URLを抽出
            img_elem = card.select_one('img')
            if img_elem and 'src' in img_elem.attrs:
                horse_info['image_url'] = img_elem['src']
            
            logger.info(f"{i}頭目の馬情報を抽出: {horse_info['name']}")
            horses.append(horse_info)
            
        except Exception as e:
            logger.error(f"{i}頭目の馬情報の抽出中にエラーが発生しました: {e}")
            logger.debug(f"エラーが発生した要素: {card}")
    
    return horses

def save_to_json(data, filename):
    """データをJSONファイルに保存する"""
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        logger.info(f"データを {filename} に保存しました。")
    except Exception as e:
        logger.error(f"ファイルの保存中にエラーが発生しました: {e}")

def main():
    # 保存したHTMLファイルを読み込む
    html_file = "rakuten_auction_page.html"
    output_file = f"horse_info_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        logger.info(f"{html_file} から馬情報を抽出中...")
        horses = extract_horse_info(html_content)
        
        # 結果を表示
        print("\n=== 抽出された馬の情報 (最初の5頭) ===")
        for i, horse in enumerate(horses[:5], 1):
            print(f"\n{i}. 馬名: {horse.get('name', '不明')}")
            print(f"   性別: {horse.get('sex', '不明')}")
            print(f"   年齢: {horse.get('age', '不明')}")
            if 'info' in horse:
                print(f"   その他の情報: {', '.join(horse['info'])}")
        
        print(f"\n合計 {len(horses)} 頭の馬情報を抽出しました。")
        
        # 結果をJSONファイルに保存
        save_to_json(horses, output_file)
        print(f"\n詳細な情報は {output_file} を確認してください。")
        
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {html_file}")
        logger.info("先に debug_page_structure.py を実行してHTMLを保存してください。")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
