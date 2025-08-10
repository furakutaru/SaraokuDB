#!/usr/bin/env python3
"""
血統情報抽出のテストスクリプト
"""
import sys
import os
from pathlib import Path
from bs4 import BeautifulSoup

# 親ディレクトリをパスに追加
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# テスト用のモッククラス
class MockScraper:
    def _clean_horse_name(self, name: str) -> str:
        """馬名を正規化"""
        if not name:
            return ""
        # 前後の空白を削除
        name = name.strip()
        # 全角スペースを半角に統一
        name = name.replace("　", " ")
        # 連続するスペースを1つに
        name = " ".join(name.split())
        return name
    
    def _extract_pedigree(self, page_text: str) -> dict:
        """血統情報を抽出・正規化"""
        result = {
            'sire': '',
            'dam': '',
            'damsire': '',
            'dam_sire': ''  # 互換性のため
        }
        
        # パターン1: 完全な形式で一度に抽出を試みる
        full_pattern = r'父[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*母[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*(?:母の?父|母父)[：:]([^\n\r\s][^\n\r：:]*)'
        full_match = re.search(full_pattern, page_text)
        
        if full_match:
            # 完全な形式でマッチした場合
            result['sire'] = self._clean_horse_name(full_match.group(1).strip())
            result['dam'] = self._clean_horse_name(full_match.group(2).strip())
            result['damsire'] = self._clean_horse_name(full_match.group(3).strip())
            result['dam_sire'] = result['damsire']  # 互換性のため
            print(f"[デバッグ] 完全な形式で血統情報を抽出: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
            return result
        
        # パターン2: 個別に抽出を試みる
        patterns = [
            (r'父[：:]([^\n\r\s][^\n\r：:]*)', 'sire'),
            (r'母[：:]([^\n\r\s][^\n\r：:]*)', 'dam'),
            (r'(?:母の?父|母父)[：:]([^\n\r\s][^\n\r：:]*)', 'damsire')
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, page_text)
            if match and not result.get(key):
                result[key] = self._clean_horse_name(match.group(1).strip())
                print(f"[デバッグ] {key} を抽出: {result[key]}")
        
        # 母の情報から母父を抽出する試み
        if not result.get('damsire') and result.get('dam'):
            # 母の情報に「母の父」が含まれている場合
            if '母の父' in result['dam']:
                parts = result['dam'].split('母の父')
                result['dam'] = self._clean_horse_name(parts[0].strip())
                if len(parts) > 1:
                    result['damsire'] = self._clean_horse_name(parts[1].strip())
            # 母の情報に「（母父：XXX）」が含まれている場合
            elif '（母父：' in result['dam'] or '(母父：' in result['dam']:
                dam_parts = re.split(r'[（(]母父[：:]', result['dam'])
                if len(dam_parts) > 1:
                    result['dam'] = self._clean_horse_name(dam_parts[0].strip())
                    damsire_part = dam_parts[1].replace('）', '').replace(')', '').strip()
                    result['damsire'] = self._clean_horse_name(damsire_part)
        
        # 互換性のため dam_sire にも damsire と同じ値を設定
        if result['damsire'] and not result['dam_sire']:
            result['dam_sire'] = result['damsire']
        
        print(f"[デバッグ] 最終的な血統情報: sire='{result['sire']}', dam='{result['dam']}', damsire='{result['damsire']}'")
        print("========================================")
        
        return result

# テストケース
test_cases = [
    {
        'name': '通常のケース',
        'input': '父：ディープインパクト 母：ウインドインハーヘア 母の父：サンデーサイレンス',
        'expected': {
            'sire': 'ディープインパクト',
            'dam': 'ウインドインハーヘア',
            'damsire': 'サンデーサイレンス'
        }
    },
    {
        'name': '全角コロンと半角コロン混在',
        'input': '父:キタサンブラック 母：レッドリヴェール 母父:キングカメハメハ',
        'expected': {
            'sire': 'キタサンブラック',
            'dam': 'レッドリヴェール',
            'damsire': 'キングカメハメハ'
        }
    },
    {
        'name': '母の情報に母父が含まれるケース',
        'input': '父：ゴールドシップ 母：トーセンダンス 母の父 ディープインパクト',
        'expected': {
            'sire': 'ゴールドシップ',
            'dam': 'トーセンダンス',
            'damsire': 'ディープインパクト'
        }
    },
    {
        'name': '括弧表記の母父',
        'input': '父：ロードカナロア 母：アパパネ（母父：ハーツクライ）',
        'expected': {
            'sire': 'ロードカナロア',
            'dam': 'アパパネ',
            'damsire': 'ハーツクライ'
        }
    },
    {
        'name': '複数行にまたがるケース',
        'input': '父：キズナ\n母：レッドアルテミス\n母父：シンボリクリスエス',
        'expected': {
            'sire': 'キズナ',
            'dam': 'レッドアルテミス',
            'damsire': 'シンボリクリスエス'
        }
    }
]

def run_tests():
    """テストを実行する"""
    scraper = MockScraper()
    all_passed = True
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n=== テストケース {i}: {test_case['name']} ===")
        print(f"入力: {test_case['input']}")
        
        try:
            result = scraper._extract_pedigree(test_case['input'])
            passed = True
            
            # 期待値との比較
            for key, expected_value in test_case['expected'].items():
                if result.get(key) != expected_value:
                    print(f"  ✗ {key}: 期待値='{expected_value}', 実際='{result.get(key)}'")
                    passed = False
                else:
                    print(f"  ✓ {key}: '{result.get(key)}'")
            
            if passed:
                print("  ✓ テスト成功")
            else:
                print("  ✗ テスト失敗")
                all_passed = False
                
        except Exception as e:
            print(f"  ✗ エラーが発生しました: {str(e)}")
            all_passed = False
    
    if all_passed:
        print("\n✅ すべてのテストが成功しました！")
        return True
    else:
        print("\n❌ 一部のテストが失敗しました")
        return False

if __name__ == "__main__":
    import re  # 正規表現モジュールをインポート
    run_tests()
