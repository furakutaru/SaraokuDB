#!/usr/bin/env python3
"""
既存のキャッシュファイルを新しい形式に変換するスクリプト
リストページ: 20250811_124216_a1a9f3e94be92e25f864231ea320699d.html
詳細ページ: 20250812_*.html
"""
import json
import re
from pathlib import Path
from bs4 import BeautifulSoup

# 設定
OLD_CACHE_DIR = Path("html_cache")  # 古いキャッシュディレクトリ
NEW_CACHE_DIR = Path("cache")  # 新しいキャッシュディレクトリ
JSON_PATH = Path("../static-frontend/public/data/horses.json")  # 馬情報のJSONファイル

# セッションID（リストページのタイムスタンプから取得）
SESSION_ID = "20250811_124216"

def load_horses_data():
    """horses.jsonから馬のデータを読み込む"""
    try:
        with open(JSON_PATH, 'r', encoding='utf-8') as f:
            data = json.load(f)
        return {horse['name']: horse['id'] for horse in data['horses']}
    except Exception as e:
        print(f"馬データの読み込み中にエラーが発生しました: {e}")
        return {}

def extract_horse_info(html_content, file_name):
    """HTMLから馬名を抽出し、ファイル名からハッシュ値をIDとして取得"""
    try:
        # ファイル名からハッシュ値を抽出（最後の_以降の文字列）
        file_hash = file_name.split('_')[-1].replace('.html', '')
        
        # タイトルタグから馬名を抽出
        title_match = re.search(r'<title>([^<]+)', html_content)
        if title_match:
            title = title_match.group(1).strip()
            # タイトルから不要な部分を除去して馬名を取得
            horse_name = re.sub(r'\s*[|｜].*$', '', title).strip()
            horse_name = re.sub(r'[\s　]+', ' ', horse_name)  # 連続する空白を1つに
            return horse_name, file_hash
        return None, file_hash
    except Exception as e:
        print(f"馬情報の抽出中にエラーが発生しました: {e}")
        return None, file_hash

def convert_cache():
    """キャッシュを新しい形式に変換"""
    # 馬のデータを読み込み（ログ出力用）
    horses = load_horses_data()
    if not horses:
        print("警告: 馬データの読み込みに失敗しましたが、ファイル名のハッシュをIDとして処理を続行します。")
    
    # 新しいキャッシュディレクトリを作成
    session_dir = NEW_CACHE_DIR / SESSION_ID
    session_dir.mkdir(parents=True, exist_ok=True)
    
    # リストページを処理
    list_page = OLD_CACHE_DIR / "20250811_124216_a1a9f3e94be92e25f864231ea320699d.html"
    if list_page.exists():
        try:
            with open(list_page, 'r', encoding='utf-8') as f:
                content = f.read()
            new_path = session_dir / "list.html"
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[一覧] {list_page} -> {new_path}")
        except Exception as e:
            print(f"[エラー] リストページの処理中にエラーが発生しました: {e}")
    
    # 詳細ページを処理
    detail_files = list(OLD_CACHE_DIR.glob("20250812_*.html"))
    matched_count = 0
    
    for file_path in detail_files:
        try:
            # ファイルを読み込み
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # HTMLから馬名とファイル名のハッシュを取得
            horse_name, file_hash = extract_horse_info(content, file_path.name)
            
            if not horse_name:
                print(f"[警告] 馬名を抽出できませんでしたが、ハッシュ値を使用して処理を続行します: {file_path.name}")
                horse_name = "unknown"
            
            # ファイル名を安全な形式に変換
            safe_name = re.sub(r'[\\/*?:"<>|]', '_', horse_name)
            
            # ファイル名のハッシュをIDとして使用
            horse_id = file_hash
            new_name = f"{safe_name}_{horse_id}.html"
            new_path = session_dir / new_name
            
            with open(new_path, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"[詳細] {file_path.name} -> {new_path.name}")
            matched_count += 1
        
        except Exception as e:
            print(f"[エラー] {file_path.name} の処理中にエラーが発生しました: {e}")
    
    # 統計情報を表示
    print(f"\n処理完了: {len(detail_files)} 件中 {matched_count} 件の馬名をマッチングしました。")
    if matched_count < len(detail_files):
        print("注意: 一部の馬名がマッチしませんでした。horses.jsonを確認してください。")

if __name__ == "__main__":
    print(f"キャッシュの変換を開始します... (セッションID: {SESSION_ID})")
    convert_cache()
    print("\nキャッシュの変換が完了しました。")
    print(f"新しいキャッシュディレクトリ: {NEW_CACHE_DIR / SESSION_ID}")
