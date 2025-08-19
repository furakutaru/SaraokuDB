#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from bs4 import BeautifulSoup
import re
from typing import Optional, Dict, Any

# カスタムモジュールから関数をインポート
from extract_race_record import extract_race_record as extract_race_record_module

# ロギング設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# 戦績情報の正規表現パターン
RACE_RECORD_PATTERN = re.compile(
    r'(\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］])|(未出走)',
    re.IGNORECASE | re.UNICODE
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

def extract_race_record(html_content: str) -> str:
    """HTMLコンテンツから戦績情報を抽出し、クリーンアップします。

    Args:
        html_content (str): HTMLコンテンツ

    Returns:
        str: クリーンアップされた戦績情報（例: "3戦0勝[0-0-0-3]"）
             戦績が見つからない場合は空文字列を返します。
    """
    if not html_content:
        logger.warning("HTMLコンテンツが空です")
        return ""

    try:
        # 1. まず正規表現で直接検索を試みる
        # 戦績パターン1: X戦Y勝[W-X-Y-Z]
        pattern1 = r'\d+戦\d+勝\s*[\[［]\s*\d+\s*-\s*\d+\s*-\s*\d+\s*-\s*\d+\s*[\]］]'
        match = re.search(pattern1, html_content)
        if match:
            cleaned = _clean_race_record(match.group(0))
            if cleaned:
                return cleaned
            
        # 2. 未出走のパターン
        if '未出走' in html_content:
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
        match = re.search(pattern2, text)
        if match:
            cleaned = _clean_race_record(match.group(0))
            if cleaned:
                return cleaned
            
        logger.warning("戦績情報が見つかりませんでした")
        return ""
        
    except Exception as e:
        logger.error(f"戦績情報の抽出中にエラーが発生しました: {str(e)}")
        return ""

def test_extraction(path: str):
    """
    指定されたパス（ファイルまたはディレクトリ）内のHTMLファイルに対して戦績抽出をテストします。
    
    Args:
        path: テストするHTMLファイルまたはHTMLファイルを含むディレクトリのパス
    """
    # テスト結果を保存するリスト
    results = []
    
    # 引数がファイルかディレクトリかを判定
    if os.path.isfile(path) and path.endswith('.html'):
        # 単一ファイルの場合
        files_to_process = [path]
    elif os.path.isdir(path):
        # ディレクトリ内のHTMLファイルを処理
        files_to_process = [
            os.path.join(path, f) 
            for f in os.listdir(path) 
            if f.endswith('.html')
        ]
    else:
        logger.error(f"無効なパスまたはファイル形式です: {path}")
        return []
    
    if not files_to_process:
        logger.warning(f"処理対象のHTMLファイルが見つかりません: {path}")
        return []
    
    # ファイルを処理
    for filepath in files_to_process:
        filename = os.path.basename(filepath)
        logger.info(f"処理中: {filepath}")
        
        try:
            # HTMLファイルをバイナリモードで読み込む
            with open(filepath, 'rb') as f:
                html_content = f.read().decode('utf-8', errors='replace')
            
            # デバッグ用にHTMLコンテンツをファイルに保存
            debug_file = os.path.join(os.path.dirname(filepath), f'debug_{os.path.basename(filepath)}.txt')
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_content)
            logger.debug(f"HTMLコンテンツを {debug_file} に保存しました")
            
            # モジュールから関数をインポートして戦績情報を抽出
            race_record = extract_race_record_module(html_content)
            
            # 結果を保存
            results.append({
                'file': filename,
                'race_record': race_record,
                'has_record': bool(race_record)
            })
            
            logger.info(f"抽出結果: {race_record}")
            
        except Exception as e:
            filename = os.path.basename(filepath) if 'filepath' in locals() else 'unknown'
            logger.error(f"{filename} の処理中にエラーが発生しました: {str(e)}")
            results.append({
                'file': filename,
                'error': str(e),
                'has_record': False
            })
    
    # 結果を表示
    print("\n=== テスト結果のサマリー ===")
    total = len(results)
    success = sum(1 for r in results if r.get('has_record', False))
    
    print(f"処理ファイル数: {total}")
    print(f"戦績抽出成功: {success} ファイル")
    print(f"戦績抽出失敗: {total - success} ファイル")
    
    if total > 0:
        print(f"\n=== 抽出例 ===")
        for i, result in enumerate(results[:5]):  # 最初の5件を表示
            status = "成功" if result.get('has_record', False) else "失敗"
            print(f"{i+1}. {result['file']}: {status}")
            if 'race_record' in result:
                print(f"   戦績: {result['race_record']}")
            elif 'error' in result:
                print(f"   エラー: {result['error']}")
    
    # 結果をファイルに保存
    output_file = os.path.join(os.path.dirname(__file__), 'race_record_test_results.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump({
            'summary': {
                'total_files': total,
                'success': success,
                'failed': total - success,
                'success_rate': (success / total) * 100 if total > 0 else 0
            },
            'results': results
        }, f, ensure_ascii=False, indent=2)
    
    print(f"\n詳細な結果を {output_file} に保存しました。")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("使用方法: python test_race_record_extraction.py <HTMLディレクトリ>")
        sys.exit(1)
    
    test_extraction(sys.argv[1])
