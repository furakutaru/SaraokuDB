#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import re
from bs4 import BeautifulSoup

def test_prize_extraction(html_file):
    """Test prize extraction from the auction list HTML"""
    print(f"\nTesting prize extraction from: {html_file}")
    print("=" * 80)
    
    # Read the HTML file
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    # Parse the HTML
    soup = BeautifulSoup(html_content, 'html.parser')
    
    # Find all horse cards
    horse_cards = soup.find_all('div', class_=lambda x: x and 'auctionTableCard' in x)
    
    if not horse_cards:
        print("No horse cards found in the HTML.")
        return
    
    print(f"Found {len(horse_cards)} horse cards")
    
    # Test prize extraction for each horse card
    for i, card in enumerate(horse_cards[:10]):  # Check first 10 horses
        print(f"\n--- Horse {i+1} ---")
        
        # 1. Try direct extraction using the known structure
        prize_div = card.find('div', class_=lambda x: x and 'price' in (x or '').lower())
        
        if prize_div:
            print(f"Found price div: {str(prize_div)[:100]}...")
            
            # Try to find value div inside price div
            value_div = prize_div.find('div', class_=lambda x: x and 'value' in (x or '').lower())
            if value_div:
                prize_text = value_div.get_text(strip=True)
                print(f"Found value div: {prize_text}")
                
                # Extract numeric value
                match = re.search(r'([\d,.]+)', prize_text)
                if match:
                    try:
                        prize = float(match.group(1).replace(',', ''))
                        print(f"Extracted prize: {prize} 万円")
                        continue
                    except (ValueError, TypeError) as e:
                        print(f"Error converting to float: {e}")
            
            # If we get here, try to extract directly from the prize_div text
            prize_text = prize_div.get_text(strip=True)
            print(f"Text from price div: {prize_text}")
            
            # Try to extract prize using regex
            match = re.search(r'([\d,.]+)', prize_text)
            if match:
                try:
                    prize = float(match.group(1).replace(',', ''))
                    print(f"Extracted prize (direct): {prize} 万円")
                    continue
                except (ValueError, TypeError) as e:
                    print(f"Error converting to float (direct): {e}")
        
        # If we get here, try to find any element with prize info
        print("Trying to find any prize element...")
        for elem in card.find_all(string=re.compile(r'[\d,.]\s*万円')):
            print(f"Found prize text: {elem.strip()}")
            match = re.search(r'([\d,.]+)', elem)
            if match:
                try:
                    prize = float(match.group(1).replace(',', ''))
                    print(f"Extracted prize (text search): {prize} 万円")
                    break
                except (ValueError, TypeError) as e:
                    print(f"Error converting to float (text search): {e}")
        else:
            print("No prize information found in this card")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("使用法: python test_prize_extraction_fixed.py <HTMLファイルパス>")
        sys.exit(1)
    
    test_prize_extraction(sys.argv[1])
