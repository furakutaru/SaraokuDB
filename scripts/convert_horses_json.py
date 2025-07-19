import json
from collections import defaultdict

INPUT_PATH = 'static-frontend/public/data/horses.json'
OUTPUT_PATH = 'static-frontend/public/data/horses_history.json'

# 履歴化するフィールド
HISTORY_FIELDS = [
    'auction_date', 'name', 'sex', 'age', 'seller', 'race_record', 'comment', 'sold_price', 'total_prize_start'
]
# 履歴を取らず最新値だけ持つフィールド
LATEST_FIELDS = ['weight', 'total_prize_latest']

with open(INPUT_PATH, encoding='utf-8') as f:
    src = json.load(f)

horses = src['horses']

class HorseHistory(dict):
    def __init__(self):
        super().__init__()
        self['id'] = None
        self['history'] = []

horse_map = defaultdict(HorseHistory)

for h in horses:
    horse_id = h.get('id')
    if horse_map[horse_id]['id'] is None:
        horse_map[horse_id]['id'] = horse_id
        # 履歴化しないフィールドをコピー
        for k in ['sire', 'dam', 'dam_sire', 'primary_image', 'disease_tags', 'netkeiba_url', 'jbis_url']:
            if k in h:
                horse_map[horse_id][k] = h[k]
        # 履歴を取らない項目の最新値をセット
        for k in LATEST_FIELDS + ['created_at', 'updated_at']:
            if k in h:
                horse_map[horse_id][k] = h[k]
    else:
        # 既にある場合は、最新値で上書き
        for k in LATEST_FIELDS + ['created_at', 'updated_at']:
            if k in h:
                horse_map[horse_id][k] = h[k]
    # 履歴部分だけ抽出
    hist = {k: h.get(k) for k in HISTORY_FIELDS}
    horse_map[horse_id]['history'].append(hist)

# metadataはそのまま
result = {
    'metadata': src.get('metadata', {}),
    'horses': list(horse_map.values())
}

with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
    json.dump(result, f, ensure_ascii=False, indent=2)

print(f'変換完了: {OUTPUT_PATH}') 