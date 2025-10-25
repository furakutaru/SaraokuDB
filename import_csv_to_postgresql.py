import csv
import psycopg2
from psycopg2 import sql
from datetime import datetime

def import_csv_to_postgres(csv_file, table_name, db_url):
    # PostgreSQLに接続
    conn = psycopg2.connect(db_url)
    cursor = conn.cursor()
    
    # 既存のデータを削除（必要に応じてコメントアウト）
    cursor.execute(sql.SQL("TRUNCATE TABLE {} CASCADE").format(sql.Identifier(table_name)))
    
    # CSVファイルを開く
    with open(csv_file, 'r', encoding='utf-8-sig') as f:
        reader = csv.DictReader(f)
        columns = reader.fieldnames
        
        # 各レコードを挿入
        for row in reader:
            # 空の値をNoneに変換
            for key in row:
                if row[key] == '':
                    row[key] = None
            
            # カラム名と値を準備
            columns_sql = sql.SQL(',').join(map(sql.Identifier, columns))
            values_sql = sql.SQL(',').join([sql.Placeholder()] * len(columns))
            
            # SQLクエリを作成
            query = sql.SQL("INSERT INTO {} ({}) VALUES ({})").format(
                sql.Identifier(table_name),
                columns_sql,
                values_sql
            )
            
            # 値を取得（辞書の順序を保持）
            values = [row[col] for col in columns]
            
            try:
                cursor.execute(query, values)
            except Exception as e:
                print(f"Error inserting row: {row}")
                print(f"Error: {e}")
                conn.rollback()
                raise
    
    # 変更をコミット
    conn.commit()
    
    # インポートしたレコード数を取得
    cursor.execute(sql.SQL("SELECT COUNT(*) FROM {}").format(sql.Identifier(table_name)))
    count = cursor.fetchone()[0]
    
    # 接続を閉じる
    cursor.close()
    conn.close()
    
    return count

if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Import CSV data to PostgreSQL')
    parser.add_argument('csv_file', help='Path to the CSV file')
    parser.add_argument('--table', default='horses', help='Target table name (default: horses)')
    parser.add_argument('--db-url', required=True, help='PostgreSQL connection URL')
    
    args = parser.parse_args()
    
    try:
        count = import_csv_to_postgres(args.csv_file, args.table, args.db_url)
        print(f"Successfully imported {count} rows to {args.table} table.")
    except Exception as e:
        print(f"Error: {e}")
        exit(1)
