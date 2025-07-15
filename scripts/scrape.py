#!/usr/bin/env python3
"""
サラブレッドオークションデータスクレイピングスクリプト
GitHub Actionsで定期実行され、結果をJSONファイルに保存
"""

import json
import os
import sys
from datetime import datetime, timedelta
from typing import List, Dict, Optional
import requests
from bs4 import BeautifulSoup
import time
import random
import re
import urllib.parse
import importlib.util

# プロジェクトルートをパスに追加
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend'))
sys.path.append(os.path.join(os.path.dirname(__file__), '../backend/scrapers'))
rakuten_scraper_path = os.path.join(os.path.dirname(__file__), '../backend/scrapers/rakuten_scraper.py')
spec = importlib.util.spec_from_file_location('rakuten_scraper', rakuten_scraper_path)
if spec is None or spec.loader is None:
    raise ImportError('rakuten_scraper.pyのロードに失敗しました')
rakuten_scraper = importlib.util.module_from_spec(spec)
spec.loader.exec_module(rakuten_scraper)
RakutenAuctionScraper = rakuten_scraper.RakutenAuctionScraper


def main():
    print("楽天オークション スクレイピング開始...")
    scraper = RakutenAuctionScraper()
    horses = scraper.scrape_all_horses()
    if not horses:
        print("取得した馬データがありません。")
        return
    # id付与・血統分割・dam_sire追加
    for idx, horse in enumerate(horses, 1):
        horse['id'] = idx
        # 血統分割
        sire = horse.get('sire', '')
        dam = ''
        dam_sire = ''
        import re
        dam_match = re.search(r'母：([^　]+)', sire)
        if dam_match:
            dam = dam_match.group(1)
        dam_sire_match = re.search(r'母の父：([^　]+)', sire)
        if dam_sire_match:
            dam_sire = dam_sire_match.group(1)
        sire_main = sire.split('　母：')[0] if '　母：' in sire else sire
        horse['sire'] = sire_main
        horse['dam'] = dam
        horse['dam_sire'] = dam_sire
        if 'comment' not in horse or horse['comment'] is None:
            horse['comment'] = ''
        # === 賞金・価格を万円単位・小数1桁に正規化 ===
        for key in ['sold_price', 'total_prize_start', 'total_prize_latest']:
            val = horse.get(key, 0)
            try:
                if isinstance(val, (int, float)) and val > 0:
                    horse[key] = round(val / 10000, 1)
                else:
                    horse[key] = 0.0
            except Exception:
                horse[key] = 0.0
    # バリデーション
    for horse in horses:
        for key in ['sold_price', 'total_prize_start', 'total_prize_latest']:
            if key in horse and (horse[key] is None or horse[key] == '' or not isinstance(horse[key], (int, float))):
                horse[key] = 0.0
    # メタデータ
    from datetime import datetime
    total_horses = len(horses)
    avg_price = sum(h.get('sold_price', 0) for h in horses) / total_horses if total_horses > 0 else 0
    data = {
        "metadata": {
            "last_updated": datetime.now().isoformat(),
            "total_horses": total_horses,
            "average_price": int(avg_price),
        },
        "horses": horses
    }
    output_dir = "static-frontend/public/data"
    os.makedirs(output_dir, exist_ok=True)
    output_file = os.path.join(output_dir, "horses.json")
    with open(output_file, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"データを {output_file} に保存しました。")

if __name__ == "__main__":
    main() 