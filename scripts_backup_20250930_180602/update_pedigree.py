#!/usr/bin/env python3
"""
既存データの血統情報を更新するスクリプト
修正された血統抽出ロジックを使用して、血統情報が欠落している馬のデータを更新
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

def update_pedigree_data():
    """既存データの血統情報を更新"""
    # プロジェクトルートからの絶対パスを使用
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(script_dir)
    history_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
    
    print(f"=== 血統情報データ更新開始 ===")
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
    
    # 血統情報が欠落している馬を特定
    missing_pedigree_horses = []
    for horse in horses:
        if not horse.get('sire') or not horse.get('dam') or not horse.get('dam_sire'):
            missing_pedigree_horses.append(horse)
    
    print(f"血統情報が欠落している馬: {len(missing_pedigree_horses)}頭")
    
    if not missing_pedigree_horses:
        print("✅ 全ての馬で血統情報が揃っています")
        return True
    
    # スクレイパーインスタンスを作成
    scraper = RakutenAuctionScraper()
    
    # 各馬の血統情報を更新
    updated_count = 0
    failed_count = 0
    
    for i, horse in enumerate(missing_pedigree_horses):
        horse_name = horse.get('name', 'Unknown')
        detail_url = horse.get('detail_url')
        
        print(f"\n{i+1}/{len(missing_pedigree_horses)}. {horse_name}:")
        print(f"   現在の血統: 父=\"{horse.get('sire', '')}\", 母=\"{horse.get('dam', '')}\", 母父=\"{horse.get('dam_sire', '')}\"")
        
        if not detail_url:
            print("   ❌ detail_urlが存在しません")
            failed_count += 1
            continue
        
        try:
            # ページを取得して血統情報を抽出
            headers = {
                'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
            }
            response = requests.get(detail_url, headers=headers, timeout=10)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.content, 'html.parser')
            pedigree_result = scraper._extract_pedigree_from_page(soup)
            
            sire = pedigree_result.get('sire', '').strip()
            dam = pedigree_result.get('dam', '').strip()
            dam_sire = pedigree_result.get('dam_sire', '').strip()
            
            if sire and dam and dam_sire:
                # 血統情報を更新
                horse['sire'] = sire
                horse['dam'] = dam
                horse['dam_sire'] = dam_sire
                
                print(f"   ✅ 血統情報更新成功")
                print(f"   新しい血統: 父=\"{sire}\", 母=\"{dam}\", 母父=\"{dam_sire}\"")
                updated_count += 1
            else:
                print(f"   ❌ 血統情報が抽出できませんでした")
                print(f"   抽出結果: 父=\"{sire}\", 母=\"{dam}\", 母父=\"{dam_sire}\"")
                failed_count += 1
            
            # レート制限のため少し待機
            time.sleep(2)
            
        except Exception as e:
            print(f"   ❌ エラー: {e}")
            failed_count += 1
    
    print(f"\n=== 更新結果 ===")
    print(f"血統情報更新成功: {updated_count}頭")
    print(f"更新失敗: {failed_count}頭")
    
    # 更新したデータを保存
    if updated_count > 0:
        try:
            with open(history_file, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            print(f"\n✅ データファイルを更新しました: {history_file}")
            
            # 更新後の統計を表示
            complete_pedigree_count = 0
            for horse in horses:
                if horse.get('sire') and horse.get('dam') and horse.get('dam_sire'):
                    complete_pedigree_count += 1
            
            print(f"完全な血統情報を持つ馬: {complete_pedigree_count}/{len(horses)}頭 ({complete_pedigree_count/len(horses)*100:.1f}%)")
            return True
        except Exception as e:
            print(f"❌ ファイルの保存に失敗しました: {e}")
            return False
    else:
        print("\n❌ 更新できた馬がありませんでした")
        return False

if __name__ == "__main__":
    success = update_pedigree_data()
    if success:
        print("\n🎉 血統情報データの更新が完了しました！")
    else:
        print("\n❌ 血統情報データの更新に失敗しました")
