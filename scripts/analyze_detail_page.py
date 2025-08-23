import os
import sys
from bs4 import BeautifulSoup

# デバッグ用のHTMLファイルを指定
html_file = '../debug/detail_page_14722.html'

# HTMLファイルを読み込む
with open(html_file, 'r', encoding='utf-8') as f:
    html_content = f.read()

# BeautifulSoupでパース
soup = BeautifulSoup(html_content, 'html.parser')

print("=== 画像関連の要素を検索 ===")

# メイン画像の検索
print("\n1. メイン画像 (id=itemphoto300):")
main_image = soup.find('dt', {'id': 'itemphoto300'})
if main_image:
    print(f"見つかりました: {main_image}")
    img_tag = main_image.find('img')
    if img_tag:
        print(f"画像タグ: {img_tag}")
        print(f"src属性: {img_tag.get('src', '見つかりません')}")
    else:
        print("画像タグが見つかりません")
else:
    print("メイン画像のコンテナが見つかりません")

# カルーセル画像の検索
print("\n2. カルーセル画像 (ul.itemphoto):")
carousel = soup.find('ul', {'class': 'itemphoto'})
if carousel:
    print(f"カルーセル要素: {carousel}")
    carousel_images = carousel.find_all('img')
    print(f"カルーセル内の画像数: {len(carousel_images)}")
    for i, img in enumerate(carousel_images, 1):
        print(f"  画像 {i}: {img.get('src', 'src属性なし')}")
else:
    print("カルーセル要素が見つかりません")

# 血統情報の検索
print("\n=== 血統情報を検索 ===")

# テーブル形式の血統情報
print("\n1. テーブル形式の血統情報 (table.pedigree):")
pedigree_table = soup.find('table', {'class': 'pedigree'})
if pedigree_table:
    print("血統テーブルが見つかりました:")
    print(pedigree_table.prettify())
else:
    print("血統テーブルが見つかりません")

# テキストベースの血統情報
print("\n2. テキストベースの血統情報:")
page_text = soup.get_text(' ', strip=True)

# 血統情報と思われるパターンを検索
import re
patterns = [
    r'父[：:]([^\n\r\u3000]+?)\s*母[：:]([^\n\r\u3000]+?)\s*母の?父[：:]([^\n\r\u3000]+?)(?=\s|\n|\r|$)',
    r'父[：:]([^\s　]+)[\s　]+母[：:]([^\s　]+)[\s　]+母の?父[：:]([^\s\n<]+)'
]

found = False
for i, pattern in enumerate(patterns, 1):
    matches = re.finditer(pattern, page_text, re.DOTALL)
    for match in matches:
        found = True
        print(f"\nパターン {i} で一致:")
        print(f"  父: {match.group(1).strip()}")
        print(f"  母: {match.group(2).strip()}")
        print(f"  母の父: {match.group(3).strip()}")

if not found:
    print("血統情報のパターンが見つかりませんでした")

# 血統情報が含まれていそうなセクションを検索
print("\n3. 血統情報が含まれていそうなセクション:")
sections = soup.find_all(['div', 'section', 'table'], class_=True)
for section in sections:
    section_text = section.get_text(' ', strip=True)
    if '父' in section_text and '母' in section_text and ('父' in section_text or '母の父' in section_text):
        print(f"\nセクション: {section.name} class={section.get('class', '')}")
        print(section.prettify()[:500] + "...")  # 最初の500文字を表示

# ページ全体から血統情報を検索
print("\n4. ページ全体から血統情報を検索:")
pedigree_keywords = ['父', '母', '母の父', '牡馬', '牝馬']
for i, text in enumerate(soup.stripped_strings):
    if any(keyword in text for keyword in pedigree_keywords):
        print(f"\nテキスト {i+1}:")
        print(text.strip())

print("\n=== スクリプト終了 ===")
