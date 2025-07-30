import json
import os
import sys
from datetime import datetime
from pathlib import Path

# 親ディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scrapers.rakuten_scraper import RakutenAuctionScraper

def load_existing_horses():
    """既存のhorses_history.jsonを読み込む"""
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'frontend',
        'public',
        'data',
        'horses_history.json'
    )
    
    if not os.path.exists(json_path):
        print(f"エラー: {json_path} が見つかりません")
        return None
    
    try:
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if 'horses' in data:
                return data['horses']
            return data
    except Exception as e:
        print(f"JSONの読み込み中にエラーが発生しました: {e}")
        return None

def update_horse_data(scraper, horse):
    """個別の馬のデータを更新"""
    if not isinstance(horse, dict):
        print(f"スキップ: 無効なデータ形式です - {horse}")
        return None
        
    if not horse.get('detail_url'):
        print(f"スキップ: 詳細URLが存在しません - {horse.get('name', '不明')}")
        return None
    
    print(f"\n=== 馬の情報を更新中: {horse.get('name')} ===")
    print(f"URL: {horse.get('detail_url')}")
    
    try:
        # 詳細ページからデータをスクレイピング
        updated_data = scraper.scrape_horse_detail(horse['detail_url'])
        
        if not updated_data:
            print("エラー: データの取得に失敗しました")
            return None
            
        # 既存のデータを保持しつつ、新しいデータで上書き
        horse.update(updated_data)
        
        # 更新日時を記録
        horse['last_updated'] = datetime.now().isoformat()
        
        print(f"更新が完了しました: {horse.get('name')}")
        return horse
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")
        return None

def save_updated_data(updated_horses):
    """更新されたデータを保存"""
    if not updated_horses:
        print("更新するデータがありません")
        return
    
    json_path = os.path.join(
        os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))),
        'frontend',
        'public',
        'data',
        'horses_history_updated.json'  # まずは別ファイルに保存
    )
    
    try:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(updated_horses, f, ensure_ascii=False, indent=2)
        print(f"\n更新されたデータを保存しました: {json_path}")
        return True
    except Exception as e:
        print(f"データの保存中にエラーが発生しました: {e}")
        return False

def main():
    # 既存の馬データを読み込み
    horses_data = load_existing_horses()
    if not horses_data:
        print("馬データの読み込みに失敗しました")
        return
        
    # 馬のリストを取得（horsesが辞書のキーになっている場合と配列の場合の両方に対応）
    if isinstance(horses_data, dict) and 'horses' in horses_data:
        horses = horses_data['horses']
    elif isinstance(horses_data, list):
        horses = horses_data
    else:
        print("無効なデータ形式です")
        return
    
    print(f"合計 {len(horses)} 頭の馬のデータを読み込みました")
    
    # スクレイパーを初期化
    scraper = RakutenAuctionScraper()
    
    # 更新された馬のデータを格納するリスト
    updated_horses = []
    
    # 各馬のデータを更新
    for i, horse in enumerate(horses, 1):
        print(f"\n[{i}/{len(horses)}] 処理中...")
        updated_horse = update_horse_data(scraper, horse)
        if updated_horse:
            updated_horses.append(updated_horse)
        
        # 10頭ごとに進捗を表示
        if i % 10 == 0:
            print(f"\n=== 進捗: {i}/{len(horses)} 頭を処理しました ===")
    
    # 更新されたデータを保存
    if save_updated_data(updated_horses):
        print("\n=== スクリプトが正常に完了しました ===")
        print(f"合計 {len(updated_horses)} 頭のデータを更新しました")
    else:
        print("\n=== エラーが発生しました ===")

if __name__ == "__main__":
    main()
