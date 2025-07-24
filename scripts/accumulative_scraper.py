#!/usr/bin/env python3
"""
積み上げ型スクレイピングスクリプト
- 既存データを保持しつつ新データを追加
- 同一馬の複数回出品に対応した履歴管理
- 詳細ページURL取得・保持
"""

import json
import os
import sys
from datetime import datetime
from typing import List, Dict, Optional, Tuple
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


class AccumulativeScraper:
    def __init__(self):
        self.scraper = RakutenAuctionScraper()
        self.history_file = "static-frontend/public/data/horses_history.json"
        
    def load_existing_data(self) -> Dict:
        """既存の履歴データを読み込み"""
        if not os.path.exists(self.history_file):
            return {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": 0,
                    "average_price": 0
                },
                "horses": []
            }
        
        try:
            with open(self.history_file, 'r', encoding='utf-8') as f:
                return json.load(f)
        except Exception as e:
            print(f"既存データの読み込みに失敗: {e}")
            return {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": 0,
                    "average_price": 0
                },
                "horses": []
            }
    
    def normalize_name(self, name: str) -> str:
        """馬名の正規化（比較用）"""
        if not name:
            return ""
        return name.strip().replace(" ", "").replace("　", "")
    
    def find_matching_horse(self, new_horse: Dict, existing_horses: List[Dict]) -> Tuple[Optional[int], Optional[Dict]]:
        """
        同一馬を検索
        判定基準: 馬名 + 血統情報（父、母、母父）
        """
        new_name = self.normalize_name(new_horse.get('name', ''))
        new_sire = self.normalize_name(new_horse.get('sire', ''))
        new_dam = self.normalize_name(new_horse.get('dam', ''))
        new_dam_sire = self.normalize_name(new_horse.get('dam_sire', ''))
        
        for idx, existing_horse in enumerate(existing_horses):
            # 馬名での一致確認
            existing_name = self.normalize_name(existing_horse.get('name', ''))
            if existing_name and new_name and existing_name == new_name:
                return idx, existing_horse
            
            # 履歴内の馬名も確認
            for history_entry in existing_horse.get('history', []):
                history_name = self.normalize_name(history_entry.get('name', ''))
                if history_name and new_name and history_name == new_name:
                    return idx, existing_horse
            
            # 血統情報での一致確認（馬名が異なる場合）
            existing_sire = self.normalize_name(existing_horse.get('sire', ''))
            existing_dam = self.normalize_name(existing_horse.get('dam', ''))
            existing_dam_sire = self.normalize_name(existing_horse.get('dam_sire', ''))
            
            if (new_sire and existing_sire and new_sire == existing_sire and
                new_dam and existing_dam and new_dam == existing_dam and
                new_dam_sire and existing_dam_sire and new_dam_sire == existing_dam_sire):
                return idx, existing_horse
        
        return None, None
    
    def create_history_entry(self, horse_data: Dict, auction_date: str) -> Dict:
        """履歴エントリを作成"""
        return {
            "auction_date": auction_date,
            "name": horse_data.get('name'),
            "sex": horse_data.get('sex'),
            "age": horse_data.get('age'),
            "seller": horse_data.get('seller'),
            "sold_price": horse_data.get('sold_price'),
            "start_price": horse_data.get('start_price'),
            "bid_num": horse_data.get('bid_num'),
            "unsold": horse_data.get('unsold', False),
            "comment": horse_data.get('comment', ''),
            "race_record": horse_data.get('race_record'),
            "total_prize_start": horse_data.get('total_prize_start'),
            "detail_url": horse_data.get('detail_url'),
            "primary_image": horse_data.get('primary_image'),
            "disease_tags": horse_data.get('disease_tags'),
            "weight": horse_data.get('weight')
        }
    
    def merge_horse_data(self, existing_horse: Dict, new_horse: Dict, auction_date: str) -> Dict:
        """既存馬データに新しい履歴を追加"""
        # 新しい履歴エントリを作成
        new_history_entry = self.create_history_entry(new_horse, auction_date)
        
        # 履歴配列に追加（重複チェック）
        if 'history' not in existing_horse:
            existing_horse['history'] = []
        
        # 同じオークション日の履歴が既に存在するかチェック
        existing_dates = [h.get('auction_date') for h in existing_horse['history']]
        if auction_date not in existing_dates:
            existing_horse['history'].append(new_history_entry)
        
        # 馬固有情報を更新（より新しい情報で上書き）
        existing_horse.update({
            'updated_at': datetime.now().isoformat(),
            'sire': new_horse.get('sire') or existing_horse.get('sire'),
            'dam': new_horse.get('dam') or existing_horse.get('dam'),
            'dam_sire': new_horse.get('dam_sire') or existing_horse.get('dam_sire'),
            'jbis_url': new_horse.get('jbis_url') or existing_horse.get('jbis_url'),
            'netkeiba_url': new_horse.get('netkeiba_url') or existing_horse.get('netkeiba_url'),
        })
        
        # 詳細ページURLを更新（新しいものがあれば）
        if new_horse.get('detail_url'):
            existing_horse['detail_url'] = new_horse.get('detail_url')
        
        return existing_horse
    
    def create_new_horse_entry(self, horse_data: Dict, auction_date: str, horse_id: int) -> Dict:
        """新しい馬エントリを作成"""
        history_entry = self.create_history_entry(horse_data, auction_date)
        
        return {
            'id': horse_id,
            'name': horse_data.get('name'),
            'sire': horse_data.get('sire'),
            'dam': horse_data.get('dam'),
            'dam_sire': horse_data.get('dam_sire'),
            'jbis_url': horse_data.get('jbis_url'),
            'netkeiba_url': horse_data.get('netkeiba_url'),
            'detail_url': horse_data.get('detail_url'),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'history': [history_entry]
        }
    
    def scrape_and_accumulate(self) -> bool:
        """スクレイピング実行＋データ積み上げ"""
        print("=== 積み上げ型スクレイピング開始 ===")
        
        # 既存データを読み込み
        existing_data = self.load_existing_data()
        existing_horses = existing_data.get('horses', [])
        
        print(f"既存馬データ: {len(existing_horses)}頭")
        
        # 新しいデータをスクレイピング
        print("新しいオークションデータを取得中...")
        new_horses = self.scraper.scrape_all_horses()
        
        if not new_horses:
            print("新しいデータが取得できませんでした")
            return False
        
        print(f"新規取得: {len(new_horses)}頭")
        
        # オークション日を取得
        auction_date = self.scraper.get_auction_date()
        
        # データ統合処理
        added_count = 0
        updated_count = 0
        next_id = max([h.get('id', 0) for h in existing_horses], default=0) + 1
        
        for new_horse in new_horses:
            # 同一馬を検索
            match_idx, existing_horse = self.find_matching_horse(new_horse, existing_horses)
            
            if existing_horse is not None:
                # 既存馬の履歴を更新
                print(f"履歴更新: {new_horse.get('name')} (ID: {existing_horse.get('id')})")
                updated_horse = self.merge_horse_data(existing_horse, new_horse, auction_date)
                existing_horses[match_idx] = updated_horse
                updated_count += 1
            else:
                # 新しい馬として追加
                print(f"新規追加: {new_horse.get('name')} (ID: {next_id})")
                new_entry = self.create_new_horse_entry(new_horse, auction_date, next_id)
                existing_horses.append(new_entry)
                next_id += 1
                added_count += 1
        
        # メタデータ更新
        total_horses = len(existing_horses)
        all_prices = []
        for horse in existing_horses:
            for history in horse.get('history', []):
                price = history.get('sold_price')
                if price and not history.get('unsold', False):
                    all_prices.append(price)
        
        avg_price = sum(all_prices) / len(all_prices) if all_prices else 0
        
        updated_data = {
            "metadata": {
                "last_updated": datetime.now().isoformat(),
                "total_horses": total_horses,
                "average_price": int(avg_price),
                "auction_date": auction_date,
                "added_horses": added_count,
                "updated_horses": updated_count
            },
            "horses": existing_horses
        }
        
        # ファイルに保存
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        print(f"=== 積み上げ完了 ===")
        print(f"新規追加: {added_count}頭")
        print(f"履歴更新: {updated_count}頭")
        print(f"総馬数: {total_horses}頭")
        print(f"保存先: {self.history_file}")
        
        return True


def main():
    """メイン実行関数"""
    scraper = AccumulativeScraper()
    success = scraper.scrape_and_accumulate()
    
    if success:
        print("スクレイピング＋積み上げが正常に完了しました")
    else:
        print("スクレイピングに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
