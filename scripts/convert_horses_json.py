import json
import os
import copy
from datetime import datetime

# 入力ファイル（楽天・JBIS等の最新データ）
INPUT_PATH = 'static-frontend/public/data/horses.json'
# 履歴型・積み上げ本番データ
HISTORY_PATH = 'static-frontend/public/data/horses_history.json'

# 履歴化するフィールド
HISTORY_FIELDS = [
    'auction_date', 'name', 'sex', 'age', 'seller', 'race_record', 'comment', 'sold_price', 'total_prize_start', 'unsold'
]
# 履歴を取らず最新値だけ持つフィールド
LATEST_FIELDS = ['weight', 'total_prize_latest']

# 1. 履歴型データを読み込み（なければ空で初期化）
if os.path.exists(HISTORY_PATH):
    with open(HISTORY_PATH, encoding='utf-8') as f:
        history_data = json.load(f)
    horses_history = {int(h['id']): h for h in history_data.get('horses', [])}
else:
    horses_history = {}

# 2. 最新データ（楽天・JBIS等）を読み込み
with open(INPUT_PATH, encoding='utf-8') as f:
    new_data = json.load(f)
new_horses = new_data['horses']

# 3. 既存IDの最大値を取得
max_id = max(horses_history.keys()) if horses_history else 0

# 4. 新データをID・name・jbis_url等で突合し、履歴型で積み上げ
name_url_to_id = {(h.get('name'), h.get('jbis_url')): i for i, h in horses_history.items()}
for h in new_horses:
    # nameとjbis_urlで既存馬を特定（IDが変わる場合も考慮）
    key = (h.get('name'), h.get('jbis_url'))
    if key in name_url_to_id:
        horse_id = name_url_to_id[key]
        base = horses_history[horse_id]
        # 履歴を追記（内容が重複しなければ）
        new_hist = {k: h.get(k) for k in HISTORY_FIELDS}
        if 'history' not in base or not isinstance(base['history'], list):
            base['history'] = []
        if not any(all(new_hist.get(k) == old.get(k) for k in HISTORY_FIELDS) for old in base['history']):
            base['history'].append(new_hist)
        # 最新値を更新
        for k in LATEST_FIELDS + ['created_at', 'updated_at']:
            if k in h:
                base[k] = h[k]
        # その他フィールドも更新（必要に応じて）
        for k in h:
            if k not in HISTORY_FIELDS + LATEST_FIELDS + ['id', 'history']:
                base[k] = h[k]
        horses_history[horse_id] = base
    else:
        # 新規馬はID自動採番
        max_id += 1
        h = copy.deepcopy(h)
        h['id'] = max_id
        h['history'] = [{k: h.get(k) for k in HISTORY_FIELDS}]
        for k in LATEST_FIELDS:
            h[k] = h.get(k)
        horses_history[max_id] = h

# 5. 全馬が必ずhistory配列を持つことを保証
for h in horses_history.values():
    if 'history' not in h or not isinstance(h['history'], list) or len(h['history']) == 0:
        hist = {k: h.get(k) for k in HISTORY_FIELDS}
        h['history'] = [hist]

# 6. horsesリストをID順で生成
horses_list = [horses_history[i] for i in sorted(horses_history.keys())]

# 7. メタデータ更新
metadata = {
    'last_updated': datetime.now().isoformat(),
    'total_horses': len(horses_list),
    'average_price': int(sum(h.get('sold_price') or 0 for h in horses_list) / len(horses_list)) if horses_list else 0
}

with open(HISTORY_PATH, 'w', encoding='utf-8') as f:
    json.dump({'metadata': metadata, 'horses': horses_list}, f, ensure_ascii=False, indent=2)

print(f"履歴型データに積み上げマージ完了: {HISTORY_PATH} (total_horses={len(horses_list)})") 