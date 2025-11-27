import requests
from bs4 import BeautifulSoup
import re
import os

RESULTS_FILE = 'results.csv'
LAST_ID_FILE = 'last_id.txt'
BASE_URL = 'https://auction.keiba.rakuten.co.jp/item/'

def extract_horse_name(full_name: str) -> str:
    """
    馬名抽出関数
    - 「の＋数字（全角半角）」があればそこまで取得
    - なければ最初のスペース（全角・半角）まで切り捨てる（表記揺れ対応）
    """
    # 「の＋数字」がある場合はそれまでを取得
    match = re.match(r'^.*?の[0-9０-９]+', full_name)
    if match:
        return match.group(0).strip()
    
    # スペース（半角または全角）で分割して先頭を取得
    parts = re.split(r'[ 　]', full_name.strip())
    if parts:
        return parts[0]

    return full_name.strip()

def fetch_horse_name(horse_id: int):
    url = BASE_URL + str(horse_id)
    print(f'Fetching ID: {horse_id}')
    try:
        response = requests.get(url)
        response.raise_for_status()
    except Exception as e:
        print(f'  → Failed to fetch {url}: {e}')
        return None, None

    soup = BeautifulSoup(response.text, 'html.parser')

    span = soup.find('span', itemprop='name')
    if not span:
        print('  → No valid horse name found.')
        return None, None

    full_name = span.get_text(strip=True)
    horse_name = extract_horse_name(full_name)

    if not horse_name or len(horse_name) < 2:
        print('  → No valid horse name extracted.')
        return None, None

    print(f'  → Found horse name: {horse_name}')
    return horse_name, url

def load_last_id():
    if os.path.exists(LAST_ID_FILE):
        with open(LAST_ID_FILE, 'r') as f:
            content = f.read().strip()
            if content.isdigit():
                return int(content)
    return 0

def save_last_id(horse_id: int):
    with open(LAST_ID_FILE, 'w') as f:
        f.write(str(horse_id))

def save_result(horse_name: str, url: str):
    with open(RESULTS_FILE, 'a', encoding='utf-8') as f:
        f.write(f'"{horse_name}","{url}"\n')

def main():
    last_id = load_last_id()
    horse_id = last_id + 1
    empty_page_count = 0
    MAX_EMPTY_PAGES = 1

    while True:
        horse_name, url = fetch_horse_name(horse_id)

        if horse_name is None:
            empty_page_count += 1
            save_last_id(horse_id)  # 空ページでも保存して次へ進む

            if empty_page_count >= MAX_EMPTY_PAGES:
                print(f'Stopping after {empty_page_count} empty page(s).')
                break
        else:
            empty_page_count = 0
            save_result(horse_name, url)
            save_last_id(horse_id)

        horse_id += 1

    print('=== Results collection finished ===')

if __name__ == '__main__':
    main()
