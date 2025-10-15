import requests
import json

def test_api_endpoints():
    base_url = "http://localhost:8000"
    
    # 1. ルートエンドポイントのテスト
    print("\n=== 1. ルートエンドポイントのテスト ===")
    try:
        response = requests.get(f"{base_url}/")
        print(f"ステータスコード: {response.status_code}")
        print(f"レスポンス: {response.json()}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 2. 馬一覧取得のテスト
    print("\n=== 2. 馬一覧取得のテスト ===")
    try:
        response = requests.get(f"{base_url}/horses/")
        print(f"ステータスコード: {response.status_code}")
        data = response.json()
        print(f"取得件数: {len(data) if isinstance(data, list) else 'N/A'}")
        if data and len(data) > 0:
            print("\n先頭の馬データ:")
            print(f"- ID: {data[0].get('id')}")
            print(f"- 名前: {data[0].get('name')}")
            print(f"- 性別: {data[0].get('sex')}")
            print(f"- 年齢: {data[0].get('age')}")
            print(f"- 父: {data[0].get('sire')}")
            print(f"- 母: {data[0].get('dam')}")
            print(f"- 母父: {data[0].get('dam_sire')}")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 3. 特定の馬データ取得のテスト
    print("\n=== 3. 特定の馬データ取得のテスト ===")
    try:
        # 最初の馬のIDを取得
        response = requests.get(f"{base_url}/horses/")
        if response.status_code == 200 and len(response.json()) > 0:
            horse_id = response.json()[0]['id']
            response = requests.get(f"{base_url}/horses/{horse_id}")
            print(f"ステータスコード: {response.status_code}")
            data = response.json()
            print("\n馬の詳細データ:")
            print(f"- ID: {data.get('id')}")
            print(f"- 名前: {data.get('name')}")
            print(f"- 性別: {data.get('sex')}")
            print(f"- 年齢: {data.get('age')}")
            print(f"- 父: {data.get('sire')}")
            print(f"- 母: {data.get('dam')}")
            print(f"- 母父: {data.get('dam_sire')}")
            print(f"- レース成績: {data.get('race_record')}")
            print(f"- 体重: {data.get('weight')}kg")
            print(f"- 初回賞金: {data.get('total_prize_start')}万円")
            print(f"- 最新賞金: {data.get('total_prize_latest')}万円")
            print(f"- 落札価格: {data.get('sold_price')}円")
            print(f"- オークション日: {data.get('auction_date')}")
            print(f"- 販売者: {data.get('seller')}")
            print(f"- コメント: {data.get('comment')}")
        else:
            print("テスト用の馬データが見つかりません")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 4. 統計情報取得のテスト
    print("\n=== 4. 統計情報取得のテスト ===")
    try:
        response = requests.get(f"{base_url}/statistics/")
        print(f"ステータスコード: {response.status_code}")
        data = response.json()
        print("\n統計情報:")
        print(f"- 総馬数: {data.get('total_horses')}頭")
        print(f"- 平均価格: {data.get('average_price'):,.0f}円")
        print(f"- 平均成長率: {data.get('average_growth_rate'):.2f}%")
        print(f"- 成長率データのある馬の数: {data.get('horses_with_growth_data')}頭")
    except Exception as e:
        print(f"エラー: {e}")
    
    # 5. オークション開催日一覧のテスト
    print("\n=== 5. オークション開催日一覧のテスト ===")
    try:
        response = requests.get(f"{base_url}/auction-dates/")
        print(f"ステータスコード: {response.status_code}")
        dates = response.json()
        print(f"\n開催日数: {len(dates)}")
        if dates:
            print("直近の開催日:")
            for i, date in enumerate(dates[:3], 1):  # 直近3件を表示
                print(f"  {i}. {date}")
    except Exception as e:
        print(f"エラー: {e}")

if __name__ == "__main__":
    print("APIエンドポイントのテストを開始します...\n")
    test_api_endpoints()
    print("\nテストが完了しました。")
