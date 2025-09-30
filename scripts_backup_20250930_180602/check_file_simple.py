import os
import sys

def main():
    if len(sys.argv) < 2:
        print("Please provide a file path")
        return
    
    file_path = sys.argv[1]
    print(f"Checking: {file_path}")
    
    try:
        if os.path.exists(file_path):
            print("File exists!")
            size = os.path.getsize(file_path)
            print(f"File size: {size} bytes")
        else:
            print("File does not exist")
    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    main()
