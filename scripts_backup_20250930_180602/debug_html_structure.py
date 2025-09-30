#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from bs4 import BeautifulSoup

def debug_html_structure(html_file):
    print(f"Debugging HTML structure for: {html_file}")
    print("=" * 80)
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all elements with class containing 'card' or 'horse' or 'auction'
    print("\nElements with class containing 'card', 'horse', or 'auction':")
    elements = soup.find_all(class_=lambda x: x and any(c in x.lower() for c in ['card', 'horse', 'auction']))
    for i, elem in enumerate(elements[:10], 1):  # Limit to first 10 elements
        print(f"\nElement {i}:")
        print(f"  Tag: {elem.name}")
        print(f"  Classes: {elem.get('class', [])}")
        print(f"  Text: {elem.get_text(strip=True)[:100]}...")
    
    # Look for potential horse name elements
    print("\nPotential horse name elements:")
    name_selectors = ['.auctionTableCard__name', '.horse-name', '.name', '.title', 'h2', 'h3']
    for selector in name_selectors:
        names = soup.select(selector)
        if names:
            print(f"\nFound {len(names)} elements with selector '{selector}':")
            for i, name in enumerate(names[:3], 1):  # Show first 3 matches
                print(f"  {i}. {name.get_text(strip=True)[:50]}...")
    
    # Look for potential seller elements
    print("\nPotential seller elements:")
    seller_selectors = ['.seller', '.owner', '.farm', '.producer', '.breeder']
    for selector in seller_selectors:
        sellers = soup.select(selector)
        if sellers:
            print(f"\nFound {len(sellers)} elements with selector '{selector}':")
            for i, seller in enumerate(sellers[:3], 1):
                print(f"  {i}. {seller.get_text(strip=True)[:50]}...")
    
    # Look for potential sex/age elements
    print("\nPotential sex/age elements:")
    sex_age_selectors = ['.horse-info', '.details', '.info', '.horseLabelWrapper']
    for selector in sex_age_selectors:
        elems = soup.select(selector)
        if elems:
            print(f"\nFound {len(elems)} elements with selector '{selector}':")
            for i, elem in enumerate(elems[:3], 1):
                print(f"  {i}. {elem.get_text(strip=True)[:100]}...")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Usage: python debug_html_structure.py <html_file>")
        sys.exit(1)
    
    html_file = sys.argv[1]
    if not os.path.exists(html_file):
        print(f"Error: File not found: {html_file}")
        sys.exit(1)
    
    debug_html_structure(html_file)
