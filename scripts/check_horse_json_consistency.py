import json
import argparse
import os

# チェック対象フィールド
CHECK_FIELDS = [
    ('sex', '性別'),
    ('unsold_count', '主取り回数'),
    ('sold_price', '落札価格'),
]

def main():
    parser = argparse.ArgumentParser(description='馬データ整合性チェックスクリプト')
    parser.add_argument('--file', required=True, help='チェック対象のJSONファイルパス')
    parser.add_argument('--id', type=int, help='特定の馬IDのみチェック（省略時は全馬）')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f'ファイルが見つかりません: {args.file}')
        return

    with open(args.file, encoding='utf-8') as f:
        data = json.load(f)

    horses = data['horses']
    for horse in horses:
        if args.id is not None and horse['id'] != args.id:
            continue
        print(f'--- ID={horse["id"]} {horse.get("history", [{}])[0].get("name", "")} ---')
        for field, label in CHECK_FIELDS:
            # 馬本体の値
            main_val = horse.get(field, None)
            # history配列の値（全要素）
            hist_vals = [h.get(field, None) for h in horse.get('history', [])]
            # すべて一致しているか
            if len(hist_vals) == 0:
                print(f'  [!] history配列が空です')
                continue
            if all(v == main_val for v in hist_vals):
                print(f'  [OK] {label}: {main_val}')
            else:
                print(f'  [警告] {label} 不一致: 本体={main_val}, history={hist_vals}')

if __name__ == '__main__':
    main() 