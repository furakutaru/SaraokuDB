"""
データのバリデーションを行うユーティリティ
"""
import re
from typing import Any, Dict, List, Optional, Union, Callable
from datetime import datetime

from ..models.horse import Sex
from ..utils.logger import get_logger

logger = get_logger(__name__)

class ValidationError(ValueError):
    """バリデーションエラークラス"""
    pass

class Validator:
    """データバリデーションのためのユーティリティクラス"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> None:
        """必須フィールドの検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            
        Raises:
            ValidationError: 値が空またはNoneの場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name}は必須です")
    
    @staticmethod
    def validate_str(value: Any, field_name: str, min_length: int = 1, max_length: int = 255) -> str:
        """文字列の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            min_length: 最小文字数
            max_length: 最大文字数
            
        Returns:
            str: 検証済みの文字列
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if not isinstance(value, str):
            value = str(value) if value is not None else ""
            
        value = value.strip()
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name}は{min_length}文字以上で入力してください")
            
        if len(value) > max_length:
            raise ValidationError(f"{field_name}は{max_length}文字以内で入力してください")
            
        return value
    
    @staticmethod
    def validate_int(value: Any, field_name: str, min_value: int = None, max_value: int = None) -> int:
        """整数の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            min_value: 最小値（Noneの場合は制限なし）
            max_value: 最大値（Noneの場合は制限なし）
            
        Returns:
            int: 検証済みの整数値
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name}は数値で入力してください")
            
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name}は{min_value}以上で入力してください")
            
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name}は{max_value}以下で入力してください")
            
        return int_value
    
    @staticmethod
    def validate_float(value: Any, field_name: str, min_value: float = None, max_value: float = None) -> float:
        """浮動小数点数の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            min_value: 最小値（Noneの場合は制限なし）
            max_value: 最大値（Noneの場合は制限なし）
            
        Returns:
            float: 検証済みの浮動小数点数値
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name}は数値で入力してください")
            
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name}は{min_value}以上で入力してください")
            
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name}は{max_value}以下で入力してください")
            
        return float_value
    
    @staticmethod
    def validate_enum(value: Any, enum_class: type, field_name: str) -> Any:
        """列挙型の検証
        
        Args:
            value: 検証する値
            enum_class: 列挙型クラス
            field_name: フィールド名（エラーメッセージ用）
            
        Returns:
            Any: 検証済みの列挙値
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        try:
            if isinstance(value, str):
                return enum_class(value)
            return value
        except ValueError:
            valid_values = [e.value for e in enum_class]
            raise ValidationError(f"{field_name}は{', '.join(valid_values)}のいずれかを指定してください")
    
    @staticmethod
    def validate_date(value: Any, field_name: str, format: str = "%Y-%m-%d") -> str:
        """日付文字列の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            format: 日付フォーマット（デフォルト: YYYY-MM-DD）
            
        Returns:
            str: フォーマットされた日付文字列
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if not value:
            raise ValidationError(f"{field_name}は必須です")
            
        if isinstance(value, str):
            try:
                # 日付としてパース可能か確認
                datetime.strptime(value, format)
                return value
            except ValueError:
                pass
                
        raise ValidationError(f"{field_name}は{format}形式で入力してください")
