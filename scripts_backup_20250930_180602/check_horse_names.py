import json
from bs4 import BeautifulSoup
import re

def check_horse_names(html_file):
    """馬名が省略されていないかチェックする"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    horse_cards = soup.select('div.auctionTableCard')
    
    total_horses = len(horse_cards)
    truncated_names = []
    
    print(f"\n=== 馬名チェック開始（全{total_horses}頭） ===\n")
    
    for i, card in enumerate(horse_cards, 1):
        # 馬名を含む要素を取得
        horse_info = card.select_one('div.auctionTableCard__horseInfo')
        if not horse_info:
            continue
            
        # 馬名を抽出（最初のテキストノードを取得）
        horse_name = next((text for text in horse_info.stripped_strings), '').strip()
        
        # 馬名が「...」で終わっているか、短すぎる場合は要確認
        if '...' in horse_name or len(horse_name) <= 2:
            truncated_names.append({
                'index': i,
                'name': horse_name,
                'full_text': horse_info.get_text(separator=' ', strip=True)[:100]
            })
            print(f"🔍 要確認 {i}頭目: {horse_name}...")
    
    # 結果を表示
    print(f"\n=== チェック結果 ===")
    print(f"総馬数: {total_horses}頭")
    print(f"要確認馬: {len(truncated_names)}頭")
    
    if truncated_names:
        print("\n以下の馬名が省略されている可能性があります:")
        for horse in truncated_names:
            print(f"- {horse['index']}頭目: {horse['name']} (テキスト: {horse['full_text']})")
    else:
        print("\n✅ 馬名の省略は見つかりませんでした。")
    
    # 結果をファイルに保存
    result = {
        'total_horses': total_horses,
        'truncated_names': truncated_names,
        'truncated_count': len(truncated_names)
    }
    
    with open('horse_name_check_result.json', 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print("\n詳細な結果を 'horse_name_check_result.json' に保存しました。")

if __name__ == "__main__":
    html_file = "rakuten_auction_page.html"
    check_horse_names(html_file)
