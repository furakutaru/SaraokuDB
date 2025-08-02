#!/usr/bin/env python3
# 血統情報抽出のテストスクリプト

import sys
import os
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

# テスト用のダミークラス
def create_test_horse_data():
    """テスト用の馬データを生成"""
    return {
        'id': 'test123',
        'name': 'テスト馬',
        'sex': '牡',
        'age': 5,
        'sire': 'テスト父',
        'dam': 'テスト母',
        'damsire': 'テスト母父',
        'weight': '450',
        'seller': 'テスト牧場',
        'auction_date': '2025-08-01',
        'comment': 'テストコメント',
        'disease_tags': ''
    }

def test_extract_pedigree():
    """血統情報抽出のテストを実行"""
    from backend.scrapers.rakuten_scraper import RakutenAuctionScraper
    
    # テストケース
    test_cases = [
        {
            'input': '父：イスラボニータ　母：ハイエストクイーン　母の父：シンボリクリスエス',
            'expected': {
                'sire': 'イスラボニータ',
                'dam': 'ハイエストクイーン',
                'damsire': 'シンボリクリスエス'
            }
        },
        {
            'input': '父：ディープインパクト 母：ウインドインハーヘア 母の父：Alzao',
            'expected': {
                'sire': 'ディープインパクト',
                'dam': 'ウインドインハーヘア',
                'damsire': 'Alzao'
            }
        },
        {
            'input': '父：キングカメハメハ　母：マンファス　母の父：Last Tycoon',
            'expected': {
                'sire': 'キングカメハメハ',
                'dam': 'マンファス',
                'damsire': 'Last Tycoon'  # スペースを含む名前もそのまま取得
            }
        },
        {
            'input': '父：ロードカナロア　母：レディブラッサム　母の父：Storm Cat',
            'expected': {
                'sire': 'ロードカナロア',
                'dam': 'レディブラッサム',
                'damsire': 'Storm Cat'  # スペースを含む名前もそのまま取得
            }
        },
        {
            'input': '父：キズナ　母：キャットクイル　母の父：Storm Cat',
            'expected': {
                'sire': 'キズナ',
                'dam': 'キャットクイル',
                'damsire': 'Storm Cat'  # スペースを含む名前もそのまま取得
            }
        },
        {
            'input': '父：ディープインパクト(7冠馬) 母：ウインドインハーヘア(重賞馬) 母の父：Alzao(海外馬)',
            'expected': {
                'sire': 'ディープインパクト',
                'dam': 'ウインドインハーヘア',
                'damsire': 'Alzao'
            }
        },
        {
            'input': '父：サンデーサイレンス　母：ウインドインハーヘア　母の父：Halo',
            'expected': {
                'sire': 'サンデーサイレンス',
                'dam': 'ウインドインハーヘア',
                'damsire': 'Halo'
            }
        },
        {
            'input': '父：キタサンブラック　母：シュガーハート　母の父：In Excess',
            'expected': {
                'sire': 'キタサンブラック',
                'dam': 'シュガーハート',
                'damsire': 'In Excess'  # スペースを含む名前もそのまま取得
            }
        },
        {
            'input': '父：ドゥラメンテ　母：キストゥヘヴン　母の父：King Kamehameha',
            'expected': {
                'sire': 'ドゥラメンテ',
                'dam': 'キストゥヘヴン',
                'damsire': 'King Kamehameha'  # スペースを含む名前もそのまま取得
            }
        },
        {
            'input': '父：ブリックスアンドモルタル　母：ビワハイジ　母の父：Sunday Silence',
            'expected': {
                'sire': 'ブリックスアンドモルタル',
                'dam': 'ビワハイジ',
                'damsire': 'Sunday Silence'  # スペースを含む名前もそのまま取得
            }
        }
    ]
    
    # テスト実行
    scraper = RakutenAuctionScraper()
    passed = 0
    failed = 0
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\n--- テストケース {i} ---")
        print(f"入力: {test_case['input']}")
        
        # ダミーのBeautifulSoupオブジェクトを作成
        class DummySoup:
            def __init__(self, text):
                self._text = text
            def get_text(self, *args, **kwargs):
                return self._text
            def find(self, *args, **kwargs):
                return None
            def find_all(self, *args, **kwargs):
                return []
        
        soup = DummySoup(test_case['input'])
        
        try:
            # 血統情報を抽出
            result = scraper._extract_pedigree_from_page(soup)
            print(f"結果: {result}")
            
            # 検証
            is_passed = all(
                result[key] == test_case['expected'][key]
                for key in ['sire', 'dam', 'damsire']
            )
            
            if is_passed:
                print("✅ 成功")
                passed += 1
            else:
                print(f"❌ 失敗: 期待値 {test_case['expected']}")
                failed += 1
                
        except Exception as e:
            print(f"❌ エラー: {str(e)}")
            failed += 1
    
    # テスト結果のサマリーを表示
    print("\n=== テスト結果 ===")
    print(f"合計: {len(test_cases)}件")
    print(f"成功: {passed}件")
    print(f"失敗: {failed}件")
    
    if failed == 0:
        print("\n🎉 すべてのテストが成功しました！")
    else:
        print(f"\n⚠️ {failed}件のテストが失敗しました。")

if __name__ == "__main__":
    test_extract_pedigree()
