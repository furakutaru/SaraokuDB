#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
馬の画像URLを抽出するモジュール
"""

import logging
from typing import Optional, Any, Dict
from bs4 import BeautifulSoup


class BaseExtractor:
    """抽出処理の基底クラス"""
    
    def __init__(self, logger=None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーオブジェクト（省略可）
        """
        self.logger = logger or logging.getLogger(__name__)
        
    def log_debug(self, message: str):
        """デバッグレベルのログを出力"""
        if self.logger:
            self.logger.debug(message)
            
    def log_info(self, message: str):
        """情報レベルのログを出力"""
        if self.logger:
            self.logger.info(message)
            
    def log_warning(self, message: str):
        """警告レベルのログを出力"""
        if self.logger:
            self.logger.warning(message)
            
    def log_error(self, message: str):
        """エラーレベルのログを出力"""
        if self.logger:
            self.logger.error(message)


class ImageExtractor(BaseExtractor):
    """馬の画像URLを抽出するクラス"""
    
    def extract(self, card) -> tuple[Optional[dict], bool]:
        """
        馬の画像URLを抽出する
        
        Args:
            card: 馬情報を含むHTML要素（BeautifulSoupオブジェクト）
            
        Returns:
            tuple[Optional[dict], bool]: (抽出した画像URLを含む辞書, 成功したかどうか)
        """
        try:
            # カードが文字列の場合はBeautifulSoupオブジェクトに変換
            if isinstance(card, str):
                soup = BeautifulSoup(card, 'html.parser')
            else:
                soup = card
            
            # メイン画像を検索
            big_image = soup.select_one('div.bigImageWrap img.topImage')
            
            if big_image and 'src' in big_image.attrs:
                image_url = big_image['src']
                self.log_debug(f'画像URLを抽出しました: {image_url}')
                return {'image_url': image_url}, True
                
            self.log_warning('画像URLが見つかりませんでした')
            return None, False
            
        except Exception as e:
            self.log_error(f'画像URLの抽出中にエラーが発生しました: {str(e)}')
            return None, False
