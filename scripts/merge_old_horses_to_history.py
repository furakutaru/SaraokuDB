import json
from collections import defaultdict

OLD_PATH = '/tmp/horses_old.json'
HISTORY_PATH = 'static-frontend/public/data/horses_history.json'

# 履歴化するフィールド
HISTORY_FIELDS = [
    'auction_date', 'name', 'sex', 'age', 'seller', 'race_record', 'comment', 'sold_price', 'total_prize_start'
]

# 履歴を取らず最新値だけ持つフィールド
LATEST_FIELDS = ['weight', 'total_prize_latest']

# 1. 既存historyデータを読み込み
with open(HISTORY_PATH, encoding='utf-8') as f:
    history_data = json.load(f)

# 2. 過去分データを読み込み
with open(OLD_PATH, encoding='utf-8') as f:
    old_data = json.load(f)

# 3. 既存馬IDセット
existing_ids = set(h['id'] for h in history_data['horses'])

# 4. 過去分をhistory形式に変換
old_horses = old_data['horses']
converted = []
for h in old_horses:
    horse_id = h.get('id')
    # history部分
    hist = {k: h.get(k, "") for k in HISTORY_FIELDS}
    # sexが無い場合は空欄
    if 'sex' not in hist or not hist['sex']:
        hist['sex'] = h.get('sex', "")
    # 馬本体
    horse = {
        'id': horse_id,
        'history': [hist],
        'sire': h.get('sire', ''),
        'dam': h.get('dam', ''),
        'dam_sire': h.get('dam_sire', ''),
        'primary_image': h.get('primary_image', ''),
        'disease_tags': h.get('disease_tags', ''),
        'netkeiba_url': h.get('netkeiba_url', ''),
        'jbis_url': h.get('jbis_url', ''),
        'weight': h.get('weight', None),
        'unsold_count': h.get('unsold_count', None),
        'total_prize_latest': h.get('total_prize_latest', 0),
        'created_at': h.get('created_at', ''),
        'updated_at': h.get('updated_at', ''),
    }
    converted.append(horse)

# 5. 既存historyにマージ
id_to_horse = {h['id']: h for h in history_data['horses']}
for h in converted:
    if h['id'] in id_to_horse:
        # 既存馬ならhistory配列の先頭に追加。ただし内容が完全一致なら追加しない
        existing_histories = id_to_horse[h['id']]['history']
        new_hist = h['history'][0]
        if not any(all(new_hist.get(k) == eh.get(k) for k in HISTORY_FIELDS) for eh in existing_histories):
            id_to_horse[h['id']]['history'].insert(0, new_hist)
    else:
        # 新規馬なら追加
        history_data['horses'].append(h)

# 疾病タグに「鼻出血」を追加
for horse in history_data['horses']:
    if 'disease_tags' in horse and isinstance(horse['disease_tags'], str):
        tags = [t.strip() for t in horse['disease_tags'].split(',') if t.strip()]
        if '鼻出血' not in tags:
            tags.append('鼻出血')
        horse['disease_tags'] = ','.join(tags)

# 6. 保存
with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
    json.dump(history_data, f, ensure_ascii=False, indent=2)

print('過去分データをhistory形式でマージしました') 