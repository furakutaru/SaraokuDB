#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import os
import re
from pathlib import Path
from typing import List, Dict, Set, Tuple

def load_latest_horses(json_path: str, count: int = 5) -> List[Dict]:
    """horses.jsonから最新の馬情報を取得する"""
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 馬情報を取得（IDでソートして最新のものを取得）
    horses = sorted(
        data['horses'],
        key=lambda x: x.get('id', ''),
        reverse=True
    )
    
    return horses[:count]

def search_horse_in_html(html_content: str, horse_names: List[str]) -> List[str]:
    """HTMLコンテンツ内で馬名を検索する"""
    found_horses = []
    
    # 馬名をエスケープして正規表現パターンを作成
    for name in horse_names:
        # 特殊文字をエスケープ
        escaped_name = re.escape(name)
        # 馬名の前後に余分な文字が入らないようにする
        pattern = f'(?:^|[^\w・]){escaped_name}(?:$|[^\w・])'
        if re.search(pattern, html_content):
            found_horses.append(name)
    
    return found_horses

def find_horse_list_pages(cache_dir: str, horse_names: List[str]) -> Dict[str, List[str]]:
    """キャッシュディレクトリ内で馬名リストを含むHTMLファイルを検索"""
    result = {}
    
    for root, _, files in os.walk(cache_dir):
        for file in files:
            if not file.endswith('.html'):
                continue
                
            file_path = os.path.join(root, file)
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                
                # 馬名を検索
                found_horses = search_horse_in_html(content, horse_names)
                
                if found_horses:
                    # 相対パスで表示
                    rel_path = os.path.relpath(file_path, start=os.path.dirname(cache_dir))
                    result[rel_path] = found_horses
                    
            except Exception as e:
                print(f"エラー: {file_path} の処理中にエラーが発生しました: {e}")
    
    return result

def main():
    # パスの設定
    base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    json_path = os.path.join(base_dir, 'static-frontend', 'public', 'data', 'horses.json')
    cache_dir = os.path.join(base_dir, 'html_cache')
    
    # 最新の5頭の馬名を取得
    latest_horses = load_latest_horses(json_path, 5)
    horse_names = [horse['name'] for horse in latest_horses]
    
    print(f"検索対象の馬名: {', '.join(horse_names)}\n")
    
    # キャッシュディレクトリ内で馬名リストを含むHTMLファイルを検索
    result = find_horse_list_pages(cache_dir, horse_names)
    
    # 結果を表示
    if not result:
        print("該当するファイルは見つかりませんでした。")
    else:
        print("以下のファイルに馬名が含まれています:\n")
        for file_path, found_horses in result.items():
            print(f"ファイル: {file_path}")
            print(f"含まれる馬名: {', '.join(found_horses)}")
            print("-" * 80)

if __name__ == "__main__":
    main()
