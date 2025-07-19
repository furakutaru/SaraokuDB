import json
import os

HISTORY_PATH = "static-frontend/public/data/horses_history.json"

# テスト馬データ
TEST_HORSE = {
    "id": 9999,
    "history": [
        {
            "auction_date": "2024-01-01",
            "name": "テストホースA",
            "sex": "牡",
            "age": "2",
            "seller": "テスト牧場",
            "race_record": "0戦0勝",
            "comment": "初回出品時のコメント。",
            "sold_price": 100000,
            "total_prize_start": 0.0
        },
        {
            "auction_date": "2024-06-01",
            "name": "テストホースB",
            "sex": "牡",
            "age": "3",
            "seller": "テスト牧場2",
            "race_record": "1戦0勝",
            "comment": "再出品時のコメント。名前が変わりました。",
            "sold_price": 200000,
            "total_prize_start": 50000
        }
    ],
    "sire": "テストサイアー",
    "dam": "テストダム",
    "dam_sire": "テストダムサイアー",
    "primary_image": "",
    "disease_tags": "なし",
    "netkeiba_url": "",
    "jbis_url": "",
    "weight": None,
    "unsold_count": None,
    "total_prize_latest": 50000,
    "created_at": "2024-01-01T00:00:00",
    "updated_at": "2024-06-01T00:00:00",
    "hidden": True
}

def main():
    with open(HISTORY_PATH, encoding="utf-8") as f:
        data = json.load(f)
    horses = data["horses"] if "horses" in data else data
    # 既存のID:9999を探す
    found = False
    for i, h in enumerate(horses):
        if h.get("id") == 9999:
            horses[i] = TEST_HORSE
            found = True
            break
    if not found:
        horses.append(TEST_HORSE)
    # 保存
    if "horses" in data:
        data["horses"] = horses
    else:
        data = horses
    with open(HISTORY_PATH, "w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print("テスト馬（ID:9999）を追加・上書きしました")

if __name__ == "__main__":
    main() 