#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from extract_sold_price import extract_sold_price

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)

def test_sold_price_extraction(html_dir):
    """指定されたディレクトリ内のHTMLファイルから落札価格を抽出してテストする"""
    if not os.path.exists(html_dir):
        print(f"エラー: ディレクトリが見つかりません: {html_dir}")
        return
    
    # HTMLファイルを検索
    html_files = []
    for root, _, files in os.walk(html_dir):
        for file in files:
            if file.endswith('.html'):
                html_files.append(os.path.join(root, file))
    
    if not html_files:
        print(f"エラー: HTMLファイルが見つかりません: {html_dir}")
        return
    
    print(f"\n{'='*80}")
    print(f"落札価格抽出テストを開始します (対象ファイル数: {len(html_files)})")
    print(f"{'='*80}")
    
    # 各HTMLファイルを処理
    results = []
    for i, html_file in enumerate(html_files, 1):
        try:
            with open(html_file, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            # 落札価格を抽出
            price = extract_sold_price(html_content)
            
            # 結果を記録
            result = {
                'file': os.path.basename(html_file),
                'price': price,
                'status': 'success' if price is not None else 'not_found'
            }
            results.append(result)
            
            # 進捗を表示
            print(f"[{i}/{len(html_files)}] {result['file']}: ", end='')
            if result['status'] == 'success':
                print(f"¥{result['price']:,}")
            else:
                print("落札価格が見つかりませんでした")
                
        except Exception as e:
            error_msg = f"エラーが発生しました: {str(e)}"
            results.append({
                'file': os.path.basename(html_file),
                'error': error_msg,
                'status': 'error'
            })
            print(f"[{i}/{len(html_files)}] {os.path.basename(html_file)}: {error_msg}")
    
    # サマリーを表示
    success_count = sum(1 for r in results if r['status'] == 'success')
    not_found_count = sum(1 for r in results if r['status'] == 'not_found')
    error_count = sum(1 for r in results if r['status'] == 'error')
    
    print(f"\n{'='*80}")
    print(f"テスト結果のサマリー:")
    print(f"- 成功: {success_count} 件")
    print(f"- 見つからず: {not_found_count} 件")
    print(f"- エラー: {error_count} 件")
    print(f"{'='*80}")
    
    # 見つからなかったファイルを表示
    if not_found_count > 0:
        print("\n落札価格が見つからなかったファイル:")
        for r in results:
            if r['status'] == 'not_found':
                print(f"- {r['file']}")
    
    # エラーが発生したファイルを表示
    if error_count > 0:
        print("\nエラーが発生したファイル:")
        for r in results:
            if r['status'] == 'error':
                print(f"- {r['file']}: {r.get('error', '不明なエラー')}")
    
    return results

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"使用法: {sys.argv[0]} <HTMLファイルまたはディレクトリ>")
        sys.exit(1)
    
    target_path = sys.argv[1]
    
    # ディレクトリが指定された場合はその中の全HTMLファイルを処理
    if os.path.isdir(target_path):
        test_sold_price_extraction(target_path)
    # ファイルが指定された場合はそのファイルのみを処理
    elif os.path.isfile(target_path) and target_path.endswith('.html'):
        with open(target_path, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        price = extract_sold_price(html_content)
        if price is not None:
            print(f"落札価格: ¥{price:,}")
        else:
            print("落札価格を見つけることができませんでした")
    else:
        print(f"エラー: 無効なパスまたはファイル形式です: {target_path}")
        print("HTMLファイルまたはHTMLファイルを含むディレクトリを指定してください")
