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
        
        # まず完全な形式で抽出を試みる
        full_pattern = r'父[：:]([^\n\r：:（）(]+?)(?:\s*[\s\u3000]|\s*[（(]|$)\s*母[：:]([^\n\r：:（(]+?)(?:\s*[（(]母父[：:]([^）)\n\r]+)[）)]|\s+母(?:の)?父[：:]?\s*([^\n\r）)\s,，、]+)|\s*$)'
        full_match = re.search(full_pattern, page_text)
        
        # 完全一致で抽出できた場合
        if full_match:
            result['sire'] = self._clean_horse_name(full_match.group(1).strip())
            result['dam'] = self._clean_horse_name(full_match.group(2).strip())
            # 母父が括弧内か別表記かでグループが異なる
            damsire = full_match.group(3) or full_match.group(4)
            if damsire:
                result['damsire'] = self._clean_horse_name(damsire.strip())
            result['dam_sire'] = result['damsire']  # 互換性のため
            print(f"[デバッグ] 完全な形式で血統情報を抽出: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
            return result
        
        
        # パターン2: 個別に抽出を試みる
        patterns = [
            # スペース区切りの母父情報用のパターン（最初にマッチさせる）
            (r'母[：:]([^\n\r：:（(]+?)\s+母(?:の)?父[：:]?\s*([^\n\r\s,，、]+)', 'damsire_with_dam'),
            # 通常のパターン
            (r'父[：:]([^\n\r：:（）(]+?)(?:\s*[（(]|$|\s)', 'sire'),
            (r'母[：:]([^\n\r：:（(]+?)(?=\s*[（(]|\s*$|\s+母(?:の)?父)', 'dam'),
            (r'(?:母の?父|母父)[：:]([^\n\r）)\s,，、]+)', 'damsire')
        ]
        
        for pattern, key in patterns:
            match = re.search(pattern, page_text)
            if match and not result.get(key):
                if key == 'damsire_with_dam':
                    # スペース区切りの母父情報の場合、damとdamsireの両方を設定
                    if not result.get('dam'):
                        result['dam'] = self._clean_horse_name(match.group(1).strip())
                    result['damsire'] = self._clean_horse_name(match.group(2).strip())
                    print(f"[デバッグ] dam を抽出: {result['dam']}")
                    print(f"[デバッグ] damsire を抽出: {result['damsire']}")
                else:
                    result[key] = self._clean_horse_name(match.group(1).strip())
                    print(f"[デバッグ] {key} を抽出: {result[key]}")
        
        # 母の情報から母父を抽出する試み
        if not result.get('damsire'):
            # 完全な形式で再度試みる
            full_pattern = r'母[：:]([^\n\r：:（(]+?)(?:\s*[（(]?母(?:の)?父[：:]([^）)\n\r]+)[）)]?|\s+母(?:の)?父[：:]?\s*([^\n\r\s,，、]+))?|母[：:]([^\n\r：:（(]+?)\s+母(?:の)?父[：:]?\s*([^\n\r\s,，、]+)'
            full_match = re.search(full_pattern, page_text)
            if full_match:
                if not result.get('dam'):
                    result['dam'] = self._clean_horse_name(full_match.group(1).strip())
                # グループ2（括弧内の母父）またはグループ3（括弧なしの母父）またはグループ5（スペース区切りの母父）から抽出
                damsire = full_match.group(2) or full_match.group(3) or full_match.group(5)
                if damsire:
                    result['damsire'] = self._clean_horse_name(damsire.strip())
                # グループ4（スペース区切りパターンの母）から dam を設定
                if full_match.group(4) and not result.get('dam'):
                    result['dam'] = self._clean_horse_name(full_match.group(4).strip())
            
            # まだ damsire が取得できていない場合、dam フィールドから抽出を試みる
            if not result.get('damsire') and result.get('dam'):
                # スペース区切りの母父情報を抽出
                space_pattern = r'^(.+?)\s+母(?:の)?父[：:]?\s*([^\s,，、]+)'
                print(f"[デバッグ] damフィールドから抽出を試みます: {result['dam']}")
                space_match = re.search(space_pattern, result['dam'])
                if space_match:
                    new_dam = self._clean_horse_name(space_match.group(1).strip())
                    new_damsire = self._clean_horse_name(space_match.group(2).strip())
                    print(f"[デバッグ] スペース区切りから抽出: dam='{new_dam}', damsire='{new_damsire}'")
                    result['dam'] = new_dam
                    result['damsire'] = new_damsire
                # 母の情報に「母の父」や「母父」が含まれる場合
                elif '母の父' in result['dam'] or '母父' in result['dam']:
                    # まず括弧内の母父情報をチェック
                    if '（母父：' in result['dam'] or '(母父：' in result['dam']:
                        dam_parts = re.split(r'[（(]母父[：:]', result['dam'])
                        if len(dam_parts) > 1:
                            result['dam'] = self._clean_horse_name(dam_parts[0].strip())
                            damsire_part = dam_parts[1].split('）')[0].split(')')[0].strip()
                            result['damsire'] = self._clean_horse_name(damsire_part)
                    else:
                        # 括弧なしの母父情報をチェック
                        if '母の父' in result['dam']:
                            parts = result['dam'].split('母の父')
                            result['dam'] = self._clean_horse_name(parts[0].strip())
                            if len(parts) > 1:
                                result['damsire'] = self._clean_horse_name(parts[1].split()[0].strip())
                        elif '母父' in result['dam']:
                            parts = result['dam'].split('母父')
                            result['dam'] = self._clean_horse_name(parts[0].strip())
                            if len(parts) > 1:
                                # 母父の後の区切り文字を考慮して抽出
                                damsire_part = re.split(r'[\s：:)]', parts[1].strip())[0]
                                result['damsire'] = self._clean_horse_name(damsire_part)
        
        # dam フィールドから余分な情報を削除
        if result.get('dam'):
            result['dam'] = re.sub(r'\s*[（(]?母(?:の)?父[^）)]*[）)]?', '', result['dam']).strip()
        
        # 互換性のため dam_sire を設定
        if result.get('damsire') and not result.get('dam_sire'):
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
        'name': '母の情報に母父が含まれるケース（スペース区切り）',
        'input': '父：ゴールドシップ 母：トーセンダンス 母の父 ディープインパクト',
        'expected': {
            'sire': 'ゴールドシップ',
            'dam': 'トーセンダンス',
            'damsire': 'ディープインパクト'
        }
    },
    {
        'name': '母の情報に母父が含まれるケース（コロン区切り）',
        'input': '父：ゴールドシップ 母：トーセンダンス 母の父：ディープインパクト',
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
        'name': '括弧表記の母父（全角括弧）',
        'input': '父：キタサンブラック 母：レッドリヴェール（母父：キングカメハメハ）',
        'expected': {
            'sire': 'キタサンブラック',
            'dam': 'レッドリヴェール',
            'damsire': 'キングカメハメハ'
        }
    },
    {
        'name': '複雑なケース',
        'input': '父：サートゥルネーション 母：ミスティックレイディ（母父：サンデーサイレンス） 母父：キングカメハメハ',
        'expected': {
            'sire': 'サートゥルネーション',
            'dam': 'ミスティックレイディ',
            'damsire': 'サンデーサイレンス'
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
