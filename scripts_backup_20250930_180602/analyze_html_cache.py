#!/usr/bin/env python3
"""
HTMLキャッシュファイルを分析し、馬名が複数含まれるファイルを特定するスクリプト
"""
import os
import re
from pathlib import Path
from typing import Dict, List, Set, Tuple, Optional
from collections import defaultdict

# 馬名のパターン（一般的な競走馬名にマッチする正規表現）
HORSE_NAME_PATTERNS = [
    # カタカナ2-10文字（・を含む場合も）
    r'[ァ-ヴー]{2,10}(?:[・][ァ-ヴー]{2,10})?',
    # アルファベットの名前（例：Deep Impact）
    r'\b[A-Z][a-z]+(?: [A-Z][a-z]+)*\b',
    # 日本語の名前（漢字・カタカナ・ひらがな）
    r'[々-龥ァ-ヴぁ-んー]{2,10}(?:[・][々-龥ァ-ヴぁ-んー]{2,10})*',
    # 馬名を含む要素のパターン
    r'data-horse-name=["\']([^"\']+)["\']',
    r'class=["\'][^"\']*horse[^"\']*["\']>[^<]*<[^>]*>([^<]+)<',
    r'<a [^>]*href=["\'][^"\']*horse[^"\']*["\'][^>]*>([^<]+)<',
]

# 無視する一般的な単語
IGNORE_WORDS = {
    # 一般的な単語
    'サラブレッド', 'オークション', '楽天', '競馬', '出品', '落札', '入札',
    '詳細', '情報', '血統', '競走馬', 'メール', '連絡先', '電話', 'FAX',
    'モバイル', '担当者', 'スケジュール', '出品申込', '締切', '更新',
    '商品ページ', 'オークション開始', 'キャンセル', '予約', '購入', '販売',
    '価格', '円', '万円', '口座', '振込', '銀行', '支店', '普通', 'インボイス',
    '制度', '対応', 'お知らせ', '注意', '利用規約', 'プライバシーポリシー',
    '特定商取引法', '表示', '会社概要', '運営会社', '利用規約', 'ヘルプ',
    'お問い合わせ', 'ログイン', '会員登録', 'マイページ', 'カート', 'お気に入り',
    '検索', 'ジャンル', 'カテゴリ', 'ランキング', '新着', 'おすすめ', '特集',
    'セール', 'キャンペーン', 'イベント', 'ニュース', 'トピックス', 'コラム',
    'インタビュー', 'レポート', 'レース', '競走', '競馬場', 'JRA', 'NAR',
    '地方競馬', '中央競馬', '重賞', 'G1', 'G2', 'G3', 'OP', '芝', 'ダート', '障害',
    '新馬', '未勝利', '1勝', '2勝', '3勝', 'コース', '距離', 'メートル', 'ハロン',
    
    # 一般的な単語（英数字）
    'html', 'http', 'https', 'www', 'com', 'jp', 'net', 'org', 'co', 'js', 'css',
    'var', 'function', 'return', 'true', 'false', 'null', 'undefined', 'object',
    'string', 'number', 'array', 'boolean', 'new', 'Date', 'window', 'document',
    
    # 一般的なクラス名やID
    'header', 'footer', 'content', 'main', 'container', 'wrapper', 'box', 'btn',
    'button', 'menu', 'nav', 'sidebar', 'form', 'input', 'select', 'option', 'img',
    'icon', 'link', 'title', 'text', 'description', 'price', 'date', 'time', 'name',
    
    # その他一般的な単語
    'data', 'item', 'list', 'view', 'page', 'section', 'block', 'element', 'class',
    'id', 'style', 'src', 'href', 'alt', 'title', 'width', 'height', 'color', 'size',
    'type', 'value', 'name', 'id', 'class', 'for', 'role', 'tabindex', 'aria-label',
}

# 無視する一般的な単語
IGNORE_WORDS = {
    'サラブレッド', 'オークション', '楽天', '競馬', '出品', '落札', '入札',
    '詳細', '情報', '血統', '競走馬', 'メール', '連絡先', '電話', 'FAX',
    'モバイル', '担当者', 'スケジュール', '出品申込', '締切', '更新',
    '商品ページ', 'オークション開始', 'キャンセル', '予約', '購入', '販売',
    '価格', '円', '万円', '口座', '振込', '銀行', '支店', '普通', 'インボイス',
    '制度', '対応', 'お知らせ', '注意', '利用規約', 'プライバシーポリシー',
    '特定商取引法', '表示', '会社概要', '運営会社', '利用規約', 'ヘルプ',
    'お問い合わせ', 'ログイン', '会員登録', 'マイページ', 'カート', 'お気に入り',
    '検索', 'ジャンル', 'カテゴリ', 'ランキング', '新着', 'おすすめ', '特集',
    '新馬', '未勝利', '1勝', '2勝', '3勝', 'コース', '距離', 'メートル', 'ハロン'
}

