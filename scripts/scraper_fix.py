#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Fix for the improved_scraper.py file
"""

def fix_scraper_file(input_file, output_file):
    """Fix the scrape_horse_list method in the input file and save to output file."""
    with open(input_file, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    # Find the start of the scrape_horse_list method
    start_line = -1
    for i, line in enumerate(lines):
        if 'def scrape_horse_list' in line:
            start_line = i
            break
    
    if start_line == -1:
        print("Error: Could not find scrape_horse_list method in the file.")
        return False
    
    # Find the end of the scrape_horse_list method
    end_line = -1
    indent = None
    for i in range(start_line + 1, len(lines)):
        # Skip empty lines at the start
        if not lines[i].strip() and indent is None:
            continue
            
        # Determine the indentation of the method body
        if indent is None and lines[i].strip():
            indent = len(lines[i]) - len(lines[i].lstrip())
            
        # Check for the end of the method (same indentation as the def line)
        if lines[i].strip() and len(lines[i]) - len(lines[i].lstrip()) == len(lines[start_line]) - len(lines[start_line].lstrip()) and i > start_line + 1:
            end_line = i - 1
            break
    
    if end_line == -1:
        end_line = len(lines) - 1
    
    # Create the fixed method content
    fixed_method = """    def scrape_horse_list(self, url: str = None, use_cache: bool = False) -> List[Dict[str, Any]]:
        """馬の一覧をスクレイピングする
        
        Args:
            url: スクレイピング対象のURL（Noneの場合はベースURLを使用）
            use_cache: キャッシュを使用するかどうか
            
        Returns:
            List[Dict[str, Any]]: 馬情報のリスト
        """
        if self.test_mode:
            self.logger.info("テストモード: サンプルデータを返します")
            return [
                {
                    "id": "test1",
                    "name": "テスト馬1",
                    "sire": "テスト父",
                    "dam": "テスト母",
                    "damsire": "テスト母父",
                    "sex": "牡",
                    "age": 3,
                    "seller": "テスト牧場",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/1"
                },
                {
                    "id": "test2",
                    "name": "テスト馬2",
                    "sire": "テスト父2",
                    "dam": "テスト母2",
                    "damsire": "テスト母父2",
                    "sex": "牝",
                    "age": 2,
                    "seller": "テスト牧場2",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/2"
                },
                {
                    "id": "test3",
                    "name": "テスト馬3",
                    "sire": "テスト父3",
                    "dam": "テスト母3",
                    "damsire": "テスト母父3",
                    "sex": "セ",
                    "age": 4,
                    "seller": "テスト牧場3",
                    "auction_date": datetime.now().strftime("%Y-%m-%d"),
                    "detail_url": f"{self.base_url}detail/3"
                }
            ]
            
        # 実際のスクレイピング処理を呼び出す
        return self._scrape_horse_list(url=url, use_cache=use_cache)
"""
    
    # Replace the method in the original content
    fixed_lines = lines[:start_line] + [fixed_method] + lines[end_line + 1:]
    
    # Write the fixed content to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        f.writelines(fixed_lines)
    
    return True

if __name__ == "__main__":
    import sys
    
    if len(sys.argv) != 3:
        print("Usage: python fix_scraper.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if fix_scraper_file(input_file, output_file):
        print(f"Successfully fixed {input_file} and saved to {output_file}")
    else:
        print("Failed to fix the file.")
        sys.exit(1)
