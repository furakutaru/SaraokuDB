#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Test script to verify debug directory creation and file writing.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def test_debug_save():
    # Get project root directory
    project_root = Path(__file__).parent.parent  # Two levels up from the script
    debug_dir = project_root / 'debug'
    
    print(f"Project root: {project_root}")
    print(f"Debug directory: {debug_dir}")
    
    # Create date-based subdirectories
    date_str = datetime.now().strftime("%Y%m%d")
    date_dir = debug_dir / date_str
    detail_dir = date_dir / 'detail'
    
    # Create directories with explicit permissions
    for directory in [debug_dir, date_dir, detail_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            # Set permissions explicitly (rwxr-xr-x)
            directory.chmod(0o755)
            print(f"✓ Created/verified directory: {directory}")
            print(f"  Permissions: {oct(directory.stat().st_mode)[-3:]}")
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
            raise
    
    # Test file writing
    test_content = f"Test content written at: {datetime.now()}\n"
    
    # 1. Test list page file
    list_page_file = date_dir / 'test_horse_list.html'
    try:
        with open(list_page_file, 'w', encoding='utf-8') as f:
            f.write(f"<html><body>{test_content}</body></html>")
        print(f"✓ Successfully wrote to: {list_page_file}")
    except Exception as e:
        print(f"✗ Failed to write to {list_page_file}: {e}")
        raise
    
    # 2. Test detail page file
    detail_file = detail_dir / 'test_detail_001.html'
    try:
        with open(detail_file, 'w', encoding='utf-8') as f:
            f.write(f"<html><body><h1>Test Detail Page</h1><p>{test_content}</p></body></html>")
        print(f"✓ Successfully wrote to: {detail_file}")
    except Exception as e:
        print(f"✗ Failed to write to {detail_file}: {e}")
        raise
    
    # 3. Test card file
    card_file = detail_dir / 'test_card_001.html'
    try:
        with open(card_file, 'w', encoding='utf-8') as f:
            f.write(f"<div class='horse-card'><h2>Test Horse</h2><p>{test_content}</p></div>")
        print(f"✓ Successfully wrote to: {card_file}")
    except Exception as e:
        print(f"✗ Failed to write to {card_file}: {e}")
        raise
    
    # List all files in the debug directory
    print("\nContents of debug directory:")
    try:
        for item in debug_dir.glob('**/*'):
            if item.is_file():
                print(f"- {item.relative_to(project_root)} (size: {item.stat().st_size} bytes)")
    except Exception as e:
        print(f"Error listing directory contents: {e}")

if __name__ == "__main__":
    print("=== Debug Directory Write Test ===\n")
    try:
        test_debug_save()
        print("\n✓ Test completed successfully!")
    except Exception as e:
        print(f"\n✗ Test failed: {e}")
        sys.exit(1)
