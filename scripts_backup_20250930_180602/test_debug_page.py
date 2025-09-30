#!/usr/bin/env python3
"""
debug_page.html に対して血統情報抽出をテストするスクリプト
"""
import re
from pathlib import Path
from bs4 import BeautifulSoup

class PedigreeExtractor:
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
    
    def extract_from_file(self, file_path: str) -> dict:
        """HTMLファイルから血統情報を抽出"""
        result = {
            'sire': '',
            'dam': '',
            'damsire': '',
            'dam_sire': ''  # 互換性のため
        }
        
        # ファイルを読み込む
        with open(file_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        # BeautifulSoupでパース
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 1. <pre>タグから抽出を試みる
        pre_tag = soup.find('pre')
        if pre_tag:
            pre_text = pre_tag.get_text()
            print("[デバッグ] <pre>タグから抽出を試みます...")
            extracted = self._extract_from_text(pre_text)
            if extracted:
                return extracted
        
        # 2. <div class="horse-info">から抽出を試みる
        horse_info = soup.find('div', class_='horse-info')
        if horse_info:
            print("[デバッグ] <div class=\"horse-info\">から抽出を試みます...")
            for p in horse_info.find_all('p'):
                extracted = self._extract_from_text(p.get_text())
                if extracted:
                    return extracted
        
        # 3. ページ全体から抽出を試みる
        print("[デバッグ] ページ全体から抽出を試みます...")
        return self._extract_from_text(html_content)
    
    def _extract_from_text(self, text: str) -> dict:
        """テキストから血統情報を抽出"""
        result = {
            'sire': '',
            'dam': '',
            'damsire': '',
            'dam_sire': ''
        }
        
        # パターン1: 完全な形式で一度に抽出を試みる
        full_pattern = r'父[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*母[：:]([^\n\r\s][^\n\r：:]*)[\s\u3000]*(?:母の?父|母父)[：:]([^\n\r\s][^\n\r：:]*)'
        full_match = re.search(full_pattern, text)
        
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
        
        found_any = False
        for pattern, key in patterns:
            match = re.search(pattern, text)
            if match:
                value = self._clean_horse_name(match.group(1).strip())
                result[key] = value
                if key == 'damsire':
                    result['dam_sire'] = value  # 互換性のため
                found_any = True
                print(f"[デバッグ] {key} を抽出: {value}")
        
        return result if found_any else {}

def main():
    # テストファイルのパス
    debug_file = Path("../debug_page.html")
    
    if not debug_file.exists():
        print(f"エラー: {debug_file} が見つかりません")
        return
    
    print(f"[情報] {debug_file} から血統情報を抽出します...")
    
    # 抽出を実行
    extractor = PedigreeExtractor()
    result = extractor.extract_from_file(debug_file)
    
    # 結果を表示
    print("\n=== 抽出結果 ===")
    print(f"父: {result.get('sire', '(抽出できませんでした)')}")
    print(f"母: {result.get('dam', '(抽出できませんでした)')}")
    print(f"母父: {result.get('damsire', '(抽出できませんでした)')}")

if __name__ == "__main__":
    main()
