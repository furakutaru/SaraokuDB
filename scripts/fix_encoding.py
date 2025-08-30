#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import io

def fix_file_encoding(input_file, output_file):
    with open(input_file, 'rb') as f:
        content = f.read()
    
    # Try to decode with different encodings
    encodings = ['utf-8', 'shift_jis', 'euc-jp', 'cp932']
    
    for encoding in encodings:
        try:
            decoded = content.decode(encoding)
            # If we get here, the decoding was successful
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(decoded)
            print(f"Successfully converted {input_file} from {encoding} to UTF-8")
            return True
        except UnicodeDecodeError:
            continue
    
    print(f"Failed to decode {input_file} with any of the supported encodings")
    return False

if __name__ == "__main__":
    if len(sys.argv) != 3:
        print("Usage: python fix_encoding.py <input_file> <output_file>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    if not fix_file_encoding(input_file, output_file):
        sys.exit(1)
