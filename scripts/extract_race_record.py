#!/usr/bin/env python3
"""
戦績情報を抽出するスクリプト

このスクリプトは、HTMLファイルから戦績情報を抽出します。
主に楽天競馬オークションの馬の詳細ページから戦績を抽出するために使用されます。
"""

import re
import logging
import html
from bs4 import BeautifulSoup
from typing import Optional, List, Pattern, Tuple

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
    ]
)
logger = logging.getLogger(__name__)

# 戦績情報の正規表現パターン
RACE_RECORD_PATTERN = re.compile(
    r'(\d+戦\d+勝\s*[\[\]［］]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］])|(未出走)'
)

def _clean_race_record(record: str) -> str:
    """戦績情報をクリーンアップします。
    
    Args:
        record (str): 抽出された戦績情報
        
    Returns:
        str: クリーンアップされた戦績情報
    """
    if not record:
        return ""
    
    # 戦績情報のパターン（例: 3戦0勝［0-0-0-3］）
    race_patterns = [
        # 通常の戦績パターン（例: 3戦0勝［0-0-0-3］）
        r'(\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］])',
        # 未出走のパターン
        r'(未出走)'
    ]
    
    # テキストを行ごとに分割して、各行でマッチングを試みる
    for line in record.split('\n'):
        line = line.strip()
        if not line:
            continue
            
        # 各パターンでマッチを試みる
        for pattern in race_patterns:
            match = re.search(pattern, line)
            if match:
                result = match.group(0)
                # 余分な空白を削除
                result = re.sub(r'\s+', '', result)
                # 半角・全角の正規化
                result = result.replace('［', '[').replace('］', ']')
                # 括弧内の余分なスペースを削除
                result = re.sub(r'\[\s*', '[', result)
                result = re.sub(r'\s*\]', ']', result)
                result = re.sub(r'\s*-\s*', '-', result)
                
                # 結果が有効な形式か確認（例: 数字戦数字勝[数字-数字-数字-数字]）
                if re.match(r'^\d+戦\d+勝\[\d+-\d+-\d+-\d+\]$', result) or result == '未出走':
                    return result
    
    # どのパターンにもマッチしなかった場合
    logger.warning(f"戦績パターンにマッチしませんでした: {record[:100]}...")
    return ""

