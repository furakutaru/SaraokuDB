#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os

# scriptsディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from extract_race_record import extract_race_record

def test_broodmare_variations():
    print("--- 繁殖牝馬のバリアントテスト（繫 vs 繁） ---")
    
    test_cases = [
        {
            "name": "通常の繁体字（タイトル）",
            "html": "<title>ナツハヨル | 繁殖牝馬 | サラブレッドオークション</title>",
            "expected": "繁殖牝馬"
        },
        {
            "name": "バリアント（タイトル: 繫）",
            "html": "<title>ナツハヨル | 繫殖牝馬 | サラブレッドオークション</title>",
            "expected": "繁殖牝馬"
        },
        {
            "name": "バリアント（タイトル: ※繫殖牝馬）",
            "html": "<title>ナツハヨル | ※繫殖牝馬 | サラブレッドオークション</title>",
            "expected": "繁殖牝馬"
        },
        {
            "name": "バリアント（馬名セクション: 繫殖牝馬）",
            "html": "<h1>ナツハヨル</h1><p>牝10歳　繫殖牝馬（空胎）</p>",
            "expected": "繁殖牝馬"
        },
        {
            "name": "バリアント（本文キーワード: 繫殖牝）",
            "html": "<div>状態：繫殖牝として繋養中</div>",
            "expected": "繁殖牝馬"
        }
    ]
    
    success_count = 0
    for case in test_cases:
        result = extract_race_record(case["html"])
        if result == case["expected"]:
            print(f"[SUCCESS] {case['name']}: '{result}' (期待値通り)")
            success_count += 1
        else:
            print(f"[FAILURE] {case['name']}: '{result}' (期待値: '{case['expected']}')")
            
    print(f"\n結果: {success_count}/{len(test_cases)} テスト成功")
    return success_count == len(test_cases)

if __name__ == "__main__":
    test_broodmare_variations()
