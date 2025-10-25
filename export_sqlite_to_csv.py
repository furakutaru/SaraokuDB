import sqlite3
import csv
import sys

def export_table_to_csv(db_path, table_name, output_file):
    # SQLiteに接続
    conn = sqlite3.connect(db_path)
    conn.text_factory = str  # テキストデータをそのまま取得する
    cursor = conn.cursor()
    
    # テーブルのカラム名を取得
    cursor.execute(f"PRAGMA table_info({table_name})")
    columns = [column[1] for column in cursor.fetchall()]
    
    # データを取得
    cursor.execute(f"SELECT * FROM {table_name}")
    rows = cursor.fetchall()
    
    # CSVに書き出し
    with open(output_file, 'w', newline='', encoding='utf-8-sig') as f:
        writer = csv.writer(f)
        writer.writerow(columns)  # ヘッダーを書き込み
        writer.writerows(rows)    # データを書き込み
    
    print(f"Exported {len(rows)} rows from {table_name} to {output_file}")

if __name__ == "__main__":
    if len(sys.argv) != 4:
        print("Usage: python export_sqlite_to_csv.py <sqlite_db_path> <table_name> <output_csv>")
        sys.exit(1)
    
    db_path = sys.argv[1]
    table_name = sys.argv[2]
    output_file = sys.argv[3]
    
    export_table_to_csv(db_path, table_name, output_file)
