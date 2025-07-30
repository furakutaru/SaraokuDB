import json
import os
from datetime import datetime

def keep_latest_horses(input_file, output_file, num_horses=9):
    # 入力ファイルを読み込む
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # 馬データを取得
    horses = data.get('horses', [])
    
    # 最新のn頭を取得（IDが大きい順）
    latest_horses = sorted(horses, key=lambda x: x.get('id', 0), reverse=True)[:num_horses]
    
    # メタデータを更新
    data['metadata'] = {
        'last_updated': datetime.now().isoformat(),
        'total_horses': len(latest_horses),
        'description': f'Latest {num_horses} horses only',
        'original_horses': len(horses)
    }
    
    # 馬データを更新
    data['horses'] = latest_horses
    
    # バックアップを作成
    backup_file = f"{input_file}.backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    os.rename(input_file, backup_file)
    print(f"Created backup: {backup_file}")
    
    # 新しいデータを書き込む
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully updated {output_file} with {len(latest_horses)} horses.")

if __name__ == '__main__':
    input_file = '/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses_history.json'
    keep_latest_horses(input_file, input_file, 9)
