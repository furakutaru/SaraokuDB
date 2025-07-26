#!/usr/bin/env python3
"""
既存データのコメントを更新するスクリプト
修正されたコメント取得ロジックを使用して、全馬のコメントを再取得・更新
"""

import json
import os
import sys
import requests
from bs4 import BeautifulSoup
import time
from typing import Dict, List

# スクレイパーのパスを追加
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'backend', 'scrapers'))
from rakuten_scraper import RakutenAuctionScraper

def update_comments():
    """既存データのコメントを更新"""
    # プロジェクトルートからの絶対パスを使用
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    history_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
    
    print(f"=== コメントデータ更新開始 ===")
    print(f"対象ファイル: {history_file}")
    
    # 既存データを読み込み
    try:
        with open(history_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
    except FileNotFoundError:
        print(f"エラー: ファイルが見つかりません: {history_file}")
        return False
    except json.JSONDecodeError as e:
        print(f"エラー: JSONの読み込みに失敗しました: {e}")
        return False
    
    horses = data.get('horses', [])
    print(f"総馬数: {len(horses)}頭")
    
    # スクレイパーインスタンスを作成
    scraper = RakutenAuctionScraper()
    
    # 各馬のコメントデータを更新
    updated_count = 0
    failed_count = 0
    already_has_comment_count = 0
    
    for i, horse in enumerate(horses):
        horse_name = horse.get('name', 'Unknown')
        detail_url = horse.get('detail_url')
        
        print(f"\n{i+1}/{len(horses)}. {horse_name}:")
        
        if not detail_url:
            print("   ❌ detail_urlが存在しません")
            failed_count += 1
            continue
        
        # 履歴内の全てのエントリでコメントを確認・更新
        history = horse.get('history', [])
        entry_updated = False
        
        for j, entry in enumerate(history):
            current_comment = entry.get('comment', '')
            
            # 既にコメントがある場合はスキップ（必要に応じて強制更新も可能）
            if current_comment and len(current_comment.strip()) > 10:
                if not entry_updated:
                    print(f"   ✅ 既にコメントが存在します（{len(current_comment)}文字）")
                    already_has_comment_count += 1
                    entry_updated = True
                continue
            
            try:
                # ページを取得してコメントを抽出
                headers = {
                    'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
                }
                response = requests.get(detail_url, headers=headers, timeout=10)
                response.raise_for_status()
                
                soup = BeautifulSoup(response.content, 'html.parser')
                extracted_comment = scraper._extract_comment(soup)
                
                if extracted_comment and len(extracted_comment.strip()) > 0:
                    entry['comment'] = extracted_comment
                    if not entry_updated:
                        print(f"   ✅ コメント更新成功（{len(extracted_comment)}文字）")
                        updated_count += 1
                        entry_updated = True
                else:
                    if not entry_updated:
                        print("   ❌ コメントが抽出できませんでした")
                        failed_count += 1
                        entry_updated = True
                
                # レート制限のため少し待機
                time.sleep(1)
                
            except Exception as e:
                if not entry_updated:
                    print(f"   ❌ エラー: {e}")
                    failed_count += 1
                    entry_updated = True
    
    print(f"\n=== 更新結果 ===")
    print(f"コメント更新成功: {updated_count}頭")
    print(f"既にコメント有り: {already_has_comment_count}頭")
    print(f"更新失敗: {failed_count}頭")
    
    # 更新したデータを保存
    if updated_count > 0:
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ データファイルを更新しました: {history_file}")
            return True
        except Exception as e:
            print(f"❌ ファイルの保存に失敗しました: {e}")
            return False
    else:
        print("\n✅ 更新の必要がありませんでした")
        return True

if __name__ == "__main__":
    success = update_comments()
    if success:
        print("\n🎉 コメントデータの更新が完了しました！")
    else:
        print("\n❌ コメントデータの更新に失敗しました")
