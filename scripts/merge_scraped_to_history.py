import json
from datetime import datetime
import os

# 入力ファイル
SCRAPED_PATH = 'scraped_horses.json'
HISTORY_PATH = 'static-frontend/public/data/horses_history.json'

# 出力ファイル
OUTPUT_PATH = 'static-frontend/public/data/horses_history.json'

def get_next_id(horses_list):
    """新しい馬に割り振るための一意なIDを生成する"""
    if not horses_list:
        return 1
    return max(h.get('id', 0) for h in horses_list) + 1

def get_horse_name(horse_data):
    """馬のデータをから名前を取得する。トップレベル、もしくは最新の履歴から取得"""
    if horse_data.get('name'):
        return horse_data.get('name')
    if horse_data.get('history'):
        # 履歴が空でないことを確認
        if horse_data['history']:
            return horse_data['history'][0].get('name')
    return None

def main():
    """
    scraped_horses.jsonのデータをhorses_history.jsonにマージする。
    - 既存の馬はhistoryに追加
    - 新規の馬は新しいエントリとして追加
    """
    # 履歴ファイルの読み込み
    if os.path.exists(HISTORY_PATH) and os.path.getsize(HISTORY_PATH) > 0:
        with open(HISTORY_PATH, 'r', encoding='utf-8') as f:
            try:
                history_data = json.load(f)
            except json.JSONDecodeError:
                history_data = {"metadata": {}, "horses": []}
    else:
        history_data = {"metadata": {}, "horses": []}

    # スクレイピングされたファイルの読み込み
    with open(SCRAPED_PATH, 'r', encoding='utf-8') as f:
        scraped_horses = json.load(f)

    # 既存の馬をdetail_urlでマッピング（KeyErrorを回避）
    existing_horses_by_url = {
        h['detail_url']: h for h in history_data.get('horses', []) if h.get('detail_url')
    }

    newly_added_horses = 0
    updated_horses = 0
    
    for scraped_horse in scraped_horses:
        detail_url = scraped_horse.get('detail_url')
        if not detail_url:
            continue
        
        existing_horse = None
        # 1. detail_urlで検索
        if detail_url in existing_horses_by_url:
            existing_horse = existing_horses_by_url[detail_url]
        else:
            # 2. 名前、父で検索
            scraped_name = scraped_horse.get('name')
            scraped_sire = scraped_horse.get('sire', '').split('　')[0].strip()
            
            for h in history_data.get('horses', []):
                h_name = get_horse_name(h)
                h_sire = h.get('sire')

                if h_name == scraped_name and h_sire == scraped_sire:
                    # 名前と父が一致したら、同一馬の可能性が高いと判断
                    existing_horse = h
                    break

        # 新しい履歴エントリを作成
        history_entry = {
            'auction_date': scraped_horse.get('auction_date'),
            'name': scraped_horse.get('name'),
            'sex': scraped_horse.get('sex'),
            'age': str(scraped_horse.get('age')),
            'seller': scraped_horse.get('seller'),
            'race_record': scraped_horse.get('race_record'),
            'comment': scraped_horse.get('comment'),
            'sold_price': scraped_horse.get('sold_price'),
            'total_prize_start': scraped_horse.get('total_prize_start', 0.0),
            'unsold': scraped_horse.get('unsold', False)
        }

        if existing_horse:
            # 既存の馬の場合
            # detail_url がなければ設定して、今後のマッチング精度を向上
            if not existing_horse.get('detail_url'):
                existing_horse['detail_url'] = detail_url
                existing_horses_by_url[detail_url] = existing_horse # マップも更新

            # 重複チェック
            is_duplicate = False
            for existing_history in existing_horse.get('history', []):
                if (existing_history.get('auction_date') == history_entry.get('auction_date') and
                    existing_history.get('sold_price') == history_entry.get('sold_price')):
                    is_duplicate = True
                    break
            
            if not is_duplicate:
                existing_horse.setdefault('history', []).insert(0, history_entry)
                # 最新情報で更新
                existing_horse['updated_at'] = datetime.now().isoformat()
                existing_horse['total_prize_latest'] = scraped_horse.get('total_prize_latest', existing_horse.get('total_prize_latest'))
                existing_horse['weight'] = scraped_horse.get('weight', existing_horse.get('weight'))
                updated_horses += 1
        else:
            # 新規の馬の場合、新しいエントリを作成
            now = datetime.now().isoformat()
            new_horse = {
                "id": get_next_id(history_data.get('horses', [])),
                "name": scraped_horse.get('name'),
                "detail_url": detail_url,
                "sire": scraped_horse.get('sire', '').split('　')[0].strip(),
                "dam": scraped_horse.get('dam', '').split('　')[0].strip(),
                "dam_sire": scraped_horse.get('dam_sire'),
                "sex": scraped_horse.get('sex'),
                "age": str(scraped_horse.get('age')),
                "seller": scraped_horse.get('seller'),
                "weight": scraped_horse.get('weight'),
                "race_record": scraped_horse.get('race_record'),
                "total_prize_start": scraped_horse.get('total_prize_start', 0.0),
                "total_prize_latest": scraped_horse.get('total_prize_latest', 0.0),
                "sold_price": scraped_horse.get('sold_price'),
                "bid_num": scraped_horse.get('bid_num'),
                "unsold": scraped_horse.get('unsold', False),
                "primary_image": scraped_horse.get('primary_image'),
                "disease_tags": scraped_horse.get('disease_tags', 'なし'),
                "comment": scraped_horse.get('comment'),
                "jbis_url": scraped_horse.get('jbis_url'),
                "netkeiba_url": scraped_horse.get('netkeiba_url'),
                "auction_date": scraped_horse.get('auction_date'),
                "created_at": now,
                "updated_at": now,
                "history": [history_entry]
            }
            history_data.setdefault('horses', []).append(new_horse)
            existing_horses_by_url[detail_url] = new_horse # マップも更新
            newly_added_horses += 1

    # メタデータの更新
    all_horses = history_data.get('horses', [])
    total_horses = len(all_horses)
    
    sold_horses = [h for h in all_horses if h.get('sold_price') and not h.get('unsold')]
    if sold_horses:
        total_price = sum(h.get('sold_price', 0) for h in sold_horses)
        average_price = total_price / len(sold_horses)
    else:
        average_price = 0

    history_data['metadata'] = {
        'last_updated': datetime.now().isoformat(),
        'total_horses': total_horses,
        'average_price': int(average_price)
    }

    # 更新されたデータをファイルに書き込み
    with open(OUTPUT_PATH, 'w', encoding='utf-8') as f:
        json.dump(history_data, f, ensure_ascii=False, indent=2)

    print(f"処理が完了しました。")
    print(f"新規追加: {newly_added_horses}頭")
    print(f"情報更新: {updated_horses}頭")
    print(f"合計: {total_horses}頭")
    print(f"出力先: {OUTPUT_PATH}")

if __name__ == '__main__':
    main() 