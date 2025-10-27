from bs4 import BeautifulSoup
import glob
import os

def extract_prize_info(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
        
        # 総賞金を探す
        for row in soup.find_all('div', class_='auctionTableRow'):
            label = row.find('div', class_='auctionTableRow__label')
            if label and '総賞金' in label.get_text():
                value = row.find('div', class_='auctionTableRow__value')
                if value:
                    return value.get_text(strip=True)
        
        # 見つからなかった場合、他の可能性を探す
        for elem in soup.find_all(string=True):
            if '総賞金' in str(elem):
                print(f"総賞金を含む要素: {elem.parent}")
        
        return None

# デバッグ用HTMLファイルを処理
debug_dir = 'debug_html'
for html_file in glob.glob(os.path.join(debug_dir, 'horse_*.html')):
    prize = extract_prize_info(html_file)
    print(f"{os.path.basename(html_file)}: {prize}")
