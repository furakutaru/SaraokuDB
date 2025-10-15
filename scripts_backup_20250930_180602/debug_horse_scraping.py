#!/usr/bin/env python3
"""
楽天オークションの馬詳細ページのスクレイピングをデバッグするスクリプト

使い方:
    python3 debug_horse_scraping.py [馬ID]

例:
    python3 debug_horse_scraping.py 38  # ID 38の馬をデバッグ
    python3 debug_horse_scraping.py 38 39 40  # 複数の馬をデバッグ
"""
import sys
import json
import os
from pprint import pprint

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

def load_horse_data(horse_id):
    """馬のデータをhorses_history.jsonから読み込む"""
    data_file = os.path.join('static-frontend', 'public', 'data', 'horses_history.json')
    
    try:
        with open(data_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        # horses配列を取得
        horses = data.get('horses', [])
        if not isinstance(horses, list):
            print(f"エラー: 馬データが配列ではありません: {type(horses)}")
            return None
        
        # 指定されたIDの馬を検索
        for horse in horses:
            if not isinstance(horse, dict):
                print(f"警告: 無効な馬データをスキップします: {type(horse)}")
                continue
                
            if horse.get('id') == horse_id:
                return horse
        
        print(f"エラー: ID {horse_id} の馬が見つかりませんでした（総数: {len(horses)}頭）")
        return None
    
    except FileNotFoundError:
        print(f"エラー: データファイルが見つかりません: {data_file}")
        return None
    except json.JSONDecodeError:
        print(f"エラー: データファイルの形式が不正です: {data_file}")
        return None

def debug_horse_scraping(horse_id):
    """指定されたIDの馬のスクレイピングをデバッグ"""
    print(f"\n{'='*50}")
    print(f"馬ID: {horse_id} のデバッグを開始")
    print(f"{'='*50}")
    
    # 馬のデータを読み込む
    horse_data = load_horse_data(horse_id)
    if not horse_data:
        print(f"馬ID {horse_id} のデータを読み込めませんでした")
        return
    
    # デバッグ用にデータ型を確認
    print(f"\n[0/4] データ型チェック:")
    print(f"- horse_data の型: {type(horse_data).__name__}")
    print(f"- キー一覧: {list(horse_data.keys())}")
    
    # 必須フィールドの存在確認
    required_fields = ['id', 'name', 'detail_url']
    missing_fields = [field for field in required_fields if field not in horse_data]
    if missing_fields:
        print(f"\n[!] 必須フィールドが不足しています: {', '.join(missing_fields)}")
        return
    
    print(f"\n[1/3] 現在の馬データ:")
    pprint(horse_data)
    
    # スクレイパーを初期化
    print(f"\n[2/3] スクレイピングを実行中...")
    scraper = RakutenAuctionScraper()
    
    # 詳細ページのURLを取得
    detail_url = horse_data.get('detail_url')
    if not detail_url:
        print(f"エラー: 詳細ページのURLがありません")
        return
    
    # スクレイピングを実行
    scraped_data = scraper.scrape_horse_detail(detail_url)
    
    if not scraped_data:
        print(f"エラー: スクレイピングに失敗しました")
        return
    
    print(f"\n[3/3] スクレイピング結果:")
    pprint(scraped_data)
    
    # 問題のあるフィールドをチェック
    print(f"\n[4/4] 問題のあるフィールド:")
    problem_fields = []
    required_fields = ['sex', 'age', 'dam_sire', 'seller', 'auction_date']
    
    for field in required_fields:
        value = scraped_data.get(field)
        if not value:
            problem_fields.append(f"- {field}: 値が空または存在しません")
    
    if problem_fields:
        print("\n".join(problem_fields))
    else:
        print("必須フィールドはすべて正常に取得されています")
    
    # デバッグ用に生のHTMLを保存
    debug_file = f"debug_horse_{horse_id}.html"
    try:
        response = scraper.session.get(detail_url)
        with open(debug_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        print(f"\nデバッグ用にHTMLを保存しました: {debug_file}")
    except Exception as e:
        print(f"\nHTMLの保存中にエラーが発生しました: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用法: python3 debug_horse_scraping.py [馬ID1] [馬ID2] ...")
        print("例: python3 debug_horse_scraping.py 38 39 40")
        sys.exit(1)
    
    # コマンドライン引数から馬IDを取得
    for horse_id_str in sys.argv[1:]:
        try:
            horse_id = int(horse_id_str)
            debug_horse_scraping(horse_id)
        except ValueError:
            print(f"エラー: 無効な馬IDです: {horse_id_str}")
        print("\n" + "="*50 + "\n")
