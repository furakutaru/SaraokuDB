"""
Test script to verify debug directory creation and file writing.
"""
import os
import sys
from pathlib import Path
from datetime import datetime

def test_debug_write():
    # Get project root directory
    project_root = Path(__file__).parent.parent
    debug_dir = project_root / 'debug'
    
    print(f"Project root: {project_root}")
    print(f"Debug directory: {debug_dir}")
    
    # Create date-based subdirectories
    date_str = datetime.now().strftime("%Y%m%d")
    date_dir = debug_dir / date_str
    detail_dir = date_dir / 'detail'
    
    # Create directories
    for directory in [debug_dir, date_dir, detail_dir]:
        try:
            directory.mkdir(parents=True, exist_ok=True)
            print(f"✓ Created/verified directory: {directory}")
            
            # Check permissions
            if os.access(directory, os.W_OK):
                print(f"  ✓ Write permissions: OK")
            else:
                print(f"  ✗ No write permissions: {directory}")
                
        except Exception as e:
            print(f"✗ Failed to create directory {directory}: {e}")
    
    # Test file writing
    test_file = detail_dir / 'test_write.txt'
    test_content = f"Test content written at: {datetime.now()}\n"
    
    try:
        with open(test_file, 'w', encoding='utf-8') as f:
            f.write(test_content)
        print(f"✓ Successfully wrote to: {test_file}")
    except Exception as e:
        print(f"✗ Failed to write to {test_file}: {e}")
    
    # List contents of debug directory
    print("\nContents of debug directory:")
    try:
        for item in debug_dir.glob('**/*'):
            print(f"- {item.relative_to(project_root)}")
    except Exception as e:
        print(f"Error listing directory contents: {e}")

if __name__ == "__main__":
    print("=== Debug Directory Write Test ===\n")
    test_debug_write()
    print("\n=== Test Complete ===")
