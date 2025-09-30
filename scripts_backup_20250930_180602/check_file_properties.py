import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Please provide a file path")
        return
    
    file_path = sys.argv[1]
    print(f"Checking: {file_path}")
    
    # Check if path exists
    if not os.path.exists(file_path):
        print("File does not exist")
        return
        
    # Check if it's a file
    if not os.path.isfile(file_path):
        print("Path exists but is not a file")
        return
        
    # Get file size
    try:
        size = os.path.getsize(file_path)
        print(f"File size: {size} bytes")
    except OSError as e:
        print(f"Error getting file size: {e}")
    
    # Try to read first few bytes
    try:
        with open(file_path, 'rb') as f:
            first_bytes = f.read(100)
            print(f"First 10 bytes: {first_bytes[:10]}")
    except Exception as e:
        print(f"Error reading file: {e}")

if __name__ == "__main__":
    main()
