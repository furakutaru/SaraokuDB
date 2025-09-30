import json
import re
from pathlib import Path
from bs4 import BeautifulSoup
from datetime import datetime

# 設定
HORSES_JSON_PATH = Path('/Users/yum.ishii/SaraokuDB/static-frontend/public/data/horses.json')
CACHE_DIR = Path('/Users/yum.ishii/SaraokuDB/cache/20250822_190555/')
BACKUP_DIR = Path('/Users/yum.ishii/SaraokuDB/data/backups')

# バックアップディレクトリの作成
BACKUP_DIR.mkdir(parents=True, exist_ok=True)

def extract_age_from_html(html_content: str) -> int:
    """HTMLから年齢を抽出する
    
    Args:
        html_content (str): HTMLコンテンツ
        
    Returns:
        int: 抽出された年齢（見つからない場合はNone）
    """
    try:
        # まずタイトルから年齢を抽出
        title_match = re.search(r'<title>(.*?)</title>', html_content)
        if title_match:
            title_text = title_match.group(1)
            # 全角数字を半角に変換
            title_text = title_text.translate(str.maketrans(
                '０１２３４５６７８９', '0123456789'))
            
            # パターン1: 「○歳」の形式（半角・全角両方に対応）
            age_match = re.search(r'(\d+)[\s　]*[歳才]', title_text)
            if age_match:
                return int(age_match.group(1))
                
            # パターン2: 「セン3歳」や「牝3歳」などのパターン
            age_match = re.search(r'[セン牝牡セ]\s*(\d+)[\s　]*[歳才]', title_text)
            if age_match:
                return int(age_match.group(1))
        
        # 生年月日から年齢を計算
        birth_year_match = re.search(r'(\d{4})年\s*\d{1,2}月\s*\d{1,2}日', html_content)
        if birth_year_match:
            birth_year = int(birth_year_match.group(1))
            current_year = datetime.now().year
            return current_year - birth_year
            
        # その他のパターンで検索
        # HTML全体から年齢を検索（最小限のパターンのみ）
        text = ' '.join(re.findall(r'>(.*?)<', html_content))  # タグの外側のテキストを取得
        text = text.translate(str.maketrans('０１２３４５６７８９', '0123456789'))
        
        # パターン3: 「年齢: ○」の形式
        age_match = re.search(r'(?:年齢|Age|年令)[:：]?\s*(\d+)', text)
        if age_match:
            return int(age_match.group(1))
            
        # パターン4: 数値 + 歳/才 の形式
        age_match = re.search(r'(\d+)[\s　]*[歳才]', text)
        if age_match:
            return int(age_match.group(1))
            
        return None
        
    except Exception as e:
        print(f"年齢抽出エラー: {str(e)}")
        return None

def update_horses_age():
    """horses.jsonの年齢情報を更新する"""
    # バックアップを作成
    backup_path = BACKUP_DIR / f"horses_backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
    with open(HORSES_JSON_PATH, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # バックアップを保存
    with open(backup_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    print(f"バックアップを保存しました: {backup_path}")
    
    updated_count = 0
    not_found_count = 0
    
    for horse in data['horses']:
        # すでに年齢がある場合はスキップ
        if horse.get('age'):
            continue
            
        # キャッシュファイルを検索
        cache_file = None
        # 馬名から不要な文字を削除（「 セン歳」などを削除）
        clean_name = re.sub(r'\s*セン[\s　]*[歳才]?\s*$', '', horse['name'].strip())
        clean_name = re.sub(r'\s+', ' ', clean_name).strip()
        
        # キャッシュファイルを検索（複数の可能性がある場合に備えてリストに保持）
        cache_files = []
        for f in CACHE_DIR.rglob('*.html'):
            with open(f, 'r', encoding='utf-8', errors='ignore') as html_file:
                content = html_file.read()
                # 馬名を直接検索（完全一致または部分一致）
                if clean_name in content:
                    cache_files.append((f, content))
        
        # 最もマッチするファイルを選択（タイトルに馬名が含まれるファイルを優先）
        best_match = None
        best_score = 0
        
        for f, content in cache_files:
            score = 0
            # タイトルに馬名が含まれる場合は高スコア
            title_match = re.search(r'<title>(.*?)</title>', content)
            if title_match and clean_name in title_match.group(1):
                score += 2
            # ファイル名に馬名が含まれる場合も高スコア
            if clean_name in str(f):
                score += 1
                
            if score > best_score:
                best_score = score
                best_match = f
        
        cache_file = best_match
        
        if not cache_file:
            print(f"警告: {horse['name']} (クリーン名: {clean_name}) のキャッシュファイルが見つかりません")
            if cache_files:
                print(f"  候補ファイル: {[str(f[0]) for f in cache_files[:3]]}...")
            not_found_count += 1
            continue
        
        try:
            # HTMLから年齢を抽出
            with open(cache_file, 'r', encoding='utf-8', errors='ignore') as f:
                html_content = f.read()
                age = extract_age_from_html(html_content)
                
                if age is not None:
                    horse['age'] = age
                    updated_count += 1
                    print(f"更新: {horse['name']} - 年齢: {age}歳")
                else:
                    # 年齢が見つからなかった場合、ファイルの内容をデバッグ用に保存
                    debug_dir = Path('debug_age_extraction')
                    debug_dir.mkdir(exist_ok=True)
                    debug_file = debug_dir / f"{horse['name']}.html"
                    with open(debug_file, 'w', encoding='utf-8') as df:
                        df.write(html_content[:5000])  # 最初の5000文字を保存
                    print(f"警告: {horse['name']} から年齢を抽出できませんでした。デバッグ用ファイルを保存: {debug_file}")
                    
        except Exception as e:
            print(f"エラー: {horse['name']} の処理中にエラーが発生しました: {str(e)}")
    
    # 更新したデータを保存
    with open(HORSES_JSON_PATH, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
    
    print(f"\n{updated_count}件の年齢情報を更新しました")
    print(f"{not_found_count}件はキャッシュファイルが見つかりませんでした")
    print(f"元のデータのバックアップ: {backup_path}")

if __name__ == "__main__":
    update_horses_age()
