import os
import re
from bs4 import BeautifulSoup
from pathlib import Path

def extract_horse_links(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        soup = BeautifulSoup(f, 'html.parser')
    
    links = []
    for a_tag in soup.find_all('a', class_='auctionTableCard__name--link'):
        href = a_tag.get('href')
        if href and href.endswith('.html'):
            links.append(href)
    
    return links

def get_cached_html_files(cache_dir):
    return [f.name for f in Path(cache_dir).glob('*.html') if f.is_file()]

def verify_links(links, cache_files):
    missing_links = []
    for link in links:
        if link not in cache_files:
            missing_links.append(link)
    return missing_links

def main():
    cache_dir = '/Users/yum.ishii/SaraokuDB/scripts/test_cache'
    html_file = os.path.join(cache_dir, 'fixed_auction_list_updated.html')
    
    print("馬のリンクを抽出中...")
    links = extract_horse_links(html_file)
    print(f"抽出されたリンク数: {len(links)}")
    
    print("キャッシュファイルを取得中...")
    cache_files = get_cached_html_files(cache_dir)
    print(f"キャッシュファイル数: {len(cache_files)}")
    
    print("リンクを検証中...")
    missing_links = verify_links(links, cache_files)
    
    if missing_links:
        print(f"\n警告: {len(missing_links)}個のリンクがキャッシュに存在しません:")
        for link in missing_links[:10]:  # 最初の10件のみ表示
            print(f"- {link}")
        if len(missing_links) > 10:
            print(f"...他{len(missing_links)-10}件")
    else:
        print("\nすべてのリンクがキャッシュに存在します。")
    
    # キャッシュにあるがリンクされていないファイルを確認
    linked_files = set(links)
    unused_files = [f for f in cache_files if f != 'fixed_auction_list_updated.html' and f not in linked_files]
    
    if unused_files:
        print(f"\n警告: {len(unused_files)}個のキャッシュファイルがリンクされていません:")
        for file in unused_files[:10]:  # 最初の10件のみ表示
            print(f"- {file}")
        if len(unused_files) > 10:
            print(f"...他{len(unused_files)-10}件")
    else:
        print("\nすべてのキャッシュファイルがリンクされています。")

if __name__ == "__main__":
    main()
