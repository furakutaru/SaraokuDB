import os
import sys
from bs4 import BeautifulSoup
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

def test_parse_html(file_path):
    # HTMLファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬名の抽出を試みる
    name_elem = soup.select_one('.auctionTableCard__name a')
    name = name_elem.get_text(strip=True) if name_elem else '名前が見つかりませんでした'
    
    # 性別と年齢の抽出を試みる
    sex_elem = soup.select_one('.horseLabelWrapper__horseSex')
    age_elem = soup.select_one('.horseLabelWrapper__horseAge')
    
    sex = sex_elem.get_text(strip=True) if sex_elem else '性別不明'
    age = age_elem.get_text(strip=True) if age_elem else '年齢不明'
    
    # 販売者情報の抽出を試みる
    seller_elem = soup.select_one('.auctionTableCard__seller .value')
    seller = seller_elem.get_text(strip=True) if seller_elem else '販売者情報なし'
    
    # 賞金情報の抽出を試みる
    prize_elem = soup.select_one('.auctionTableCard__price .value')
    prize = prize_elem.get_text(strip=True) if prize_elem else '賞金情報なし'
    
    # 結果を表示
    print(f"馬名: {name}")
    print(f"性別: {sex}, 年齢: {age}")
    print(f"販売者: {seller}")
    print(f"賞金: {prize}")
    
    # デバッグ用にHTMLの一部を表示
    print("\n=== デバッグ情報 ===")
    print(f"auctionTableCard__name 要素: {bool(name_elem)}")
    print(f"horseLabelWrapper__horseSex 要素: {bool(sex_elem)}")
    print(f"horseLabelWrapper__horseAge 要素: {bool(age_elem)}")
    print(f"auctionTableCard__seller .value 要素: {bool(seller_elem)}")
    print(f"auctionTableCard__price .value 要素: {bool(prize_elem)}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python test_scraper.py <HTMLファイルのパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    if not os.path.exists(file_path):
        print(f"エラー: ファイルが見つかりません: {file_path}")
        sys.exit(1)
    
    test_parse_html(file_path)
