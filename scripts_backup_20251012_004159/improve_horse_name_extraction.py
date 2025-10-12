import re
import json
from pathlib import Path

class HorseNameExtractor:
    def __init__(self):
        # 性別と年齢のパターン
        self.sex_age_pattern = re.compile(
            r'([牡牝セ]\s*[\d歳]+)'
        )
        # 余分な情報を除去するパターン
        self.cleanup_patterns = [
            r'※.*$',  # コメント
            r'登録抹消.*$',
            r'[\s　]+$'  # 末尾のスペース
        ]
    
    def extract_horse_name(self, title):
        """タイトルから馬名を抽出"""
        # 最初の「|」より前を取得
        name_part = title.split('|')[0].strip()
        
        # 性別と年齢のパターンを削除
        name = re.sub(self.sex_age_pattern, '', name_part)
        
        # その他の不要な情報を削除
        for pattern in self.cleanup_patterns:
            name = re.sub(pattern, '', name)
        
        # 連続したスペースを1つに
        name = re.sub(r'[\s　]+', ' ', name.strip())
        
        return name
    
    def extract_sex_age(self, title):
        """タイトルから性別と年齢を抽出"""
        match = self.sex_age_pattern.search(title)
        if not match:
            return None, None
            
        sex_age = match.group(1)
        # 性別と年齢を分離
        sex = sex_age[0]  # 最初の1文字が性別
        age = ''.join(c for c in sex_age[1:] if c.isdigit())  # 数字のみ抽出
        
        return sex, age

def update_horses_data():
    """horses.jsonのデータを更新"""
    extractor = HorseNameExtractor()
    
    # ファイルを読み込み
    horses_path = Path('/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json')
    with open(horses_path, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    updated = 0
    for horse in data.get('horses', []):
        # タイトルから情報を抽出
        title = f"{horse.get('name', '')} {horse.get('sex', '')}{horse.get('age', '')}歳"
        
        # 馬名を更新
        new_name = extractor.extract_horse_name(title)
        if new_name and new_name != horse.get('name'):
            print(f"馬名を更新: '{horse.get('name')}' -> '{new_name}'")
            horse['name'] = new_name
            updated += 1
        
        # 性別と年齢を更新（空の場合のみ）
        if not horse.get('age'):
            sex, age = extractor.extract_sex_age(title)
            if sex and age:
                horse['sex'] = sex
                horse['age'] = age
                print(f"性別・年齢を更新: {horse.get('name')} - 性別: {sex}, 年齢: {age}")
                updated += 1
    
    if updated > 0:
        # バックアップを作成
        backup_path = horses_path.with_stem(f"{horses_path.stem}_backup_{horses_path.suffix[1:]}")
        import shutil
        shutil.copy2(horses_path, backup_path)
        print(f"\nバックアップを作成しました: {backup_path}")
        
        # 更新したデータを保存
        with open(horses_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"{updated}件のデータを更新しました")
    else:
        print("更新するデータはありませんでした")

if __name__ == "__main__":
    update_horses_data()