def extract_race_record(html_content: str) -> str:
    """HTMLコンテンツから戦績情報を抽出し、クリーンアップします。

    Args:
        html_content (str): HTMLコンテンツ

    Returns:
        str: クリーンアップされた戦績情報（例: "3戦0勝[0-0-0-3]"）
             戦績が見つからない場合は空文字列を返します。
    """
    try:
        if not html_content or not html_content.strip():
            logger.warning("空のHTMLコンテンツが渡されました")
            return ""
            
        # デバッグ用にHTMLコンテンツの先頭500文字をログに出力
        logger.debug(f"HTMLコンテンツの先頭500文字: {html_content[:500]}...")
        
        # 1. まずタイトルタグをチェック（特殊なエンコーディングに対応）
        title_match = re.search(r'<title>(.*?)</title>', html_content, re.DOTALL)
        if title_match:
            title = title_match.group(1)
            logger.debug(f"タイトル: {title}")
            
            # タイトルに「繁殖牝馬」または「※繁殖牝馬」が含まれているかチェック
            if any(k in title for k in ['繁殖牝馬', '※繁殖牝馬', '繫殖牝馬', '※繫殖牝馬']):
                logger.info(f"タイトルに繁殖牝馬のキーワードを検出: {title}")
                return '繁殖牝馬'
                
            # タイトルに「空胎」が含まれている場合も繁殖牝馬とみなす
            if '空胎' in title:
                logger.info(f"タイトルに「空胎」を検出: {title}")
                return '繁殖牝馬'
        
        # HTMLをデコード
        decoded_content = html.unescape(html_content)
        
        # デバッグ用にデコード後のコンテンツの先頭500文字をログに出力
        logger.debug(f"デコード後のコンテンツ先頭500文字: {decoded_content[:500]}...")
        
        # 1. 馬名と性別・年齢のパターンを検索（例: アンソレイユ　　牝３歳　　※繁殖牝馬（空胎））
        horse_info_pattern = r'<h1[^>]*>([^<]+?)</h1>\s*<p[^>]*>([^<]+?)</p>'
        horse_info_match = re.search(horse_info_pattern, decoded_content, re.DOTALL)
        
        if horse_info_match:
            horse_name = horse_info_match.group(1).strip()
            horse_details = horse_info_match.group(2).strip()
            logger.debug(f"馬名: {horse_name}, 詳細: {horse_details}")
            
            # 馬名または詳細に「繁殖牝馬」が含まれているかチェック
            if any(k in horse_name for k in ['繁殖牝馬', '繫殖牝馬']) or any(k in horse_details for k in ['繁殖牝馬', '繫殖牝馬']):
                logger.info(f"繁殖牝馬と判定されました（馬名/詳細に含まれる）: {horse_name} - {horse_details}")
                return '繁殖牝馬'
        
        # 2. 馬名のみをチェック（念のため）
        horse_name_match = re.search(r'<h1[^>]*>(.*?)</h1>', decoded_content, re.DOTALL)
        if horse_name_match:
            horse_name = horse_name_match.group(1).strip()
            logger.debug(f"馬名: {horse_name}")
            if '繁殖牝馬' in horse_name:
                logger.info(f"馬名に「繁殖牝馬」が含まれています: {horse_name}")
                return '繁殖牝馬'
        
        # 3. 繁殖牝馬のチェック（受胎状況または繁殖牝馬の表記が含まれる場合）
        broodmare_keywords = ['受胎状況', '繁殖牝馬', '繁殖牝', '※繁殖', '繫殖牝馬', '繫殖牝', '※繫殖']
        
        # デコードされたコンテンツでキーワードを検索
        found_keywords = [k for k in broodmare_keywords if k in decoded_content]
        if found_keywords:
            logger.info(f"繁殖牝馬と判定されました（キーワード: {found_keywords}）")
            return '繁殖牝馬'
        else:
            # デバッグ用に最初の500文字をログに出力
            logger.debug(f"デコードされたコンテンツの先頭: {decoded_content[:500]}...")
            # ファイルに出力して完全な内容を確認
            with open('debug_decoded_content.txt', 'w', encoding='utf-8') as f:
                f.write(decoded_content)
            logger.info(f"完全なデコード済みコンテンツを debug_decoded_content.txt に保存しました")
            
        # タイトルタグ内に繁殖牝馬の表記があるか確認
        soup = BeautifulSoup(decoded_content, 'html.parser')
        title_tag = soup.find('title')
        if title_tag and any(keyword in title_tag.get_text() for keyword in broodmare_keywords):
            logger.info("タイトルから繁殖牝馬と判定されました")
            return '繁殖牝馬'
            
        # 2. まず正規表現で直接検索を試みる
        # 戦績パターン1: X戦Y勝[W-X-Y-Z]
        pattern1 = r'\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］]'
        match = re.search(pattern1, decoded_content)
        if match:
            cleaned = _clean_race_record(match.group(0))
            if cleaned:
                return cleaned
            
        # 3. 未出走のパターン
        if '未出走' in decoded_content or '未出走' in str(soup):
            return '未出走'
            
        # 3. BeautifulSoupで詳細に検索
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 3.1 テーブル内の戦績情報を探す
        for table in soup.find_all('table'):
            for row in table.find_all('tr'):
                th = row.find('th')
                if th and ('通算成績' in th.get_text() or '戦績' in th.get_text()):
                    td = row.find('td')
                    if td:
                        race_record = td.get_text(strip=True)
                        cleaned = _clean_race_record(race_record)
                        if cleaned:
                            return cleaned
        
        # 3.2 戦績表のセルを直接検索
        for td in soup.find_all('td'):
            td_text = td.get_text(strip=True)
            if '戦' in td_text and '勝' in td_text and ('[' in td_text or '［' in td_text):
                cleaned = _clean_race_record(td_text)
                if cleaned:
                    return cleaned
        
        # 4. テキスト全体から直接検索を試みる
        text = soup.get_text(' ', strip=True)
        
        # 戦績パターン1: X戦Y勝[W-X-Y-Z]
        match = re.search(pattern1, text)
        if match:
            cleaned = _clean_race_record(match.group(0))
            if cleaned:
                return cleaned
            
        # 戦績パターン2: X戦Y勝（より緩いパターン）
        pattern2 = r'\d+戦\d+勝'
        match = re.search(pattern2, decoded_content)
        if match:
            cleaned = _clean_race_record(match.group(0))
            if cleaned:
                return cleaned
            
        logger.warning("戦績情報が見つかりませんでした")
        return ""
        
    except Exception as e:
        logger.error(f"戦績情報の抽出中にエラーが発生しました: {str(e)}")
        return ""

