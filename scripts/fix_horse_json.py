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
    parser.add_argument('--normalize-sold-price', action='store_true', help='sold_priceが1000未満なら×10000して円単位に統一')
    parser.add_argument('--normalize-prize', action='store_true', help='history配列のtotal_prize_start, total_prize_latestも1000未満なら×10000して円単位に統一')
    parser.add_argument('--denormalize-prize', action='store_true', help='history配列のtotal_prize_start, total_prize_latestが10000以上なら/10000して万円単位に戻す')
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
        # sold_price正規化
        if args.normalize_sold_price:
            # 馬本体
            if 'sold_price' in horse and isinstance(horse['sold_price'], (int, float)) and 0 < horse['sold_price'] < 1000:
                horse['sold_price'] = int(horse['sold_price'] * 10000)
            # history配列
            if 'history' in horse and isinstance(horse['history'], list):
                for h in horse['history']:
                    sp = h.get('sold_price')
                    if isinstance(sp, (int, float)) and 0 < sp < 1000:
                        h['sold_price'] = int(sp * 10000)
        # 賞金正規化
        if args.normalize_prize:
            if 'history' in horse and isinstance(horse['history'], list):
                for h in horse['history']:
                    for k in ['total_prize_start', 'total_prize_latest']:
                        val = h.get(k)
                        if isinstance(val, (int, float)) and 0 < val < 1000:
                            h[k] = int(val * 10000)
        # 賞金を万円単位に戻す
        if args.denormalize_prize:
            if 'history' in horse and isinstance(horse['history'], list):
                for h in horse['history']:
                    for k in ['total_prize_start', 'total_prize_latest']:
                        val = h.get(k)
                        if isinstance(val, (int, float)) and val >= 10000:
                            h[k] = round(val / 10000, 1)
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