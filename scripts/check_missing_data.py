import json
import os
from pathlib import Path

def load_json_data(file_path):
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)

def check_missing_data(data):
    total_horses = len(data.get('horses', []))
    missing_data = {
        'sire': 0,
        'dam': 0,
        'dam_sire': 0,
        'weight': 0,
        'comment': 0,
        'disease_tags': 0,
        'image_url': 0,
        'total_prize': 0
    }
    
    for horse in data.get('horses', []):
        # 最新の履歴を取得
        latest_history = horse.get('history', [{}])[0] if horse.get('history') else {}
        
        # 父、母、母父のチェック（history内の最新データを確認）
        if not latest_history.get('sire') and not horse.get('sire'):
            missing_data['sire'] += 1
        if not latest_history.get('dam') and not horse.get('dam'):
            missing_data['dam'] += 1
        if not latest_history.get('dam_sire') and not horse.get('dam_sire'):
            missing_data['dam_sire'] += 1
            
        # 馬体重のチェック（history内の最新データを確認）
        if not latest_history.get('weight') and not horse.get('weight'):
            missing_data['weight'] += 1
        
        # コメントのチェック（空文字はNG）
        if 'comment' not in latest_history or not latest_history['comment']:
            missing_data['comment'] += 1
        
        # 病気タグのチェック（存在しないかNoneの場合はNG、空文字はOK）
        if 'disease_tags' not in latest_history or latest_history['disease_tags'] is None:
            missing_data['disease_tags'] += 1
        
        # 画像URLのチェック（primary_imageを確認）
        if 'primary_image' not in horse or not horse['primary_image']:
            missing_data['image_url'] += 1
            
        # 総賞金のチェック（total_prize_latestを確認）
        if 'total_prize_latest' not in horse or horse['total_prize_latest'] is None:
            missing_data['total_prize'] += 1
    
    # 結果をパーセンテージで表示
    result = {}
    for key, count in missing_data.items():
        if total_horses > 0:
            percentage = (count / total_horses) * 100
            result[key] = {
                'missing_count': count,
                'percentage': f"{percentage:.1f}%"
            }
    
    return {
        'total_horses': total_horses,
        'missing_data': result
    }

def main():
    # データファイルのパス
    data_dir = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data'
    data_file = data_dir / 'horses_history.json'
    
    if not data_file.exists():
        print(f"エラー: {data_file} が見つかりません。")
        return
    
    # データを読み込む
    print(f"データを読み込み中: {data_file}")
    data = load_json_data(data_file)
    
    # 不足データをチェック
    result = check_missing_data(data)
    
    # 結果を表示
    print(f"\n=== データ取得状況 ===")
    print(f"総馬数: {result['total_horses']}頭")
    print("\n不足データの内訳:")
    for field, info in result['missing_data'].items():
        print(f"- {field}: {info['missing_count']}頭 ({info['percentage']})")
    
    # 結果をファイルに保存
    output_file = data_dir / 'data_coverage_report.json'
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, ensure_ascii=False, indent=2)
    
    print(f"\nレポートを保存しました: {output_file}")

if __name__ == "__main__":
    main()
