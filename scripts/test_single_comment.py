#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import json
from bs4 import BeautifulSoup
from datetime import datetime

def _extract_comment(html_content):
    """
    馬の詳細ページからコメントを抽出する
    
    Args:
        html_content (str): 馬の詳細ページのHTML
        
    Returns:
        str: 抽出されたコメントテキスト。見つからない場合は空文字列。
    """
    try:
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. 「本馬について」セクションを探す
        section = None
        for elem in soup.find_all(['div', 'section', 'article']):
            if '本馬について' in elem.get_text():
                section = elem
                break
        
        if section:
            # 2. <hr>タグ以降のテキストを取得
            hr_tag = section.find('hr')
            if hr_tag:
                # <hr>以降のすべてのテキストを取得
                comment_parts = []
                for sibling in hr_tag.next_siblings:
                    if hasattr(sibling, 'get_text'):
                        text = sibling.get_text(separator=' ', strip=True)
                        if text:
                            comment_parts.append(text)
                
                if comment_parts:
                    # テキストを結合して整形
                    comment = ' '.join(comment_parts)
                    # 連続する空白を1つに置換
                    comment = ' '.join(comment.split())
                    return comment
        
        # 3. フォールバック: <pre>タグ内のテキストを取得
        pre_tag = soup.find('pre')
        if pre_tag:
            comment = pre_tag.get_text(separator='\n', strip=True)
            return ' '.join(comment.split())
        
        return ""
        
    except Exception as e:
        print(f"コメントの抽出中にエラーが発生: {e}")
        import traceback
        print(traceback.format_exc())
        return ""

def test_comment_extraction(html_file):
    """ローカルのHTMLファイルからコメントを抽出してテスト"""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # コメントを抽出
        print("コメントを抽出中...")
        comment = _extract_comment(html_content)
        
        # 結果を表示
        print("\n=== 抽出結果 ===")
        print(f"ファイル: {html_file}")
        print(f"コメントの長さ: {len(comment) if comment else 0}文字")
        print("\n=== コメント内容 ===")
        print(comment if comment else "コメントは見つかりませんでした")
        
        # 結果を辞書として返す
        return {
            "file": html_file,
            "status": "success",
            "comment_length": len(comment) if comment else 0,
            "comment": comment if comment else ""
        }
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        return {
            "file": html_file,
            "status": "error",
            "message": str(e)
        }

if __name__ == "__main__":
    if len(sys.argv) > 1:
        # コマンドライン引数からHTMLファイルを指定
        html_file = sys.argv[1]
    else:
        # デフォルトのテストファイル
        html_file = "/Users/yum.ishii/SaraokuDB/cache/20250818/details/sess_1755492270_item_14705.html"
    
    # ファイルの存在確認
    if not os.path.exists(html_file):
        print(f"エラー: ファイルが見つかりません: {html_file}")
        sys.exit(1)
    
    # テストを実行
    result = test_comment_extraction(html_file)
    
    # 結果をJSONファイルに保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comment_test_result_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nテスト結果を {output_file} に保存しました")
