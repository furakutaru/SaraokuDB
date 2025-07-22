import json
import time
import requests
from bs4 import BeautifulSoup

with open('static-frontend/public/data/horses_history.json', encoding='utf-8') as f:
    data = json.load(f)

horses = [h.get('name', h.get('history', [{}])[0].get('name', '')) for h in data['horses'] if not h.get('detail_url')]

results = []

for name in horses:
    query = f"{name} サラブレッドオークション"
    url = f"https://www.google.com/search?q={requests.utils.quote(query)}"
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        found = False
        for item in soup.select('div.yuRUbf > a'):
            title = item.get_text()
            link = item.get('href')
            if name in title:
                results.append({'name': name, 'title': title, 'url': link})
                found = True
                break
        if not found:
            results.append({'name': name, 'title': None, 'url': None, 'note': 'Not found'})
    except Exception as e:
        results.append({'name': name, 'title': None, 'url': None, 'note': f'ERROR: {e}'})
    time.sleep(1.5)  # Googleへの負荷軽減

with open('scripts/auto_search_detail_urls_google_result.json', 'w', encoding='utf-8') as f:
    json.dump(results, f, ensure_ascii=False, indent=2) 