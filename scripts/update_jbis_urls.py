#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional, List
import requests

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)

def search_jbis_url(session, horse_name: str, sire: str, dam: str) -> Optional[str]:
    """馬名、父、母を元にJBISで検索し、最も確からしいURLを返す"""
    try:
        search_url = "https://www.jbis.or.jp/horse/list/"
        params = {"sname": horse_name}
        response = session.post(search_url, data=params, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.content, 'html.parser')
        
        results = soup.select('table.tbl-data-04 tr:not(:first-child)')
        if not results:
            return None

        # 候補の中から父・母が一致するものを探す
        best_match_url = None
        for row in results:
            cols = row.find_all('td')
            if len(cols) > 4:
                # リンクからIDを抽出し、正しいURLを組み立てる
                link = cols[0].find('a')
                if not link or 'href' not in link.attrs: continue
                
                match = re.search(r"javascript:pop_horse\('(.+?)'\);", link['href'])
                if not match: continue
                
                horse_id = match.group(1)
                candidate_url = f"https://www.jbis.or.jp/horse/{horse_id}/"
                
                row_sire = cols[3].get_text(strip=True)
                row_dam = cols[4].get_text(strip=True)
                
                if sire in row_sire and dam in row_dam:
                    best_match_url = candidate_url
                    break # 完全一致が見つかったら終了
        
        return best_match_url

    except Exception as e:
        print(f"  - JBIS検索エラー ({horse_name}): {e}")
        return None

def main():
    print("=== JBIS URL補完スクリプト ===")
    
    json_path = "static-frontend/public/data/horses_history.json"
    if not os.path.exists(json_path):
        print(f"❌ JSONファイルが見つかりません: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    horses = data.get('horses', [])
    print(f"✅ {len(horses)}頭の馬データを読み込みました")
    
    session = requests.Session()
    session.headers.update({
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
    })
    
    updated_count = 0
    
    for i, horse in enumerate(horses, 1):
        if not horse.get('jbis_url'):
            horse_name = horse.get('name', '名前不明')
            sire = horse.get('sire')
            dam = horse.get('dam')

            print(f"  {i}/{len(horses)}: {horse_name} - JBIS URLを検索中...")

            if not sire or not dam:
                 print("  - 父または母の情報が不足しているため、検索をスキップします。")
                 continue

            url = search_jbis_url(session, horse_name, sire, dam)
            
            if url:
                horse['jbis_url'] = url
                horse['updated_at'] = datetime.now().isoformat()
                updated_count += 1
                print(f"    -> URLが見つかりました: {url}")
            else:
                print("    -> URLが見つかりませんでした。")
            
            time.sleep(2) # サーバー負荷軽減

    if updated_count > 0:
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {updated_count}頭のJBIS URLを補完しました: {json_path}")
    else:
        print("\n✅ URLの補完が必要な馬はいませんでした。")

if __name__ == "__main__":
    main() 