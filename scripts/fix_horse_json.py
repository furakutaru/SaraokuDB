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
    parser.add_argument('--id', type=int, required=True, help='修正対象の馬ID')
    parser.add_argument('--set', nargs='+', required=True, help='修正内容（例: sex=セン unsold_count=1 sold_price=0）')
    parser.add_argument('--history', action='store_true', help='history配列の全要素も修正する場合に指定')
    parser.add_argument('--both', action='store_true', help='history配列と馬本体の両方を同時に修正')
    args = parser.parse_args()

    if not os.path.exists(args.file):
        print(f'ファイルが見つかりません: {args.file}')
        return

    with open(args.file, encoding='utf-8') as f:
        data = json.load(f)

    found = False
    for horse in data['horses']:
        if horse['id'] == args.id:
            found = True
            for k, v in parse_set_args(args.set).items():
                # --both: history配列と馬本体両方
                if args.both and 'history' in horse:
                    for hist in horse['history']:
                        hist[k] = v
                    # 馬本体にも
                    if k in horse:
                        if isinstance(horse[k], int):
                            horse[k] = int(v)
                        elif isinstance(horse[k], float):
                            horse[k] = float(v)
                        else:
                            horse[k] = v
                    else:
                        horse[k] = v
                # --historyのみ
                elif args.history and 'history' in horse:
                    for hist in horse['history']:
                        if k in hist:
                            hist[k] = v
                # 馬本体のみ
                elif k in horse:
                    if isinstance(horse[k], int):
                        horse[k] = int(v)
                    elif isinstance(horse[k], float):
                        horse[k] = float(v)
                    else:
                        horse[k] = v
            break
    if not found:
        print(f'ID={args.id} の馬が見つかりません')
        return

    with open(args.file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f'ID={args.id} の馬データを修正しました')

if __name__ == '__main__':
    main() 