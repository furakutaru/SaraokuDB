#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import re
import logging
import traceback
from typing import Optional, Dict, Any
from bs4 import BeautifulSoup

def extract_horse_weight(html_content: str) -> Optional[int]:
    """
    HTMLコンテンツから馬体重を抽出する
    
    Args:
        html_content (str): 馬の詳細ページのHTMLコンテンツ
        
    Returns:
        Optional[int]: 抽出された馬体重（kg単位）、見つからない場合はNone
    """
    try:
        # パターン1: 「最終出走馬体重：392kg」の形式
        weight_match = re.search(r'最終出走馬体重[：:](\d+)kg', html_content)
        
        # パターン2: 「馬体重は416キロ」の形式
        if not weight_match:
            weight_match = re.search(r'馬体重[は:：](\d+)[\sキロ]', html_content)
        
        if weight_match:
            try:
                weight = int(weight_match.group(1))
                logging.debug(f"馬体重を抽出しました: {weight}kg")
                return weight
            except (ValueError, TypeError, IndexError) as e:
                logging.warning(f"馬体重の数値変換に失敗: {weight_match.groups()} - {str(e)}")
        
        # デバッグ用にHTMLの一部を出力
        logging.warning("馬体重を抽出できませんでした")
        debug_section = re.search(r'(?:最終出走馬体重|馬体重)[^\d]*(\d+)', html_content[:1000])
        if debug_section:
            logging.debug(f"一致しなかったパターンの例: {debug_section.group(0)}")
        return None
        
    except Exception as e:
        logging.error(f"馬体重の抽出中にエラーが発生: {str(e)}")
        logging.error(traceback.format_exc())
        return None

def add_horse_weight(horse_info: Dict[str, Any], html_content: str) -> Dict[str, Any]:
    """
    馬情報辞書に馬体重を追加する
    
    Args:
        horse_info (Dict[str, Any]): 馬情報を含む辞書
        html_content (str): 馬の詳細ページのHTMLコンテンツ
        
    Returns:
        Dict[str, Any]: 馬体重が追加された馬情報辞書
    """
    weight = extract_horse_weight(html_content)
    horse_info['weight'] = weight  # Always set weight, even if None
    if weight is not None:
        logging.debug(f'馬体重を設定: {weight}kg')
    else:
        logging.debug('馬体重の抽出に失敗しました')
    return horse_info

if __name__ == "__main__":
    # テスト用のコード
    import sys
    
    if len(sys.argv) > 1:
        with open(sys.argv[1], 'r', encoding='utf-8') as f:
            html_content = f.read()
            weight = extract_horse_weight(html_content)
            print(f'抽出された馬体重: {weight}kg' if weight is not None else '馬体重を抽出できませんでした')
