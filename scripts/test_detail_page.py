#!/usr/bin/env python3
"""
馬詳細ページから血統情報を抽出するテストスクリプト
"""
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def extract_pedigree(html_file: str) -> dict:
    """HTMLファイルから血統情報を抽出"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    result = {
        'sire': None,    # 父
        'dam': None,      # 母
        'damsire': None,  # 母父
        'pedigree_text': None  # 生体情報テキスト
    }
    
    # 1. 生体情報テキストを取得
    pre_tag = soup.find('pre', class_='k_pre')
    if pre_tag:
        result['pedigree_text'] = pre_tag.get_text(strip=True)
    
    # 2. 血統情報を抽出するための複数の方法を試す
    
    # 方法1: 生体情報テキストから正規表現で抽出
    if result['pedigree_text']:
        # パターン1: 「父：」「母：」「母の父：」形式
        pattern1 = r'父：([^\s\n]+)[\s\n]*母：([^\s\n]+)[\s\n]*母の父：([^\s\n(]+)'
        match = re.search(pattern1, result['pedigree_text'])
        if match:
            result['sire'] = match.group(1).strip()
            result['dam'] = match.group(2).strip()
            result['damsire'] = match.group(3).strip()
    
    # 方法2: テーブル形式の情報を確認
    if not all([result['sire'], result['dam'], result['damsire']]):
        # 父、母、母父がすべて取得できていない場合のみ実行
        table = soup.find('table', class_='horseInfoTable')
        if table:
            rows = table.find_all('tr')
            for row in rows:
                th = row.find('th')
                td = row.find('td')
                if th and td:
                    label = th.get_text(strip=True)
                    value = td.get_text(strip=True)
                    if '父' in label:
                        result['sire'] = value
                    elif '母' in label and '父' not in label:
                        result['dam'] = value
                    elif '母の父' in label or '母父' in label:
                        result['damsire'] = value
    
    # 方法3: 生体情報テキストを再度解析（別パターン）
    if result['pedigree_text'] and not all([result['sire'], result['dam'], result['damsire']]):
        # パターン2: 改行区切りで情報が並んでいる場合
        lines = [line.strip() for line in result['pedigree_text'].split('\n') if line.strip()]
        for i, line in enumerate(lines):
            if '父：' in line:
                result['sire'] = line.replace('父：', '').strip()
            elif '母：' in line and '父' not in line:
                result['dam'] = line.replace('母：', '').strip()
            elif '母の父：' in line or '母父：' in line:
                damsire_line = line.replace('母の父：', '').replace('母父：', '').strip()
                # 余分な情報（通算成績など）が含まれている場合を想定して最初の単語を取得
                result['damsire'] = damsire_line.split()[0] if damsire_line else None
    
    return result

def main():
    # テストファイルのパス（サッカレッロの詳細ページ）
    detail_page_file = Path("../html_cache/20250808_212010_eaa0ef29903bfe8c0558f09bc6a9aaf8.html")
    
    if not detail_page_file.exists():
        print(f"エラー: {detail_page_file} が見つかりません")
        return
    
    print(f"[情報] {detail_page_file} から血統情報を抽出します...")
    
    # 血統情報を抽出
    pedigree_info = extract_pedigree(detail_page_file)
    
    # 結果を表示
    print("\n=== 抽出結果 ===")
    print(f"父: {pedigree_info['sire'] or '抽出できませんでした'}")
    print(f"母: {pedigree_info['dam'] or '抽出できませんでした'}")
    print(f"母父: {pedigree_info['damsire'] or '抽出できませんでした'}")
    
    # 生体情報テキストのプレビューを表示
    if pedigree_info['pedigree_text']:
        print("\n=== 生体情報テキスト（先頭200文字） ===")
        print(pedigree_info['pedigree_text'][:200] + "...")
    
    # 結果をJSONファイルに保存
    output_file = Path("extracted_pedigree.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(pedigree_info, f, ensure_ascii=False, indent=2)
    
    print(f"\n[完了] 抽出結果を {output_file} に保存しました")

if __name__ == "__main__":
    main()
