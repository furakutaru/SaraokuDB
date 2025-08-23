"""
馬の基本情報（馬名、性別、年齢）を取得するモジュール
"""
import re
from typing import Dict, Optional, Tuple


def extract_name_sex_age(card) -> Tuple[Optional[Dict[str, str]], bool]:
    """
    馬のカードから基本情報（馬名、性別、年齢）を抽出する
    
    Args:
        card: BeautifulSoupのカード要素
        
    Returns:
        Tuple[Optional[Dict[str, str]], bool]: 
            - 抽出した基本情報の辞書（失敗時はNone）
            - 成功可否（True: 成功, False: 失敗）
    """
    try:
        # 馬名を抽出
        name_elem = card.select_one('.auctionTableCard__name, .horse-name, [data-testid="horse-name"]')
        if not name_elem:
            return None, False
            
        # 馬名のクリーンアップ処理
        name = _clean_horse_name(name_elem)
        
        # 性別と年齢を取得
        sex_elem = card.select_one('.horseLabelWrapper__horseSex')
        age_elem = card.select_one('.horseLabelWrapper__horseAge')
        
        sex = sex_elem.get_text(strip=True) if sex_elem else ''
        age = _extract_age(age_elem, card) if age_elem else ''
        
        return {
            'name': name,
            'sex': sex,
            'age': age
        }, True
        
    except Exception as e:
        return None, False


def _clean_horse_name(name_elem) -> str:
    """馬名をクリーンアップする"""
    # テキストノードを直接取得して、不要な子要素のテキストを除外
    text_nodes = [text for text in name_elem.find_all(text=True, recursive=True) 
                 if text.parent.name not in ['script', 'style']]
    
    # 1. まず、要素内のすべてのテキストを取得
    name = name_elem.get_text(' ', strip=True)
    
    # 2. テキストノードから直接名前を抽出
    if text_nodes:
        first_text = text_nodes[0].strip()
        if len(first_text) > 2 and (not name or len(first_text) < len(name)):
            name = first_text
    
    # 3. タイトル属性を確認
    title = name_elem.get('title', '').strip()
    if not title and name_elem.get('data-original-title'):
        title = name_elem.get('data-original-title', '').strip()
    
    # 4. タイトル属性からも名前を抽出
    if title and (not name or len(title) > len(name)):
        name = title
    
    # 5. 親要素のテキストを確認
    if name_elem.parent:
        parent_text = name_elem.parent.get_text(' ', strip=True)
        if (parent_text and len(parent_text) > len(name) and 
            len(re.findall(r'[0-9]', parent_text)) < 3):
            name = parent_text
    
    # 6. 馬名のクリーンアップ
    # 改行やタブをスペースに置換
    name = re.sub(r'[\n\r\t]+', ' ', name)
    
    # 7. 最初の馬名部分を抽出
    name_match = re.search(r'^([^\s\(\[\{\n\r\t]+(?:\s+[^\s\(\[\{\n\r\t]+)*)', name)
    if name_match:
        name = name_match.group(1).strip()
    
    # 8. 不要な接尾辞を削除
    name = re.sub(r'\s*(?:…|\.\.\.|販売申込者|総賞金|基本情報|競走成績|詳細血統表).*$', '', name).strip()
    
    # 9. 金額表記を削除
    name = re.sub(r'\d+\.?\d*\s*万円?', '', name).strip()
    
    # 10. 不要な記号を削除
    name = re.sub(r'^[\s\-\*\+\=\~_…]+', '', name)  # 先頭の記号
    name = re.sub(r'[\-\*\+\=\~_…]+$', '', name)  # 末尾の記号
    
    # 11. 連続するスペースを1つにし、前後の空白を削除
    name = re.sub(r'\s+', ' ', name).strip()
    
    # 12. 名前が空または短すぎる場合は、最初のテキストノードをそのまま使用
    if not name or len(name) < 2:
        if text_nodes and len(text_nodes) > 0:
            name = text_nodes[0].strip()
            # 不要なテキストを削除
            name = re.sub(r'\s*(?:…|\.\.\.|販売申込者|総賞金|基本情報|競走成績|詳細血統表).*$', '', name).strip()
    
    # 13. 名前の後処理: 不要なテキストを削除
    name = re.sub(r'\s*\.{3,}$', '', name)  # 末尾の「...」を削除
    name = re.sub(r'\s*…+\s*$', '', name)    # 末尾の「…」を削除
    
    return name


def _extract_age(age_elem, card) -> str:
    """年齢を抽出する"""
    age = age_elem.get_text(strip=True)
    
    # 年齢が空の場合は代替セレクタを試す
    if not age:
        # 代替セレクタ1: 年齢が含まれている可能性のある要素を検索
        age_alt = card.select_one('.auctionTableCard__age .value')
        if age_alt:
            age = age_alt.get_text(strip=True)
        
        # 代替セレクタ2: 性別と年齢が同じ要素内にある場合
        if not age and card.select_one('.horseLabelWrapper__horseSex'):
            parent_text = card.select_one('.horseLabelWrapper__horseSex').parent.get_text(' ', strip=True)
            age_match = re.search(r'(\d+)歳', parent_text)
            if age_match:
                age = age_match.group(1)
        
        # 代替セレクタ3: カード全体から年齢を検索
        if not age:
            card_text = card.get_text(' ', strip=True)
            age_match = re.search(r'(\d+)歳', card_text)
            if age_match:
                age = age_match.group(1)
    
    # 年齢から数字のみを抽出（例：「3歳」→「3」）
    age_match = re.search(r'(\d+)', str(age))
    return age_match.group(1) if age_match else ''
