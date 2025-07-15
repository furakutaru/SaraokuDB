import requests
from bs4 import BeautifulSoup
import re
import time
import urllib.parse
from bs4 import Tag

# 検索対象の馬名
TARGET_HORSE_NAME = "クレテイユ"

# Google検索クエリ
GOOGLE_SEARCH_URL = "https://www.google.com/search?q=" + urllib.parse.quote(f"site:db.netkeiba.com {TARGET_HORSE_NAME}")

headers = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/113.0.0.0 Safari/537.36"
}

def get_netkeiba_url_from_google():
    """
    Google検索結果からNetKeiba馬ページURLを抽出
    """
    res = requests.get(GOOGLE_SEARCH_URL, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")
    print("--- Google検索結果のaタグ一覧 ---")
    for a in soup.find_all("a", href=True):
        print(f"href: {a['href']}")
        print(f"text: {a.get_text(strip=True)}")
    print("--- ここまで ---")
    for a in soup.find_all("a", href=True):
        href = a["href"]
        # Googleの検索結果リンクは"/url?q=..."形式
        m = re.match(r"/url\?q=(https://db\.netkeiba\.com/horse/\d{10}/)", href)
        if m:
            return m.group(1)
    return None

def get_prize_from_netkeiba(horse_url):
    """
    NetKeiba馬ページから賞金情報を抽出
    """
    res = requests.get(horse_url, headers=headers)
    res.encoding = res.apparent_encoding
    soup = BeautifulSoup(res.text, "html.parser")
    # 賞金情報はプロフィールテーブル内にある
    profile_table = soup.find("table", class_="db_prof_table")
    if not isinstance(profile_table, Tag):
        print("プロフィールテーブルが見つかりませんでした。")
        return None
    rows = [row for row in profile_table.find_all("tr") if isinstance(row, Tag)]
    for row in rows:
        th = row.find("th")
        td = row.find("td")
        if th and td and "総賞金" in th.get_text():
            return td.get_text(strip=True)
    return None

def main():
    print(f"馬名: {TARGET_HORSE_NAME}")
    url = get_netkeiba_url_from_google()
    if not url:
        print("Google検索からNetKeibaページURLを特定できませんでした。")
        return
    print(f"NetKeibaページ: {url}")
    prize = get_prize_from_netkeiba(url)
    if prize:
        print(f"総賞金: {prize}")
    else:
        print('-')

if __name__ == "__main__":
    main() 