#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
import logging
from pathlib import Path

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# テスト対象のモジュールから関数をインポート
from scripts.process_horse_details import _extract_comment, _extract_disease_tags

def test_disease_extraction(html_file):
    """
    指定されたHTMLファイルからコメントを抽出し、病気タグを検出するテストを実行
    
    Args:
        html_file (str): テストするHTMLファイルのパス
    """
    try:
        # HTMLファイルを読み込む
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # コメントを抽出
        comment = _extract_comment(html_content)
        print(f"\n{'='*50}")
        print(f"ファイル: {os.path.basename(html_file)}")
        print(f"{'='*50}")
        
        if not comment:
            print("コメントは見つかりませんでした。")
            return
            
        # コメントの一部を表示（最初の200文字）
        print("\n=== 抽出されたコメント（一部） ===")
        preview = comment[:200] + ("..." if len(comment) > 200 else "")
        print(f"{preview}")
        print(f"コメントの長さ: {len(comment)}文字")
        
        # 病気タグを抽出
        disease_tags = _extract_disease_tags(comment)
        print("\n=== 検出された病気タグ ===")
        if disease_tags == "なし":
            print("病気タグは見つかりませんでした。")
        else:
            print(f"検出されたタグ: {disease_tags}")
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {e}", exc_info=True)

def main():
    # テスト用のHTMLファイルを指定
    test_files = [
        "/Users/yum.ishii/SaraokuDB/cache/20250818/details/sess_1755492270_item_14705.html",
        "/Users/yum.ishii/SaraokuDB/cache/20250817/details/sess_1755447898_item_14703.html",
        # 必要に応じて他のテストファイルを追加
    ]
    
    for test_file in test_files:
        if os.path.exists(test_file):
            test_disease_extraction(test_file)
        else:
            print(f"ファイルが見つかりません: {test_file}")

if __name__ == "__main__":
    main()
