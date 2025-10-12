#!/usr/bin/env python3
"""
移行後のデータを検証するスクリプト

使用方法:
    python validate_migrated_data.py <移行後のJSONファイルパス>
"""
import json
import sys
from typing import Dict, List, Any, Optional
from datetime import datetime


def load_json_file(file_path: str) -> Any:
    """JSONファイルを読み込む"""
    with open(file_path, 'r', encoding='utf-8') as f:
        return json.load(f)


def validate_horse(horse: Dict) -> List[str]:
    """1頭分の馬データを検証"""
    errors = []
    
    # 必須フィールドのチェック
    required_fields = ['id', 'basic_info', 'race_records', 'auction_history', 'metadata']
    for field in required_fields:
        if field not in horse:
            errors.append(f"必須フィールドがありません: {field}")
    
    if 'basic_info' in horse:
        basic_info = horse['basic_info']
        required_basic_fields = ['name', 'sex', 'age', 'sire', 'dam', 'damsire']
        for field in required_basic_fields:
            if field not in basic_info or not basic_info[field]:
                errors.append(f"基本情報に必須フィールドがありません: basic_info.{field}")
    
    if 'race_records' in horse:
        race_records = horse['race_records']
        if 'total_prize_money' not in race_records or race_records['total_prize_money'] is None:
            errors.append("レコードに総賞金が設定されていません")
    
    # オークション履歴の検証
    if 'auction_history' in horse and isinstance(horse['auction_history'], list):
        for i, auction in enumerate(horse['auction_history']):
            if not auction.get('date'):
                errors.append(f"オークション履歴 {i+1} に日付が設定されていません")
    
    return errors


def main():
    if len(sys.argv) != 2:
        print("エラー: 引数が正しくありません。")
        print("使用方法: python validate_migrated_data.py <移行後のJSONファイルパス>")
        sys.exit(1)
    
    file_path = sys.argv[1]
    
    try:
        print(f"ファイルを読み込んでいます: {file_path}")
        data = load_json_file(file_path)
        
        # メタデータの検証
        if 'metadata' not in data:
            print("エラー: メタデータがありません")
            sys.exit(1)
        
        # 馬データの検証
        if 'horses' not in data or not isinstance(data['horses'], list):
            print("エラー: 馬データが正しくありません")
            sys.exit(1)
        
        print(f"\n検証を開始します: {len(data['horses'])}頭の馬データ")
        
        # 各馬のデータを検証
        total_errors = 0
        for i, horse in enumerate(data['horses']):
            errors = validate_horse(horse)
            if errors:
                total_errors += len(errors)
                print(f"\n馬ID {horse.get('id', '不明')} でエラーを検出:")
                for error in errors:
                    print(f"  - {error}")
            
            # 進捗表示
            if (i + 1) % 100 == 0:
                print(f"{i + 1}頭を検証しました...")
        
        # 結果を表示
        print("\n" + "=" * 50)
        print(f"検証が完了しました")
        print(f"総馬数: {len(data['horses'])}")
        print(f"検出されたエラー数: {total_errors}")
        
        if total_errors == 0:
            print("\n✅ すべてのデータが正常に検証されました")
        else:
            print(f"\n❌ {total_errors}件のエラーが見つかりました")
            sys.exit(1)
        
    except Exception as e:
        print(f"\nエラーが発生しました: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
