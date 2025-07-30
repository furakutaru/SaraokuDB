import json

def main():
    # データを読み込む
    with open('../static-frontend/public/data/horses_history.json', 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 各馬の最終更新日時を取得
    horses_with_dates = []
    for horse in data['horses']:
        if 'history' in horse and horse['history']:
            # 最新の履歴の日付を取得
            latest_date = ''
            for h in horse['history']:
                if 'scraped_at' in h and h['scraped_at'] > latest_date:
                    latest_date = h['scraped_at']
            if latest_date:
                horses_with_dates.append((latest_date, horse))
    
    # 日付でソート（新しい順）
    horses_with_dates.sort(reverse=True, key=lambda x: x[0])
    
    # 最新の9頭を表示
    print('直近のスクレイピングで追加された馬（最新9頭）:')
    for i, (date, horse) in enumerate(horses_with_dates[:9], 1):
        print(f"{i}. ID: {horse['id']}, 馬名: {horse['name']}, 最終更新: {date}")

if __name__ == "__main__":
    main()
