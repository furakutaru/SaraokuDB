#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
from bs4 import BeautifulSoup

# キャッシュディレクトリのパス
CACHE_DIR = "/Users/yum.ishii/SaraokuDB/cache/20250822_190555/details"

def extract_price_from_html(html_content):
    """HTMLから価格情報を抽出する"""
    import re
    
    # 1. 主取りチェック
    unsold_keywords = ['主取り', '不成立', '落札不成立', '売却不成立']
    for keyword in unsold_keywords:
        if keyword in html_content:
            return {"status": "unsold", "price": None, "reason": keyword}
    
    # 2. JavaScript のデータから価格を抽出
    # 入札履歴から最高価格を取得
    bid_history_match = re.search(r'"bid_history":\s*(\[.*?\])', html_content, re.DOTALL)
    if bid_history_match:
        import json
        try:
            bid_history = json.loads(bid_history_match.group(1))
            if bid_history and len(bid_history) > 0:
                # 最高価格を取得（最後の入札が最高価格）
                highest_bid = bid_history[-1]
                if 'price' in highest_bid:
                    return {
                        "status": "sold", 
                        "price": highest_bid['price'], 
                        "source": f"bid_history: {highest_bid['price']}円"
                    }
        except json.JSONDecodeError:
            pass  # JSONのパースに失敗した場合は次の方法を試す
    
    # 3. 直接的な価格表記を検索
    price_patterns = [
        (r'"current_price"\s*:\s*(\d+)', 1),  # "current_price": 1000000
        (r'"price"\s*:\s*(\d+)', 1),         # "price": 1000000
        (r'落札価格[：:](?:\s*)([\d,]+)(?:\s*万円|万)', 10000),  # 「落札価格：1,000万円」形式
        (r'落札価格[：:](?:\s*)([\d,]+)(?:\s*円)', 1),          # 「落札価格：1,000円」形式
        (r'価格[：:](?:\s*)([\d,]+)(?:\s*万円|万)', 10000),     # 「価格：1,000万円」形式
        (r'¥\s*([\d,]+)', 1),                                    # 「¥1,000」形式
    ]
    
    for pattern, multiplier in price_patterns:
        match = re.search(pattern, html_content)
        if match:
            price_str = match.group(1).replace(',', '')
            if price_str.isdigit():
                price = int(price_str) * multiplier
                return {
                    "status": "sold", 
                    "price": price, 
                    "source": f"regex: {pattern} (x{multiplier})"
                }
    
    # 4. 価格要素を検索
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        price_elements = soup.select('.price, .price-value, .sold-price, [itemprop="price"]')
        for element in price_elements:
            price_text = element.get_text(strip=True)
            price_match = re.search(r'([\d,]+)(?:\s*万円|\s*万|\s*円)?', price_text)
            if price_match:
                price_str = price_match.group(1).replace(',', '')
                if price_str.isdigit():
                    price = int(price_str)
                    if '万' in price_text:
                        price *= 10000
                    return {"status": "sold", "price": price, "source": f"element: {price_text}"}
    except Exception as e:
        print(f"Error parsing HTML: {e}")
    
    return {"status": "not_found", "price": None, "reason": "No price information found"}

def test_cached_files():
    """キャッシュされたHTMLファイルをテストする"""
    if not os.path.exists(CACHE_DIR):
        print(f"エラー: キャッシュディレクトリが見つかりません: {CACHE_DIR}")
        return
    
    # キャッシュファイルの一覧を取得
    html_files = [f for f in os.listdir(CACHE_DIR) if f.endswith('.html')]
    
    print(f"\n{'='*80}")
    print(f"キャッシュされたHTMLファイルから価格情報を抽出します (合計: {len(html_files)}ファイル)")
    print(f"{'='*80}\n")
    
    results = []
    
    for i, filename in enumerate(html_files, 1):
        filepath = os.path.join(CACHE_DIR, filename)
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            # 馬名を抽出（デバッグ用）
            title = ""
            if '<title>' in html_content:
                title = html_content.split('<title>')[1].split('|')[0].strip()
                
            # 価格情報を抽出
            result = extract_price_from_html(html_content)
            result['filename'] = filename
            result['title'] = title
            results.append(result)
            
            # 進捗表示
            status_icon = "✅" if result['status'] == 'sold' else "❌" if result['status'] == 'unsold' else "❓"
            print(f"{i:3d}/{len(html_files)} {status_icon} {title[:20]:<20} | {result['status']:<8} | {result.get('price', 'N/A'):>10,} | {result.get('reason', '')}")
            
        except Exception as e:
            print(f"{i:3d}/{len(html_files)} ❌ エラー: {str(e)}")
    
    # 集計結果を表示
    print("\n" + "="*80)
    print("抽出結果の集計:")
    print("="*80)
    
    sold_count = sum(1 for r in results if r['status'] == 'sold')
    unsold_count = sum(1 for r in results if r['status'] == 'unsold')
    not_found_count = sum(1 for r in results if r['status'] == 'not_found')
    
    print(f"総ファイル数: {len(results)}")
    print(f"落札済み: {sold_count}件")
    print(f"主取り: {unsold_count}件")
    print(f"価格不明: {not_found_count}件")
    
    # 落札価格の統計
    prices = [r['price'] for r in results if r['status'] == 'sold' and r['price'] is not None]
    if prices:
        print(f"\n落札価格の統計:")
        print(f"  最高価格: {max(prices):,}円")
        print(f"  最低価格: {min(prices):,}円")
        print(f"  平均価格: {sum(prices)/len(prices):,.0f}円")
    
    # 結果をJSONに保存
    output_file = "price_extraction_results.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な結果を {output_file} に保存しました。")

if __name__ == "__main__":
    test_cached_files()
