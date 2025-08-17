import os
import re
import logging
import unicodedata
from bs4 import BeautifulSoup
from pathlib import Path
from typing import Dict, Optional

# 設定
CACHE_DIR = 'test_cache'
LIST_PAGE = 'fixed_auction_list.html'
OUTPUT_FILE = 'fixed_auction_list_updated.html'

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('fix_links.log')
    ]
)

def normalize_text(text: str) -> str:
    """テキストを正規化（正規化形式KC、全角→半角、連続する空白を1つに）"""
    if not text:
        return ''
    # 正規化（NFKC: 互換文字を分解し、結合文字を合成）
    text = unicodedata.normalize('NFKC', text)
    # 全角スペースを半角スペースに
    text = text.replace('　', ' ')
    # 連続するスペースを1つに
    text = ' '.join(text.split())
    return text.strip()

def extract_horse_name_from_title(title: str) -> Optional[str]:
    """タイトルから馬名を抽出"""
    if not title:
        return None
    
    # パイプ記号で分割して最初の部分を取得
    name_part = title.split('|')[0].strip()
    # 不要な接頭辞/接尾辞を削除
    name = re.sub(r'^【[^】]*】\s*|\s*[※※].*$', '', name_part)
    
    # エンブレイスメントの表記ゆれを修正
    if 'エンブレイス' in name:
        name = 'エンブレイスメント'
    
    return normalize_text(name) if name else None

