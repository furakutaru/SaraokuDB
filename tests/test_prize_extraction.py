import re
from bs4 import BeautifulSoup

def extract_prize_money(html_content):
    """HTMLから賞金情報を抽出するテスト関数"""
    soup = BeautifulSoup(html_content, 'html.parser')
    total_prize = 0.0
    
    # 賞金を含む行を探す
    prize_row = None
    for row in soup.find_all('div', class_=lambda x: x and 'auctionTableRow' in x):
        if 'auctionTableRow__price' in row.get('class', []):
            label = row.find('div', class_='label')
            if label and '総賞金' in label.get_text(strip=True):
                prize_row = row
                break
    
    if not prize_row:
        # 別のパターンを試す
        for row in soup.find_all('div', class_=lambda x: x and 'price' in x.lower()):
            label = row.find('div', class_=lambda x: x and 'label' in x.lower())
            if label and '総賞金' in label.get_text(strip=True):
                prize_row = row
                break
    
    if prize_row:
        # 価格を含む要素を探す
        value_elem = prize_row.find('div', class_='value')
        if not value_elem:
            # 別のクラス名を試す
            value_elem = prize_row.find('div', class_=lambda x: x and 'value' in x.lower())
            
        if value_elem:
            prize_text = value_elem.get_text(strip=True)
            print(f"賞金テキスト: {prize_text}")
            
            # 数値部分を抽出（例: "379.0万円" -> 379.0）
            match = re.search(r'([\d,\.]+)', prize_text)
            if match:
                try:
                    total_prize = float(match.group(1).replace(',', ''))
                    print(f"抽出した総賞金: {total_prize}万円")
                except ValueError as e:
                    print(f"賞金の数値変換エラー: {e}")
    
    return total_prize

# テスト実行
if __name__ == "__main__":
    # テストケース1: 通常の賞金表記
    test_html1 = """
    <div class="auctionTableRow auctionTableRow__price">
        <div class="label">総賞金</div>
        <div class="value">379.0万円</div>
    </div>
    """
    
    # テストケース2: クラス名が異なる場合
    test_html2 = """
    <div class="price-info">
        <div class="label-text">総賞金</div>
        <div class="value-text">1,234.5万円</div>
    </div>
    """
    
    print("=== テストケース1 ===")
    result1 = extract_prize_money(test_html1)
    print(f"テストケース1の賞金: {result1}万円\n")
    
    print("=== テストケース2 ===")
    result2 = extract_prize_money(test_html2)
    print(f"テストケース2の賞金: {result2}万円")
