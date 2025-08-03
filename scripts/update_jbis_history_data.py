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

class SimpleScraper:
    """シンプルなHTTPセッション管理クラス（RakutenAuctionScraperの代替）"""
    def __init__(self):
        import requests
        from requests.adapters import HTTPAdapter
        from urllib3.util.retry import Retry
        
        self.session = requests.Session()
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[500, 502, 503, 504],
            allowed_methods=["GET"]
        )
        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)
        
        # ヘッダー設定
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        })

# RakutenAuctionScraper の代わりに SimpleScraper を使用
RakutenAuctionScraper = SimpleScraper


def normalize_jbis_url(jbis_url: str) -> str:
    """JBIS URLを基本情報ページのURLに正規化する"""
    if not jbis_url:
        return jbis_url
    
    # /pedigree/ や /record/ を除去して基本情報ページのURLに変換
    normalized_url = jbis_url
    if '/pedigree/' in jbis_url:
        normalized_url = jbis_url.replace('/pedigree/', '/')
    elif '/record/' in jbis_url:
        normalized_url = jbis_url.replace('/record/', '/')
    
    # 末尾のスラッシュを確保
    if not normalized_url.endswith('/'):
        normalized_url += '/'
    
    return normalized_url

def get_jbis_prize(scraper_session, jbis_url: str) -> Optional[float]:
    """JBISのページから総賞金を取得する"""
    if not jbis_url or not jbis_url.startswith('http'):
        return None
    
    # URL正規化: 血統情報ページや競走成績ページを基本情報ページに変換
    normalized_url = normalize_jbis_url(jbis_url)
    if normalized_url != jbis_url:
        print(f"  - URL正規化: {jbis_url} -> {normalized_url}")

    retries = 3
    for attempt in range(retries):
        try:
            response = scraper_session.get(normalized_url, timeout=30)  # タイムアウトを30秒に延長
            response.raise_for_status()
            soup = BeautifulSoup(response.content, 'html.parser')

            # 方法1: dtタグから総賞金を取得（最も確実）
            total_prize_dt = soup.find('dt', string=re.compile(r'^\s*総賞金\s*$'))
            if total_prize_dt:
                dd = total_prize_dt.find_next_sibling('dd')
                if dd:
                    prize_text = dd.get_text(strip=True)
                    # 数値を抽出（例: "9077.9万円" -> 9077.9）
                    prize_num_match = re.search(r'([\d,]+\.?\d*)', prize_text)
                    if prize_num_match:
                        try:
                            prize_str = prize_num_match.group(1).replace(',', '')
                            prize_value = float(prize_str)
                            print(f"  - dtタグから賞金取得成功: {prize_value}万円")
                            return prize_value
                        except ValueError:
                            print(f"  - dtタグの賞金を数値変換できませんでした: {prize_text}")
            
            # 方法2: スペースを考慮した正規表現（dtタグが失敗した場合のフォールバック）
            page_text = soup.get_text()
            prize_match = re.search(r'総賞金\s*([\d,]+\.?\d*)\s*万円', page_text)
            if prize_match:
                try:
                    prize_str = prize_match.group(1).replace(',', '')
                    prize_value = float(prize_str)
                    print(f"  - 正規表現から賞金取得成功: {prize_value}万円")
                    return prize_value
                except ValueError:
                    print(f"  - 正規表現の賞金を数値変換できませんでした: {prize_match.group(1)}")
            
            print(f"  - 賞金データが見つかりませんでした")
            return None
        except requests.exceptions.RequestException as e:
            print(f"  - ページ取得エラー ({normalized_url}) - 試行 {attempt + 1}/{retries}: {e}")
            if attempt < retries - 1:
                time.sleep(3 * (attempt + 1))
                continue
            else:
                print(f"  - {retries}回のリトライに失敗しました。")
                return None
        except Exception as e:
            print(f"  - 予期せぬエラー ({normalized_url}): {e}")
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