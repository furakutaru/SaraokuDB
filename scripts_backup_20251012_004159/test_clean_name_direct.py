#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys

def clean_horse_name(name):
    """馬名をクリーンアップする関数"""
    if not name:
        return "不明な馬"
    
    # コメント記号以降を削除
    name = re.sub(r'※.*$', '', name)
    # 括弧内の文字列を削除
    name = re.sub(r'\s*[（(][^）)]*[）)]', '', name)
    # 前後の空白を削除
    name = name.strip()
    # 連続する空白を1つのスペースに置換
    name = re.sub(r'\s+', ' ', name)
    
    return name if name else "不明な馬"

def run_tests():
    test_cases = [
        ("サトノダイヤモンド", "サトノダイヤモンド"),
        (" サトノダイヤモンド ", "サトノダイヤモンド"),
        ("サトノダイヤモンド※", "サトノダイヤモンド"),
        ("サトノダイヤモンド（牡3）", "サトノダイヤモンド"),
        ("サトノ ダイヤモンド", "サトノ ダイヤモンド"),
        ("サトノ　ダイヤモンド", "サトノ ダイヤモンド"),
        ("", "不明な馬"),
        (None, "不明な馬"),
        ("A" * 100, "A" * 100)
    ]
    
    with open('test_output.txt', 'w', encoding='utf-8') as f:
        f.write("=== 馬名クリーニングのテストを開始します ===\n\n")
        
        for i, (input_name, expected) in enumerate(test_cases, 1):
            result = clean_horse_name(input_name)
            status = "✓ 成功" if result == expected else f"✗ 失敗: 期待値 '{expected}' に対して実際の結果は '{result}' でした"
            
            output = f"テスト {i}:\n"
            output += f"  入力: {repr(input_name)}\n"
            output += f"  期待: {repr(expected)}\n"
            output += f"  結果: {status}\n\n"
            
            f.write(output)
            print(output, end='')
        
        f.write("=== テスト完了 ===\n")
    
    print("テスト結果を 'test_output.txt' に保存しました。")

if __name__ == "__main__":
    run_tests()
