import json
import os

def check_horses_file(file_path):
    print(f"Checking file: {file_path}")
    print(f"File exists: {os.path.exists(file_path)}")
    print(f"File size: {os.path.getsize(file_path) if os.path.exists(file_path) else 0} bytes")
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        print("\nFile loaded successfully!")
        print(f"Data type: {type(data)}")
        
        if isinstance(data, list):
            print(f"\nFile contains a list with {len(data)} items")
            if len(data) > 0:
                print("\nFirst item:")
                print(json.dumps(data[0], ensure_ascii=False, indent=2))
                
                # Check required fields in first item
                required_fields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller', 'auction_date']
                print("\nRequired fields check for first horse:")
                for field in required_fields:
                    exists = field in data[0]
                    value = data[0].get(field, 'MISSING')
                    print(f"  {field}: {'EXISTS' if exists else 'MISSING'} - Value: {value}")
                    
        elif isinstance(data, dict):
            print(f"\nFile contains a dictionary with keys: {list(data.keys())}")
            if 'horses' in data:
                print(f"\nFound 'horses' key with {len(data['horses'])} items")
                if len(data['horses']) > 0:
                    print("\nFirst horse:")
                    print(json.dumps(data['horses'][0], ensure_ascii=False, indent=2))
                    
                    # Check required fields in first horse
                    required_fields = ['id', 'name', 'sex', 'age', 'sire', 'dam', 'damsire', 'seller', 'auction_date']
                    print("\nRequired fields check for first horse:")
                    for field in required_fields:
                        exists = field in data['horses'][0]
                        value = data['horses'][0].get(field, 'MISSING')
                        print(f"  {field}: {'EXISTS' if exists else 'MISSING'} - Value: {value}")
                        
    except json.JSONDecodeError as e:
        print(f"\nError decoding JSON: {e}")
        print("\nFirst 500 characters of file:")
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read(500))
    except Exception as e:
        print(f"\nError: {e}")

if __name__ == "__main__":
    file_path = "/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json"
    check_horses_file(file_path)
