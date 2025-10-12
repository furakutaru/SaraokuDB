"""
抽出処理の基底クラスを提供するモジュール
"""
import logging
from typing import Any, Dict, Optional
from abc import ABC, abstractmethod

class BaseExtractor(ABC):
    """抽出処理の基底クラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    @abstractmethod
    def extract(self, *args, **kwargs) -> Any:
        """抽出処理を実行する抽象メソッド
        
        Returns:
            Any: 抽出結果
        """
        pass
