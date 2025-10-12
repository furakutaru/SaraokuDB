#!/usr/bin/env python3
"""
レース記録抽出機能の単体テストスクリプト

使い方:
    python -m scripts.test_race_record_extraction_standalone
"""

import sys
import os
import json
from pathlib import Path
from bs4 import BeautifulSoup

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.race_record_extractor import RaceRecordExtractor

def test_race_record_extraction():
    """キャッシュからレース記録の抽出をテストする"""
    # テスト対象のディレクトリパス
    test_dir = Path("html_dump/details")
    
    if not test_dir.exists():
        print(f"エラー: テストディレクトリが見つかりません: {test_dir}")
        return
    
    # HTMLファイルの一覧を取得
    html_files = sorted(list(test_dir.glob("*.html")))
    
    if not html_files:
        print(f"エラー: HTMLファイルが見つかりません: {cache_dir}")
        return
    
    print(f"見つかったHTMLファイル: {len(html_files)}件")
    print("全てのファイルをテストします...\n")
    
    # 抽出器を初期化
    extractor = RaceRecordExtractor()
    
    # 全てのファイルを処理
    for i, html_file in enumerate(html_files, 1):
        print(f"--- テスト {i} ---")
        print(f"\n--- ファイル {i}/{len(html_files)}: {html_file.name} ---")
        
        try:
            # HTMLファイルを読み込み
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # レース記録を抽出
            race_data, success = extractor.extract(html_content)
            
            if success:
                print("✅ レース記録の抽出に成功しました")
                print("抽出結果:")
                print(json.dumps(race_data, ensure_ascii=False, indent=2))
            else:
                print("❌ レース記録の抽出に失敗しました")
                
                # デバッグ用にHTMLの一部を表示
                soup = BeautifulSoup(html_content, 'html.parser')
                pre_tag = soup.find('pre')
                if pre_tag:
                    print("\n<pre>タグの内容:")
                    print(pre_tag.get_text()[:200] + "...")
                else:
                    print("<pre>タグが見つかりませんでした")
            
        except Exception as e:
            print(f"エラーが発生しました: {str(e)}")
        
        print("\n" + "="*80 + "\n")

if __name__ == "__main__":
    test_race_record_extraction()
