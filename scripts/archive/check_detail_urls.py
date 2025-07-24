import json
import requests
from bs4 import BeautifulSoup

with open('static-frontend/public/data/horses_history.json', encoding='utf-8') as f:
    data = json.load(f)

results = []
for horse in data['horses']:
    url = horse.get('detail_url')
    history_names = [h.get('name') for h in horse.get('history', []) if h.get('name')]
    if not url:
        results.append({'history_names': history_names, 'url': None, 'result': 'NO_URL'})
        continue
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        # タイトルまたはh1から馬名を抽出
        title = soup.title.string.strip() if soup.title else ''
        h1 = soup.find('h1')
        h1_text = h1.get_text().strip() if h1 else ''
        # 馬名候補
        candidates = []
        if title:
            candidates.append(title.split()[0].replace('\u3000', '').replace('　', ''))
        if h1_text:
            candidates.append(h1_text.split()[0].replace('\u3000', '').replace('　', ''))
        # history配列の馬名と一致するか
        matched = any(n in candidates for n in history_names)
        results.append({
            'history_names': history_names,
            'url': url,
            'title': title,
            'h1': h1_text,
            'matched': matched
        })
    except Exception as e:
        results.append({'history_names': history_names, 'url': url, 'error': str(e)})

with open('scripts/check_detail_urls_result.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2)

print('チェック完了: scripts/check_detail_urls_result.json') 