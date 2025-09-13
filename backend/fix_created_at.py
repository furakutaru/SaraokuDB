import sqlite3
from datetime import datetime

def fix_created_at():
    # データベースに接続
    conn = sqlite3.connect('data/horses.db')
    cursor = conn.cursor()
    
    try:
        # 問題のあるレコードを取得
        cursor.execute("SELECT id, created_at FROM horses WHERE created_at LIKE '%.%'")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} records with problematic created_at format")
        
        for row_id, date_str in rows:
            try:
                # 日付をパースして正規化
                if date_str and isinstance(date_str, str):
                    # ミリ秒を含むISO形式の日付をパース
                    dt = datetime.fromisoformat(date_str.replace('Z', '+00:00'))
                    # SQLiteのdatetime形式に変換
                    formatted_date = dt.strftime('%Y-%m-%d %H:%M:%S')
                    # データベースを更新
                    cursor.execute(
                        "UPDATE horses SET created_at = ? WHERE id = ?",
                        (formatted_date, row_id)
                    )
                    print(f"Fixed record {row_id}: {date_str} -> {formatted_date}")
                
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
    fix_created_at()
