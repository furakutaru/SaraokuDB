import json
from bs4 import BeautifulSoup
import re

def extract_horse_info(card, index):
    """馬のカードから情報を抽出する"""
    # 馬名を含む要素を取得
    horse_info = card.select_one('div.auctionTableCard__horseInfo')
    if not horse_info:
        return None
    
    # 馬名を抽出（最初のテキストノード）
    horse_name = next((text for text in horse_info.stripped_strings), '').strip()
    
    # 性別と年齢を抽出
    age_sex_elem = card.select_one('div:first-child')
    age_sex = age_sex_elem.get_text(separator=' ', strip=True) if age_sex_elem else '不明'
    
    # 販売者情報を抽出
    seller_elem = card.select_one('div.auctionTableCard__seller')
    seller = seller_elem.get_text(separator=' ', strip=True) if seller_elem else '不明'
    
    # 賞金情報を抽出
    prize_elem = card.select_one('div.auctionTableCard__prize')
    prize = prize_elem.get_text(separator=' ', strip=True) if prize_elem else '不明'
    
    # 馬名が省略されている可能性のあるパターン
    is_truncated = '...' in horse_name or len(horse_name) <= 2
    
    return {
        'index': index,
        'name': horse_name,
        'age_sex': age_sex,
        'seller': seller,
        'prize': prize,
        'is_truncated': is_truncated,
        'full_text': card.get_text(separator=' | ', strip=True)[:200]
    }

def main():
    html_file = "rakuten_auction_page.html"
    output_file = "horse_names_analysis.json"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        horse_cards = soup.select('div.auctionTableCard')
        
        results = []
        for i, card in enumerate(horse_cards, 1):
            result = extract_horse_info(card, i)
            if result:
                results.append(result)
        
        # 結果を表示
        print(f"\n=== 馬名チェック結果（全{len(results)}頭） ===\n")
        
        # 要確認の馬を表示
        truncated_horses = [h for h in results if h['is_truncated']]
        
        if truncated_horses:
            print(f"⚠️ 以下の{len(truncated_horses)}頭の馬名に問題の可能性があります:\n")
            for horse in truncated_horses:
                print(f"{horse['index']}頭目: {horse['name']}")
                print(f"   性別・年齢: {horse['age_sex']}")
                print(f"   販売者: {horse['seller']}")
                print(f"   賞金: {horse['prize']}")
                print(f"   テキスト: {horse['full_text'][:100]}...\n")
        else:
            print("✅ 馬名の省略や問題は見つかりませんでした。")
        
        # 最初の5頭の情報を表示
        print("\n=== 最初の5頭の情報 ===\n")
        for horse in results[:5]:
            print(f"{horse['index']}頭目: {horse['name']} ({horse['age_sex']})")
            print(f"   販売者: {horse['seller']}")
            print(f"   賞金: {horse['prize']}")
            print(f"   テキスト: {horse['full_text'][:100]}...\n")
        
        # 結果をJSONファイルに保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump({
                'total_horses': len(results),
                'truncated_count': len(truncated_horses),
                'horses': results
            }, f, ensure_ascii=False, indent=2)
        
        print(f"\n詳細な結果を '{output_file}' に保存しました。")
        
    except FileNotFoundError:
        print(f"エラー: ファイル '{html_file}' が見つかりません。")
    except Exception as e:
        print(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    main()
