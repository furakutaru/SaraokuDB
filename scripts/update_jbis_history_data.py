#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import time
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import Optional
import requests

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
if project_root not in sys.path:
    sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))

try:
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
except ImportError:
    # --- フォールバック ---
    # backend/scrapers/rakuten_scraper.py を動的に読み込む
    try:
        from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
    except ImportError:
        # フォールバック: 直接インポート
        import importlib.util
        scraper_path = os.path.join(project_root, 'backend', 'scrapers', 'rakuten_scraper.py')
        spec = importlib.util.spec_from_file_location("rakuten_scraper", scraper_path)
        if spec and spec.loader:
            rakuten_scraper = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(rakuten_scraper)
            RakutenAuctionScraper = rakuten_scraper.RakutenAuctionScraper
        else:
            print("❌ rakuten_scraper.pyのロードに失敗しました。")
            sys.exit(1)


def get_jbis_prize(scraper_session, jbis_url: str) -> Optional[float]:
    """JBISのページから総賞金を取得する"""
    if not jbis_url or not jbis_url.startswith('http'):
        return None

    retries = 3
    for attempt in range(retries):
        try:
            response = scraper_session.get(jbis_url, timeout=30)  # タイムアウトを30秒に延長
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 「総賞金」のdtタグを見つける
            total_prize_dt = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
            if total_prize_dt:
                # dtの次のddタグが賞金額
                dd = total_prize_dt.find_next_sibling('dd')
                if dd:
                    prize_text = dd.get_text(strip=True).replace(',', '').replace('万円', '')
                    try:
                        return float(prize_text)
                    except ValueError:
                        print(f"  - 賞金額を数値に変換できませんでした: {prize_text}")
                        return None
            return None
        except requests.exceptions.RequestException as e:
            print(f"  - ページ取得エラー ({jbis_url}) - 試行 {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            else:
                print(f"  - {retries}回のリトライに失敗しました。")
                return None
        except Exception as e:
            print(f"  - 予期せぬエラー ({jbis_url}): {e}")
            return None
    return None

def get_horse_name(horse_data):
    """馬データから名前を取得する。トップレベル、もしくは履歴から取得"""
    if horse_data.get('name'):
        return horse_data.get('name')
    if horse_data.get('history'):
        if horse_data['history']:
            return horse_data['history'][0].get('name')
    return '名前不明'


def main():
    print("=== JBISデータ更新スクリプト (履歴ファイル版) ===")
    
    json_path = "static-frontend/public/data/horses_history.json"
    if not os.path.exists(json_path):
        print(f"❌ JSONファイルが見つかりません: {json_path}")
        return
    
    with open(json_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    horses = data.get('horses', [])
    print(f"✅ {len(horses)}頭の馬データを読み込みました")
    
    scraper = RakutenAuctionScraper()
    updated_count = 0
    
    for i, horse in enumerate(horses, 1):
        jbis_url = horse.get('jbis_url')
        horse_name = get_horse_name(horse)
        print(f"  {i}/{len(horses)}: {horse_name} - JBIS賞金取得中...")
        
        if not jbis_url:
            print("  - JBIS URLがありません。スキップします。")
            continue

        prize = get_jbis_prize(scraper.session, jbis_url)
        
        if prize is not None:
            # 賞金が更新されていればフラグを立てる
            if horse.get('total_prize_latest') != prize:
                 horse['total_prize_latest'] = prize
                 horse['updated_at'] = datetime.now().isoformat()
                 updated_count += 1
                 print(f"    -> 賞金を {prize} 万円に更新しました。")
        else:
            print("  - 賞金を取得できませんでした。")

        # サーバー負荷軽減
        time.sleep(1.5)

    if updated_count > 0:
        # 更新されたJSONを保存
        data['metadata']['last_updated'] = datetime.now().isoformat()
        with open(json_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"\n✅ {updated_count}頭のJBISデータを更新しました: {json_path}")
    else:
        print("\n✅ 更新が必要な馬はいませんでした。")


if __name__ == '__main__':
    main() 