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
    
    def extract(self, html_content: str) -> Optional[str]:
        """
        詳細ページのHTMLから馬の画像URLを抽出する
        
        Args:
            html_content (str): 詳細ページのHTML
            
        Returns:
            Optional[str]: 画像のURL（見つからない場合はNone）
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # メイン画像を検索
        big_image = soup.select_one('img.photo')
        
        if big_image and 'src' in big_image.attrs:
            return big_image['src']
            
        return None
