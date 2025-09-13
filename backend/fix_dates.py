import sqlite3
from datetime import datetime
import json

def fix_dates():
    # データベースに接続
    conn = sqlite3.connect('data/horses.db')
    cursor = conn.cursor()
    
    try:
        # 問題のあるレコードを取得
        cursor.execute("SELECT id, auction_date FROM horses WHERE auction_date LIKE '%T%'")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} records with potential date format issues")
        
        for row_id, date_str in rows:
            try:
                # 日付をパースして正規化
                if date_str and isinstance(date_str, str):
                    # 既にリスト形式のJSON文字列か確認
                    if date_str.startswith('[') and date_str.endswith(']'):
                        try:
                            dates = json.loads(date_str)
                            # リスト内の各日付をチェック
                            fixed_dates = []
                            for d in dates:
                                if d and isinstance(d, str) and 'T' in d:
                                    dt = datetime.fromisoformat(d.replace('Z', '+00:00'))
                                    fixed_dates.append(dt.isoformat())
                                else:
                                    fixed_dates.append(d)
                            # 更新
                            cursor.execute(
                                "UPDATE horses SET auction_date = ? WHERE id = ?",
                                (json.dumps(fixed_dates), row_id)
                            )
                            print(f"Fixed record {row_id}: {date_str} -> {fixed_dates}")
                        except json.JSONDecodeError:
                            # JSONとしてパースできない場合はスキップ
                            continue
                    else:
                        # 単一の日付文字列の場合
                        dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                        cursor.execute(
                            "UPDATE horses SET auction_date = ? WHERE id = ?",
                            (dt.isoformat(), row_id)
                        )
                        print(f"Fixed record {row_id}: {date_str} -> {dt.isoformat()}")
                
                # 変更をコミット
                conn.commit()
                
            except Exception as e:
                print(f"Error processing record {row_id}: {str(e)}")
                # エラーが発生した場合はロールバック
                conn.rollback()
    
    except Exception as e:
        print(f"Error: {str(e)}")
        conn.rollback()
    
    finally:
        conn.close()

if __name__ == "__main__":
    fix_dates()
