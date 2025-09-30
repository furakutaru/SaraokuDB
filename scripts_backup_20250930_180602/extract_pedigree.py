import re
from bs4 import BeautifulSoup

def extract_pedigree(html_file):
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # Use regex to find the pedigree information
    pedigree_pattern = r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\s\<]+)'
    match = re.search(pedigree_pattern, content)
    
    if match:
        return {
            'sire': match.group(1),      # 父 (Father)
            'dam': match.group(2),       # 母 (Mother)
            'damsire': match.group(3)    # 母の父 (Mother's Father / Damsire)
        }
    return None

if __name__ == "__main__":
    html_file = 'debug_pedigree_page.html'
    pedigree = extract_pedigree(html_file)
    
    if pedigree:
        print("Pedigree Information:")
        print(f"Sire (父): {pedigree['sire']}")
        print(f"Dam (母): {pedigree['dam']}")
        print(f"Damsire (母の父): {pedigree['damsire']}")
    else:
        print("No pedigree information found in the HTML file.")
