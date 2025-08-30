#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys

def fix_encoding(input_file, output_file):
    # Read the file in binary mode
    with open(input_file, 'rb') as f:
        content = f.read()
    
    # Try to decode with different encodings
    encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932', 'latin1']
    
    for encoding in encodings:
        try:
            # Try to decode with the current encoding
            decoded = content.decode(encoding)
            
            # Write the content with UTF-8 encoding
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(decoded)
            
            print(f"Successfully decoded with {encoding}")
            return True
            
        except UnicodeDecodeError as e:
            print(f"Failed to decode with {encoding}: {e}")
            continue
    
    print("Failed to decode the file with any of the supported encodings")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_encoding_final.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not fix_encoding(input_file, output_file):
        sys.exit(1)
