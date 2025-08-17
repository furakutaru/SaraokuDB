import os
import sys

def check_file_size(file_path):
    try:
        size = os.path.getsize(file_path)
        print(f"File size: {size} bytes")
        return True
    except OSError as e:
        print(f"Error accessing file: {e}")
        return False

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_file_size(sys.argv[1])
    else:
        print("Please provide a file path as an argument")