def _clean_race_record(record: str) -> str:
    """戦績情報をクリーンアップします。
    
    Args:
        record (str): 抽出された戦績情報
        
    Returns:
        str: クリーンアップされた戦績情報
    """
    if not record:
        return ""
    
    # 前後の空白を削除
    record = record.strip()
    
    # 戦績パターン1: X戦Y勝[W-X-Y-Z] パターン
    pattern1 = r'(\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］])'
    match = re.search(pattern1, record)
    if match:
        # マッチした部分だけを取得
        cleaned = match.group(1)
        # 余分な空白を正規化
        cleaned = re.sub(r'\s+', '', cleaned)
        # 全角括弧を半角に統一
        cleaned = cleaned.replace('［', '[').replace('］', ']')
        # 括弧内の余分なスペースを削除
        cleaned = re.sub(r'\[\s*', '[', cleaned)
        cleaned = re.sub(r'\s*\]', ']', cleaned)
        cleaned = re.sub(r'\s*-\s*', '-', cleaned)
        
        # 結果が有効な形式か確認（例: 数字戦数字勝[数字-数字-数字-数字]）
        if re.match(r'^\d+戦\d+勝\[\d+-\d+-\d+-\d+\]$', cleaned):
            return cleaned
    
    # 戦績パターン2: X戦Y勝 パターン（より緩いパターン）
    pattern2 = r'(\d+戦\d+勝)'
    match = re.search(pattern2, record)
    if match:
        # マッチした部分だけを返す
        return match.group(1)
        
    # 未出走パターン
    if '未出走' in record:
        return '未出走'
        
    logger.warning(f"戦績パターンにマッチしませんでした: {record[:100]}...")
    return ""

def extract_race_record_from_file(file_path: str) -> str:
    """ファイルから戦績情報を抽出します。

    Args:
        file_path (str): HTMLファイルのパス

    Returns:
        str: 抽出された戦績情報
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        return extract_race_record(html_content)
    except Exception as e:
        logger.error(f"ファイルの読み込み中にエラーが発生しました: {str(e)}")
        return ""

def test_extract_race_record():
    """戦績情報の抽出をテストします。"""
    test_cases = [
        # 通常のテストケース
        ("3戦0勝［0-0-0-3］", "3戦0勝［0-0-0-3］"),
        ("5戦2勝［2-0-1-2］", "5戦2勝［2-0-1-2］"),
        ("10戦3勝［3-1-2-4］", "10戦3勝［3-1-2-4］"),
        ("未出走", "未出走"),
        ("1戦1勝［1-0-0-0］", "1戦1勝［1-0-0-0］"),
        
        # 余分な情報が含まれるケース
        ("1戦1勝［1-0-0-0］ 最終出走馬体重：424kg 中央獲得賞金：0.0万円", "1戦1勝［1-0-0-0］"),
        ("2戦1勝［1-0-0-1］ 地方獲得賞金：250.0万円", "2戦1勝［1-0-0-1］"),
        ("3戦2勝［2-0-0-1］ その他の情報", "3戦2勝［2-0-0-1］"),
        
        # 実際の例
        ("1戦1勝［1-0-0-0］　　　　最終出走馬体重：424kg\n中央獲得賞金：0.0万円　　　地方獲得賞金：250.0万円競走成績を検索本馬について父ミスチヴィアスアレックスは...", "1戦1勝［1-0-0-0］"),
    ]
    
    for i, (html, expected) in enumerate(test_cases, 1):
        result = extract_race_record(html)
        status = "✓" if result == expected else "✗"
        print(f"テスト {i}: {status}")
        print(f"  期待: {expected}")
        print(f"  結果: {result}")
        print()

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) > 1:
        # ファイルパスが指定された場合はそのファイルを処理
        file_path = sys.argv[1]
        race_record = extract_race_record_from_file(file_path)
        print(f"戦績情報: {race_record}")
    else:
        # テストを実行
        print("戦績情報抽出のテストを実行します...")
        test_extract_race_record()
