import sqlite3
import json

def check_dates():
    # データベースに接続
    conn = sqlite3.connect('data/horses.db')
    cursor = conn.cursor()
    
    try:
        # すべてのレコードを取得
        cursor.execute("SELECT id, name, auction_date FROM horses WHERE auction_date IS NOT NULL")
        rows = cursor.fetchall()
        
        print(f"Found {len(rows)} records with auction_date")
        
        for row_id, name, date_str in rows:
            try:
                # 日付がJSON文字列として有効か確認
                if date_str and isinstance(date_str, str):
                    try:
                        # JSONとしてパースを試みる
                        dates = json.loads(date_str)
                        if not isinstance(dates, list):
                            print(f"Record {row_id} ({name}): auction_date is not a list: {date_str}")
                            continue
                        
                        # リスト内の各日付をチェック
                        for i, d in enumerate(dates):
                            if d and isinstance(d, str) and 'T' in d:
                                print(f"Record {row_id} ({name}): Contains ISO date with 'T': {d}")
                    except json.JSONDecodeError:
                        # JSONとしてパースできない場合
                        if 'T' in date_str:
                            print(f"Record {row_id} ({name}): Invalid JSON and contains 'T': {date_str}")
                        else:
                            print(f"Record {row_id} ({name}): Invalid JSON format: {date_str}")
            
            except Exception as e:
                print(f"Error processing record {row_id}: {str(e)}")
    
    except Exception as e:
        print(f"Error: {str(e)}")
    
    finally:
        conn.close()

if __name__ == "__main__":
    check_dates()
