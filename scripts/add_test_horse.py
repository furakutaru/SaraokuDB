import json

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
    "jbis_url": ""
}

PATH = 'static-frontend/public/data/horses_history.json'

def add_test_horse():
    with open(PATH, encoding='utf-8') as f:
        data = json.load(f)
    horses = data.get('horses', [])
    # すでにテスト馬が存在しないか確認
    if any(h.get('id') == 9999 for h in horses):
        print('テスト馬はすでに追加されています')
        return
    horses.append(TEST_HORSE)
    data['horses'] = horses
    with open(PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print('テスト馬を追加しました')

if __name__ == '__main__':
    add_test_horse() 