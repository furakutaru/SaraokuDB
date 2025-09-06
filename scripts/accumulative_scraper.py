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
import argparse
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
    from improved_scraper import ImprovedRakutenScraper
except ImportError as e:
    print(f"Error importing ImprovedRakutenScraper: {e}")
    # 絶対パスでのインポートを試みる
    try:
        from scripts.improved_scraper import ImprovedRakutenScraper
    except ImportError as e2:
        print(f"Error importing with absolute path: {e2}")
        raise


import logging

class AccumulativeScraper:
    def __init__(self, enable_history=None, mode='development'):
        # ロガーの初期化
        self.logger = logging.getLogger('AccumulativeScraper')
        self.logger.setLevel(logging.INFO)
        
        # コンソールハンドラを追加（まだ存在しなければ）
        if not self.logger.handlers:
            ch = logging.StreamHandler()
            ch.setLevel(logging.INFO)
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            ch.setFormatter(formatter)
            self.logger.addHandler(ch)
        
        # テストモードの設定（development/testモードの場合はTrue、productionモードの場合はFalse）
        test_mode = mode in ['development', 'dev', 'test']
        
        # スクレイパーを初期化
        if mode == 'test':
            from improved_scraper import TestConfig
            config = TestConfig(use_cache=test_mode)
        else:
            from improved_scraper import ScraperConfig
            config = ScraperConfig(use_cache=test_mode, max_workers=1)
            
        self.scraper = ImprovedRakutenScraper(config=config)
        
        # プロジェクトルートからの絶対パスを使用
        script_dir = os.path.dirname(os.path.abspath(__file__))
        project_root = os.path.dirname(script_dir)
        self.history_file = os.path.join(project_root, "static-frontend", "public", "data", "horses_history.json")
        
        # 履歴管理の制御設定
        self.mode = mode
        if enable_history is not None:
            self.enable_history = enable_history
        else:
            # 環境変数またはモードで制御
            env_history = os.getenv('ENABLE_HISTORY_TRACKING', '').lower()
            if env_history in ['true', '1', 'yes']:
                self.enable_history = True
            elif env_history in ['false', '0', 'no']:
                self.enable_history = False
            else:
                # モードベースの制御
                self.enable_history = mode in ['production', 'prod']
        
        print(f"履歴追加モード: {'有効' if self.enable_history else '無効'} (mode: {mode})")
        
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
        """履歴エントリを作成
        
        Args:
            horse_data: 馬のデータを含む辞書
            auction_date: オークション日（YYYY-MM-DD形式）
            
        Returns:
            新しい履歴エントリを含む辞書
        """
        # 血統情報を統一（damsire と dam_sire の両方に同じ値を設定）
        damsire = horse_data.get('damsire') or horse_data.get('dam_sire', '')
        
        # 必須フィールドのデフォルト値を設定
        default_values = {
            # 基本情報
            'name': horse_data.get('name', ''),
            'sex': horse_data.get('sex', ''),
            'age': horse_data.get('age', 0),
            'seller': horse_data.get('seller', ''),
            'auction_date': auction_date,
            
            # 血統情報
            'sire': horse_data.get('sire', ''),
            'dam': horse_data.get('dam', ''),
            'damsire': damsire,
            'dam_sire': damsire,  # 後方互換性のため
            
            # オークション情報
            'sold_price': horse_data.get('sold_price'),
            'start_price': horse_data.get('start_price'),
            'bid_num': horse_data.get('bid_num', 0),
            'unsold': horse_data.get('unsold', False),
            
            # その他の情報
            'comment': horse_data.get('comment', ''),
            'disease_tags': horse_data.get('disease_tags', []),
            'weight': horse_data.get('weight'),
            'race_record': horse_data.get('race_record', {}),
            'total_prize_start': horse_data.get('total_prize_start', 0),
            'total_prize_latest': horse_data.get('total_prize_latest', 0),
            
            # URL情報
            'jbis_url': horse_data.get('jbis_url', ''),
            'netkeiba_url': horse_data.get('netkeiba_url', ''),  # オプショナル
            'detail_url': horse_data.get('detail_url', ''),
            'primary_image': horse_data.get('primary_image', '')
        }
        
        # オークション日を設定
        default_values['auction_date'] = auction_date
        
        # デバッグ用に作成したエントリを表示
        print(f"履歴エントリ作成: {default_values['name'] or 'Unknown'} - {auction_date}")
        print(f"  性別: {default_values['sex']}, 年齢: {default_values['age']}, 販売者: {default_values['seller']}")
        print(f"  馬体重: {default_values['weight']}kg, 賞金: {default_values['total_prize_latest']}万円, コメント長: {len(default_values['comment'])}文字")
        print(f"  病気タグ: {default_values['disease_tags']}")
        
        return default_values
    
    def merge_horse_data(self, existing_horse: Dict, new_horse: Dict, auction_date: str) -> Dict:
        """既存馬データに新しい履歴を追加
        
        Args:
            existing_horse: 既存の馬データ
            new_horse: 新しい馬データ
            auction_date: オークション日（YYYY-MM-DD形式）
            
        Returns:
            更新された馬データ
        """
        # 必須フィールドのリストを定義（優先度順）
        required_fields = [
            'sex', 'age', 'seller', 'sire', 'dam', 'damsire', 'dam_sire', 
            'jbis_url', 'auction_date', 'name', 'comment', 'disease_tags'
        ]
        
        # 既存の履歴を取得
        history = existing_horse.get('history', [])
        
        # 新しい履歴エントリを作成
        new_history_entry = self.create_history_entry(new_horse, auction_date)
        
        # 履歴に追加（重複チェック付き）
        history_dates = {h.get('auction_date') for h in history}
        if auction_date not in history_dates and self.enable_history:
            history.append(new_history_entry)
            print(f"✅ 履歴を追加: {existing_horse.get('name', 'Unknown')} - {auction_date}")
        else:
            print(f"⚠️ 履歴追加スキップ: {existing_horse.get('name', 'Unknown')} - {auction_date} (テストモード)")

        # 血統情報を統一（damsire と dam_sire の両方に同じ値を設定）
        damsire = (
            new_horse.get('damsire') or 
            new_horse.get('dam_sire') or 
            existing_horse.get('damsire') or 
            existing_horse.get('dam_sire', '') or
            '不明'  # デフォルト値
        )
        
        # フィールド更新の優先順位を定義
        def get_priority_value(field, default=''):
            # 新しいデータを優先、なければ既存のデータ、それもなければデフォルト値
            return (
                new_horse.get(field) 
                if field in new_horse and new_horse[field] not in (None, '')
                else existing_horse.get(field, default)
            )
        
        # 必須フィールドの値を確実に設定
        def get_required_field(field):
            # 1. 新しいデータから取得を試みる
            value = new_horse.get(field)
            if value not in (None, ''):
                return value
                
            # 2. 既存のデータから取得を試みる
            value = existing_horse.get(field)
            if value not in (None, ''):
                return value
                
            # 3. 履歴から最新の有効な値を探す
            for h in reversed(history):
                hist_value = h.get(field)
                if hist_value not in (None, ''):
                    return hist_value
            
            # 4. デフォルト値を返す
            if field == 'age':
                return 0
            elif field == 'auction_date':
                return auction_date
            elif field in ['sire', 'dam', 'damsire', 'dam_sire']:
                return '不明'
            elif field == 'disease_tags':
                return []
            elif field == 'race_record':
                return {}
            return ''
        
        # 更新するフィールドを定義
        update_fields = {
            # 基本情報
            'name': get_priority_value('name', '不明'),
            'sex': get_required_field('sex'),
            'age': get_required_field('age'),
            'seller': get_required_field('seller'),
            'auction_date': get_required_field('auction_date'),
            
            # 血統情報
            'sire': get_required_field('sire'),
            'dam': get_required_field('dam'),
            'damsire': damsire if damsire != '不明' else get_required_field('damsire'),
            'dam_sire': damsire if damsire != '不明' else get_required_field('damsire'),  # 後方互換性のため
            
            # URL情報
            'jbis_url': get_required_field('jbis_url'),
            'netkeiba_url': get_priority_value('netkeiba_url'),  # オプショナル
            'detail_url': get_priority_value('detail_url', existing_horse.get('detail_url', '')),
            
            # その他の情報
            'comment': get_priority_value('comment', ''),
            'disease_tags': get_priority_value('disease_tags', []),
            'primary_image': get_priority_value('primary_image', ''),
            'total_prize_latest': get_priority_value('total_prize_latest', 0),
            'weight': get_priority_value('weight'),
            'race_record': get_priority_value('race_record', {}),
            'updated_at': datetime.now().isoformat(),
            'history': history
        }
        
        # 最新の体重をトップレベルに反映
        latest_weight = self._get_latest_weight(history)
        if latest_weight is not None:
            update_fields['weight'] = latest_weight
        
        # 必須フィールドの検証とデバッグ情報
        missing_fields = []
        for field in required_fields:
            value = update_fields.get(field)
            if value in (None, '', 0) and field != 'age':  # age=0は有効
                missing_fields.append(field)
                # デバッグ情報を出力
                print(f"⚠️ 必須フィールドが不足: {field}")
                print(f"  - 新しいデータ: {new_horse.get(field)}")
                print(f"  - 既存データ: {existing_horse.get(field)}")
                print(f"  - 履歴: {[h.get(field) for h in history if h.get(field) not in (None, '')]}")
        
        if missing_fields:
            print(f"⚠️ 必須フィールドが不足しています: {', '.join(missing_fields)}")
            print(f"  デフォルト値を設定します")
            
            # 不足フィールドにデフォルト値を設定
            for field in missing_fields:
                if field == 'age':
                    update_fields[field] = 0
                elif field == 'auction_date':
                    update_fields[field] = auction_date
                elif field in ['sire', 'dam', 'damsire', 'dam_sire']:
                    update_fields[field] = '不明'
                elif field == 'disease_tags':
                    update_fields[field] = []
                elif field == 'race_record':
                    update_fields[field] = {}
                else:
                    update_fields[field] = ''
        
        # 既存の馬データを更新
        existing_horse.update(update_fields)
        
        # デバッグ用に更新されたフィールドを表示
        print(f"\n=== 馬データ更新 (ID: {existing_horse.get('id')}) ===")
        print(f"馬名: {existing_horse.get('name')}")
        print(f"性別: {existing_horse.get('sex')}, 年齢: {existing_horse.get('age')}, 販売者: {existing_horse.get('seller')}")
        print(f"血統: {existing_horse.get('sire')} - {existing_horse.get('dam')} (母父: {existing_horse.get('damsire')})")
        print(f"JBIS URL: {existing_horse.get('jbis_url')}")
        print(f"オークション日: {existing_horse.get('auction_date')}")
        print(f"馬体重: {existing_horse.get('weight', 'N/A')}kg, 賞金: {existing_horse.get('total_prize_latest', 0)}万円")
        print(f"コメント: {len(existing_horse.get('comment', ''))}文字, 病気タグ: {existing_horse.get('disease_tags', [])}")
        print(f"画像: {'あり' if existing_horse.get('primary_image') else 'なし'}")
        print(f"履歴エントリ: {len(existing_horse.get('history', []))}件")
        print("=" * 50)
        
        return existing_horse
    
    def clear_history_data(self, backup=True) -> bool:
        """履歴データをクリアし、必要に応じてバックアップを作成"""
        try:
            if not os.path.exists(self.history_file):
                print("✅ 履歴ファイルが存在しません")
                return True
            
            # バックアップ作成
            if backup:
                backup_file = f"{self.history_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(self.history_file, backup_file)
                print(f"💾 バックアップ作成: {backup_file}")
            
            # 新しい空のデータ構造を作成
            empty_data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": 0,
                    "average_price": 0
                },
                "horses": []
            }
            
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(empty_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 履歴データをクリアしました: {self.history_file}")
            return True
            
        except Exception as e:
            print(f"❌ 履歴データのクリアに失敗: {e}")
            return False
    
    def restore_from_backup(self, backup_file: str) -> bool:
        """バックアップからデータを復元"""
        try:
            if not os.path.exists(backup_file):
                print(f"❌ バックアップファイルが存在しません: {backup_file}")
                return False
            
            import shutil
            shutil.copy2(backup_file, self.history_file)
            print(f"✅ バックアップから復元しました: {backup_file} -> {self.history_file}")
            return True
            
        except Exception as e:
            print(f"❌ バックアップからの復元に失敗: {e}")
            return False
    
    def reset_history_count(self, backup=True, keep_latest_only=True, reset_mode='keep_latest', target_date=None) -> bool:
        """
        履歴カウントをリセットし、指定された条件に応じて履歴を管理
        
        Args:
            backup (bool): バックアップを作成するか
            keep_latest_only (bool): 最新履歴のみを保持するか（後方互換性のため保持）
            reset_mode (str): リセットモード
                - 'keep_latest': 最新履歴のみ保持（デフォルト）
                - 'remove_latest': 最新履歴のみ削除
                - 'keep_oldest': 最古履歴のみ保持
                - 'remove_oldest': 最古履歴のみ削除
                - 'keep_by_date': 指定日付の履歴のみ保持
                - 'remove_by_date': 指定日付の履歴のみ削除
            target_date (str): 日付指定モード用の対象日付（YYYY-MM-DD形式）
        """
        try:
            if not os.path.exists(self.history_file):
                print("❌ 履歴ファイルが存在しません")
                return False
            
            # バックアップ作成
            if backup:
                backup_file = f"{self.history_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
                import shutil
                shutil.copy2(self.history_file, backup_file)
                print(f"💾 バックアップ作成: {backup_file}")
            
            # 既存データを読み込み
            existing_data = self.load_existing_data()
            existing_horses = existing_data.get('horses', [])
            
            if not existing_horses:
                print("❌ 履歴データが空です")
                return False
            
            # 後方互換性のためのkeep_latest_onlyをreset_modeに変換
            if keep_latest_only and reset_mode == 'keep_latest':
                reset_mode = 'keep_latest'
            elif not keep_latest_only and reset_mode == 'keep_latest':
                reset_mode = 'keep_all'  # 全履歴保持
            
            reset_count = 0
            total_history_before = 0
            total_history_after = 0
            
            print(f"🔄 履歴カウントリセットを開始: {len(existing_horses)}頭の馬を処理")
            print(f"🔧 リセットモード: {reset_mode}")
            if target_date:
                print(f"📅 対象日付: {target_date}")
            
            for horse in existing_horses:
                history = horse.get('history', [])
                total_history_before += len(history)
                original_count = len(history)
                
                if len(history) <= 1:
                    # 履歴が1件以下の場合は処理しない
                    total_history_after += len(history)
                    continue
                
                new_history = self._filter_history_by_mode(history, reset_mode, target_date)
                
                if len(new_history) != original_count:
                    horse['history'] = new_history
                    reset_count += 1
                    total_history_after += len(new_history)
                    print(f"  ✅ {horse.get('name', 'Unknown')}: {original_count}件 -> {len(new_history)}件")
                else:
                    total_history_after += len(history)
            
            # メタデータを更新
            updated_data = {
                "metadata": {
                    "last_updated": datetime.now().isoformat(),
                    "total_horses": len(existing_horses),
                    "average_price": existing_data.get('metadata', {}).get('average_price', 0),
                    "auction_date": datetime.now().strftime('%Y-%m-%d'),
                    "history_reset": True,
                    "reset_date": datetime.now().isoformat(),
                    "horses_reset": reset_count,
                    "total_history_before": total_history_before,
                    "total_history_after": total_history_after
                },
                "horses": existing_horses
            }
            
            # ファイルに保存
            with open(self.history_file, 'w', encoding='utf-8') as f:
                json.dump(updated_data, f, ensure_ascii=False, indent=2)
            
            print(f"✅ 履歴カウントリセットが完了しました")
            print(f"  リセット対象: {reset_count}頭")
            print(f"  履歴数: {total_history_before}件 -> {total_history_after}件")
            print(f"  保存先: {self.history_file}")
            
            return True
            
        except Exception as e:
            print(f"❌ 履歴カウントリセットに失敗: {e}")
            return False
    
    def _filter_history_by_mode(self, history: List[Dict], reset_mode: str, target_date: str = None) -> List[Dict]:
        """
        指定されたモードに応じて履歴をフィルタリング
        
        Args:
            history (List[Dict]): 元の履歴リスト
            reset_mode (str): リセットモード
            target_date (str): 日付指定モード用の対象日付
            
        Returns:
            List[Dict]: フィルタリング後の履歴リスト
        """
        if not history:
            return history
        
        # 日付でソートした履歴を作成
        sorted_history = sorted(history, key=lambda x: x.get('auction_date', ''))
        
        if reset_mode == 'keep_latest':
            # 最新の履歴のみ保持
            return [sorted_history[-1]] if sorted_history else []
        
        elif reset_mode == 'remove_latest':
            # 最新の履歴のみ削除
            return sorted_history[:-1] if len(sorted_history) > 1 else []
        
        elif reset_mode == 'keep_oldest':
            # 最古の履歴のみ保持
            return [sorted_history[0]] if sorted_history else []
        
        elif reset_mode == 'remove_oldest':
            # 最古の履歴のみ削除
            return sorted_history[1:] if len(sorted_history) > 1 else []
        
        elif reset_mode == 'keep_by_date':
            # 指定日付の履歴のみ保持
            if not target_date:
                print(f"⚠️  日付指定モードですが対象日付が指定されていません")
                return history
            return [h for h in history if h.get('auction_date') == target_date]
        
        elif reset_mode == 'remove_by_date':
            # 指定日付の履歴のみ削除
            if not target_date:
                print(f"⚠️  日付指定モードですが対象日付が指定されていません")
                return history
            return [h for h in history if h.get('auction_date') != target_date]
        
        elif reset_mode == 'keep_all':
            # 全履歴保持（リセットしない）
            return history
        
        else:
            print(f"⚠️  不明なリセットモード: {reset_mode}")
            return history
    
    def _get_latest_weight(self, history: List[Dict]) -> Optional[int]:
        """履歴から最新の体重を取得"""
        if not history:
            return None
        
        # 履歴を日付順でソート（最新が最後）
        sorted_history = sorted(history, key=lambda x: x.get('auction_date', ''))
        
        # 最新の履歴から体重を取得
        for entry in reversed(sorted_history):
            weight = entry.get('weight')
            if weight is not None:
                return weight
        
        return None
    
    def create_new_horse_entry(self, horse_data: Dict, auction_date: str, horse_id: int) -> Dict:
        """新しい馬エントリを作成
        
        Args:
            horse_data: 馬のデータを含む辞書
            auction_date: オークション日（YYYY-MM-DD形式）
            horse_id: 馬の一意のID
            
        Returns:
            新しい馬エントリを含む辞書
        """
        # 血統情報を統一（damsire と dam_sire の両方に同じ値を設定）
        damsire = horse_data.get('damsire') or horse_data.get('dam_sire', '')
        
        # 新しい馬エントリの基本情報
        new_entry = {
            # 必須フィールド
            'id': horse_id,
            'name': horse_data.get('name', ''),
            'sex': horse_data.get('sex', ''),
            'age': horse_data.get('age', 0),
            'seller': horse_data.get('seller', ''),
            'sire': horse_data.get('sire', ''),
            'dam': horse_data.get('dam', ''),
            'damsire': damsire,
            'dam_sire': damsire,  # 後方互換性のため
            'jbis_url': horse_data.get('jbis_url', ''),
            'auction_date': horse_data.get('auction_date', auction_date),
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
            'history': [],
            
            # オプションフィールド
            'netkeiba_url': horse_data.get('netkeiba_url', ''),  # オプショナル
            'detail_url': horse_data.get('detail_url', ''),
            'comment': horse_data.get('comment', ''),
            'disease_tags': horse_data.get('disease_tags', []),
            'primary_image': horse_data.get('primary_image', ''),
            'total_prize_latest': horse_data.get('total_prize_latest', 0),
            'weight': horse_data.get('weight'),
            'race_record': horse_data.get('race_record', {})
        }
        
        # 履歴エントリを作成（必須フィールドが確実に含まれるように）
        history_entry = self.create_history_entry(new_entry, new_entry['auction_date'])
        new_entry['history'].append(history_entry)
        
        # デバッグ用に作成したエントリを表示
        print(f"\n=== 新規馬エントリ作成 (ID: {horse_id}) ===")
        print(f"馬名: {new_entry['name']}")
        print(f"性別: {new_entry['sex']}, 年齢: {new_entry['age']}, 販売者: {new_entry['seller']}")
        print(f"父: {new_entry['sire']}, 母: {new_entry['dam']}, 母父: {new_entry['damsire']}")
        print(f"JBIS URL: {new_entry['jbis_url']}")
        print(f"オークション日: {new_entry['auction_date']}")
        print(f"馬体重: {new_entry.get('weight', 'N/A')}kg")
        print(f"総賞金: {new_entry.get('total_prize_latest', 0)}万円")
        print(f"コメント長: {len(new_entry.get('comment', ''))}文字")
        print(f"病気タグ: {new_entry.get('disease_tags', [])}")
        print("=" * 50)
        print(f"JBIS URL: {new_entry['jbis_url']}")
        print(f"Netkeiba URL: {new_entry['netkeiba_url']}")
        print(f"オークション日: {new_entry['auction_date']}")
        print(f"馬体重: {new_entry.get('weight')}kg, 賞金: {new_entry['total_prize_latest']}万円")
        print(f"コメント長: {len(new_entry['comment'])}文字, 病気タグ: {new_entry['disease_tags']}")
        
        return new_entry
    
    def save_data(self, data, filepath=None):
        """データをJSONファイルに保存する
        
        Args:
            data: 保存するデータ
            filepath: 保存先ファイルパス（省略時はデフォルトパス）
        """
        if filepath is None:
            filepath = os.path.join('static-frontend', 'public', 'data', 'horses.json')
            
        # ディレクトリが存在しない場合は作成
        os.makedirs(os.path.dirname(filepath), exist_ok=True)
        
        try:
            with open(filepath, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.logger.info(f"データを保存しました: {filepath}")
            return True
        except Exception as e:
            self.logger.error(f"データの保存中にエラーが発生しました: {str(e)}")
            return False
            
    def scrape_and_accumulate(self) -> bool:
        """スクレイピング実行＋データ積み上げ
        
        Returns:
            bool: スクレイピングとデータの保存が成功したかどうか
        """
        print("=== 積み上げ型スクレイピング開始 ===")
        
        # 既存データを読み込み
        existing_data = self.load_existing_data()
        existing_horses = existing_data.get('horses', [])
        
        print(f"既存馬データ: {len(existing_horses)}頭")
        
        # 新しいデータをスクレイピング
        # スクレイピング実行
        try:
            # スクレイピングを実行
            if hasattr(self.scraper, 'scrape_all_horses'):
                # RakutenAuctionScraper の場合
                new_horses = self.scraper.scrape_all_horses()
            else:
                # ImprovedRakutenScraper の場合
                new_horses = self.scraper.scrape_horse_list(use_cache=True)
            if not new_horses:
                print("スクレイピング結果が空です")
                return False
            
            print(f"新規取得: {len(new_horses)}頭")
            
            # オークション日を現在の日付で設定
            from datetime import datetime
            auction_date = datetime.now().strftime('%Y-%m-%d')
            print(f"オークション日: {auction_date}")
            
            # データ統合処理
            added_count = 0
            updated_count = 0
            # 既存のIDを数値として抽出
            existing_ids = []
            for h in existing_horses:
                try:
                    existing_ids.append(int(h.get('id', 0)))
                except (ValueError, TypeError):
                    pass
            # 次のIDを数値として計算
            next_id = (max(existing_ids, default=0) + 1) if existing_ids else 1
            
            # デバッグ用に新しい馬データを表示
            print("\n=== 新規取得データのサマリー ===")
            for i, horse in enumerate(new_horses, 1):
                print(f"{i}. {horse.get('name')} - 性別: {horse.get('sex')}, 年齢: {horse.get('age')}, 販売者: {horse.get('seller')}")
                print(f"   父: {horse.get('sire')}, 母: {horse.get('dam')}, 母父: {horse.get('damsire') or horse.get('dam_sire')}")
            
            print("\n=== データ統合処理を開始します ===")
            
            for new_horse in new_horses:
                # 既存の馬を検索
                existing_horse = next(
                    (h for h in existing_horses 
                     if h['name'] == new_horse['name'] and 
                        h.get('age') == new_horse.get('age')),
                    None
                )
                
                if existing_horse:
                    # 既存の馬情報を更新
                    existing_horse.update(new_horse)
                    updated_count += 1
                # 新しい馬の場合はIDを割り当て
                if not existing_horse:
                    new_horse['id'] = str(next_id)
                    next_id += 1
                    existing_horses.append(new_horse)
                    added_count += 1
            
            # データを保存
            self.save_data(existing_horses)
            
            print(f"\n=== スクレイピング完了 ===")
            print(f"追加: {added_count}頭, 更新: {updated_count}頭")
            
            return True
            
        except Exception as e:
            self.logger.error(f"スクレイピング中にエラーが発生しました: {str(e)}")
            import traceback
            self.logger.error(traceback.format_exc())
            return False
            # 必須フィールドのデフォルト値を設定
            default_values = {
                'comment': '',
                'disease_tags': [],
                'total_prize_latest': 0,
                'primary_image': '',
                'race_record': {}
            }
            
            # デフォルト値で上書き（既存の値があればそれを使用）
            for key, default in default_values.items():
                if key not in new_horse:
                    new_horse[key] = default
            
            # 同一馬を検索
            match_idx, existing_horse = self.find_matching_horse(new_horse, existing_horses)
            
            if existing_horse is not None:
                # 既存馬の履歴を更新
                print(f"\n=== 既存馬の履歴を更新: {new_horse.get('name')} (ID: {existing_horse.get('id')}) ===")
                updated_horse = self.merge_horse_data(existing_horse, new_horse, auction_date)
                existing_horses[match_idx] = updated_horse
                updated_count += 1
            else:
                # 新しい馬として追加
                print(f"\n=== 新規馬を追加: {new_horse.get('name')} (ID: {next_id}) ===")
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
        print(f"保存先ディレクトリ作成: {os.path.dirname(self.history_file)}")
        os.makedirs(os.path.dirname(self.history_file), exist_ok=True)
        print(f"ファイル保存開始: {self.history_file}")
        print(f"保存データサイズ: 馬数={len(existing_horses)}, メタデータ={updated_data['metadata']}")
        
        with open(self.history_file, 'w', encoding='utf-8') as f:
            json.dump(updated_data, f, ensure_ascii=False, indent=2)
        
        print(f"ファイル保存完了: {self.history_file}")
        
        # 保存確認
        if os.path.exists(self.history_file):
            file_size = os.path.getsize(self.history_file)
            print(f"保存確認OK: ファイルサイズ={file_size}バイト")
        else:
            print(f"[エラー] ファイル保存に失敗: {self.history_file}")
        
        print(f"=== 積み上げ完了 ===")
        print(f"新規追加: {added_count}頭")
        print(f"履歴更新: {updated_count}頭")
        print(f"総馬数: {total_horses}頭")
        print(f"保存先: {self.history_file}")
        
        return True


def main():
    """メイン実行関数"""
    parser = argparse.ArgumentParser(
        description='積み上げ型スクレイピングスクリプト',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用例:
  # 本番モード（履歴追加有効）
  python3 accumulative_scraper.py --mode production
  
  # テストモード（履歴追加無効）
  python3 accumulative_scraper.py --mode test
  
  # 環境変数で制御
  ENABLE_HISTORY_TRACKING=true python3 accumulative_scraper.py
  
  # データクリア（バックアップ付き）
  python3 accumulative_scraper.py --clear-data
  
  # バックアップから復元
  python3 accumulative_scraper.py --restore backup_file.json
  
  # 履歴リセット例:
  # 最新履歴のみ保持（デフォルト）
  python3 accumulative_scraper.py --reset-history
  
  # 最新履歴のみ削除（古いデータのみ保持）
  python3 accumulative_scraper.py --reset-history --reset-mode remove_latest
  
  # 最古履歴のみ保持
  python3 accumulative_scraper.py --reset-history --reset-mode keep_oldest
  
  # 最古履歴のみ削除
  python3 accumulative_scraper.py --reset-history --reset-mode remove_oldest
  
  # 特定日付の履歴のみ保持
  python3 accumulative_scraper.py --reset-history --reset-mode keep_by_date --target-date 2025-07-25
  
  # 特定日付の履歴のみ削除
  python3 accumulative_scraper.py --reset-history --reset-mode remove_by_date --target-date 2025-07-25
        """
    )
    
    parser.add_argument(
        '--mode', 
        choices=['production', 'prod', 'development', 'dev', 'test'],
        default='development',
        help='実行モード (production: 履歴追加有効, test/development: 履歴追加無効)'
    )
    
    parser.add_argument(
        '--enable-history',
        action='store_true',
        help='履歴追加を強制的に有効化'
    )
    
    parser.add_argument(
        '--disable-history',
        action='store_true', 
        help='履歴追加を強制的に無効化'
    )
    
    parser.add_argument(
        '--clear-data',
        action='store_true',
        help='履歴データをクリア（バックアップ作成）'
    )
    
    parser.add_argument(
        '--restore',
        metavar='BACKUP_FILE',
        help='バックアップファイルからデータを復元'
    )
    
    parser.add_argument(
        '--no-backup',
        action='store_true',
        help='データクリア時にバックアップを作成しない'
    )
    
    parser.add_argument(
        '--reset-history',
        action='store_true',
        help='履歴カウントをリセット（最新履歴のみ保持）'
    )
    
    parser.add_argument(
        '--keep-all-history',
        action='store_true',
        help='履歴リセット時に全履歴を保持（カウントのみリセット）'
    )
    
    parser.add_argument(
        '--reset-mode',
        choices=['keep_latest', 'remove_latest', 'keep_oldest', 'remove_oldest', 'keep_by_date', 'remove_by_date'],
        default='keep_latest',
        help='履歴リセットモードを指定'
    )
    
    parser.add_argument(
        '--target-date',
        metavar='YYYY-MM-DD',
        help='日付指定モード用の対象日付（keep_by_date/remove_by_dateで使用）'
    )
    
    args = parser.parse_args()
    
    # 履歴追加の制御設定
    enable_history = None
    if args.enable_history:
        enable_history = True
    elif args.disable_history:
        enable_history = False
    
    # スクレイパーインスタンスを作成
    scraper = AccumulativeScraper(enable_history=enable_history, mode=args.mode)
    
    # データクリア処理
    if args.clear_data:
        print("🗑️  履歴データのクリアを実行中...")
        success = scraper.clear_history_data(backup=not args.no_backup)
        if success:
            print("✅ 履歴データのクリアが完了しました")
        else:
            print("❌ 履歴データのクリアに失敗しました")
            sys.exit(1)
        return
    
    # バックアップ復元処理
    if args.restore:
        print(f"💾 バックアップからの復元を実行中: {args.restore}")
        success = scraper.restore_from_backup(args.restore)
        if success:
            print("✅ バックアップからの復元が完了しました")
        else:
            print("❌ バックアップからの復元に失敗しました")
            sys.exit(1)
        return
    
    # 履歴カウントリセット処理
    if args.reset_history:
        print("🔄 履歴カウントリセットを実行中...")
        
        # リセットモードの決定
        reset_mode = args.reset_mode
        if args.keep_all_history:
            reset_mode = 'keep_all'
        
        # 日付指定モードのバリデーション
        if reset_mode in ['keep_by_date', 'remove_by_date'] and not args.target_date:
            print("❌ 日付指定モードでは --target-date オプションが必要です")
            sys.exit(1)
        
        # 日付形式のバリデーション
        if args.target_date:
            import re
            if not re.match(r'\d{4}-\d{2}-\d{2}', args.target_date):
                print("❌ 日付は YYYY-MM-DD 形式で指定してください")
                sys.exit(1)
        
        # 後方互換性のためのkeep_latest_onlyを設定
        keep_latest_only = (reset_mode == 'keep_latest')
        
        success = scraper.reset_history_count(
            backup=not args.no_backup, 
            keep_latest_only=keep_latest_only,
            reset_mode=reset_mode,
            target_date=args.target_date
        )
        
        if success:
            mode_descriptions = {
                'keep_latest': '最新履歴のみ保持',
                'remove_latest': '最新履歴のみ削除',
                'keep_oldest': '最古履歴のみ保持',
                'remove_oldest': '最古履歴のみ削除',
                'keep_by_date': f'{args.target_date}の履歴のみ保持',
                'remove_by_date': f'{args.target_date}の履歴のみ削除',
                'keep_all': '全履歴保持'
            }
            description = mode_descriptions.get(reset_mode, reset_mode)
            print(f"✅ 履歴カウントリセット（{description}）が完了しました")
        else:
            print("❌ 履歴カウントリセットに失敗しました")
            sys.exit(1)
        return
    
    # 通常のスクレイピング処理
    success = scraper.scrape_and_accumulate()
    
    if success:
        print("✅ スクレイピング＋積み上げが正常に完了しました")
    else:
        print("❌ スクレイピングに失敗しました")
        sys.exit(1)


if __name__ == "__main__":
    main()
