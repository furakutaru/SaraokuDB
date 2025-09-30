#!/usr/bin/env python3
"""
top page から馬のリストを抽出するテストスクリプト
"""
import re
import json
from pathlib import Path
from bs4 import BeautifulSoup

def extract_horse_list(html_file: str) -> list:
    """HTMLファイルから馬のリストを抽出"""
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    horses = []
    
    # 馬の情報が含まれる要素を探す
    horse_elements = soup.find_all('div', class_='auctionTableCard')
    
    for element in horse_elements:
        horse_info = {}
        
        # 馬名を抽出
        name_element = element.find('a', class_='auctionTableCard__name')
        if name_element:
            horse_info['name'] = name_element.get_text(strip=True)
            
            # 詳細ページのURLを抽出
            detail_url = name_element.get('href', '')
            if detail_url and not detail_url.startswith('http'):
                horse_info['detail_url'] = f"https://auction.keiba.rakuten.co.jp{detail_url}"
        
        # 販売者情報を抽出
        seller_element = element.find('div', class_='auctionTableCard__seller')
        if seller_element:
            seller_text = seller_element.get_text(strip=True)
            seller_name = seller_text.replace('販売申込者', '').strip()
            horse_info['seller'] = seller_name
        
        # 生年月日を抽出
        birthday_element = element.find('div', class_='auctionTableCard__birthday')
        if birthday_element:
            birthday_text = birthday_element.get_text(strip=True)
            birthday = birthday_text.replace('生年月日', '').strip()
            horse_info['birthday'] = birthday
        
        # 性別と年齢を抽出
        sex_element = element.find('div', class_='horseLabelWrapper__horseSex')
        if sex_element:
            horse_info['sex'] = sex_element.get_text(strip=True)
        
        age_element = element.find('div', class_='horseLabelWrapper__horseAge')
        if age_element:
            horse_info['age'] = age_element.get_text(strip=True)
        
        # 外部リンク（JBISなど）を抽出
        links = element.find_all('a', class_='auctionTableCard__externalLink')
        for link in links:
            if 'jbis' in link.get('href', ''):
                horse_info['jbis_url'] = link['href']
        
        if horse_info:
            horses.append(horse_info)
    
    return horses

def main():
    # テストファイルのパス
    top_page_file = Path("../html_cache/20250808_211927_a1a9f3e94be92e25f864231ea320699d.html")
    
    if not top_page_file.exists():
        print(f"エラー: {top_page_file} が見つかりません")
        return
    
    print(f"[情報] {top_page_file} から馬のリストを抽出します...")
    
    # 馬のリストを抽出
    horses = extract_horse_list(top_page_file)
    
    # 結果を表示
    print(f"\n=== 抽出結果 ({len(horses)}頭) ===")
    for i, horse in enumerate(horses, 1):
        print(f"\n{i}. {horse.get('name', '名前不明')}")
        print(f"   性別: {horse.get('sex', '不明')}, 年齢: {horse.get('age', '不明')}")
        print(f"   生年月日: {horse.get('birthday', '不明')}")
        print(f"   販売者: {horse.get('seller', '不明')}")
        print(f"   JBIS URL: {horse.get('jbis_url', 'なし')}")
        print(f"   詳細URL: {horse.get('detail_url', 'なし')}")
    
    # 結果をJSONファイルに保存
    output_file = Path("extracted_horses.json")
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(horses, f, ensure_ascii=False, indent=2)
    
    print(f"\n[完了] 抽出結果を {output_file} に保存しました")

if __name__ == "__main__":
    main()
