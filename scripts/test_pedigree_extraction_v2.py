#!/usr/bin/env python3
"""
血統情報抽出のテストスクリプト（v2）
更新された _extract_pedigree_from_page メソッドをテストします
"""
import sys
import os
from pathlib import Path
import re
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
    
    def _extract_pedigree_from_page(self, soup) -> dict:
        """
        ページから血統情報（父、母、母父）を抽出する（更新版）
        """
        result = {
            'sire': '不明',
            'dam': '不明',
            'damsire': '不明',
            'dam_sire': '不明'  # 互換性のため
        }
        
        try:
            # 1. テーブルから血統情報を探す
            tables = soup.find_all('table')
            for table in tables:
                rows = table.find_all('tr')
                for row in rows:
                    text = row.get_text(separator=' ', strip=True)
                    if '父：' in text and '母：' in text and '母の父：' in text:
                        # パターン1: 父：XXX 母：YYY 母の父：ZZZ 形式
                        pattern1 = r'父：([^\n\r：:（）(]+?)(?:\s*[（(]|$|\s+)(?:母：|母[^：:]*?[：:])([^\n\r：:（(]+?)(?:\s*[（(]|$|\s+)(?:母の父[：:]?|母父[：:]?|母の父[^：:]*?[：:])([^\n\r）)\s,，、]+)'
                        match = re.search(pattern1, text)
                        if match:
                            result['sire'] = self._clean_horse_name(match.group(1).strip())
                            result['dam'] = self._clean_horse_name(match.group(2).strip())
                            result['damsire'] = self._clean_horse_name(match.group(3).strip())
                            result['dam_sire'] = result['damsire']
                            print(f"[デバッグ] テーブルから血統情報を抽出: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
                            return result
            
            # 2. ページ全体のテキストから抽出を試みる
            page_text = soup.get_text(separator=' ', strip=True)
            
            # パターン2: 父：XXX 母：YYY 母の父：ZZZ 形式（改行含む）
            pattern2 = r'父[：:]([^\n\r：:（）(]+?)(?:\s*[（(]|$|\s+)(?:母：|母[^：:]*?[：:])([^\n\r：:（(]+?)(?:\s*[（(]|$|\s+)(?:母の父[：:]?|母父[：:]?|母の父[^：:]*?[：:])([^\n\r）)\s,，、]+)'
            match = re.search(pattern2, page_text)
            if match:
                result['sire'] = self._clean_horse_name(match.group(1).strip())
                result['dam'] = self._clean_horse_name(match.group(2).strip())
                result['damsire'] = self._clean_horse_name(match.group(3).strip())
                result['dam_sire'] = result['damsire']
                print(f"[デバッグ] ページ全体から血統情報を抽出: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
                return result
            
            # 3. 個別のパターンで抽出を試みる
            patterns = [
                (r'父[：:]([^\n\r：:（）(]+?)(?:\s*[（(]|$|\s+)', 'sire'),
                (r'母[：:]([^\n\r：:（(]+?)(?=\s*[（(]|\s*$|\s+母(?:の)?父)', 'dam'),
                (r'(?:母の?父|母父)[：:]([^\n\r）)\s,，、]+)', 'damsire'),
                (r'母[：:]([^\n\r：:（(]+?)\s+母(?:の)?父[：:]?\s*([^\n\r\s,，、]+)', 'damsire_with_dam')
            ]
            
            for pattern, key in patterns:
                match = re.search(pattern, page_text)
                if match:
                    if key == 'damsire_with_dam' and (not result.get('dam') or not result.get('damsire')):
                        if not result.get('dam'):
                            result['dam'] = self._clean_horse_name(match.group(1).strip())
                        if not result.get('damsire'):
                            result['damsire'] = self._clean_horse_name(match.group(2).strip())
                            result['dam_sire'] = result['damsire']
                        print(f"[デバッグ] dam を抽出: {result.get('dam', 'N/A')}")
                        print(f"[デバッグ] damsire を抽出: {result.get('damsire', 'N/A')}")
                    elif key in ['sire', 'dam', 'damsire'] and (not result.get(key, '').strip() or result.get(key) == '不明'):
                        result[key] = self._clean_horse_name(match.group(1).strip())
                        if key == 'damsire':
                            result['dam_sire'] = result['damsire']
                        print(f"[デバッグ] {key} を抽出: {result[key]}")
            
            # 4. まだ damsire が取得できていない場合、dam フィールドから抽出を試みる
            if (not result.get('damsire') or result.get('damsire') == '不明') and result.get('dam'):
                # パターン: 「母名 母父：母父名」または「母名 母父名」
                patterns = [
                    r'^(.+?)\s+母(?:の)?父[：:]?\s*([^\s,，、]+)',
                    r'^(.+?)\s+([^\s,，、]+)\s*$'
                ]
                
                for pattern in patterns:
                    match = re.search(pattern, result['dam'])
                    if match:
                        new_dam = self._clean_horse_name(match.group(1).strip())
                        new_damsire = self._clean_horse_name(match.group(2).strip())
                        if new_dam and new_damsire and new_damsire not in ['不明', '']:
                            print(f"[デバッグ] 母名から分離: dam='{new_dam}', damsire='{new_damsire}'")
                            result['dam'] = new_dam
                            result['damsire'] = new_damsire
                            result['dam_sire'] = new_damsire
                            break
            
            # 5. 結果を返す前に不要な空白や改行を削除
            for key in ['sire', 'dam', 'damsire']:
                if result.get(key) and result[key] != '不明':
                    result[key] = re.sub(r'\s+', ' ', str(result[key])).strip()
            
            # 6. デバッグ情報を出力
            print(f"[デバッグ] 最終的な血統情報: sire={result['sire']}, dam={result['dam']}, damsire={result['damsire']}")
            
            return result
            
        except Exception as e:
            print(f"血統情報の抽出中にエラーが発生しました: {str(e)}")
            import traceback
            traceback.print_exc()
            return result

def load_test_html(filepath):
    """テスト用のHTMLファイルを読み込む"""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"ファイルの読み込み中にエラーが発生しました: {e}")
        return None

def test_pedigree_extraction(html_content):
    """血統情報の抽出をテストする"""
    soup = BeautifulSoup(html_content, 'html.parser')
    scraper = MockScraper()
    
    print("\n" + "="*80)
    print("血統情報の抽出を開始します...")
    print("="*80)
    
    # 血統情報を抽出
    pedigree = scraper._extract_pedigree_from_page(soup)
    
    print("\n" + "="*80)
    print("抽出結果:")
    print(f"父: {pedigree['sire']}")
    print(f"母: {pedigree['dam']}")
    print(f"母父: {pedigree['damsire']}")
    print("="*80 + "\n")
    
    return pedigree

def main():
    # テスト用のHTMLファイルパスを指定（キャッシュディレクトリから最初の5つのファイルを使用）
    cache_dir = Path("cache/20250822_190555/details")
    test_files = sorted(cache_dir.glob("*.html"))[:5]  # 最初の5つのHTMLファイルを使用
    
    for filepath in test_files:
        if not os.path.exists(filepath):
            print(f"エラー: ファイルが見つかりません: {filepath}")
            continue
            
        print(f"\n{'='*80}")
        print(f"テストファイル: {filepath}")
        print(f"{'='*80}")
        
        # HTMLファイルを読み込む
        html_content = load_test_html(filepath)
        if html_content:
            test_pedigree_extraction(html_content)

if __name__ == "__main__":
    main()
