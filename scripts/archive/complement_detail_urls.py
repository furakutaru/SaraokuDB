import json
import unicodedata

def normalize(name):
    if not name:
        return ''
    return unicodedata.normalize('NFKC', name).replace(' ', '').replace('\u3000', '').strip()

# 1. 手動で調査済みの未補完馬名→URLマップ
manual_url_map = {
    'イチジョウサクラ': 'https://auction.keiba.rakuten.co.jp/item/14510',
    'ゴールデンマーチ': 'https://auction.keiba.rakuten.co.jp/item/14511',
    'ジンガブリッツ': 'https://auction.keiba.rakuten.co.jp/item/14512',
    'シュヴァルツボーイ': 'https://auction.keiba.rakuten.co.jp/item/14513',
    'ナプラフォルゴー': 'https://auction.keiba.rakuten.co.jp/item/14514',
    'デーレーアネラ': 'https://auction.keiba.rakuten.co.jp/item/14515',
    'レーベンヘルツ': 'https://auction.keiba.rakuten.co.jp/item/14516',
    'レモンアイカー': 'https://auction.keiba.rakuten.co.jp/item/14517',
    'セイレジーナ': 'https://auction.keiba.rakuten.co.jp/item/14518',
    'クレテイユ': 'https://auction.keiba.rakuten.co.jp/item/14519',
}

# 2. horses_history.jsonを読み込み
with open('static-frontend/public/data/horses_history.json', encoding='utf-8') as f:
    data = json.load(f)

# 3. 未補完馬に手動URLをセット
for horse in data['horses']:
    if not horse.get('detail_url'):
        # history配列の馬名も含めて突合
        set_url = None
        if normalize(horse.get('name')) in manual_url_map:
            set_url = manual_url_map[normalize(horse.get('name'))]
        else:
            for h in horse.get('history', []):
                if normalize(h.get('name')) in manual_url_map:
                    set_url = manual_url_map[normalize(h.get('name'))]
                    break
        if set_url:
            horse['detail_url'] = set_url

# 4. 上書き保存
with open('static-frontend/public/data/horses_history.json', 'w', encoding='utf-8') as f:
    json.dump(data, f, ensure_ascii=False, indent=2)

print('手動URL補完完了') 