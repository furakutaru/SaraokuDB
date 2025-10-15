#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import logging
import glob
from datetime import datetime
from bs4 import BeautifulSoup
from urllib.parse import urljoin

# ログ設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('extract_horses_consistent.log', encoding='utf-8'),
        logging.StreamHandler()
    ]
)

def extract_horse_info(html_file):
    """リストページのHTMLから馬情報を抽出する（メインスクリプトと同様の実装）"""
    logging.info(f"Starting extraction from {html_file}")
    
    try:
        # バイナリモードでファイルを読み込み、適切なエンコーディングを推測
        with open(html_file, 'rb') as f:
            raw_data = f.read()
        
        # エンコーディングを推測
        encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']
        content = None
        
        for enc in encodings:
            try:
                content = raw_data.decode(enc)
                break
            except UnicodeDecodeError:
                continue
        
        if content is None:
            content = raw_data.decode('utf-8', errors='replace')
        
        # HTMLをパース
        soup = BeautifulSoup(content, 'html.parser')
        
    except Exception as e:
        logging.error(f"Error processing file {html_file}: {str(e)}", exc_info=True)
        return []
    
    horses = []
    
    # 馬情報を含むテーブルを検索
    horse_sections = []
    tables = soup.find_all('table')
    logging.info(f"Found {len(tables)} tables in the document")
    
    # 馬情報を含むテーブルを検索（クラス名で検索）
    for table in tables:
        # 馬名を含む要素を検索
        name_elem = table.select_one('.auctionTableCard__name')
        if name_elem:
            horse_sections.append(table)
    
    logging.info(f"Found {len(horse_sections)} potential horse sections")
    
    for section in horse_sections:
        try:
            # 馬名を抽出（複数のクラス名で検索）
            name_elem = (section.select_one('.auctionTableCard__name') or 
                        section.select_one('.horse-name') or
                        section.select_one('h1, h2, h3, strong'))
                            
            if not name_elem:
                logging.warning(f"馬名要素が見つかりません: {section}")
                continue
                
            name = ' '.join(name_elem.get_text().split())
            
            # 馬名が省略されているかどうかをチェック
            is_name_truncated = ('...' in name or len(name) < 2 or 
                              (re.search(r'[\u30A1-\u30FF]+$', name) and not re.search(r'[\u30A1-\u30FF]{2,}[^\u30A1-\u30FF]*$', name)))
            
            # 詳細ページのリンクを取得
            detail_link = None
            for a in section.find_all('a', href=True):
                if 'item' in a['href']:
                    detail_link = a['href']
                    if not detail_link.startswith(('http://', 'https://')):
                        detail_link = urljoin('https://auction.keiba.rakuten.co.jp', detail_link)
                    break
            
            # 詳細ページから馬名を取得（メインスクリプトと同様の処理）
            if detail_link:
                try:
                    # 詳細ページのキャッシュを確認
                    cache_dir = os.path.dirname(html_file)
                    details_dir = os.path.join(cache_dir, 'details')
                    item_id = re.search(r'item[_-]?(\d+)', detail_link)
                    
                    if item_id:
                        item_id = item_id.group(1)
                        detail_file = os.path.join(details_dir, f"sess_*_item_{item_id}.html")
                        matching_files = glob.glob(detail_file)
                        
                        if matching_files:
                            with open(matching_files[0], 'r', encoding='utf-8') as f:
                                detail_content = f.read()
                                detail_soup = BeautifulSoup(detail_content, 'html.parser')
                                
                                # 詳細ページから馬名を抽出（複数のパターンに対応）
                                full_name_elem = None
                                name_selectors = [
                                    'h1.horse-name', 'h2.horse-name', 'h3.horse-name',
                                    'div.horse-name', 'span.horse-name',
                                    '.auctionTableCard__name',
                                    'div.auctionTableCard__name',
                                    'h1.auctionTableCard__name',
                                    'h1', 'h2', 'h3', 'strong',
                                    'div.horseName', 'span.horseName',
                                    'div.horse_name', 'span.horse_name',
                                    'div.horse-name', 'span.horse-name',
                                    'div.horse__name', 'span.horse__name'
                                ]
                                
                                for selector in name_selectors:
                                    elem = detail_soup.select_one(selector)
                                    if elem and elem.get_text(strip=True):
                                        full_name_elem = elem
                                        break
                                        
                                if full_name_elem:
                                    full_name = ' '.join(full_name_elem.get_text().split())
                                    if full_name and (len(full_name) > len(name) or name in full_name):
                                        name = full_name
                                        logging.info(f"詳細ページから完全な馬名を取得: {name}")
                except Exception as e:
                    logging.warning(f"Failed to get full name from detail page: {e}")
            
            # 馬情報を抽出
            details_text = section.get_text(separator='\n', strip=True)
            
            horse_info = {
                'name': name,
                'extracted_at': datetime.now().isoformat(),
                'source_file': os.path.basename(html_file)
            }
            
            # 血統情報を抽出
            pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\n]+)', details_text)
            if pedigree_match:
                horse_info.update({
                    'sire': pedigree_match.group(1).strip(),
                    'dam': pedigree_match.group(2).strip(),
                    'damsire': pedigree_match.group(3).strip()
                })
            
            # レース成績を抽出
            record_match = re.search(r'通算成績：([^\[]+)\[([^\]]+)\]', details_text)
            if record_match:
                horse_info['race_record'] = {
                    'summary': record_match.group(1).strip(),
                    'record': record_match.group(2).strip()
                }
            
            # 賞金を抽出
            prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', details_text)
            if prize_match:
                try:
                    horse_info['prize_money'] = float(prize_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            
            # オークション日を抽出
            auction_match = re.search(r'※(\d{4}年\d{1,2}月\d{1,2}日)落札', details_text)
            if auction_match:
                horse_info['auction_date'] = auction_match.group(1)
            
            # コメントを抽出
            comment_section = re.search(r'本馬について[^\n]*\n(.*?)(?=\n\s*※|$)', details_text, re.DOTALL)
            if comment_section:
                horse_info['comments'] = comment_section.group(1).strip()
            
            logging.info(f"Extracted info for horse: {name}")
            horses.append(horse_info)
            
        except Exception as e:
            logging.error(f"Error processing horse section: {str(e)}", exc_info=True)
            continue
    
    return horses

def main():
    # 最新のキャッシュディレクトリを取得
    cache_base = '/Users/yum.ishii/SaraokuDB/cache'
    cache_dirs = sorted([d for d in os.listdir(cache_base) if os.path.isdir(os.path.join(cache_base, d))])
    
    if not cache_dirs:
        logging.error("No cache directories found")
        return
    
    latest_cache = os.path.join(cache_base, cache_dirs[-1])
    list_file = os.path.join(latest_cache, 'list.html')
    
    if not os.path.exists(list_file):
        logging.error(f"List file not found: {list_file}")
        return
    
    logging.info(f"Processing cache directory: {latest_cache}")
    
    # 馬情報を抽出
    horses = extract_horse_info(list_file)
    
    # 結果を保存
    output_file = os.path.join(latest_cache, 'extracted_horses_consistent.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(horses, f, ensure_ascii=False, indent=2)
    
    logging.info(f"Extracted {len(horses)} horses to {output_file}")

if __name__ == "__main__":
    main()
