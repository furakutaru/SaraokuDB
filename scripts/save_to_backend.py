#!/usr/bin/env python3
import json
import os
import sys
import requests
from pathlib import Path
from typing import Dict, Any, List

# プロジェクトのルートディレクトリをPythonパスに追加
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# バックエンドのベースURL
BASE_URL = "http://localhost:8001"

def load_horses_data() -> List[Dict[str, Any]]:
    """フロントエンドのhorses.jsonから馬データを読み込む"""
    file_path = project_root / 'static-frontend' / 'public' / 'data' / 'horses.json'
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def save_horse_to_backend(horse_data: Dict[str, Any]) -> bool:
    """バックエンドのAPIを呼び出して馬データを保存"""
    # 賞金情報を抽出（数値に変換）
    prize_money = horse_data.get("prize_money", {})
    total_prize_str = prize_money.get("total_prize", "0").replace(",", "").replace("円", "")
    
    # バックエンドが期待する形式にデータを変換
    # 配列として保存する必要があるフィールドをJSON文字列に変換
    sex = json.dumps([horse_data.get("sex", "")]) if horse_data.get("sex") else None
    age = int(horse_data.get("age", 0)) if horse_data.get("age") is not None else None
    sold_price = int(horse_data.get("sold_price", 0)) if horse_data.get("sold_price") is not None else None
    auction_date = json.dumps([""])  # 空の配列をデフォルト値として設定
    seller = json.dumps([""])  # 空の配列をデフォルト値として設定
    comment = json.dumps([horse_data.get("comment", "")]) if horse_data.get("comment") else None
    
    payload = {
        "name": horse_data["name"],
        "sex": sex,
        "age": age,  # 整数として送信
        "sire": horse_data.get("sire", ""),
        "dam": horse_data.get("dam", ""),
        "dam_sire": horse_data.get("damsire", ""),
        "race_record": json.dumps(horse_data.get("race_records", [])),  # JSON文字列として保存
        "weight": 0,  # デフォルト値として0を設定
        "total_prize_start": float(total_prize_str or 0),
        "total_prize_latest": float(total_prize_str or 0),
        "sold_price": sold_price,  # 整数として送信
        "auction_date": auction_date,
        "seller": seller,
        "disease_tags": ",".join(horse_data.get("disease_tags", [])),
        "comment": comment,
        "image_url": horse_data.get("image_url", {}).get("url", "")
    }
    
    # バックエンドのAPIエンドポイントにPOSTリクエストを送信
    print(f"\n[DEBUG] 送信データ: {json.dumps(payload, ensure_ascii=False, indent=2)}")
    
    try:
        response = requests.post(f"{BASE_URL}/horses/", json=payload, timeout=30)
        response.raise_for_status()
        
        result = response.json()
        print(f"✅ 保存成功: {horse_data['name']} (ID: {result.get('id')})")
        print(f"[DEBUG] レスポンス: {json.dumps(result, ensure_ascii=False, indent=2)}")
        return True
        
    except requests.exceptions.HTTPError as http_err:
        error_msg = f"HTTPエラー: {http_err}"
        if hasattr(http_err, 'response') and http_err.response is not None:
            try:
                error_msg += f"\nステータスコード: {http_err.response.status_code}"
                error_msg += f"\nレスポンス本文: {http_err.response.text}"
                error_msg += f"\nヘッダー: {dict(http_err.response.headers)}"
            except Exception as e:
                error_msg += f"\n追加情報の取得中にエラーが発生しました: {str(e)}"
        print(f"❌ エラーが発生しました ({horse_data.get('name', '不明')}): {error_msg}")
        
    except requests.exceptions.RequestException as req_err:
        print(f"❌ リクエストエラーが発生しました ({horse_data.get('name', '不明')}): {str(req_err)}")
        
    except json.JSONDecodeError as json_err:
        print(f"❌ JSONデコードエラーが発生しました ({horse_data.get('name', '不明')}): {str(json_err)}")
        
    except Exception as e:
        import traceback
        print(f"❌ 予期せぬエラーが発生しました ({horse_data.get('name', '不明')}): {str(e)}")
        print(f"\n[DEBUG] トレースバック:\n{traceback.format_exc()}")
        
    return False

def main():
    print("=== 馬データをバックエンドに保存します ===")
    
    # 馬データを読み込む
    try:
        horses = load_horses_data()
        print(f"読み込んだ馬の数: {len(horses)}")
        
        # 最初の1頭のみを処理
        horse = horses[0]
        print(f"\n[1/1] 処理中: {horse.get('name', '名前不明')}")
        
        # データの確認
        print("\n[DEBUG] 馬データの構造:")
        for key, value in horse.items():
            print(f"- {key}: {type(value).__name__}")
            if key == 'race_records' and value:
                print(f"  - race_records[0]: {type(value[0]).__name__} with keys: {list(value[0].keys())}")
        
        # 1頭のみ保存を試みる
        if save_horse_to_backend(horse):
            print("\n✅ 1頭の馬データを正常に保存しました")
        else:
            print("\n❌ 馬データの保存に失敗しました")
            
    except Exception as e:
        import traceback
        print(f"\n❌ エラーが発生しました: {str(e)}")
        print("\n[DEBUG] スタックトレース:")
        traceback.print_exc()
        return

if __name__ == "__main__":
    main()
