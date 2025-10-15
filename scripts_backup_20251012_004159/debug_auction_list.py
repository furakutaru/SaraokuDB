import sys
from bs4 import BeautifulSoup

def debug_auction_list(file_path):
    # HTMLファイルを読み込む
    with open(file_path, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬のカードを検索
    horse_cards = soup.select('.auctionTableCard')
    print(f"Found {len(horse_cards)} horse cards in the list")
    
    # 最初の馬のカードを表示
    if horse_cards:
        first_card = horse_cards[0]
        print("\n=== First Horse Card HTML (first 1000 chars) ===")
        print(str(first_card)[:1000])
        
        # 馬名の抽出を試みる
        name_elem = first_card.select_one('.auctionTableCard__name a')
        print(f"\nName element found: {bool(name_elem)}")
        if name_elem:
            print(f"Name text: {name_elem.get_text(strip=True)}")
        
        # 性別と年齢の抽出を試みる
        sex_elem = first_card.select_one('.horseLabelWrapper__horseSex')
        age_elem = first_card.select_one('.horseLabelWrapper__horseAge')
        print(f"\nSex element found: {bool(sex_elem)}")
        print(f"Age element found: {bool(age_elem)}")
        
        if sex_elem:
            print(f"Sex text: {sex_elem.get_text(strip=True)}")
        if age_elem:
            print(f"Age text: {age_elem.get_text(strip=True)}")
        
        # 販売者情報の抽出を試みる
        seller_elem = first_card.select_one('.auctionTableCard__seller .value')
        print(f"\nSeller element found: {bool(seller_elem)}")
        if seller_elem:
            print(f"Seller text: {seller_elem.get_text(strip=True)}")
        
        # 賞金情報の抽出を試みる
        prize_elem = first_card.select_one('.auctionTableCard__price .value')
        print(f"\nPrize element found: {bool(prize_elem)}")
        if prize_elem:
            print(f"Prize text: {prize_elem.get_text(strip=True)}")
    
    # すべてのクラスを表示
    print("\n=== All classes in the document ===")
    all_classes = set()
    for element in soup.find_all(class_=True):
        all_classes.update(element['class'])
    print("\n".join(sorted(all_classes)))

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_auction_list.py <path_to_html_file>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    debug_auction_list(file_path)
