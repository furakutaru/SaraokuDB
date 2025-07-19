import json
import os
import sys
from datetime import datetime
from typing import List, Dict
import importlib.util

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))
sys.path.append(os.path.join(project_root, 'backend/scrapers'))

# 楽天スクレイパーをインポート
try:
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
except ImportError:
    rakuten_scraper_path = os.path.join(project_root, 'backend/scrapers/rakuten_scraper.py')
    spec = importlib.util.spec_from_file_location('rakuten_scraper', rakuten_scraper_path)
    if spec is None or spec.loader is None:
        raise ImportError('rakuten_scraper.pyのロードに失敗しました')
    rakuten_scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rakuten_scraper)
    RakutenAuctionScraper = rakuten_scraper.RakutenAuctionScraper

INPUT_PATH = 'static-frontend/public/data/horses.json'
OUTPUT_PATH = 'static-frontend/public/data/horses.json'

with open(INPUT_PATH, encoding='utf-8') as f:
    src = json.load(f)

horses = src['horses']

scraper = RakutenAuctionScraper()
new_horses = []
for i, horse in enumerate(horses, 1):
    detail_url = horse.get('detail_url')
    if not detail_url:
        print(f"[{i}] {horse.get('name', '')}: detail_urlなし → スキップ")
        continue
    print(f"[{i}] {horse.get('name', '')}: {detail_url} から再取得")
    detail_data = scraper.scrape_horse_detail(detail_url)
    if detail_data:
        # 既存データのIDや履歴などを引き継ぐ
        merged = {**horse, **detail_data}
        merged['sex'] = detail_data['sex']  # sexは必ず詳細ページの値で上書き
        merged['id'] = horse.get('id', i)
        merged['created_at'] = horse.get('created_at', datetime.now().isoformat())
        merged['updated_at'] = datetime.now().isoformat()
        new_horses.append(merged)
    else:
        print(f"  → 詳細ページ取得失敗: {detail_url}")

# メタデータ更新
total_horses = len(new_horses)
avg_price = sum(h.get('sold_price', 0) for h in new_horses) / total_horses if total_horses > 0 else 0
data = {
    "metadata": {
        "last_updated": datetime.now().isoformat(),
        "total_horses": total_horses,
        "average_price": int(avg_price),
    },
    "horses": new_horses
}

with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
    json.dump(data, f, ensure_ascii=False, indent=2)
print(f"再取得データを {OUTPUT_PATH} に保存しました。") 