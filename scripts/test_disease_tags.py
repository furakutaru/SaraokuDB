#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
from pathlib import Path
from typing import Dict, List, Set, Optional, Any
import sys

def load_json_file(file_path: str) -> Dict:
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"ファイルの読み込みに失敗しました: {e}")
        sys.exit(1)

def extract_disease_tags(comment: str) -> str:
    """
    コメントから疾病タグを抽出（複数該当時はカンマ区切り、重複なし）
    
    Args:
        comment: 抽出対象のコメントテキスト
        
    Returns:
        str: 抽出されたタグをカンマ区切りで返す。該当なしの場合は空文字を返す
    """
    try:
        if not comment or not isinstance(comment, str):
            return ""
            
        # 正規化: 全角・半角の統一、改行・タブをスペースに置換
        normalized_comment = comment.translate(
            str.maketrans({
                '\n': ' ', '\t': ' ', '　': ' ',  # 全角スペースも半角に
                '（': '(', '）': ')', '［': '[', '］': ']',
                '，': ',', '．': '.', '：': ':', '；': ';'
            })
        )
        
        # 疾病キーワードと正規表現パターンのマッピング
        disease_patterns = {
            '骨折': [r'骨折', r'こっせつ', r'折[傷損]'],
            '屈腱炎': [r'屈腱炎', r'くっけんえん', r'屈腱の?炎症'],
            '球節炎': [r'球節炎', r'きゅうせつえん', r'球節の?炎症'],
            '蹄葉炎': [r'蹄葉炎', r'ていようえん', r'蹄の?炎症', r'蹄葉の?炎症'],
            '靭帯損傷': [r'靭帯(損傷|断裂|切[断裁])', r'じんたい(そんしょう|だんれつ|せつ[だんざい])'],
            '捻挫': [r'捻挫', r'ねんざ'],
            '腫れ': [r'腫[れ脹]', r'はれ', r'腫脹'],
            '炎症': [r'炎症', r'えんしょう'],
            '裂蹄': [r'裂蹄', r'れってい'],
            '関節炎': [r'関節炎', r'かんせつえん'],
            '筋炎': [r'筋炎', r'きんえん'],
            '筋肉痛': [r'筋肉痛', r'きんにくつう'],
            '神経麻痺': [r'神経麻痺', r'しんけいまひ'],
            '腰痛': [r'腰痛', r'ようつう'],
            '跛行': [r'跛行', r'はこう'],
            '蹄壁疾患': [r'蹄壁(疾患|異常)', r'ていへき(しっかん|いじょう)'],
            '蹄叉腐爛': [r'蹄叉腐爛', r'ていさふらん'],
            '骨膜炎': [r'骨膜炎', r'こつまくえん'],
            '亀裂': [r'亀裂', r'きれつ'],
            '外傷': [r'外傷', r'がいしょう'],
            '脱臼': [r'脱[臼]?', r'だっ[きゅう]'],
            '肉離れ': [r'肉離れ', r'にくばなれ'],
            '裂傷': [r'裂傷', r'れっしょう'],
            '打撲': [r'打撲', r'だぼく'],
            '挫傷': [r'挫傷', r'ざしょう'],
            '腫瘍': [r'腫瘍', r'しゅよう'],
            '出血': [r'出血', r'しゅっけつ'],
            '貧血': [r'貧血', r'ひんけつ'],
            '咽頭虚脱': [r'咽頭虚脱', r'いんとうきょだつ'],
            '軟口蓋異常': [r'軟口蓋(異常|麻痺)', r'なんこうがい(いじょう|まひ)'],
            '呼吸器疾患': [r'呼吸器(疾患|異常)', r'こきゅうき(しっかん|いじょう)'],
            '心臓疾患': [r'心臓(疾患|異常)', r'しんぞう(しっかん|いじょう)'],
            '消化器疾患': [r'消化器(疾患|異常)', r'しょうかき(しっかん|いじょう)'],
            '皮膚病': [r'皮膚病', r'ひふびょう', r'皮膚炎'],
            'アレルギー': [r'アレルギー', r'あれるぎー'],
            '感染症': [r'感染症', r'かんせんしょう'],
            '手術歴': [r'手術(歴|を受ける|を実施)', r'しゅじゅつ(れき|をうける|をじっし)'],
        }
        
        found = set()
        
        # 各パターンでマッチング
        for tag, patterns in disease_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_comment, re.IGNORECASE):
                    found.add(tag)
                    break  # 1つでもマッチしたら次のタグへ
        
        # 除外パターン（誤検出を防ぐため）
        exclude_patterns = [
            r'骨折[なけれ]',  # 「骨折なし」など
            r'[な無]?骨折',   # 「無骨折」など
            r'[な無]?炎症',   # 「無炎症」など
            r'異常[な無]',    # 「異常なし」など
            r'問題[な無]',    # 「問題なし」など
            r'[な無]?手術',   # 「無手術」など
            r'[な無]?疾患',   # 「無疾患」など
        ]
        
        # 除外パターンにマッチするタグを削除
        filtered_tags = []
        for tag in found:
            exclude = False
            for pattern in exclude_patterns:
                if re.search(pattern, normalized_comment):
                    exclude = True
                    break
            if not exclude:
                filtered_tags.append(tag)
        
        # 重複を削除してソート
        unique_sorted_tags = sorted(list(set(filtered_tags)))
        
        return ','.join(unique_sorted_tags) if unique_sorted_tags else ""
        
    except Exception as e:
        print(f"疾病タグの抽出に失敗: {e}")
        return ""

def process_horses_data(data: Dict) -> Dict:
    """馬のデータを処理して病歴タグを抽出する"""
    total_horses = 0
    horses_with_disease = 0
    
    print("病歴タグの抽出を開始します...\n")
    
    for horse in data.get('horses', []):
        total_horses += 1
        horse_name = horse.get('name', '不明')
        
        # 各履歴エントリを処理
        for history in horse.get('history', []):
            comment = history.get('comment', '')
            if not comment:
                continue
                
            # 病歴タグを抽出
            disease_tags = extract_disease_tags(comment)
            
            # タグがあれば表示
            if disease_tags:
                print(f"馬名: {horse_name}")
                print(f"抽出タグ: {disease_tags}")
                print(f"コメント: {comment[:100]}...\n")
                horses_with_disease += 1
                break  # 1つでもタグがあれば十分
    
    print(f"\n処理が完了しました。")
    print(f"総馬数: {total_horses}頭")
    print(f"病歴タグが検出された馬: {horses_with_disease}頭")
    
    return data

def main():
    # 入力ファイルと出力ファイルのパス
    input_file = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data' / 'horses_history.json'
    output_file = Path(__file__).parent.parent / 'static-frontend' / 'public' / 'data' / 'horses_history_with_disease.json'
    
    # データを読み込む
    print(f"ファイルを読み込んでいます: {input_file}")
    data = load_json_file(str(input_file))
    
    # 病歴タグを抽出して処理
    processed_data = process_horses_data(data)
    
    # 結果を保存
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(processed_data, f, ensure_ascii=False, indent=2)
    
    print(f"\n結果を保存しました: {output_file}")

if __name__ == "__main__":
    main()
