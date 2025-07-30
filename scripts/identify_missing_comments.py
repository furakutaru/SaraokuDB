import json

# データを読み込む
with open('../static-frontend/public/data/horses_history.json', 'r', encoding='utf-8') as f:
    data = json.load(f)

# コメントが取得できていない馬を抽出
missing_comments = []
for horse in data['horses']:
    comment_found = False
    if 'history' in horse and horse['history']:
        for history in horse['history']:
            if history.get('comment') and history['comment'] != '取得できませんでした':
                comment_found = True
                break
    if not comment_found:
        missing_comments.append({
            'id': horse['id'],
            'name': horse['name'],
            'detail_url': horse.get('detail_url', 'N/A')
        })

print(f'コメントが取得できていない馬: {len(missing_comments)}頭')
for i, horse in enumerate(missing_comments, 1):
    print(f"{i}. ID: {horse['id']}, 馬名: {horse['name']}, URL: {horse['detail_url']}")
