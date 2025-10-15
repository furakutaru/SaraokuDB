import os
import sys
from bs4 import BeautifulSoup
import re
from pathlib import Path

# Import the RaceRecordExtractor
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
from scripts.race_record_extractor import RaceRecordExtractor

def extract_race_record(html_content):
    """Extract race record from HTML content using RaceRecordExtractor"""
    extractor = RaceRecordExtractor()
    result, success = extractor.extract(html_content)
    if not success:
        return {}
    
    summary = result.get('summary', {})
    
    # 繁殖牝馬の場合はstatusを設定
    if not summary and '繁殖牝馬' in html_content:
        return {'status': 'broodmare'}
        
    return summary

def main():
    cache_dir = Path('/Users/yum.ishii/SaraokuDB/cache')
    html_files = list(cache_dir.glob('*.html'))
    
    print(f"Found {len(html_files)} HTML files in cache directory")
    
    for i, html_file in enumerate(html_files, 1):
        print(f"\n--- Processing file {i}/{len(html_files)}: {html_file.name} ---")
        
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
                
            # Extract race record
            record = extract_race_record(html_content)
            
            if record:
                if record.get('status') == 'unraced':
                    print("✅ 未出走馬を検出")
                elif record.get('status') == 'broodmare':
                    print("✅ 繁殖牝馬を検出")
                else:
                    print(f"✅ レース記録を検出: {record}")
            else:
                print("ℹ️ レース記録が見つかりませんでした")
                
                # For debugging: Check if this is a horse detail page
                soup = BeautifulSoup(html_content, 'html.parser')
                pre_tag = soup.find('pre')
                if pre_tag:
                    pre_text = pre_tag.get_text()
                    if '通算成績' in pre_text:
                        print("  ℹ️ '通算成績' found in pre tag but not extracted")
                        # Print first 200 chars of pre_text for debugging
                        print(f"  Preview: {pre_text[:200]}...")
                    else:
                        print("  ℹ️ No '通算成績' found in pre tag")
                else:
                    print("  ℹ️ No pre tag found in HTML")
                    
        except Exception as e:
            print(f"❌ Error processing {html_file.name}: {str(e)}")

if __name__ == "__main__":
    main()
