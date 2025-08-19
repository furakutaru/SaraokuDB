#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import sys
import os
import re
import logging

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('encoding_check.log', mode='w', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)

def check_file_encoding(filepath):
    """ファイルのエンコーディングをチェックし、内容を表示する"""
    try:
        # ファイルをバイナリモードで読み込む
        with open(filepath, 'rb') as f:
            content = f.read()
            
        # ファイルサイズを表示
        logger.info(f"ファイルサイズ: {len(content)} バイト")
        
        # 先頭1000バイトを16進数で表示
        hex_dump = ' '.join(f'{b:02x}' for b in content[:1000])
        logger.info(f"先頭1000バイト (16進数): {hex_dump}")
        
        # 文字列として表示
        try:
            # UTF-8でデコードを試みる
            decoded = content.decode('utf-8')
            logger.info("\n=== UTF-8 デコード結果 (先頭500文字) ===")
            logger.info(decoded[:500])
        except UnicodeDecodeError as e:
            logger.error(f"UTF-8 デコードエラー: {e}")
            
            # Shift-JISでデコードを試みる
            try:
                decoded = content.decode('shift_jis')
                logger.info("\n=== Shift-JIS デコード結果 (先頭500文字) ===")
                logger.info(decoded[:500])
            except UnicodeDecodeError as e:
                logger.error(f"Shift-JIS デコードエラー: {e}")
        
        # タイトルタグを検索
        title_match = re.search(rb'<title>(.*?)</title>', content, re.DOTALL)
        if title_match:
            title = title_match.group(1)
            logger.info("\n=== タイトルタグの内容 (生データ) ===")
            logger.info(title)
            
            # タイトルをUTF-8でデコード
            try:
                title_decoded = title.decode('utf-8')
                logger.info("\n=== タイトル (UTF-8デコード) ===")
                logger.info(title_decoded)
                
                # 繁殖牝馬のチェック
                if '繁殖牝馬' in title_decoded:
                    logger.info("繁殖牝馬のキーワードを検出しました")
                else:
                    logger.info("繁殖牝馬のキーワードは見つかりませんでした")
                    
            except UnicodeDecodeError:
                logger.error("タイトルのデコードに失敗しました")
        else:
            logger.warning("タイトルタグが見つかりませんでした")
            
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}")

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(f"使用法: {sys.argv[0]} <ファイルパス>")
        sys.exit(1)
    
    filepath = sys.argv[1]
    if not os.path.exists(filepath):
        logger.error(f"ファイルが見つかりません: {filepath}")
        sys.exit(1)
    
    check_file_encoding(filepath)
