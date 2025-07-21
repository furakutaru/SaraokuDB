import json
import argparse
import os
import requests
from bs4 import BeautifulSoup
import re

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

def fix_prize_values(horses):
    """賞金が異常値（10000万円以上など）の場合、1000で割って修正する"""
    fixed_count = 0
    for horse in horses:
        for key in ['total_prize_start', 'total_prize_latest']:
            val = horse.get(key)
            if isinstance(val, (int, float)) and val is not None and val >= 10000:
                horse[key] = round(val / 1000, 1)
                fixed_count += 1
        # history配列も修正
        if 'history' in horse and isinstance(horse['history'], list):
            for h in horse['history']:
                for key in ['total_prize_start', 'total_prize_latest']:
                    val = h.get(key)
                    if isinstance(val, (int, float)) and val is not None and val >= 10000:
                        h[key] = round(val / 1000, 1)
                        fixed_count += 1
    return fixed_count

def fix_name_values(horses):
    """
    馬名から「（インボイス登録あり）」などの注釈を除去する
    """
    fixed_count = 0
    pattern = re.compile(r'（インボイス登録あり）')
    for horse in horses:
        if 'name' in horse and horse['name']:
            new_name = pattern.sub('', horse['name']).strip()
            if new_name != horse['name']:
                horse['name'] = new_name
                fixed_count += 1
        # history配列も修正
        if 'history' in horse and isinstance(horse['history'], list):
            for h in horse['history']:
                if 'name' in h and h['name']:
                    new_name = pattern.sub('', h['name']).strip()
                    if new_name != h['name']:
                        h['name'] = new_name
                        fixed_count += 1
    return fixed_count

def main():
    parser = argparse.ArgumentParser(description='馬データ部分修正スクリプト')
    parser.add_argument('--file', required=True, help='修正対象のJSONファイルパス')
    parser.add_argument('--id', type=int, help='修正対象の馬ID（省略時は全馬）')
    parser.add_argument('--set', nargs='+', help='修正内容（例: sex=セン unsold_count=1 sold_price=0）')
    parser.add_argument('--history', action='store_true', help='history配列の全要素も修正する場合に指定')
    parser.add_argument('--both', action='store_true', help='history配列と馬本体の両方を同時に修正')
    parser.add_argument('--truncate-history', action='store_true', help='history配列を先頭1件だけにする')
    parser.add_argument('--clean-disease-tags', action='store_true', help='disease_tagsから「なし」と疾病が両方入っている場合に「なし」を除去')
    parser.add_argument('--refetch-prize-from-detail', action='store_true', help='detail_urlから落札時の賞金（total_prize_start）を再取得・補完')
    parser.add_argument('--fix-prize', action='store_true', help='賞金の異常値（10000万円以上）を自動修正')
    parser.add_argument('--fix-name', action='store_true', help='馬名の注釈を除去する')
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
        # disease_tagsの「なし」除去
        if args.clean_disease_tags:
            # 本体
            tags = horse.get('disease_tags')
            if isinstance(tags, str):
                tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                if 'なし' in tag_list and len(tag_list) > 1:
                    tag_list = [t for t in tag_list if t != 'なし']
                if not tag_list:
                    tag_list = ['なし']
                horse['disease_tags'] = ','.join(tag_list)
            # history配列
            if 'history' in horse and isinstance(horse['history'], list):
                for h in horse['history']:
                    tags = h.get('disease_tags')
                    if isinstance(tags, str):
                        tag_list = [t.strip() for t in tags.split(',') if t.strip()]
                        if 'なし' in tag_list and len(tag_list) > 1:
                            tag_list = [t for t in tag_list if t != 'なし']
                        if not tag_list:
                            tag_list = ['なし']
                        h['disease_tags'] = ','.join(tag_list)
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

    if args.refetch_prize_from_detail:
        for horse in horses:
            url = horse.get('detail_url') or horse.get('history', [{}])[0].get('detail_url')
            if not url:
                continue
            try:
                response = requests.get(url, timeout=30)
                response.raise_for_status()
                soup = BeautifulSoup(response.content, 'html.parser')
                page_text = soup.get_text()
                # 総賞金・中央・地方の全パターンをカバー
                total_prize_match = re.search(r'総獲得賞金[：:]*\s*([\d.]+)万?円', page_text)
                central_prize_match = re.search(r'中央獲得賞金[：:]*\s*([\d.]+)万?円', page_text)
                local_prize_match = re.search(r'地方獲得賞金[：:]*\s*([\d.]+)万?円', page_text)
                total_prize = None
                if total_prize_match:
                    try:
                        total_prize = float(total_prize_match.group(1))
                    except Exception:
                        total_prize = None
                else:
                    try:
                        central = float(central_prize_match.group(1)) if central_prize_match else 0.0
                        local = float(local_prize_match.group(1)) if local_prize_match else 0.0
                        if central or local:
                            total_prize = central + local
                        else:
                            total_prize = None
                    except Exception:
                        total_prize = None
                if total_prize is not None:
                    horse['total_prize_start'] = total_prize
            except Exception as e:
                pass

    if args.fix_prize:
        fixed = fix_prize_values(horses)
        print(f'賞金の異常値を{fixed}件修正しました')

    if args.fix_name:
        fixed = fix_name_values(horses)
        print(f'馬名の注釈を{fixed}件修正しました')

    with open(args.file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('修正を保存しました')

if __name__ == '__main__':
    main() 