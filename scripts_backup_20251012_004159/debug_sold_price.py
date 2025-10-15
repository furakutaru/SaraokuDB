import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

def debug_sold_price(detail_url):
    """落札価格のデバッグ用関数"""
    scraper = RakutenAuctionScraper()
    
    print(f"\n{'='*50}")
    print(f"デバッグ開始: {detail_url}")
    
    # 詳細ページを取得
    response = scraper.session.get(detail_url, timeout=30)
    response.encoding = 'utf-8'  # エンコーディングを明示的に指定
    
    # HTMLをファイルに保存（デバッグ用）
    with open('debug_page.html', 'w', encoding='utf-8') as f:
        f.write(response.text)
    print("HTMLを debug_page.html に保存しました")
    
    # BeautifulSoupでパース
    from bs4 import BeautifulSoup
    soup = BeautifulSoup(response.text, 'html.parser')
    
    # 落札価格要素を探す
    sold_price_elem = soup.find('th', string='落札価格')
    print(f"\n落札価格要素の検索結果: {sold_price_elem}")
    
    if sold_price_elem:
        td = sold_price_elem.find_next_sibling('td')
        print(f"隣接するtd要素: {td}")
        if td:
            sold_price_text = td.get_text(strip=True)
            print(f"抽出されたテキスト: {sold_price_text}")
            
            # 数値のみ抽出
            import re
            price_match = re.search(r'(\d{1,3}(?:,\d{3})*)', sold_price_text)
            if price_match:
                price = int(price_match.group(1).replace(',', ''))
                print(f"抽出された価格: {price}万円")
            else:
                print("価格の数値が見つかりませんでした")
    
    print(f"\n{'='*50}\n")

if __name__ == "__main__":
    import sys
    if len(sys.argv) > 1:
        test_url = sys.argv[1]
    else:
        test_url = input("デバッグする楽天オークションの詳細ページURLを入力してください: ")
    debug_sold_price(test_url)
