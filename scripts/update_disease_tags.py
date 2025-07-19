#!/usr/bin/env python3
"""
既存のJSONデータから疾病タグを再抽出するスクリプト
疾病ワードリストを更新した後に実行して、過去分にも疾病タグを反映
"""

import json
import os
import sys
import re
from typing import List, Dict
from backend.database.models import SessionLocal, Horse

# 疾病ワードリスト（scripts/scrape.pyと同じ）
DISEASE_WORDS = [
    "骨折", "屈腱炎", "喉鳴り", "疝痛", "蹴行", "球節炎", "骨瘤", "骨膜炎", "骨軟骨症", "骨折歴", "骨片",
    "喉頭片麻痺", "喘鳴症", "脚部不安", "関節炎", "腱炎", "脱臼", "筋肉痛", "腰痛", "腹痛",
    "さく癖", "軟腫", "傷腫れ", "捻挫", "痒痛"
    # 必要に応じて追加
]

# 否定表現のパターン
NEGATION_PATTERNS = [
    r'なし', r'無し', r'ない', r'無い', r'ありません', r'ありませんでした',
    r'見られない', r'認められない', r'確認されない', r'発見されない',
    r'異常なし', r'問題なし', r'特になし', r'特にない'
]

def extract_disease_tags(comment: str) -> List[str]:
    """コメントから疾病ワードを抽出しリストで返す（否定表現を除外）"""
    if not comment or comment == "なし":
        return []
    
    tags = []
    comment_lower = comment.lower()
    
    for word in DISEASE_WORDS:
        if word in comment:
            # 否定表現をチェック
            if not is_negated(comment, word):
                tags.append(word)
    
    return list(set(tags))  # 重複排除

def is_negated(comment: str, disease_word: str) -> bool:
    """疾病ワードが否定表現で使われているかチェック"""
    # 疾病ワードの前後の文脈をチェック
    word_index = comment.find(disease_word)
    if word_index == -1:
        return False
    
    # 疾病ワードの前後20文字を取得
    start = max(0, word_index - 20)
    end = min(len(comment), word_index + len(disease_word) + 20)
    context = comment[start:end]
    
    # 否定表現パターンをチェック
    for pattern in NEGATION_PATTERNS:
        if re.search(pattern, context):
            return True
    
    return False

def update_disease_tags_in_json(json_path: str, output_path: str = None):
    """JSONファイルの疾病タグを更新"""
    if output_path is None:
        output_path = json_path
    
    try:
        # JSONファイルを読み込み
        with open(json_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print(f"処理開始: {len(data.get('horses', []))}頭の馬データ")
        
        # 各馬の疾病タグを更新
        updated_count = 0
        for horse in data.get('horses', []):
            old_tags = horse.get('disease_tags', '')
            comment = horse.get('comment', '')
            
            # 疾病タグを再抽出
            new_tags = extract_disease_tags(comment)
            
            # タグを文字列に変換（カンマ区切り）
            if new_tags:
                horse['disease_tags'] = ', '.join(new_tags)
            else:
                horse['disease_tags'] = 'なし'
            
            # 変更があったかチェック
            if old_tags != horse['disease_tags']:
                updated_count += 1
                print(f"更新: {horse.get('name', 'Unknown')} - {old_tags} → {horse['disease_tags']}")
        
        # 更新されたJSONを保存
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"\n処理完了: {updated_count}頭の疾病タグを更新しました")
        print(f"保存先: {output_path}")
        
    except Exception as e:
        print(f"エラーが発生しました: {e}")

def migrate_auction_date_to_array():
    db = SessionLocal()
    try:
        horses = db.query(Horse).all()
        updated = 0
        for horse in horses:
            # auction_dateがNoneならスキップ
            if horse.__dict__["auction_date"] is None:
                continue
            # 既に配列(JSON)ならスキップ
            try:
                val = json.loads(horse.__dict__["auction_date"])
                if isinstance(val, list):
                    continue
            except Exception:
                pass
            # 配列でなければ配列化
            horse.__dict__["auction_date"] = json.dumps([horse.__dict__["auction_date"]])
            updated += 1
        db.commit()
        print(f"auction_dateを配列化したレコード数: {updated}")
    except Exception as e:
        print(f"auction_date配列化に失敗: {e}")
        db.rollback()
    finally:
        db.close()

def main():
    """メイン処理"""
    # データファイルのパス
    data_dir = os.path.join(os.path.dirname(os.path.dirname(__file__)), 'data')
    json_path = os.path.join(data_dir, 'horses.json')
    
    # static-frontendのpublicディレクトリにもコピー
    static_frontend_path = os.path.join(
        os.path.dirname(os.path.dirname(__file__)), 
        'static-frontend', 'public', 'data', 'horses.json'
    )
    
    if not os.path.exists(json_path):
        print(f"エラー: {json_path} が見つかりません")
        return
    
    print("疾病タグ更新スクリプト（否定表現対応版）")
    print("=" * 60)
    print(f"疾病ワード数: {len(DISEASE_WORDS)}")
    print(f"疾病ワード: {', '.join(DISEASE_WORDS)}")
    print(f"否定表現パターン: {len(NEGATION_PATTERNS)}個")
    print("=" * 60)
    
    # メインデータファイルを更新
    update_disease_tags_in_json(json_path)
    
    # static-frontendのデータファイルも更新（存在する場合）
    if os.path.exists(static_frontend_path):
        print("\nstatic-frontendのデータファイルも更新中...")
        update_disease_tags_in_json(static_frontend_path)
    else:
        print(f"\n注意: {static_frontend_path} が見つかりません")

if __name__ == "__main__":
    migrate_auction_date_to_array()
    main() 