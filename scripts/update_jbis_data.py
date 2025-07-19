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

# 楽天スクレイパーをインポート
try:
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
except ImportError:
    # フォールバック: 直接インポート
    import importlib.util
    rakuten_scraper_path = os.path.join(project_root, 'backend/scrapers/rakuten_scraper.py')
    spec = importlib.util.spec_from_file_location('rakuten_scraper', rakuten_scraper_path)
    if spec is None or spec.loader is None:
        raise ImportError('rakuten_scraper.pyのロードに失敗しました')
    rakuten_scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rakuten_scraper)
    RakutenAuctionScraper = rakuten_scraper.RakutenAuctionScraper

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
                prize_match = re.search(r'総獲得賞金\s*([\d,]+\.?\d*)万?円', page_text)
                if prize_match:
                    prize_str = prize_match.group(1).replace(',', '')
                    try:
                        horse['total_prize_latest'] = float(prize_str)
                    except Exception:
                        horse['total_prize_latest'] = None
                else:
                    horse['total_prize_latest'] = None
            except Exception as e:
                horse['total_prize_latest'] = None
        else:
            horse['total_prize_latest'] = None
        
        # サーバーに負荷をかけないよう少し待機
        time.sleep(1)
    
    # 更新されたJSONを保存
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"✅ JBISデータで更新完了: {json_path}")

if __name__ == "__main__":
    main() 