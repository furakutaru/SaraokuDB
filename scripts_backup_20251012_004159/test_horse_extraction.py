#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import logging
from bs4 import BeautifulSoup
from components.horse_info_extractor import HorseInfoExtractor

# ログ設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)  # 標準出力にログを表示
    ]
)

# テスト用のHTML
TEST_HTML = """
<div data-v-a815ad89="">
    <div data-v-4bfd299b="" data-v-a815ad89="" class="horseLabelWrapper" style="margin-right: 24px;">
        <div data-v-4bfd299b="" class="horseLabelWrapper__horseAge">2歳</div>
        <div data-v-4bfd299b="" style="background-color: rgb(123, 211, 255);" class="horseLabelWrapper__horseSex">牡</div>
    </div>
</div>
"""

def test_horse_extraction():
    import sys
    print("テストを開始します...", flush=True)
    
    # HTMLをパース
    print("\nHTMLをパース中...", flush=True)
    soup = BeautifulSoup(TEST_HTML, 'html.parser')
    print(f"パースされたHTML: {soup.prettify()}", flush=True)
    
    # 抽出を実行
    print("\n性別と年齢の抽出を開始します...", flush=True)
    extractor = HorseInfoExtractor()
    result = extractor._extract_sex_and_age(soup)
    
    # 結果を表示
    print("\n=== 抽出結果 ===", flush=True)
    print(f"性別: {result.get('sex', '取得できませんでした')}", flush=True)
    print(f"年齢: {result.get('age', '取得できませんでした')}", flush=True)
    
    # 検証
    assert 'sex' in result, "性別が抽出できていません"
    assert 'age' in result, "年齢が抽出できていません"
    assert result['sex'] == '牡', f"性別が正しく抽出されていません: {result.get('sex')}"
    assert result['age'] == 2, f"年齢が正しく抽出されていません: {result.get('age')}"
    
    print("\nテストが正常に完了しました！", flush=True)
    return result

if __name__ == "__main__":
    try:
        result = test_horse_extraction()
        sys.exit(0)
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)
