import os
import json
from bs4 import BeautifulSoup
from pathlib import Path

def extract_horse_name(html_content):
    """HTMLから馬名を抽出する関数"""
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # タイトルから馬名を抽出
    title = soup.find('title')
    title_text = title.get_text() if title else ""
    
    # 馬名と思われる部分を抽出（「|」より前の部分）
    name_from_title = title_text.split('|')[0].strip() if '|' in title_text else title_text.strip()
    
    # その他の要素からも馬名を探す
    name_elements = soup.find_all(['h1', 'h2', 'h3', 'div'], class_=lambda x: x and 'name' in x.lower())
    names_from_elements = [el.get_text().strip() for el in name_elements]
    
    return {
        'title': title_text,
        'name_from_title': name_from_title,
        'names_from_elements': names_from_elements,
        'raw_html': str(soup)[:500] + '...'  # デバッグ用に最初の500文字を保存
    }

def analyze_cache_files():
    """キャッシュファイルを分析して馬名を抽出"""
    cache_dir = Path('/Users/yum.ishii/SaraokuDB/cache/20250822_190555/details/')
    results = []
    
    for i, file_path in enumerate(cache_dir.glob('*.html')):
        if i >= 10:  # 最初の10ファイルのみチェック
            break
            
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
            
        result = extract_horse_name(content)
        results.append({
            'file': str(file_path.name),
            **result
        })
    
    # 結果を保存
    output_path = 'horse_name_analysis.json'
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    print(f"分析結果を {output_path} に保存しました")
    return results

def check_existing_horse_names():
    """既存のhorses.jsonから馬名を確認"""
    with open('/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    print("\n現在のhorses.jsonから抽出した馬名:")
    for i, horse in enumerate(data.get('horses', [])[:20]):  # 最初の20頭を表示
        print(f"{i+1}. {horse.get('name')} (性別: {horse.get('sex', '不明')}, 年齢: {horse.get('age', '不明')})")

if __name__ == "__main__":
    print("キャッシュファイルから馬名を分析中...")
    analyze_cache_files()
    
    print("\n既存のhorses.jsonを確認中...")
    check_existing_horse_names()