def find_horse_detail_pages(cache_dir: str) -> Dict[str, str]:
    """馬の詳細ページのファイルを検索して、正規化した馬名とファイルのマッピングを作成"""
    horse_files = {}
    processed = 0
    
    for filename in os.listdir(cache_dir):
        if filename == LIST_PAGE or not filename.endswith('.html'):
            continue
            
        filepath = os.path.join(cache_dir, filename)
        try:
            with open(filepath, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
                # タイトルタグから馬名を抽出
                title_match = re.search(r'<title>([^<]+)', content)
                if title_match:
                    title = title_match.group(1)
                    horse_name = extract_horse_name_from_title(title)
                    if horse_name:
                        # 重複チェック
                        if horse_name in horse_files:
                            logging.warning(f"Duplicate horse name found: {horse_name} in {filename} and {horse_files[horse_name]}")
                        horse_files[horse_name] = filename
                        processed += 1
        except Exception as e:
            logging.error(f"Error processing {filename}: {e}", exc_info=True)
    
    logging.info(f"Processed {processed} horse detail pages, found {len(horse_files)} unique horse names")
    return horse_files

def find_best_match(horse_name: str, horse_files: Dict[str, str]) -> Optional[str]:
    """最も一致する馬名を見つける（完全一致→部分一致の順で試す）"""
    # 完全一致
    if horse_name in horse_files:
        return horse_name
    
    # 正規化して再試行
    normalized_name = normalize_text(horse_name)
    if normalized_name in horse_files:
        return normalized_name
    
    # 部分一致（前方一致）
    for name in horse_files:
        if name.startswith(normalized_name) or normalized_name.startswith(name):
            return name
    
    # 部分一致（含む）
    for name in horse_files:
        if normalized_name in name or name in normalized_name:
            return name
    
    return None

def fix_horse_links():
    """オークションリストの馬名リンクを修正するメイン関数"""
    logging.info("Starting to fix horse links...")
    
    # リストページを読み込む
    list_page_path = os.path.join(CACHE_DIR, LIST_PAGE)
    try:
        with open(list_page_path, 'r', encoding='utf-8') as f:
            soup = BeautifulSoup(f, 'html.parser')
    except Exception as e:
        logging.error(f"Failed to read list page {list_page_path}: {e}", exc_info=True)
        return
    
    # エンブレイスメントのマッピングを定義
    name_mapping = {
        'エンブレイスメン': 'エンブレイスメント',
        'エンブレイスメン...': 'エンブレイスメント'
    }
    
    # 馬の詳細ページを検索
    horse_files = find_horse_detail_pages(CACHE_DIR)
    if not horse_files:
        logging.error("No horse detail pages found!")
        return
    
    # 各馬のリンクを修正
    fixed_count = 0
    not_found = []
    used_files = set()  # 使用済みのファイルを追跡
    
    for link in soup.find_all('a', class_='auctionTableCard__name--link'):
        original_name = link.get_text(strip=True)
        horse_name = normalize_text(original_name)
        original_href = link.get('href', '')
        
        # エンブレイスメントのリンクを直接修正
        if 'エンブレイスメン' in original_name and original_href == '/item/14645':
            correct_file = '20250812_134141_d86c357c6b7b505c30f04be739699ea7.html'
            link['href'] = correct_file
            link.string = 'エンブレイスメント'  # 馬名も修正
            logging.info(f"Fixed Embracement link: {original_name} -> エンブレイスメント ({correct_file})")
            fixed_count += 1
            used_files.add(correct_file)
            continue
            
        # 相対パス（/item/12345）を処理
        if original_href.startswith('/item/') and original_href[6:].isdigit():
            # 数字部分を抽出
            item_id = original_href.split('/')[-1]
            # 対応するファイルを検索
            matched_file = None
            for file in os.listdir(CACHE_DIR):
                if file.startswith(item_id) and file.endswith('.html'):
                    matched_file = file
                    break
            
            if matched_file:
                link['href'] = matched_file
                logging.info(f"Fixed relative path: {original_href} -> {matched_file}")
                fixed_count += 1
                used_files.add(matched_file)
                
                # 馬名の表記を修正
                for wrong_name, correct_name in name_mapping.items():
                    if wrong_name in original_name:
                        link.string = correct_name
                        logging.info(f"Fixed horse name: {original_name} -> {correct_name}")
                        break
                        
                continue
        
        # 既存のファイル名を検証
        if os.path.basename(original_href) in os.listdir(CACHE_DIR):
            # 既に正しいファイル名が設定されている場合
            used_files.add(os.path.basename(original_href))
            continue
        
        # 馬名でマッチングを試みる
        matched_name = find_best_match(horse_name, horse_files)
        
        if matched_name and horse_files[matched_name] not in used_files:
            # 重複を避けてファイルを割り当て
            link['href'] = horse_files[matched_name]
            logging.info(f"Matched by name: {original_name} -> {horse_files[matched_name]}")
            fixed_count += 1
            used_files.add(horse_files[matched_name])
        else:
            logging.warning(f"No unique match found for: {original_name}")
            not_found.append(original_name)
    
    # 結果をログに記録
    logging.info(f"Fixed {fixed_count} links, {len(not_found)} not found")
    if not_found:
        logging.warning(f"Horses not found: {', '.join(not_found)}")
    
    # 未使用のファイルを確認
    all_files = set(f for f in os.listdir(CACHE_DIR) if f.endswith('.html') and f != LIST_PAGE)
    unused_files = all_files - used_files
    if unused_files:
        logging.info(f"Unused files: {', '.join(sorted(unused_files))}")
    
    # 修正したHTMLを保存
    output_path = os.path.join(CACHE_DIR, OUTPUT_FILE)
    try:
        with open(output_path, 'w', encoding='utf-8') as f:
            # HTML5のDOCTYPEを明示的に指定
            f.write('<!DOCTYPE html>\n')
            # 修正したHTMLを書き出し
            f.write(str(soup))
        
        logging.info(f"Successfully saved fixed list page to {output_path}")
        print(f"Success! Fixed {fixed_count} links. {len(not_found)} horses not found.")
        if unused_files:
            print(f"Unused files: {', '.join(sorted(unused_files))}")
        
    except Exception as e:
        logging.error(f"Failed to save output file: {e}", exc_info=True)
        print(f"Error: Failed to save output file: {e}")
    
    print(f"修正したファイル: {output_path}")
    print(f"元のファイル: {list_page_path} (変更なし)")

if __name__ == "__main__":
    fix_horse_links()
