import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from bs4 import BeautifulSoup
import re

def test_prize_extraction(html_file):
    """HTMLファイルから賞金情報を抽出するテスト"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    total_prize = 0.0
    
    # 馬のリスト要素を探す
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    
    for element in horse_elements[:2]:  # 最初の2頭のみテスト
        print("\n=== 馬の情報を抽出中 ===")
        
        # 馬名を抽出
        name_elem = element.select_one('.auctionTableCard__name, .horseName')
        name = name_elem.get_text(strip=True) if name_elem else '名前不明'
        print(f"馬名: {name}")
        
        # 賞金を抽出
        print("\n賞金抽出を開始...")
        prize_row = None
        
        # パターン1: auctionTableRow__price クラスを持つ要素を探す
        for row in element.find_all('div', class_=lambda x: x and 'auctionTableRow' in x):
            if 'auctionTableRow__price' in row.get('class', []):
                label = row.find('div', class_='label')
                if label and '総賞金' in label.get_text(strip=True):
                    prize_row = row
                    break
        
        # パターン2: price を含むクラス名の要素を探す
        if not prize_row:
            for row in element.find_all('div', class_=lambda x: x and 'price' in str(x).lower()):
                label = row.find('div', class_=lambda x: x and 'label' in str(x).lower())
                if label and '総賞金' in label.get_text(strip=True):
                    prize_row = row
                    break
        
        if prize_row:
            print("賞金行を発見しました")
            print(f"HTML: {prize_row.prettify()[:200]}...")  # 最初の200文字を表示
            
            # 価格を含む要素を探す
            value_elem = prize_row.find('div', class_='value')
            if not value_elem:
                value_elem = prize_row.find('div', class_=lambda x: x and 'value' in str(x).lower())
            
            if value_elem:
                prize_text = value_elem.get_text(strip=True)
                print(f"賞金テキスト: {prize_text}")
                
                # 数値部分を抽出
                match = re.search(r'([\d,\.]+)', prize_text)
                if match:
                    try:
                        total_prize = float(match.group(1).replace(',', ''))
                        print(f"抽出した総賞金: {total_prize}万円")
                    except ValueError as e:
                        print(f"賞金の数値変換エラー: {e}")
            else:
                print("価格要素が見つかりませんでした")
        else:
            print("賞金行が見つかりませんでした")
            
        print("-" * 50)

if __name__ == "__main__":
    # テスト用のHTMLファイルを指定
    html_file = "list.html"  # 適切なパスに変更してください
    
    if os.path.exists(html_file):
        test_prize_extraction(html_file)
    else:
        print(f"エラー: {html_file} が見つかりません")
        print("テスト用のHTMLファイルを指定してください")
