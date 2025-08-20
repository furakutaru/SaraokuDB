#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
from bs4 import BeautifulSoup

def debug_prize_extraction(html_file):
    """Debug prize extraction from the auction list HTML"""
    print(f"\nDebugging prize extraction from: {html_file}")
    print("=" * 80)
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Print the first 1000 characters to understand the structure
    print("\n=== HTML Preview ===")
    print(html_content[:1000] + "..." if len(html_content) > 1000 else html_content)
    print("=" * 80)
    
    # Try to find any div with class containing 'price'
    price_divs = soup.find_all('div', class_=lambda x: x and 'price' in x.lower())
    print(f"\nFound {len(price_divs)} divs with 'price' in class")
    for i, div in enumerate(price_divs[:5]):  # Show first 5 matches
        print(f"\n--- Price Div {i+1} ---")
        print(f"Class: {div.get('class', 'No class')}")
        print(f"Text: {div.get_text(strip=True)}")
        print(f"HTML: {str(div)[:200]}...")
    
    # Try to find any element containing '万円'
    yen_elements = soup.find_all(string=re.compile('万円'))
    print(f"\nFound {len(yen_elements)} elements containing '万円'")
    for i, elem in enumerate(yen_elements[:5]):  # Show first 5 matches
        print(f"\n--- Yen Element {i+1} ---")
        print(f"Text: {str(elem).strip()}")
        print(f"Parent: {str(elem.parent)[:200]}...")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用法: python debug_prize_extraction.py <HTMLファイルパス>")
        sys.exit(1)
    
    import re  # Import here to avoid issues with the script
    debug_prize_extraction(sys.argv[1])
