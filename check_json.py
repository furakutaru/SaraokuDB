import json

with open('/Users/yum.ishii/SaraokuDB/cache/20250818/processed_horses.json', 'r', encoding='utf-8') as f:
    data = json.load(f)
    print(f"Number of records: {len(data)}")
    print("First record:")
    print(json.dumps(data[0], ensure_ascii=False, indent=2))
