import json
import requests
from bs4 import BeautifulSoup
import time

# horses_history.jsonの全馬（トップレベルhorses＋history配列）からdetail_urlをリストアップ
with open('static-frontend/public/data/horses_history.json', encoding='utf-8') as f:
    data = json.load(f)

# detail_urlを持つ全馬（トップレベル＋history配列）をリストアップ
horse_targets = []  # (ref, idx, is_history, history_idx, name, url)
for idx, horse in enumerate(data['horses']):
    if horse.get('detail_url'):
        horse_targets.append((horse, idx, False, None, horse.get('name'), horse['detail_url']))
    if 'history' in horse:
        for hidx, h in enumerate(horse['history']):
            if h.get('detail_url'):
                horse_targets.append((h, idx, True, hidx, h.get('name'), h['detail_url']))

print(f"スクレイピング対象: {len(horse_targets)}頭")

# スクレイピング関数（必要に応じて拡張）
def scrape_auction(url):
    try:
        r = requests.get(url, timeout=10, headers={'User-Agent': 'Mozilla/5.0'})
        soup = BeautifulSoup(r.text, 'html.parser')
        # 馬名
        name = soup.find('h1').get_text(strip=True) if soup.find('h1') else ''
        # 年齢・性別
        info = soup.find('div', class_='horse-info')
        age, sex = '', ''
        if info:
            txt = info.get_text()
            for s in ['牡','牝','セン']: # 性別
                if s in txt:
                    sex = s
            for a in ['2','3','4','5','6','7','8','9','10']:
                if a+'歳' in txt:
                    age = a
        # セラー
        seller = ''
        for tag in soup.find_all('th'):
            if '販売申込者' in tag.get_text():
                seller = tag.find_next('td').get_text(strip=True)
        # 戦績
        race_record = ''
        for tag in soup.find_all('th'):
            if '戦績' in tag.get_text():
                race_record = tag.find_next('td').get_text(strip=True)
        # コメント
        comment = ''
        for tag in soup.find_all('th'):
            if 'コメント' in tag.get_text():
                comment = tag.find_next('td').get_text(strip=True)
        # 画像URL
        img = ''
        img_tag = soup.find('img', {'class': 'horse-image'})
        if img_tag:
            img = img_tag['src']
        return {
            'name': name,
            'age': age,
            'sex': sex,
            'seller': seller,
            'race_record': race_record,
            'comment': comment,
            'primary_image': img,
        }
    except Exception as e:
        return {'error': str(e)}

# 全馬分スクレイピング
errors = []
for ref, idx, is_history, hidx, name, url in horse_targets:
    print(f"SCRAPING: {name} -> {url}")
    result = scrape_auction(url)
    if 'error' in result:
        errors.append({'name': name, 'url': url, 'error': result['error']})
        continue
    # データ上書き
    for k, v in result.items():
        if v:
            ref[k] = v
    time.sleep(1)  # サーバー負荷配慮

# 保存
with open('static-frontend/public/data/horses_history.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"完了。エラー馬: {len(errors)}")
if errors:
    for e in errors:
        print(f"ERROR: {e['name']} {e['url']} {e['error']}") 