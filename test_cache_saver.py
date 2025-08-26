"""
競馬オークションサイトからHTMLを取得してキャッシュするスクリプト
"""

import sys
import os
import json
import requests
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
sys.path.insert(0, str(Path(__file__).parent))

from scripts.core.cache.cache_saver import CacheSaver

def fetch_horse_list():
    """オークションサイトから馬の一覧を取得"""
    url = "https://auction.keiba.rakuten.co.jp/"
    print(f"オークションサイトから馬の一覧を取得中: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # 馬の一覧を取得（実際のサイト構造に合わせて調整が必要）
        horse_links = soup.select('a[href*="/item/"]')
        horse_ids = list(set(link['href'].split('/')[-1] for link in horse_links if link['href'].startswith('/item/')))
        
        print(f"馬の一覧を取得しました: {len(horse_ids)}頭")
        return horse_ids
    except Exception as e:
        print(f"馬の一覧の取得中にエラーが発生しました: {e}")
        return []

def fetch_horse_detail(horse_id):
    """馬の詳細ページを取得"""
    url = f"https://auction.keiba.rakuten.co.jp/item/{horse_id}"
    print(f"馬の詳細を取得中: {url}")
    
    try:
        response = requests.get(url)
        response.raise_for_status()
        return response.text
    except Exception as e:
        print(f"馬の詳細の取得中にエラーが発生しました (ID: {horse_id}): {e}")
        return None

def main():
    # テスト用のディレクトリを設定
    base_dir = Path("test_cache_output")
    
    # 既存のキャッシュをクリア
    if base_dir.exists():
        import shutil
        shutil.rmtree(base_dir)
    
    # キャッシュセーバーを初期化
    cache = CacheSaver(base_dir=base_dir)
    
    # トップページ（リストページ）を取得して保存
    list_url = "https://auction.keiba.rakuten.co.jp/"
    print(f"\n=== リストページの取得と保存 ===")
    print(f"リストページを取得中: {list_url}")
    
    try:
        response = requests.get(list_url)
        response.raise_for_status()
        list_html = response.text
        
        # リストページを保存
        saved_list_path = cache.save_html(list_url, list_html)
        if saved_list_path and saved_list_path.exists():
            print(f"✅ リストページを保存しました: {saved_list_path.relative_to(base_dir)}")
        else:
            print("❌ リストページの保存に失敗しました")
            return
            
        # 馬の一覧を取得
        horse_ids = fetch_horse_list()
        
        if not horse_ids:
            print("馬の一覧を取得できませんでした。スクリプトを終了します。")
            return
            
    except requests.RequestException as e:
        print(f"リストページの取得中にエラーが発生しました: {e}")
        return
    
    # 各馬の詳細ページを取得して保存
    print(f"\n=== 詳細ページの保存を開始します (全{len(horse_ids)}頭) ===")
    for i, horse_id in enumerate(horse_ids, 1):
        detail_url = f"https://auction.keiba.rakuten.co.jp/item/{horse_id}"
        detail_html = fetch_horse_detail(horse_id)
        
        if detail_html:
            saved_detail_path = cache.save_html(detail_url, detail_html)
            if saved_detail_path and saved_detail_path.exists():
                print(f"✅ 詳細ページを保存しました ({i}/{len(horse_ids)}): {saved_detail_path.name}")
                print(f"   - URL: {detail_url}")
            else:
                print(f"❌ 詳細ページの保存に失敗しました ({i}/{len(horse_ids)}): {horse_id}")
    
    # メタデータの確認
    print("\n=== メタデータの確認 ===")
    metadata_path = cache.session_dir / "metadata.json"
    if metadata_path.exists():
        with open(metadata_path, 'r', encoding='utf-8') as f:
            metadata = json.load(f)
            print(f"セッションID: {metadata.get('session_id')}")
            print(f"開始時刻: {metadata.get('start_time')}")
            print(f"保存ファイル数: {len(metadata.get('files', {}))}件")
    
    # ディレクトリ構造の確認
    print("\n=== ディレクトリ構造の確認 ===")
    print("test_cache_output/")
    for root, dirs, files in os.walk(base_dir):
        level = root.replace(str(base_dir), '').count(os.sep)
        indent = '    ' * level
        print(f"{indent}{os.path.basename(root)}/")
        subindent = '    ' * (level + 1)
        for f in files:
            print(f"{subindent}{f}")

if __name__ == "__main__":
    main()
