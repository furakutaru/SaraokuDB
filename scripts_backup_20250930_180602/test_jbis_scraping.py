# test_jbis_scraping.py
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from test_prize_extraction_final import extract_prize_from_jbis

# テスト用の馬のリスト（馬名とJBIS URLのペア）
test_horses = [
    {"name": "ディープインパクト", "url": "https://www.jbis.or.jp/horse/0000742976/"},
    {"name": "キタサンブラック", "url": "https://www.jbis.or.jp/horse/0001156551/"},
    {"name": "コントレイル", "url": "https://www.jbis.or.jp/horse/0001282706/"},
    {"name": "エフフォーリア", "url": "https://www.jbis.or.jp/horse/0001303150/"},
    {"name": "ソダシ", "url": "https://www.jbis.or.jp/horse/0001316058/"}
]

def run_tests():
    print("JBISスクレイピングテストを開始します...\n")
    
    for horse in test_horses:
        print(f"【{horse['name']}】の賞金情報を取得中...")
        print(f"URL: {horse['url']}")
        
        prize = extract_prize_from_jbis(horse['url'])
        print(f"総賞金: {prize:,.1f}万円\n")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    run_tests()
