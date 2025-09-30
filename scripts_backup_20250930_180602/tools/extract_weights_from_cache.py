#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import re
import json
import logging
from pathlib import Path
from bs4 import BeautifulSoup
from typing import Dict, List, Optional, Tuple

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('extract_weights.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

class WeightExtractor:
    """キャッシュファイルから馬の体重情報を抽出するクラス"""
    
    def __init__(self, cache_dir: str, output_file: str = 'extracted_weights.json'):
        """
        初期化
        
        Args:
            cache_dir: キャッシュファイルが保存されているディレクトリ
            output_file: 抽出結果を保存するファイル名
        """
        self.cache_dir = Path(cache_dir)
        self.output_file = Path(output_file)
        self.results: List[Dict[str, any]] = []
    
    def extract_weight(self, soup: BeautifulSoup) -> Optional[int]:
        """
        BeautifulSoupオブジェクトから馬体重を抽出する
        
        Args:
            soup: 解析対象のBeautifulSoupオブジェクト
            
        Returns:
            Optional[int]: 抽出された馬体重（kg）、抽出できない場合はNone
        """
        try:
            # 馬体重を含む可能性のある要素を検索
            weight_elements = soup.find_all(string=re.compile(r'\d+\s*kg'))
            
            for elem in weight_elements:
                # 数値と「kg」の組み合わせを検索
                match = re.search(r'(\d+)\s*kg', elem, re.IGNORECASE)
                if match:
                    weight = int(match.group(1))
                    # 馬体重として妥当な範囲かチェック（300kg〜600kg）
                    if 300 <= weight <= 600:
                        return weight
            
            return None
            
        except Exception as e:
            logger.error(f"馬体重の抽出中にエラーが発生しました: {str(e)}")
            return None
    
    def extract_horse_info(self, soup: BeautifulSoup, file_path: Path) -> Dict[str, any]:
        """
        馬の基本情報を抽出する
        
        Args:
            soup: 解析対象のBeautifulSoupオブジェクト
            file_path: 解析対象のファイルパス
            
        Returns:
            Dict[str, any]: 抽出された馬の情報
        """
        result = {
            'file': str(file_path.name),
            'name': None,
            'weight': None,
            'sex': None,
            'age': None
        }
        
        try:
            # 馬名の抽出
            title_elem = soup.find('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                # タイトルから馬名を抽出（例: 「メイショウユウモウ　　セン３歳　　※中央競馬　登録抹消」）
                name_match = re.search(r'^([^※]+?)(?:\s*※|$)', title_text)
                if name_match:
                    result['name'] = name_match.group(1).strip()
            
            # 性別・年齢の抽出
            info_elem = soup.find(string=re.compile(r'[牡牝セ]\s*\d*'))
            if info_elem:
                info_text = info_elem.get_text(strip=True)
                # 性別（牡・牝・セ）
                sex_match = re.search(r'([牡牝セ])', info_text)
                if sex_match:
                    result['sex'] = sex_match.group(1)
                # 年齢（数字）
                age_match = re.search(r'(\d+)', info_text)
                if age_match:
                    result['age'] = int(age_match.group(1))
            
            # 馬体重の抽出
            result['weight'] = self.extract_weight(soup)
            
        except Exception as e:
            logger.error(f"馬情報の抽出中にエラーが発生しました ({file_path}): {str(e)}")
        
        return result
    
    def process_cache_files(self):
        """キャッシュファイルを処理する"""
        # キャッシュファイルの一覧を取得
        cache_files = list(self.cache_dir.glob('**/*.html'))
        logger.info(f"処理対象のキャッシュファイル数: {len(cache_files)}")
        
        for i, file_path in enumerate(cache_files, 1):
            try:
                # HTMLファイルを読み込む
                with open(file_path, 'r', encoding='utf-8') as f:
                    html_content = f.read()
                
                # BeautifulSoupで解析
                soup = BeautifulSoup(html_content, 'html.parser')
                
                # 馬情報を抽出
                horse_info = self.extract_horse_info(soup, file_path)
                self.results.append(horse_info)
                
                # 進捗をログに出力
                if i % 10 == 0 or i == len(cache_files):
                    logger.info(f"処理中: {i}/{len(cache_files)} ファイル目")
                
            except Exception as e:
                logger.error(f"ファイルの処理中にエラーが発生しました ({file_path}): {str(e)}")
    
    def save_results(self):
        """抽出結果をJSONファイルに保存する"""
        try:
            with open(self.output_file, 'w', encoding='utf-8') as f:
                json.dump(self.results, f, ensure_ascii=False, indent=2)
            logger.info(f"抽出結果を {self.output_file} に保存しました")
        except Exception as e:
            logger.error(f"結果の保存中にエラーが発生しました: {str(e)}")

def main():
    # キャッシュディレクトリのパス
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache"
    
    # 出力ファイルのパス
    output_file = "/Users/yum.ishii/SaraokuDB/extracted_weights.json"
    
    # 抽出処理を実行
    extractor = WeightExtractor(cache_dir, output_file)
    extractor.process_cache_files()
    extractor.save_results()
    
    # 結果のサマリーを表示
    total = len(extractor.results)
    with_weight = sum(1 for r in extractor.results if r['weight'] is not None)
    logger.info(f"処理が完了しました。合計 {total} 件中、馬体重が抽出できたのは {with_weight} 件です。")

if __name__ == "__main__":
    main()
