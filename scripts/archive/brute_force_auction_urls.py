import json
import sys
import os
import time
import re
from datetime import datetime
from bs4 import BeautifulSoup
import requests

# プロジェクトルートをパスに追加
project_root = os.path.dirname(os.path.dirname(__file__))
sys.path.append(project_root)
sys.path.append(os.path.join(project_root, 'backend'))
sys.path.append(os.path.join(project_root, 'backend/scrapers'))

# RakutenAuctionScraperをimport
try:
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
except ImportError:
    rakuten_scraper_path = os.path.join(project_root, 'backend/scrapers/rakuten_scraper.py')
    import importlib.util
    spec = importlib.util.spec_from_file_location('rakuten_scraper', rakuten_scraper_path)
    if spec is None or spec.loader is None:
        raise ImportError('rakuten_scraper.pyのロードに失敗しました')
    rakuten_scraper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(rakuten_scraper)
    RakutenAuctionScraper = rakuten_scraper.RakutenAuctionScraper

# 補完対象馬名とauction URLの対応リスト
auction_urls = {
    'テルバスタ': 'https://auction.keiba.rakuten.co.jp/item/14502',
    'ガルヴァナイズ': 'https://auction.keiba.rakuten.co.jp/item/14508',
    'ポップスター': 'https://auction.keiba.rakuten.co.jp/item/14504',
    'レンダリング': 'https://auction.keiba.rakuten.co.jp/item/14507',
    'エールブラーヴ': 'https://auction.keiba.rakuten.co.jp/item/14509',
    'アクアノート': 'https://auction.keiba.rakuten.co.jp/item/14505',
    'リュウノシャモニー': 'https://auction.keiba.rakuten.co.jp/item/14506',
}

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
errors = []
for ref, idx, is_history, hidx, name, url in horse_targets:
    print(f"SCRAPING: {name} -> {url}")
    try:
        r = requests.get(url, timeout=30, headers={'User-Agent': 'Mozilla/5.0'})
        r.raise_for_status()
        soup = BeautifulSoup(r.text, 'html.parser')
        # 馬名
        name_tag = soup.find('h1', class_='itemDetail__title')
        full_name = name_tag.get_text(strip=True) if name_tag and name_tag.get_text() is not None else ''
        if not full_name:
            title_tag = soup.find('title')
            if title_tag and title_tag.get_text() is not None:
                full_name = title_tag.get_text(strip=True)
        name_match = re.match(r'^([\w\-ァ-ヶ一-龠ぁ-んＡ-Ｚａ-ｚA-Za-z0-9]+)', full_name)
        horse_name = name_match.group(1) if name_match else full_name.split()[0]
        ref['name'] = horse_name
        # 年齢
        page_text = soup.get_text() or ''
        age = ''
        age_match = re.search(r'([0-9]{1,2})歳', page_text)
        if age_match:
            age = age_match.group(1)
        ref['age'] = age
        # 性別
        sex = ''
        title_text = ''
        if name_tag and name_tag.get_text() is not None:
            title_text = name_tag.get_text().strip()
        else:
            title_tag = soup.find('title')
            if title_tag and title_tag.get_text() is not None:
                title_text = title_tag.get_text().strip()
        sex_match = re.match(r'^.+?[ \t\u3000]+(牡|牝|セン)[ \t\u3000]*\d{1,2}歳', title_text)
        if sex_match:
            sex = sex_match.group(1)
        ref['sex'] = sex
        # 販売申込者
        seller = ''
        seller_match = re.search(r'販売申込者：([^\n\r\t]+)', page_text)
        if seller_match:
            seller = seller_match.group(1).strip()
            seller = re.sub(r'（.*$', '', seller).strip()
        ref['seller'] = seller
        # コメント
        comment = ''
        desc_div = soup.find('div', class_='itemDetail__description')
        if desc_div and getattr(desc_div, 'text', None):
            comment = str(desc_div.text).strip() if desc_div.text is not None else ''
        if not comment:
            remarks_div = soup.find('div', class_='itemDetail__remarks')
            if remarks_div and getattr(remarks_div, 'text', None):
                comment = str(remarks_div.text).strip() if remarks_div.text is not None else ''
        if not comment:
            div = soup.find('div', class_='comment')
            if div and getattr(div, 'text', None):
                comment = str(div.text).strip() if div.text is not None else ''
            else:
                p = soup.find('p', class_='comment')
                if p and getattr(p, 'text', None):
                    comment = str(p.text).strip() if p.text is not None else ''
        ref['comment'] = comment
        # 画像URL
        primary_image = ''
        images = soup.find_all('img', src=True)
        for img in images:
            src = img.get('src', '')
            if 'horse' in src.lower() and any(ext in src.lower() for ext in ['.jpg', '.jpeg', '.png']):
                primary_image = src
                break
        ref['primary_image'] = primary_image
        # 成績
        race_record = ''
        record_match = re.search(r'(\d+戦\d+勝［\d+-\d+-\d+-\d+］)', page_text)
        if record_match:
            race_record = record_match.group(1)
        ref['race_record'] = race_record
        # 疾病タグ
        disease_keywords = [
            'さく癖', '球節炎', '骨折', '屈腱炎', '蹄葉炎',
            '皮膚病', '捻挫', '腫れ', '旋回癖', '靭帯損傷',
            '砂のぼり', '蟻洞', '鼻出血', '骨瘤', '滑膜炎'
        ]
        found_tags = []
        for keyword in disease_keywords:
            if keyword in comment and keyword not in found_tags:
                found_tags.append(keyword)
        ref['disease_tags'] = ','.join(found_tags) if found_tags else 'なし'
    except Exception as e:
        errors.append({'name': name, 'url': url, 'error': str(e)})
        continue
    time.sleep(1)

with open('static-frontend/public/data/horses_history.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print(f"完了。エラー馬: {len(errors)}")
if errors:
    for e in errors:
        print(f"ERROR: {e['name']} {e['url']} {e['error']}") 