def is_valid_horse_name(name: str) -> bool:
    """有効な馬名かどうかをチェックする"""
    # 短すぎる名前は除外
    if len(name) < 2:
        return False
        
    # 無視する単語が含まれている場合は除外
    if any(ignore in name for ignore in IGNORE_WORDS):
        return False
        
    # 数字だけの名前は除外
    if re.match(r'^\d+$', name):
        return False
        
    # 一般的なファイル拡張子は除外
    if any(ext in name.lower() for ext in ['.jpg', '.png', '.gif', '.js', '.css']):
        return False
        
    return True

def find_horse_names(text: str) -> Set[str]:
    """テキストから馬名を抽出する"""
    # スクリプトとスタイルタグを削除
    text = re.sub(r'<script\b[^<]*(?:(?!<\/script>)<[^<]*)*<\/script>', '', text, flags=re.IGNORECASE)
    text = re.sub(r'<style\b[^<]*(?:(?!<\/style>)<[^<]*)*<\/style>', '', text, flags=re.IGNORECASE)
    
    # コメントを削除
    text = re.sub(r'<!--.*?-->', '', text, flags=re.DOTALL)
    
    # 馬名を抽出する前に、馬名が含まれていそうな部分を特定
    horse_sections = []
    
    # 馬名が含まれていそうなセクションを抽出
    horse_blocks = re.findall(r'(<div[^>]*class=["\'].*?horse.*?["\'][^>]*>.*?<\/div>)', text, re.DOTALL | re.IGNORECASE)
    horse_sections.extend(horse_blocks)
    
    # テーブル内の行からも抽出を試みる
    table_rows = re.findall(r'<tr[^>]*>.*?<\/tr>', text, re.DOTALL | re.IGNORECASE)
    for row in table_rows:
        if 'horse' in row.lower() or '馬名' in row or '競走馬' in row:
            horse_sections.append(row)
    
    # 馬名が含まれていそうなセクションが見つからない場合は全文を使用
    if not horse_sections:
        horse_sections = [text]
    
    horse_names = set()
    
    # 各セクションから馬名を抽出
    for section in horse_sections:
        # HTMLタグを一時的に保持
        temp_text = section
        
        # 馬名が含まれていそうな要素を抽出
        for pattern in HORSE_NAME_PATTERNS:
            matches = re.finditer(pattern, temp_text)
            for match in matches:
                # グループ1があればそれを使用、なければマッチ全体を使用
                name = match.group(1) if len(match.groups()) > 0 else match.group(0)
                if not name:
                    continue
                name = name.strip('"\'')
                # 余分な引用符や括弧を削除
                name = re.sub(r'^[\"\'\[\(]*(.*?)[\"\'\]\)]*$', r'\1', name)
                if is_valid_horse_name(name):
                    horse_names.add(name)
        
        # タグ内のテキストからも抽出を試みる
        temp_text = re.sub(r'<[^>]+>', ' ', temp_text)  # HTMLタグをスペースに置換
        temp_text = re.sub(r'&[a-z0-9]+;', ' ', temp_text)  # HTMLエンティティをスペースに
        temp_text = re.sub(r'\s+', ' ', temp_text).strip()  # 連続する空白を1つに
        
        # 長いテキストから馬名らしきものを抽出
        words = re.findall(r'[\w・]{2,20}', temp_text)
        for word in words:
            if is_valid_horse_name(word):
                horse_names.add(word)
    
    return horse_names

def analyze_cache_files(cache_dir: str = 'html_cache', min_horses: int = 2) -> Dict[str, List[str]]:
    """キャッシュディレクトリ内のHTMLファイルを分析し、馬名が複数含まれるファイルを返す"""
    cache_path = Path(cache_dir)
    if not cache_path.exists() or not cache_path.is_dir():
        print(f"エラー: キャッシュディレクトリ '{cache_dir}' が見つかりません")
        return {}
    
    result = {}
    
    # HTMLファイルを処理
    for file_path in cache_path.glob('*.html'):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
                # 馬名を検索
                horse_names = find_horse_names(content)
                
                # 馬名が一定数以上見つかった場合に記録
                if len(horse_names) >= min_horses:
                    result[str(file_path)] = sorted(list(horse_names))
                    print(f"Found {len(horse_names)} horse names in {file_path.name}")
                    
        except Exception as e:
            print(f"エラー: {file_path} の処理中にエラーが発生しました: {e}")
    
    return result

def main():
    print("HTMLキャッシュファイルの分析を開始します...")
    
    # キャッシュディレクトリ内のファイルを分析
    horse_files = analyze_cache_files()
    
    # 結果を表示
    if horse_files:
        print("\n馬名が複数含まれるファイルが見つかりました:")
        print("-" * 80)
        
        for file_path, names in horse_files.items():
            print(f"\nファイル: {file_path}")
            print(f"馬名 ({len(names)}件): {', '.join(names[:10])}" + 
                  ("..." if len(names) > 10 else ""))
    else:
        print("\n馬名が複数含まれるファイルは見つかりませんでした。")

if __name__ == "__main__":
    main()
