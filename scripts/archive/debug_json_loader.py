import json

with open('static-frontend/public/data/horses_history.json', encoding='utf-8') as f:
    horses = json.load(f)['horses']

with open('scripts/brute_force_auction_urls_result.json', encoding='utf-8') as f:
    results = json.load(f)

found = set(x['name'] for x in results if x.get('note') is None)
missing = [h.get('name', h.get('history', [{}])[0].get('name', '')) for h in horses if not h.get('detail_url') and h.get('name', h.get('history', [{}])[0].get('name', '')) not in found]

print('残りの未発見馬:', len(missing), missing) 