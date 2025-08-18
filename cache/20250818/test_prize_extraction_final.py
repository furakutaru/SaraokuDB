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
    
    # 馬のリスト要素を探す
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    
    for idx, element in enumerate(horse_elements[:2], 1):  # 最初の2頭のみテスト
        print(f"\n=== 馬 {idx}の情報 ===")
        
        # 馬名を抽出
        name_elem = element.select_one('.auctionTableCard__name, .horseName')
        name = name_elem.get_text(strip=True) if name_elem else '名前不明'
        print(f"馬名: {name}")
        
        # 賞金を抽出
        print("\n賞金抽出を開始...")
        
        # 1. まずはauctionTableCard__priceクラスを直接探す
        price_elem = element.select_one('.auctionTableCard__price .value')
        
        if price_elem:
            prize_text = price_elem.get_text(strip=True)
            print(f"賞金テキスト: {prize_text}")
            
            # 数値部分を抽出（例: "0.0万円" -> 0.0）
            match = re.search(r'([\d,\.]+)', prize_text)
            if match:
                try:
                    total_prize = float(match.group(1).replace(',', ''))
                    print(f"抽出した総賞金: {total_prize}万円")
                except ValueError as e:
                    print(f"賞金の数値変換エラー: {e}")
        else:
            print("警告: 賞金要素が見つかりませんでした")
        
        # 2. 他の価格関連要素を表示（デバッグ用）
        debug_price_elems = element.find_all('div', class_=lambda x: x and 'price' in str(x).lower())
        if debug_price_elems:
            print("\nデバッグ: その他の価格関連要素:")
            for i, elem in enumerate(debug_price_elems, 1):
                print(f"  {i}. クラス: {elem.get('class', [])}, テキスト: {elem.get_text(strip=True)}")
        
        print("-" * 50)

if __name__ == "__main__":
    # テスト用のHTMLファイルを指定
    html_file = "list.html"  # 適切なパスに変更してください
    
    if os.path.exists(html_file):
        test_prize_extraction(html_file)
    else:
        print(f"エラー: {html_file} が見つかりません")
        print("テスト用のHTMLファイルを指定してください")
