import os
import sys
import json
import requests
from dotenv import load_dotenv

# プロジェクトルートの.envを読み込む
load_dotenv('.env')

def test_horse_detail(horse_name):
    # APIのベースURL（デフォルトはローカルの8000）
    api_base = os.environ.get('API_BASE', 'http://localhost:8000/api')
    
    # 馬名からIDを検索
    search_url = f"{api_base}/horses?q={horse_name}"
    print(f"Searching for {horse_name} at {search_url}...")
    
    try:
        response = requests.get(search_url)
        response.raise_for_status()
        data = response.json()
        
        horses = data.get('horses', [])
        if not horses:
            print(f"Horse '{horse_name}' not found.")
            return
        
        target_horse = None
        for h in horses:
            if h['name'] == horse_name:
                target_horse = h
                break
        
        if not target_horse:
            print(f"Horse '{horse_name}' not found in search results.")
            return
            
        horse_id = target_horse['id']
        print(f"Found horse ID: {horse_id}")
        
        # 詳細情報を取得
        detail_url = f"{api_base}/horses/{horse_id}"
        print(f"Fetching detail from {detail_url}...")
        
        response = requests.get(detail_url)
        response.raise_for_status()
        detail = response.json()
        
        print("\n--- Race Record Info ---")
        print(f"Name: {detail.get('name')}")
        print(f"race_record (compat): {json.dumps(detail.get('race_record'), ensure_ascii=False)}")
        print(f"race_records (detailed): {json.dumps(detail.get('race_records'), ensure_ascii=False)}")
        print(f"unified_race_records: {json.dumps(detail.get('unified_race_records'), ensure_ascii=False)}")
        
        # 検証
        recs = detail.get('race_records', {})
        total = recs.get('total_races', 0)
        wins = recs.get('wins', 0)
        
        print(f"\nVerification: {total} races, {wins} wins")
        if total > 0:
            print("✅ Success: Race record is no longer 0!")
        else:
            print("❌ Failure: Race record is still 0.")

    except Exception as e:
        print(f"Error: {e}")

if __name__ == "__main__":
    horse_name = "フローティローズ"
    if len(sys.argv) > 1:
        horse_name = sys.argv[1]
    test_horse_detail(horse_name)
