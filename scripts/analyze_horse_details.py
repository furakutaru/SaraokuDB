#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天競馬オークションの詳細ページを分析するスクリプト

このスクリプトは、キャッシュされたHTMLファイルから馬の詳細情報を抽出し、
その結果を分析してレポートを生成します。
"""

import os
import re
import json
import logging
from pathlib import Path
from urllib.parse import urljoin
from typing import Dict, List, Any, Optional, Tuple
from bs4 import BeautifulSoup

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class HorseDetailAnalyzer:
    """馬の詳細ページを分析するクラス"""
    
    def __init__(self, base_url: str = "https://auction.keiba.rakuten.co.jp/"):
        """初期化メソッド"""
        self.base_url = base_url
        self.results = []
        self.field_stats = {}
        self.error_count = 0
        self.total_files = 0
    
    def analyze_directory(self, directory: str, limit: int = 10) -> Dict[str, Any]:
        """指定されたディレクトリ内のHTMLファイルを分析する"""
        directory_path = Path(directory)
        if not directory_path.exists() or not directory_path.is_dir():
            logger.error(f"ディレクトリが見つかりません: {directory}")
            return {}
        
        html_files = list(directory_path.glob("*.html"))
        self.total_files = len(html_files)
        logger.info(f"分析を開始します: {self.total_files}件のHTMLファイルを処理します")
        
        for i, html_file in enumerate(html_files[:limit], 1):
            logger.info(f"処理中: {i}/{min(limit, self.total_files)} - {html_file.name}")
            result = self.analyze_html_file(html_file)
            self.results.append(result)
            
            # フィールドの統計を更新
            self._update_field_stats(result)
        
        return self._generate_report()
    
    def analyze_html_file(self, file_path: Path) -> Dict[str, Any]:
        """単一のHTMLファイルを分析する"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                html_content = f.read()
            
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # 基本情報の抽出
            result = {
                'file': str(file_path.name),
                'extracted_data': {},
                'status': 'success'
            }
            
            # 1. 馬名の抽出
            name_elem = soup.select_one('title')
            if name_elem:
                result['extracted_data']['name'] = name_elem.get_text(strip=True).split('|')[0].strip()
            
            # 2. 基本情報のテーブルを探す
            info_table = soup.select_one('table')
            if info_table:
                # テーブル内のテキストを取得
                table_text = info_table.get_text(' ', strip=True)
                result['extracted_data']['table_text'] = table_text
                
                # 血統情報の抽出
                pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\s]+)', table_text)
                if pedigree_match:
                    result['extracted_data']['sire'] = pedigree_match.group(1)
                    result['extracted_data']['dam'] = pedigree_match.group(2)
                    result['extracted_data']['damsire'] = pedigree_match.group(3)
                
                # 通算成績の抽出
                record_match = re.search(r'通算成績：([^\s]+)', table_text)
                if record_match:
                    result['extracted_data']['record'] = record_match.group(1)
                
                # 馬体重の抽出
                weight_match = re.search(r'馬体重：([\d,]+)kg', table_text)
                if not weight_match:
                    weight_match = re.search(r'最終出走馬体重：([\d,]+)kg', table_text)
                if weight_match:
                    result['extracted_data']['weight'] = int(weight_match.group(1).replace(',', ''))
                
                # 獲得賞金の抽出
                prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', table_text)
                if prize_match:
                    result['extracted_data']['prize_money'] = float(prize_match.group(1).replace(',', ''))
                
                # 生年月日の抽出
                birth_match = re.search(r'(\d{4})年(\d+)月(\d+)日生', table_text)
                if birth_match:
                    result['extracted_data']['birth_date'] = f"{birth_match.group(1)}-{birth_match.group(2).zfill(2)}-{birth_match.group(3).zfill(2)}"
            
            # 3. 画像URLの抽出
            img_elem = soup.select_one('img[src*="/horse/"]')
            if img_elem:
                img_src = img_elem.get('src', '')
                result['extracted_data']['image_url'] = urljoin(self.base_url, img_src) if img_src else ''
            
            # 4. コメントの抽出
            comment_elem = soup.find('div', class_=lambda x: x and 'comment' in str(x).lower())
            if comment_elem:
                result['extracted_data']['comment'] = comment_elem.get_text(' ', strip=True)[:200] + '...'  # 最初の200文字のみ
            
            return result
            
        except Exception as e:
            self.error_count += 1
            logger.error(f"{file_path.name} の解析中にエラーが発生しました: {e}")
            return {
                'file': str(file_path.name),
                'error': str(e),
                'status': 'error'
            }
    
    def _update_field_stats(self, result: Dict[str, Any]) -> None:
        """フィールドの統計情報を更新する"""
        if result.get('status') != 'success' or 'extracted_data' not in result:
            return
        
        for field, value in result['extracted_data'].items():
            if field not in self.field_stats:
                self.field_stats[field] = {
                    'count': 0,
                    'sample': None
                }
            
            self.field_stats[field]['count'] += 1
            
            # 最初のサンプルを保存
            if self.field_stats[field]['sample'] is None:
                self.field_stats[field]['sample'] = value
    
    def _generate_report(self) -> Dict[str, Any]:
        """分析レポートを生成する"""
        success_count = sum(1 for r in self.results if r.get('status') == 'success')
        error_rate = (self.error_count / len(self.results)) * 100 if self.results else 0
        
        # フィールドごとの存在率を計算
        field_coverage = {}
        for field, stats in self.field_stats.items():
            field_coverage[field] = {
                'count': stats['count'],
                'coverage': (stats['count'] / len(self.results)) * 100,
                'sample': stats['sample']
            }
        
        # カバレッジでソート
        field_coverage = dict(sorted(
            field_coverage.items(),
            key=lambda x: x[1]['coverage'],
            reverse=True
        ))
        
        return {
            'total_files': self.total_files,
            'processed': len(self.results),
            'success': success_count,
            'errors': self.error_count,
            'error_rate': error_rate,
            'field_coverage': field_coverage,
            'sample_results': self.results[:3]  # 最初の3件の結果をサンプルとして含める
        }

def main():
    """メインの実行関数"""
    import argparse
    
    parser = argparse.ArgumentParser(description='楽天競馬オークションの詳細ページを分析する')
    parser.add_argument('directory', help='分析するHTMLファイルが含まれるディレクトリ')
    parser.add_argument('--limit', type=int, default=10, help='処理する最大ファイル数')
    parser.add_argument('--output', help='結果を保存するJSONファイルのパス')
    args = parser.parse_args()
    
    analyzer = HorseDetailAnalyzer()
    report = analyzer.analyze_directory(args.directory, args.limit)
    
    # レポートを表示
    print("\n=== 分析レポート ===")
    print(f"処理したファイル数: {report['processed']}/{report['total_files']}")
    print(f"成功: {report['success']}")
    print(f"エラー: {report['errors']} (エラー率: {report['error_rate']:.1f}%)")
    
    print("\n=== フィールドカバレッジ ===")
    for field, stats in report['field_coverage'].items():
        print(f"{field}: {stats['coverage']:.1f}% ({stats['count']}/{report['processed']})")
        if stats['sample'] is not None and field != 'table_text' and field != 'comment':
            print(f"  例: {stats['sample']}")
    
    # 結果をJSONファイルに保存
    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        print(f"\n結果を {args.output} に保存しました")
    
    return 0

if __name__ == "__main__":
    import sys
    sys.exit(main())
