import json
import argparse
import os

# 使い方例:
# python3 fix_horse_json.py --file static-frontend/public/data/horses_history.json --id 3 --set sex=セン --set unsold_count=1 --set sold_price=0

def parse_set_args(set_args):
    result = {}
    for s in set_args:
        if '=' not in s:
            continue
        k, v = s.split('=', 1)
        result[k] = v
    return result

def main():
    parser = argparse.ArgumentParser(description='馬データ部分修正スクリプト')
    parser.add_argument('--file', required=True, help='修正対象のJSONファイルパス')
    parser.add_argument('--id', type=int, help='修正対象の馬ID（省略時は全馬）')
    parser.add_argument('--set', nargs='+', help='修正内容（例: sex=セン unsold_count=1 sold_price=0）')
    parser.add_argument('--history', action='store_true', help='history配列の全要素も修正する場合に指定')
    parser.add_argument('--both', action='store_true', help='history配列と馬本体の両方を同時に修正')
    parser.add_argument('--truncate-history', action='store_true', help='history配列を先頭1件だけにする')
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
        # history配列を1件だけにする
        if args.truncate_history and 'history' in horse and isinstance(horse['history'], list) and len(horse['history']) > 1:
            horse['history'] = [horse['history'][0]]
        # 既存の部分修正ロジック ...
        if args.set:
            set_dict = parse_set_args(args.set)
            if args.both:
                for k, v in set_dict.items():
                    horse[k] = v
                    if 'history' in horse and isinstance(horse['history'], list):
                        for h in horse['history']:
                            h[k] = v
            elif args.history:
                if 'history' in horse and isinstance(horse['history'], list):
                    for h in horse['history']:
                        for k, v in set_dict.items():
                            h[k] = v
            else:
                for k, v in set_dict.items():
                    horse[k] = v

    with open(args.file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

if __name__ == '__main__':
    main() 