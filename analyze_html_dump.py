#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
from pathlib import Path

def analyze_html_file(file_path):
    """Analyze an HTML file and print basic information."""
    try:
        # Get file size
        file_size = os.path.getsize(file_path)
        
        # Read file content
        with open(file_path, 'rb') as f:
            content = f.read()
            
        # Try to decode as UTF-8
        try:
            text = content.decode('utf-8')
            encoding = 'utf-8'
        except UnicodeDecodeError:
            try:
                text = content.decode('shift_jis')
                encoding = 'shift_jis'
            except:
                text = content.decode('utf-8', errors='ignore')
                encoding = 'unknown'
        
        # Count lines and characters
        line_count = len(text.splitlines())
        char_count = len(text)
        
        # Print file info
        print(f"\nFile: {file_path}")
        print(f"Size: {file_size} bytes")
        print(f"Encoding: {encoding}")
        print(f"Lines: {line_count}")
        print(f"Characters: {char_count}")
        
        # Print first 200 characters
        print("\nFirst 200 characters:")
        print(text[:200].replace('\n', ' ').replace('\r', ' '))
        
        # Check for common HTML elements
        print("\nCommon elements:")
        for element in ['<div', '<table', '<tr', '<td', '<a href', 'class="', 'id="']:
            count = text.count(element)
            if count > 0:
                print(f"  {element}...: {count}")
        
        return True
        
    except Exception as e:
        print(f"Error analyzing {file_path}: {e}")
        return False

def main():
    # Set the directory to analyze
    base_dir = Path("/Users/yum.ishii/SaraokuDB/html_dump")
    
    # Analyze index.html
    index_file = base_dir / "index.html"
    if index_file.exists():
        print("="*80)
        print(f"ANALYZING INDEX FILE: {index_file}")
        print("="*80)
        analyze_html_file(index_file)
    
    # Analyze detail files
    details_dir = base_dir / "details"
    if details_dir.exists() and details_dir.is_dir():
        print("\n" + "="*80)
        print(f"ANALYZING DETAIL FILES IN: {details_dir}")
        print("="*80)
        
        # Get all HTML files in details directory
        html_files = list(details_dir.glob("*.html"))
        
        # Analyze first 3 files as samples
        for i, html_file in enumerate(html_files[:3]):
            print(f"\n{'='*40} File {i+1} {'='*40}")
            analyze_html_file(html_file)

if __name__ == "__main__":
    main()
