#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import sys

def fix_scraper_file(input_file, output_file):
    with open(input_file, 'rb') as f:
        content = f.read()
    
    try:
        # Try to decode with UTF-8 first
        content = content.decode('utf-8')
    except UnicodeDecodeError:
        # If UTF-8 fails, try other encodings
        try:
            content = content.decode('shift_jis')
        except UnicodeDecodeError:
            try:
                content = content.decode('euc-jp')
            except UnicodeDecodeError:
                try:
                    content = content.decode('cp932')
                except UnicodeDecodeError as e:
                    print(f"Failed to decode file: {e}")
                    return False
    
    # Define the fixed method
    fixed_method = """    def scrape_horse_list(self, url: str = None, use_cache: bool = False) -> List[Dict[str, Any]]:
        \"\"\"馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 馬情報のリスト
        \"\"\"
        if self.test_mode:
            self.logger.info(\"テストモード: サンプルデータを返します\")
            return [
                {
                    \"id\": \"test1\",
                    \"name\": \"テスト馬1\",
                    \"sire\": \"テスト父\",
                    \"dam\": \"テスト母\",
                    \"damsire\": \"テスト母父\",
                    \"sex\": \"牡\",
                    \"age\": 3,
                    \"seller\": \"テスト牧場\",
                    \"auction_date\": datetime.now().strftime(\"%Y-%m-%d\"),
                    \"detail_url\": f\"{self.base_url}detail/1\"
                },
                {
                    \"id\": \"test2\",
                    \"name\": \"テスト馬2\",
                    \"sire\": \"テスト父2\",
                    \"dam\": \"テスト母2\",
                    \"damsire\": \"テスト母父2\",
                    \"sex\": \"牝\",
                    \"age\": 2,
                    \"seller\": \"テスト牧場2\",
                    \"auction_date\": datetime.now().strftime(\"%Y-%m-%d\"),
                    \"detail_url\": f\"{self.base_url}detail/2\"
                },
                {
                    \"id\": \"test3\",
                    \"name\": \"テスト馬3\",
                    \"sire\": \"テスト父3\",
                    \"dam\": \"テスト母3\",
                    \"damsire\": \"テスト母父3\",
                    \"sex\": \"セ\",
                    \"age\": 4,
                    \"seller\": \"テスト牧場3\",
                    \"auction_date\": datetime.now().strftime(\"%Y-%m-%d\"),
                    \"detail_url\": f\"{self.base_url}detail/3\"
                }
            ]
            
        # 実際のスクレイピング処理を呼び出す
        return self._scrape_horse_list(url=url, use_cache=use_cache)
"""
    
    # Use regex to find and replace the method
    pattern = r'def\s+scrape_horse_list\([\s\S]*?return\s+self\._scrape_horse_list\([^)]*\)'
    
    try:
        # Try to replace using regex
        new_content, count = re.subn(
            pattern,
            fixed_method,
            content,
            flags=re.MULTILINE
        )
        
        if count == 0:
            print("Warning: Could not find the method to replace. The file might be already fixed or the pattern doesn't match.")
        
        # Write the fixed content to the output file
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        print(f"Successfully fixed the file. Output written to {output_file}")
        return True
        
    except Exception as e:
        print(f"Error while fixing the file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python scraper_fix_v2.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not fix_scraper_file(input_file, output_file):
        sys.exit(1)
