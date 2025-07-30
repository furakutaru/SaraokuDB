import sys
import os
import json
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

def fetch_page(url):
    """シンプルにrequestsでページを取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def test_comment_extraction():
    # テスト対象の馬のURLリスト（コメントが取得できていない馬）
    test_urls = [
        {"name": "アローロ", "url": "https://auction.keiba.rakuten.co.jp/item/14601"},
        {"name": "ウエスタンタマヤ", "url": "https://auction.keiba.rakuten.co.jp/item/14602"},
        {"name": "ジャスマン", "url": "https://auction.keiba.rakuten.co.jp/item/14603"},
        {"name": "ウインエンデバー", "url": "https://auction.keiba.rakuten.co.jp/item/14604"},
        {"name": "ジューンアレグロ", "url": "https://auction.keiba.rakuten.co.jp/item/14605"},
        {"name": "ミリオンヒット", "url": "https://auction.keiba.rakuten.co.jp/item/14606"},
        {"name": "セレニティ", "url": "https://auction.keiba.rakuten.co.jp/item/14607"},
        {"name": "ウィルトゥーウェル", "url": "https://auction.keiba.rakuten.co.jp/item/14608"},
        {"name": "スカリーワグ", "url": "https://auction.keiba.rakuten.co.jp/item/14609"},
    ]

    scraper = RakutenAuctionScraper()
    results = []

    for horse in test_urls:
        print(f"\n=== テスト中: {horse['name']} ===")
        print(f"URL: {horse['url']}")
        
        try:
            # シンプルにページを取得
            print("ページを取得中...")
            html_content = fetch_page(horse['url'])
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # コメントを抽出
            print("コメントを抽出中...")
            comment = scraper._extract_comment(soup)
            
            # 病気タグを抽出（オプション）
            disease_tags = ""
            if comment:
                disease_tags = scraper._extract_disease_tags(comment)
            
            # 結果を保存
            result = {
                "name": horse['name'],
                "status": "success",
                "comment_length": len(comment) if comment else 0,
                "comment_preview": comment[:200] + "..." if comment and len(comment) > 200 else (comment if comment else ""),
                "disease_tags": disease_tags
            }
            results.append(result)
            
            print(f"抽出されたコメントの長さ: {len(comment) if comment else 0}文字")
            print(f"抽出された病気タグ: {disease_tags}")
            
            # コメントが見つからない場合はHTMLを保存
            if not comment:
                debug_file = f"debug_{horse['name']}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                print(f"[警告] コメントが見つかりませんでした。デバッグ用に {debug_file} を保存しました。")
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
            results.append({"name": horse['name'], "status": "error", "message": str(e)})
            
            # エラーが発生した場合もHTMLを保存
            try:
                debug_file = f"error_{horse['name']}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup) if 'soup' in locals() else 'No HTML content')
                print(f"エラー詳細を {debug_file} に保存しました。")
            except Exception as e2:
                print(f"エラー詳細の保存に失敗しました: {str(e2)}")
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comment_extraction_test_results_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"\n=== テスト完了 ===")
    print(f"結果は {output_file} に保存されました")
    
    # サマリーを表示
    success_count = sum(1 for r in results if r['status'] == 'success' and r.get('comment_length', 0) > 0)
    print(f"\n=== サマリー ===")
    print(f"テストした馬の数: {len(test_urls)}")
    print(f"コメントの抽出に成功: {success_count}頭")
    print(f"コメントの抽出に失敗: {len(test_urls) - success_count}頭")

if __name__ == "__main__":
    test_comment_extraction()
