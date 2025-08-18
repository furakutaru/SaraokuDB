import os
from bs4 import BeautifulSoup

def analyze_html_structure(html_file):
    """HTMLファイルの構造を分析する"""
    print(f"\n=== {html_file} の構造を分析中 ===\n")
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # 馬のリスト要素を探す
    horse_elements = soup.select('div.auctionTableCard, div.auctionTableRow')
    print(f"馬の要素数: {len(horse_elements)}")
    
    if not horse_elements:
        print("馬の要素が見つかりませんでした。利用可能なクラス名:")
        all_divs = soup.find_all('div', class_=True)
        classes = set()
        for div in all_divs[:100]:  # 最初の100個のdivをチェック
            classes.update(div.get('class', []))
        print("利用可能なクラス:", ", ".join(classes))
        return
    
    # 最初の馬の要素を詳しく分析
    first_horse = horse_elements[0]
    print("\n=== 最初の馬の要素の構造 ===")
    print(first_horse.prettify()[:500] + "...")
    
    # 価格関連の要素を探す
    print("\n=== 価格関連の要素 ===")
    price_elements = []
    for tag in first_horse.find_all(['div', 'span']):
        classes = tag.get('class', [])
        if classes and any(c.lower() in ['price', 'value'] for c in classes):
            price_elements.append(tag)
    
    if not price_elements:
        print("価格関連の要素が見つかりませんでした。")
    else:
        for i, elem in enumerate(price_elements, 1):
            print(f"\n価格要素 {i}:")
            print(f"クラス: {elem.get('class', [])}")
            print(f"テキスト: {elem.get_text(strip=True)}")
            print(f"親要素: {elem.parent.name} (クラス: {elem.parent.get('class', [])})")
    
    # 総賞金のラベルを探す
    print("\n=== 総賞金のラベルを検索 ===")
    for label in first_horse.find_all(string=re.compile(r'総賞金')):
        print(f"ラベル: {label.strip()}")
        print(f"親要素: {label.parent.prettify()[:200]}...")

if __name__ == "__main__":
    import re
    
    # 現在のディレクトリのlist.htmlを探す
    current_dir = os.path.dirname(os.path.abspath(__file__))
    html_file = os.path.join(current_dir, "list.html")
    
    if os.path.exists(html_file):
        analyze_html_structure(html_file)
    else:
        print(f"エラー: {html_file} が見つかりません")
        print("利用可能なファイル:")
        for f in os.listdir(current_dir):
            if f.endswith('.html'):
                print(f"- {f}")
