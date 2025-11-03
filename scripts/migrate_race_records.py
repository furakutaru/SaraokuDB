#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from datetime import datetime
from typing import Dict, Any, Optional, List

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# データベース接続の設定
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker
from dotenv import load_dotenv

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('migrate_race_records.log')
    ]
)
logger = logging.getLogger(__name__)

# 環境変数の読み込み
env_path = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'backend', '.env')
if os.path.exists(env_path):
    load_dotenv(env_path, override=True)

# データベース接続URLの取得
DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    raise ValueError("DATABASE_URL が環境変数に設定されていません")

# データベースエンジンの作成
engine = create_engine(DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

def parse_race_record(record_str: Optional[str]) -> Dict[str, Any]:
    """
    レコード文字列をパースして、新しい形式に変換する
    
    Args:
        record_str: データベースから取得したレコード文字列
        
    Returns:
        Dict[str, Any]: 新しい形式のレコード
    """
    if not record_str:
        return {
            'total_races': 0,
            'wins': 0,
            'record_format': 'simple',
            'formatted_record': '0戦0勝'
        }
    
    try:
        # 既に新しい形式の場合はそのまま返す
        record = json.loads(record_str)
        if all(key in record for key in ['total_races', 'wins', 'record_format', 'formatted_record']):
            return record
            
        # 古い形式の場合は変換を試みる
        if isinstance(record, list) and len(record) > 0:
            # 最初のレコードから必要な情報を抽出
            first_record = record[0] if isinstance(record[0], dict) else {}
            
            # コメントから戦績を抽出するロジック（必要に応じて実装）
            # ここでは単純な例を示しています
            total_races = 0
            wins = 0
            formatted_record = '0戦0勝'
            
            return {
                'total_races': total_races,
                'wins': wins,
                'record_format': 'simple',
                'formatted_record': formatted_record
            }
        
        # 不明な形式の場合はデフォルト値を返す
        return {
            'total_races': 0,
            'wins': 0,
            'record_format': 'simple',
            'formatted_record': '0戦0勝'
        }
    except json.JSONDecodeError as e:
        logger.error(f"JSONのパースに失敗しました: {e}")
        return {
            'total_races': 0,
            'wins': 0,
            'record_format': 'simple',
            'formatted_record': '0戦0勝'
        }

def migrate_race_records():
    """race_record カラムを新しい形式にマイグレーションする"""
    db = SessionLocal()
    updated_count = 0
    error_count = 0
    
    try:
        # すべての馬レコードを取得
        result = db.execute(text("SELECT id, race_record FROM horses"))
        horses = result.fetchall()
        
        logger.info(f"処理対象の馬レコード数: {len(horses)}")
        
        for horse in horses:
            horse_id, race_record_str = horse
            
            try:
                # 新しい形式に変換
                new_record = parse_race_record(race_record_str)
                
                # データベースを更新
                update_sql = text("""
                    UPDATE horses 
                    SET race_record = :race_record, 
                        updated_at = NOW()
                    WHERE id = :horse_id
                """)
                
                db.execute(
                    update_sql,
                    {
                        'race_record': json.dumps(new_record, ensure_ascii=False),
                        'horse_id': horse_id
                    }
                )
                
                updated_count += 1
                
                if updated_count % 100 == 0:
                    logger.info(f"{updated_count} 件のレコードを更新しました")
                    
            except Exception as e:
                error_count += 1
                logger.error(f"馬ID {horse_id} の更新中にエラーが発生しました: {e}")
                continue
        
        # 変更をコミット
        db.commit()
        
        logger.info(f"マイグレーションが完了しました。更新件数: {updated_count}, エラー件数: {error_count}")
        
    except Exception as e:
        db.rollback()
        logger.error(f"マイグレーション中にエラーが発生しました: {e}")
        raise
    finally:
        db.close()

if __name__ == "__main__":
    logger.info("マイグレーションを開始します...")
    migrate_race_records()
    logger.info("マイグレーションが完了しました。")
