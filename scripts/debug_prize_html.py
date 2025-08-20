#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup

def analyze_prize_structure(html_file):
    """Analyze the HTML structure to understand how prize information is stored"""
    print(f"\nAnalyzing prize structure in: {html_file}")
    print("=" * 80)
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all horse cards
    horse_cards = soup.find_all('div', class_=lambda x: x and 'auctionTableCard' in (x or '').lower())
    
    if not horse_cards:
        print("No horse cards found in the HTML.")
        return
    
    print(f"Found {len(horse_cards)} horse cards")
    
    # Collect statistics
    prize_count = 0
    zero_prize_count = 0
    non_zero_prize_count = 0
    
    # Analyze first 10 horses
    for i, card in enumerate(horse_cards[:10]):
        print(f"\n--- Horse {i+1} ---")
        
        # Print the HTML structure of the card (first 500 chars)
        card_html = str(card)[:500] + '...' if len(str(card)) > 500 else str(card)
        print(f"Card HTML: {card_html}")
        
        # Look for any div that might contain prize information
        for div in card.find_all('div'):
            div_class = div.get('class', [])
            div_text = div.get_text(strip=True)
            
            # Check if this div might contain prize info
            if 'price' in str(div_class).lower() or '賞金' in div_text:
                print(f"\nPotential prize div found:")
                print(f"  Class: {div_class}")
                print(f"  Text: {div_text}")
                print(f"  Full HTML: {str(div)[:200]}...")
                
                # Check for nested elements
                if div.find('div'):
                    print("  Nested elements found:")
                    for child in div.find_all(recursive=False):
                        print(f"    - {child.name} (class={child.get('class', '')}): {child.get_text(strip=True)}")
                
                # Check if this is a zero prize
                if '0.0' in div_text or '0,0' in div_text:
                    zero_prize_count += 1
                    print("  Detected zero prize")
                else:
                    non_zero_prize_count += 1
                    print("  Detected non-zero prize")
                
                prize_count += 1
    
    print(f"\n=== Summary ===")
    print(f"Total prize elements found: {prize_count}")
    print(f"Zero prizes: {zero_prize_count}")
    print(f"Non-zero prizes: {non_zero_prize_count}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用法: python debug_prize_html.py <HTMLファイルパス>")
        sys.exit(1)
    
    analyze_prize_structure(sys.argv[1])
