import os
import sys

def check_file(path):
    print(f"Checking: {path}")
    print(f"File exists: {os.path.exists(path)}")
    if os.path.exists(path):
        try:
            size = os.path.getsize(path)
            print(f"File size: {size} bytes"
                  f" ({(size/1024/1024):.2f} MB)" if size > 0 else "0 bytes")
            
            # Try to read first 100 bytes
            try:
                with open(path, 'rb') as f:
                    first_100 = f.read(100)
                print(f"First 100 bytes: {first_100}")
            except Exception as e:
                print(f"Error reading file: {e}")
                
        except Exception as e:
            print(f"Error getting file size: {e}")
    else:
        print("File does not exist or is not accessible")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        check_file(sys.argv[1])
    else:
        print("Please provide a file path")
