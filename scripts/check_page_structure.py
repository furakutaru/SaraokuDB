#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import json
import logging
from pathlib import Path
from typing import Dict, Any, List, Optional
import requests
from bs4 import BeautifulSoup

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('page_structure_debug.log')
    ]
)
logger = logging.getLogger(__name__)

def save_page_content(url: str, output_dir: str = 'debug_output') -> Dict[str, Any]:
    """ページの内容を保存して構造を分析する"""
    # 出力ディレクトリの作成
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True, parents=True)
    
    # リクエストを送信
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
        'Connection': 'keep-alive',
        'Upgrade-Insecure-Requests': '1',
    }
    
    try:
        logger.info(f"Fetching URL: {url}")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # レスポンスをファイルに保存
        page_content = response.text
        output_file = output_path / 'auction_page.html'
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(page_content)
        logger.info(f"Page content saved to: {output_file}")
        
        # 基本情報を解析
        soup = BeautifulSoup(page_content, 'html.parser')
        
        # ページのメタ情報を収集
        meta_info = {
            'title': getattr(soup.title, 'string', 'No title'),
            'meta_tags': [
                {
                    'name': tag.get('name', ''),
                    'property': tag.get('property', ''),
                    'content': tag.get('content', '')
                }
                for tag in soup.find_all('meta')
            ],
            'h1_tags': [h1.get_text(strip=True) for h1 in soup.find_all('h1')],
            'h2_tags': [h2.get_text(strip=True) for h2 in soup.find_all('h2')],
            'h3_tags': [h3.get_text(strip=True) for h3 in soup.find_all('h3')],
            'form_elements': [
                {
                    'id': form.get('id'),
                    'name': form.get('name'),
                    'action': form.get('action'),
                    'method': form.get('method')
                }
                for form in soup.find_all('form')
            ],
            'script_srcs': [script.get('src') for script in soup.find_all('script') if script.get('src')],
            'link_hrefs': [link.get('href') for link in soup.find_all('link') if link.get('href')],
            'horse_related_elements': []
        }
        
        # 馬に関連する要素を検索
        for element in soup.find_all(True):
            if any(term in str(element).lower() for term in ['馬', 'horse', 'sire', 'dam', 'damsire', 'auction']):
                meta_info['horse_related_elements'].append({
                    'tag': element.name,
                    'class': element.get('class', []),
                    'id': element.get('id'),
                    'text': element.get_text(strip=True)[:100]  # 最初の100文字のみ
                })
        
        # 解析結果を保存
        result_file = output_path / 'page_analysis.json'
        with open(result_file, 'w', encoding='utf-8') as f:
            json.dump(meta_info, f, ensure_ascii=False, indent=2)
        
        logger.info(f"Analysis result saved to: {result_file}")
        return meta_info
        
    except Exception as e:
        logger.error(f"Error fetching page: {e}", exc_info=True)
        return {'error': str(e)}

def main():
    # テスト用のURL
    url = 'https://auction.keiba.rakuten.co.jp/'
    
    # ページの構造を分析
    result = save_page_content(url)
    
    # 結果を表示
    if 'error' in result:
        print(f"エラーが発生しました: {result['error']}")
    else:
        print("\n=== ページ分析結果 ===")
        print(f"タイトル: {result.get('title', 'N/A')}")
        print(f"見出し (h1): {', '.join(result.get('h1_tags', []))}")
        print(f"見出し (h2): {', '.join(result.get('h2_tags', []))}")
        print(f"見出し (h3): {', '.join(result.get('h3_tags', []))}")
        print("\n=== 馬に関連する要素の例 ===")
        for i, elem in enumerate(result.get('horse_related_elements', [])[:5], 1):
            print(f"{i}. {elem.get('tag')} (class: {elem.get('class')}, id: {elem.get('id')}): {elem.get('text')}")

if __name__ == "__main__":
    main()
