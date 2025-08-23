import sys
import os
from bs4 import BeautifulSoup
from pathlib import Path

# Add the parent directory to the path so we can import the scraper
sys.path.append(str(Path(__file__).parent))
from improved_scraper import ImprovedRakutenScraper

def test_age_extraction():
    """年齢抽出のテストを実行"""
    # テスト用のHTMLファイルを読み込む
    test_html = """
    <html>
    <head><title>テスト馬名　　牝3歳　　※中央競馬　登録抹消 | サラブレッドオークション</title></head>
    <body>
        <div class="auctionTableCard">
            <div class="auctionTableCard__header">
                <div class="auctionTableCard__name">テスト馬名</div>
                <div class="auctionTableCard__age">3歳</div>
            </div>
            <div class="auctionTableCard__body">
                <div>性別: 牝</div>
                <div>生年月日: 2022年3月15日</div>
                <div>父: テスト父馬</div>
                <div>母: テスト母馬</div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # BeautifulSoupでパース
    soup = BeautifulSoup(test_html, 'html.parser')
    
    # テスト用のscraperインスタンスを作成
    scraper = ImprovedRakutenScraper(test_mode=True)
    
    # 年齢要素を取得
    age_elem = soup.select_one('.auctionTableCard__age')
    card = soup.select_one('.auctionTableCard')
    
    # 年齢を抽出
    age = scraper._extract_age(age_elem, card)
    
    # 結果を表示
    print(f"抽出した年齢: {age}歳")
    
    # 期待される年齢（2025年現在なら3歳）
    expected_age = 3
    
    if age == expected_age:
        print(f"✅ テスト成功: 期待通り{expected_age}歳が抽出されました")
    else:
        print(f"❌ テスト失敗: 期待値={expected_age}歳, 実際={age}歳")

if __name__ == "__main__":
    test_age_extraction()
