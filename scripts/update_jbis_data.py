#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import re
from bs4 import BeautifulSoup

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))
sys.path.append(os.path.join(project_root, 'backend/scrapers'))

from backend.scrapers.rakuten_scraper import RakutenAuctionScraper

def main():
    print("=== JBISデータ更新スクリプト ===")
    
    # 既存のJSONを読み込み
    json_path = "static-frontend/public/data/horses.json"
    if not os.path.exists(json_path):
        print(f"❌ JSONファイルが見つかりません: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print(f"✅ {len(data['horses'])}頭の馬データを読み込みました")
    
    # JBISから現在の賞金情報を取得
    scraper = RakutenAuctionScraper()
    
    for i, horse in enumerate(data['horses'], 1):
        print(f"  {i}/{len(data['horses'])}: {horse['name']} - JBIS賞金取得中...")
        
        if horse.get('jbis_url'):
            try:
                response = scraper.session.get(horse['jbis_url'], timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.get_text()
                
                # 総賞金を抽出
                prize_match = re.search(r'総賞金\s*([\d,]+\.?\d*)万円', page_text)
                if prize_match:
                    prize_str = prize_match.group(1).replace(',', '')
                    total_prize_latest = float(prize_str)
                    print(f"    ✅ 総賞金パターンで取得: {total_prize_latest}万円")
                    
                    # オークション時と現在の賞金を比較
                    start_prize = horse.get('total_prize_start', 0)
                    if start_prize > 0 and total_prize_latest == 0:
                        # オークション時は賞金があるが、現在は0 → オークション時の値を採用
                        horse['total_prize_latest'] = start_prize
                        horse['prize_diff'] = '0万円'
                        print(f"    ✅ オークション時の賞金を採用: {start_prize}万円")
                    elif start_prize == 0 and total_prize_latest > 0:
                        # オークション時は0だが、現在は賞金がある → 現在の値を採用
                        horse['total_prize_start'] = total_prize_latest
                        horse['total_prize_latest'] = total_prize_latest
                        horse['prize_diff'] = '0万円'
                        print(f"    ✅ 現在の賞金を採用: {total_prize_latest}万円")
                    else:
                        # 通常の差額計算
                        horse['total_prize_latest'] = total_prize_latest
                        diff = round(total_prize_latest - start_prize, 1)
                        sign = '+' if diff >= 0 else ''
                        horse['prize_diff'] = f'{sign}{diff}万円'
                        print(f"    ✅ 差額計算: {horse['prize_diff']}")
                else:
                    horse['prize_diff'] = '-'
                    print(f"    ❌ 賞金情報を取得できませんでした")
            except Exception as e:
                horse['prize_diff'] = '-'
                print(f"    ❌ エラー: {e}")
        else:
            horse['prize_diff'] = '-'
            print(f"    ❌ JBIS URLがありません")
        
        # サーバーに負荷をかけないよう少し待機
        time.sleep(1)
    
    # 更新されたJSONを保存
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JBISデータで更新完了: {json_path}")

if __name__ == "__main__":
    main() 