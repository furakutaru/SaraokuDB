#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Set, Optional, Any, Tuple

# デバッグ用の色設定
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'

def load_json_file(file_path: str) -> Dict:
    """JSONファイルを読み込む"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"{Colors.FAIL}ファイルの読み込みに失敗しました: {e}{Colors.ENDC}")
        sys.exit(1)

def extract_disease_tags(comment: str, debug: bool = False) -> str:
    """
    コメントから疾病タグを抽出（複数該当時はカンマ区切り、重複なし）
    
    Args:
        comment: 抽出対象のコメントテキスト
        debug: デバッグ情報を表示するかどうか
        
    Returns:
        str: 抽出されたタグをカンマ区切りで返す。該当なしの場合は空文字を返す
    """
    try:
        if not comment or not isinstance(comment, str):
            if debug:
                print(f"{Colors.WARNING}コメントが空または文字列ではありません{Colors.ENDC}")
            return ""
            
        if debug:
            print(f"{Colors.HEADER}=== 疾病タグ抽出開始 ==={Colors.ENDC}")
            print(f"{Colors.OKBLUE}コメントの最初の100文字: {comment[:100]}...{Colors.ENDC}")
        
        # 正規化: 全角・半角の統一、改行・タブをスペースに置換
        normalized_comment = comment.translate(
            str.maketrans({
                '\n': ' ', '\t': ' ', '　': ' ',  # 全角スペースも半角に
                '（': '(', '）': ')', '［': '[', '］': ']',
                '，': ',', '．': '.', '：': ':', '；': ';',
                '・': ' ', '、': ' ', '。': ' '  # 句読点もスペースに
            })
        )
        
        if debug:
            print(f"{Colors.OKCYAN}正規化後: {normalized_comment[:100]}...{Colors.ENDC}")
        
        # 疾病キーワードと正規表現パターンのマッピング
        disease_patterns = {
            '骨折': [r'骨折', r'こっせつ', r'折[傷損]'],
            '屈腱炎': [r'屈腱炎', r'くっけんえん', r'屈腱の?炎症'],
            '球節炎': [r'球節炎', r'きゅうせつえん', r'球節の?炎症'],
            '蹄葉炎': [r'蹄葉炎', r'ていようえん', r'蹄の?炎症', r'蹄葉の?炎症'],
            '靭帯損傷': [r'靭帯(損傷|断裂|切[断裁])', r'じんたい(そんしょう|だんれつ|せつ[だんざい])'],
            '捻挫': [r'捻挫', r'ねんざ'],
            '腫れ': [r'腫[れ脹]', r'はれ', r'腫脹'],
            '炎症': [r'(?<![無な])炎症', r'えんしょう(?![なな])'],  # 否定後読み・先読みで除外
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
        
        # 除外パターン（誤検出を防ぐため）
        exclude_patterns = [
            # 骨折関連の除外パターン
            r'骨折[な無]い',         # 「骨折ない」
            r'骨折[はも]?無い',      # 「骨折は無い」「骨折も無い」
            r'骨折[はも]?ない',      # 「骨折はない」「骨折もない」
            r'骨折[はも]?無し',      # 「骨折は無し」「骨折も無し」
            r'骨折[はも]?なし',      # 「骨折はなし」「骨折もなし」
            r'骨折[はも]?無',        # 「骨折は無」「骨折も無」
            r'骨折[はも]?無[かっ]?た', # 「骨折は無かった」「骨折も無かった」
            r'骨折[はも]?な[かっ]?た', # 「骨折はなかった」「骨折もなかった」
            r'骨折[はも]?無いです',  # 「骨折は無いです」「骨折も無いです」
            r'骨折[はも]?無いと',    # 「骨折は無いと」「骨折も無いと」
            r'骨折[はも]?無いが',    # 「骨折は無いが」「骨折も無いが」
            r'骨折[はも]?無いので',  # 「骨折は無いので」「骨折も無いので」
            r'無骨折',               # 「無骨折」
            
            # 炎症関連の除外パターン
            r'[な無]?炎症',          # 「無炎症」「な炎症」
            r'炎症[はも]?無い',      # 「炎症は無い」「炎症も無い」
            r'炎症[はも]?ない',      # 「炎症はない」「炎症もない」
            r'炎症[はも]?無し',      # 「炎症は無し」「炎症も無し」
            r'炎症[はも]?なし',      # 「炎症はなし」「炎症もなし」
            r'炎症[はも]?無',        # 「炎症は無」「炎症も無」
            r'炎症[はも]?無かった',  # 「炎症は無かった」「炎症も無かった」
            r'炎症[はも]?な[かっ]?た', # 「炎症はなかった」「炎症もなかった」
            r'炎症[はも]?無[かっ]?た', # 「炎症は無かった」「炎症も無かった」
            r'炎症[はも]?無いです',  # 「炎症は無いです」「炎症も無いです」
            r'炎症[はも]?無いと',    # 「炎症は無いと」「炎症も無いと」
            r'炎症[はも]?無いが',    # 「炎症は無いが」「炎症も無いが」
            r'炎症[はも]?無いので',  # 「炎症は無いので」「炎症も無いので」
            
            # その他の一般的な除外パターン
            r'異常[な無]',    # 「異常なし」「異常な」
            r'問題[な無]',    # 「問題なし」「問題な」
            r'心配[な無]',    # 「心配なし」「心配な」
            r'懸念[な無]',    # 「懸念なし」「懸念な」
            r'所見[な無]',    # 「所見なし」「所見な」
            r'特記[な無]',    # 「特記なし」「特記な」
            r'以上[な無]',    # 「以上なし」「以上な」
            r'その他[な無]',  # 「その他なし」「その他な」
            r'特にな[し無]',  # 「特になし」「特に無」
            r'現在[はも]?無い', # 「現在は無い」「現在も無い」
            r'現在[はも]?ない', # 「現在はない」「現在もない」
            r'現在[はも]?無し', # 「現在は無し」「現在も無し」
            r'現在[はも]?なし', # 「現在はなし」「現在もなし」
            r'現在[はも]?無',   # 「現在は無」「現在も無」
            r'現在[はも]?無かった', # 「現在は無かった」「現在も無かった」
            r'現在[はも]?な[かっ]?た', # 「現在はなかった」「現在もなかった」
            r'現在[はも]?無[かっ]?た', # 「現在は無かった」「現在も無かった」
            r'現在[はも]?無いです', # 「現在は無いです」「現在も無いです」
            r'現在[はも]?無いと',   # 「現在は無いと」「現在も無いと」
            r'現在[はも]?無いが',   # 「現在は無いが」「現在も無いが」
            r'現在[はも]?無いので'  # 「現在は無いので」「現在も無いので」
        ]
        
        found = set()
        
        # 各パターンでマッチング
        for tag, patterns in disease_patterns.items():
            for pattern in patterns:
                if re.search(pattern, normalized_comment, re.IGNORECASE):
                    if debug:
                        print(f"{Colors.OKGREEN}マッチ: タグ '{tag}' - パターン '{pattern}'{Colors.ENDC}")
                    found.add(tag)
                    break  # 1つでもマッチしたら次のタグへ
        
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
    """馬のデータを処理して病歴タグを抽出し、データに保存する"""
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
                # コメントがなければスキップ
                history['disease_tags'] = ""
                continue
                
            # 病歴タグを抽出
            disease_tags = extract_disease_tags(comment)
            
            # タグを保存
            history['disease_tags'] = disease_tags
            
            # タグがあれば表示
            if disease_tags:
                print(f"馬名: {horse_name}")
                print(f"抽出タグ: {disease_tags}")
                print(f"コメント: {comment[:100]}...\n")
                horses_with_disease += 1
    
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
