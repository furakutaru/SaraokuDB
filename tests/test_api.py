import requests
import json
import sys
from typing import List, Dict, Any, Optional

def test_api_endpoints(base_url: str = "http://localhost:8001"):
    """バックエンドのAPIエンドポイントをテストする"""
    print(f"=== バックエンドAPIテストを開始します ({base_url}) ===\n")
    
    # 1. ルートエンドポイントのテスト
    print("1. ルートエンドポイントのテスト")
    try:
        response = requests.get(f"{base_url}/")
        print(f"  - ステータスコード: {response.status_code}")
        print(f"  - レスポンス: {response.json()}")
    except Exception as e:
        print(f"  - エラー: {e}")
    
    # 2. 馬一覧取得のテスト
    print("\n2. 馬一覧取得のテスト")
    try:
        response = requests.get(f"{base_url}/horses/")
        print(f"  - ステータスコード: {response.status_code}")
        data = response.json()
        print(f"  - 取得件数: {len(data) if isinstance(data, list) else 'N/A'}")
        if data and len(data) > 0:
            print("  - 先頭の馬データ:")
            print(f"    - ID: {data[0].get('id')}")
            print(f"    - 名前: {data[0].get('name')}")
    except Exception as e:
        print(f"  - エラー: {e}")
    
    # 3. 特定の馬データ取得のテスト
    print("\n3. 特定の馬データ取得のテスト")
    try:
        # 最初の馬のIDを取得
        response = requests.get(f"{base_url}/horses/")
        if response.status_code == 200 and len(response.json()) > 0:
            horse_id = response.json()[0]['id']
            response = requests.get(f"{base_url}/horses/{horse_id}")
            print(f"  - ステータスコード: {response.status_code}")
            data = response.json()
            print(f"  - 馬名: {data.get('name')}")
            print(f"  - 性別: {data.get('sex')}")
            print(f"  - 父: {data.get('sire')}")
        else:
            print("  - テスト用の馬データが見つかりません")
    except Exception as e:
        print(f"  - エラー: {e}")
    
    # 4. 統計情報取得のテスト
    print("\n4. 統計情報取得のテスト")
    try:
        response = requests.get(f"{base_url}/statistics/")
        print(f"  - ステータスコード: {response.status_code}")
        data = response.json()
        print(f"  - 総馬数: {data.get('total_horses')}")
        print(f"  - 平均価格: {data.get('average_price'):,}円")
        print(f"  - 平均成長率: {data.get('average_growth_rate'):.2f}%")
    except Exception as e:
        print(f"  - エラー: {e}")
    
    # 5. オークション開催日一覧のテスト
    print("\n5. オークション開催日一覧のテスト")
    try:
        response = requests.get(f"{base_url}/auction-dates/")
        print(f"  - ステータスコード: {response.status_code}")
        dates = response.json()
        print(f"  - 開催日数: {len(dates)}")
        if dates:
            print(f"  - 直近の開催日: {dates[0]}")
    except Exception as e:
        print(f"  - エラー: {e}")
    
    print("\n=== テスト完了 ===")

if __name__ == "__main__":
    # カスタムURLが指定されている場合はそれを使用
    base_url = sys.argv[1] if len(sys.argv) > 1 else "http://localhost:8001"
    test_api_endpoints(base_url)
