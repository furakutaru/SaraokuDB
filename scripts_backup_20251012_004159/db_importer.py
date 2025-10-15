#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
データベースへのインポート機能を提供するモジュール
"""
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
from datetime import datetime
from sqlalchemy.orm import Session

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class DBImporter:
    def __init__(self, db_session: Session):
        """
        データベースインポーターの初期化
        
        Args:
            db_session: SQLAlchemyのセッションオブジェクト
        """
        self.db = db_session
        from backend.database.models import Horse  # 循環インポートを避けるために関数内でインポート
        self.Horse = Horse

    def _convert_to_json_if_needed(self, value, field_name):
        """
        フィールド名に基づいて値を適切な形式に変換する
        
        Args:
            value: 変換前の値
            field_name: フィールド名
            
        Returns:
            変換後の値
        """
        if value is None:
            return None
            
        # JSON文字列として保存する必要があるフィールド
        json_fields = ['sex', 'age', 'sold_price', 'auction_date', 'seller', 'comment', 'disease_tags']
        
        if field_name in json_fields:
            if field_name == 'disease_tags' and isinstance(value, str):
                # すでにJSON文字列の場合はそのまま返す
                if value.startswith('[') and value.endswith(']'):
                    return value
                # カンマ区切りの文字列の場合はリストに変換
                return json.dumps(value.split(','), ensure_ascii=False)
            elif field_name == 'comment' and isinstance(value, str):
                # コメントはそのまま保存
                return json.dumps([value], ensure_ascii=False)
            elif field_name in ['sex', 'seller', 'comment'] and isinstance(value, str):
                # 単一の文字列を1要素の配列として保存
                return json.dumps([value], ensure_ascii=False)
            elif field_name in ['age', 'sold_price'] and isinstance(value, (int, float)):
                # 単一の数値を1要素の配列として保存
                return json.dumps([value], ensure_ascii=False)
            elif field_name == 'auction_date' and isinstance(value, str):
                # 日付文字列を1要素の配列として保存
                return json.dumps([value], ensure_ascii=False)
            elif isinstance(value, (list, dict)):
                # 既にリストまたは辞書の場合はJSON文字列に変換
                return json.dumps(value, ensure_ascii=False)
            else:
                # その他の場合はそのままJSONエンコード
                return json.dumps([str(value)], ensure_ascii=False)
        
        # 画像URLが辞書型の場合は文字列に変換
        if field_name == 'image_url' and isinstance(value, dict):
            return value.get('image_url', '')
            
        return value

    def import_horse(self, horse_data: Dict[str, Any]) -> bool:
        """
        馬データをデータベースにインポートする
        
        Args:
            horse_data: インポートする馬データの辞書
            
        Returns:
            bool: インポートが成功したかどうか
        """
        try:
            horse_id = horse_data.get('id')
            if not horse_id:
                logger.error("馬IDが存在しません")
                return False

            # データの前処理
            processed_data = {}
            for key, value in horse_data.items():
                processed_data[key] = self._convert_to_json_if_needed(value, key)

            # 必須フィールドのチェックとデフォルト値の設定
            required_fields = {
                'name': '',
                'sex': '[]',  # JSON配列として保存
                'age': '[0]',  # JSON配列として保存
                'sire': '',
                'dam': '',
                'dam_sire': '',  # データベースでは dam_sire になっている
                'race_record': '{}',  # JSONオブジェクトとして保存
                'weight': 0,
                'total_prize_start': 0.0,
                'total_prize_latest': 0.0,
                'sold_price': '[0]',  # JSON配列として保存
                'auction_date': '[]',  # JSON配列として保存
                'seller': '[]',  # JSON配列として保存
                'jbis_url': '',
                'image_url': '',
                'primary_image': '',
                'comment': '[]',  # JSON配列として保存
                'disease_tags': '[]',  # JSON配列として保存
                'unsold_count': 0,
                'auction_id': str(horse_id)
            }

            # 必須フィールドをマージ
            for field, default in required_fields.items():
                if field not in processed_data or processed_data[field] is None:
                    processed_data[field] = default
                elif field in ['sex', 'age', 'sold_price', 'auction_date', 'seller', 'comment', 'disease_tags']:
                    # JSON文字列として保存するフィールドの処理
                    if not isinstance(processed_data[field], str) or not processed_data[field].strip().startswith('['):
                        processed_data[field] = default

            # 既存の馬データを検索
            existing_horse = self.db.query(self.Horse).filter(
                self.Horse.auction_id == str(horse_id)
            ).first()

            if existing_horse:
                # 既存データを更新
                for key, value in processed_data.items():
                    if hasattr(existing_horse, key) and key != 'id' and key != 'auction_id':
                        setattr(existing_horse, key, value)
                existing_horse.updated_at = datetime.utcnow()
                logger.info(f"馬データを更新しました: {horse_id}")
            else:
                # 新しいデータを作成
                db_horse = self.Horse()
                for key, value in processed_data.items():
                    if hasattr(db_horse, key) and key != 'id':
                        setattr(db_horse, key, value)
                self.db.add(db_horse)
                logger.info(f"新しい馬データを追加しました: {horse_id}")

            self.db.commit()
            return True

        except Exception as e:
            self.db.rollback()
            logger.error(f"馬データのインポート中にエラーが発生しました (ID: {horse_id}): {e}")
            import traceback
            logger.error(traceback.format_exc())
            return False

    def import_from_json(self, json_file: Path) -> Dict[str, int]:
        """
        JSONファイルから馬データをインポートする
        
        Args:
            json_file: インポートするJSONファイルのパス
            
        Returns:
            Dict: インポート結果のサマリ
        """
        try:
            with open(json_file, 'r', encoding='utf-8') as f:
                horses_data = json.load(f)
        except Exception as e:
            logger.error(f"JSONファイルの読み込みに失敗しました: {e}")
            return {"total": 0, "success": 0, "failed": 0}

        if not isinstance(horses_data, list):
            horses_data = [horses_data]

        total = len(horses_data)
        success = 0
        failed = 0

        for horse_data in horses_data:
            if self.import_horse(horse_data):
                success += 1
            else:
                failed += 1

        logger.info(f"インポート完了: 合計 {total} 件中 {success} 件成功, {failed} 件失敗")
        return {"total": total, "success": success, "failed": failed}


def main():
    """スタンドアロンで実行するためのメイン関数"""
    import argparse
    from sqlalchemy import create_engine
    from sqlalchemy.orm import sessionmaker
    from backend.database.models import Base
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='JSONファイルからデータベースに馬データをインポートする')
    parser.add_argument('json_file', type=str, help='インポートするJSONファイルのパス')
    parser.add_argument('--db-path', type=str, default='sqlite:///backend/data/horses.db',
                      help='データベースのパス (デフォルト: sqlite:///backend/data/horses.db)')
    args = parser.parse_args()
    
    # データベース接続
    engine = create_engine(args.db_path, connect_args={"check_same_thread": False})
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    
    # テーブルが存在しない場合は作成
    Base.metadata.create_all(bind=engine)
    
    # セッションを作成
    db = SessionLocal()
    
    try:
        # インポーターを初期化
        importer = DBImporter(db)
        
        # ファイルパスをPathオブジェクトに変換
        json_file = Path(args.json_file)
        
        # インポートを実行
        result = importer.import_from_json(json_file)
        
        # 結果を表示
        print(f"\nインポート結果:")
        print(f"  合計: {result['total']}件")
        print(f"  成功: {result['success']}件")
        print(f"  失敗: {result['failed']}件")
        
        return 0 if result['failed'] == 0 else 1
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")
        return 1
    finally:
        db.close()


if __name__ == '__main__':
    import sys
    sys.exit(main())
