#!/usr/bin/env python3
"""
全ての馬の next_update_due_date を初期化するスクリプト

オークション日に基づいて next_update_due_date を設定：
- オークション日が90日以上前 → next_update_due_date = NULL（即座に更新対象）
- オークション日が90日未満 → next_update_due_date = オークション日 + 90日
"""

import os
import sys
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path
from sqlalchemy import create_engine, text
from dotenv import load_dotenv

# 環境変数の読み込み
env_path = Path(__file__).parent / 'backend' / '.env'
if env_path.exists():
    load_dotenv(env_path, override=True)
else:
    load_dotenv()

DATABASE_URL = os.getenv('DATABASE_URL')
if not DATABASE_URL:
    print("ERROR: DATABASE_URL not set")
    sys.exit(1)

if DATABASE_URL.startswith('postgres') and 'sslmode=' not in DATABASE_URL:
    DATABASE_URL += "?sslmode=require"

def extract_latest_history_value(raw_value):
    """履歴カラム（JSON文字列/配列）から最新値を取得"""
    if raw_value is None:
        return None
    if isinstance(raw_value, list):
        return raw_value[-1] if raw_value else None
    if isinstance(raw_value, dict):
        return raw_value.get('auction_date') or raw_value.get('date') or raw_value.get('value')
    if isinstance(raw_value, str):
        stripped = raw_value.strip()
        if not stripped:
            return None
        if stripped.startswith('[') or stripped.startswith('{'):
            try:
                parsed = json.loads(stripped)
                if isinstance(parsed, list) and parsed:
                    return parsed[-1]
                if isinstance(parsed, dict):
                    return parsed.get('auction_date') or parsed.get('date') or parsed.get('value')
            except json.JSONDecodeError:
                return stripped
        return stripped
    return raw_value

def parse_latest_auction_date(raw_value):
    """auction_date の履歴から最新日付を datetime.date で返す"""
    latest_value = extract_latest_history_value(raw_value)
    if not latest_value:
        return None
    
    if isinstance(latest_value, dict):
        latest_value = latest_value.get('auction_date') or latest_value.get('date')
    
    if latest_value is None:
        return None
    
    latest_str = str(latest_value).strip()
    if not latest_str:
        return None
    
    for fmt in ("%Y-%m-%d", "%Y/%m/%d", "%Y.%m.%d", "%Y%m%d"):
        try:
            return datetime.strptime(latest_str[:10], fmt).date()
        except ValueError:
            continue
    return None

def main():
    engine = create_engine(DATABASE_URL)
    now_utc = datetime.now(timezone.utc)
    ninety_days_ago = now_utc.date() - timedelta(days=90)
    
    print(f"Current UTC: {now_utc}")
    print(f"90 days ago: {ninety_days_ago}")
    print()
    
    with engine.connect() as conn:
        # 全ての非引退馬を取得
        result = conn.execute(text(
            "SELECT id, name, auction_date, next_update_due_date "
            "FROM horses "
            "WHERE is_retired = false"
        ))
        
        horses = result.fetchall()
        print(f"Processing {len(horses)} non-retired horses...")
        print()
        
        updated_count = 0
        set_to_null_count = 0
        set_to_future_count = 0
        no_auction_date_count = 0
        
        for horse in horses:
            horse_id, name, auction_date_raw, current_due_date = horse
            
            # オークション日をパース
            auction_date = parse_latest_auction_date(auction_date_raw)
            
            if auction_date is None:
                # オークション日が不明な場合は NULL（即座に更新対象）
                new_due_date = None
                no_auction_date_count += 1
            elif auction_date <= ninety_days_ago:
                # 90日以上前のオークション → NULL（即座に更新対象）
                new_due_date = None
                set_to_null_count += 1
            else:
                # 90日未満 → オークション日 + 90日
                new_due_date = datetime.combine(
                    auction_date + timedelta(days=90),
                    datetime.min.time()
                ).replace(tzinfo=timezone.utc)
                set_to_future_count += 1
            
            # 更新が必要かチェック
            if current_due_date != new_due_date:
                if new_due_date is None:
                    conn.execute(
                        text("UPDATE horses SET next_update_due_date = NULL WHERE id = :id"),
                        {"id": horse_id}
                    )
                else:
                    conn.execute(
                        text("UPDATE horses SET next_update_due_date = :due_date WHERE id = :id"),
                        {"id": horse_id, "due_date": new_due_date}
                    )
                updated_count += 1
                
                if updated_count <= 10:  # 最初の10件をログ出力
                    print(f"ID {horse_id} ({name}): {auction_date} → {new_due_date}")
        
        # コミット
        conn.commit()
        
        print()
        print("=" * 60)
        print(f"Total processed: {len(horses)}")
        print(f"Updated: {updated_count}")
        print(f"  - Set to NULL (eligible now): {set_to_null_count}")
        print(f"  - Set to future date: {set_to_future_count}")
        print(f"  - No auction date (set to NULL): {no_auction_date_count}")
        print("=" * 60)
        
        # 確認クエリ
        result = conn.execute(text(
            "SELECT COUNT(*) FROM horses "
            "WHERE is_retired = false AND (next_update_due_date IS NULL OR next_update_due_date <= :now)"
        ), {"now": now_utc})
        eligible_count = result.scalar()
        
        print(f"\nHorses eligible for update now: {eligible_count}")

if __name__ == "__main__":
    main()
