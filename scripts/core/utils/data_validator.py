"""
データのバリデーションを行うユーティリティ
"""
import re
from typing import Any, Dict, List, Optional, Union, Callable, TypeVar, Type
from datetime import datetime, date
from enum import Enum

from ..models.horse import Sex
from ..utils.logger import get_logger

T = TypeVar('T', bound=Enum)

logger = get_logger(__name__)

class ValidationError(ValueError):
    """バリデーションエラークラス"""
    pass

class Validator:
    """データバリデーションのためのユーティリティクラス"""
    
    @staticmethod
    def validate_required(value: Any, field_name: str) -> bool:
        """必須フィールドの検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            
        Returns:
            bool: 検証が成功した場合はTrue
            
        Raises:
            ValidationError: 値が空またはNoneの場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            raise ValidationError(f"{field_name} は必須です")
        return True
    
    @staticmethod
    def validate_string(value: Any, field_name: str, required: bool = True, min_length: int = 1, max_length: int = 255) -> Optional[str]:
        """文字列の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            required: 必須かどうか
            min_length: 最小文字数
            max_length: 最大文字数
            
        Returns:
            Optional[str]: 検証済みの文字列（空文字列の場合は空文字列を返す）
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return value if value == "" else None
            raise ValidationError(f"{field_name} は必須です")
            
        if not isinstance(value, str):
            raise ValidationError(f"{field_name} は文字列である必要があります")
            
        value = str(value).strip()
        
        if len(value) < min_length:
            raise ValidationError(f"{field_name} は{min_length}文字以上で入力してください")
            
        if len(value) > max_length:
            raise ValidationError(f"{field_name} は{max_length}文字以内で入力してください")
            
        return value
    
    @staticmethod
    def validate_integer(value: Any, field_name: str, required: bool = True, min_value: int = None, max_value: int = None) -> Optional[int]:
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
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        try:
            int_value = int(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} は整数である必要があります")
            
        if min_value is not None and int_value < min_value:
            raise ValidationError(f"{field_name} は {min_value} 以上である必要があります")
            
        if max_value is not None and int_value > max_value:
            raise ValidationError(f"{field_name} は {max_value} 以下である必要があります")
            
        return int_value
    
    @staticmethod
    def validate_float(value: Any, field_name: str, required: bool = True, min_value: float = None, max_value: float = None) -> Optional[float]:
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
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        try:
            float_value = float(value)
        except (ValueError, TypeError):
            raise ValidationError(f"{field_name} は数値である必要があります")
            
        if min_value is not None and float_value < min_value:
            raise ValidationError(f"{field_name} は {min_value} 以上である必要があります")
            
        if max_value is not None and float_value > max_value:
            raise ValidationError(f"{field_name} は {max_value} 以下である必要があります")
            
        return float_value
    
    @staticmethod
    def validate_enum(value: Any, field_name: str, enum_class: type, required: bool = True) -> Any:
        """列挙型の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            enum_class: 列挙型クラス
            required: 必須かどうか
            
        Returns:
            Any: 検証済みの列挙値
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        if not isinstance(value, (str, enum_class)):
            raise ValidationError(f"{field_name} は文字列または列挙型である必要があります")
            
        try:
            if isinstance(value, str):
                # 文字列の場合、値と一致する列挙値を探す
                for e in enum_class:
                    if e.value == value:
                        return e
                # 見つからなかった場合はエラー
                raise ValueError()
            return value  # enum_class のインスタンスはそのまま返す
        except (ValueError, TypeError):
            valid_values = [e.value for e in enum_class]
            raise ValidationError(f"{field_name} は {valid_values} のいずれかである必要があります")
    
    @staticmethod
    def validate_boolean(value: Any, field_name: str, required: bool = True) -> Optional[bool]:
        """真偽値の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            required: 必須かどうか
            
        Returns:
            Optional[bool]: 検証済みの真偽値
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        if isinstance(value, bool):
            return value
            
        if isinstance(value, str):
            value = value.lower().strip()
            if value in ('true', '1', 'yes', 'on'):
                return True
            if value in ('false', '0', 'no', 'off'):
                return False
                
        if isinstance(value, int):
            return bool(value)
            
        raise ValidationError(f"{field_name} は真偽値である必要があります")
        
    @staticmethod
    def validate_dict(value: Any, field_name: str, required: bool = True) -> Optional[Dict]:
        """辞書の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            required: 必須かどうか
            
        Returns:
            Optional[Dict]: 検証済みの辞書
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if value is None:
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        if not isinstance(value, dict):
            raise ValidationError(f"{field_name} は辞書である必要があります")
            
        return value
        
    @staticmethod
    def validate_list(value: Any, field_name: str, required: bool = True, min_length: int = 0, 
                     max_length: int = None, element_type: type = None) -> Optional[List]:
        """リストの検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            required: 必須かどうか
            min_length: 最小要素数
            max_length: 最大要素数（オプション）
            element_type: リスト要素の型（オプション）
            
        Returns:
            Optional[List]: 検証済みのリスト
            
        Raises:
            ValidationError: 検証に失敗した場合
        """
        if value is None:
            if not required:
                return None
            raise ValidationError(f"{field_name} は必須です")
            
        if not isinstance(value, (list, tuple)):
            raise ValidationError(f"{field_name} はリストまたはタプルである必要があります")
            
        result = list(value)  # タプルの場合はリストに変換
        
        # 要素の型チェック
        if element_type is not None:
            for i, item in enumerate(result):
                if not isinstance(item, element_type):
                    type_name = element_type.__name__
                    raise ValidationError(f"{field_name} の要素は{type_name}型である必要があります")
        
        if len(result) < min_length:
            raise ValidationError(f"{field_name} は {min_length} 個以上の要素が必要です")
            
        if max_length is not None and len(result) > max_length:
            raise ValidationError(f"{field_name} は {max_length} 個以下の要素である必要があります")
            
        return result
    
    @staticmethod
    def validate_date(value: Any, field_name: str, format: str = "%Y-%m-%d", required: bool = True, min_date: date = None, max_date: date = None) -> Optional[date]:
        """日付文字列の検証
        
        Args:
            value: 検証する値
            field_name: フィールド名（エラーメッセージ用）
            format: 日付フォーマット（デフォルト: YYYY-MM-DD）
            required: 必須かどうか
            min_date: 最小日付（この日付以降であること）
            max_date: 最大日付（この日付以前であること）
            
        Returns:
            Optional[date]: 検証済みの日付オブジェクト（必須でない場合はNoneを返すことがある）
            
        Raises:
            ValueError: 検証に失敗した場合
        """
        if value is None or (isinstance(value, str) and not value.strip()):
            if not required:
                return None
            raise ValueError(f"{field_name} は必須です")
            
        date_value = None
        try:
            if isinstance(value, str):
                # まず日付形式を検証
                try:
                    date_value = datetime.strptime(value, format).date()
                except ValueError:
                    # 日付形式が無効な場合
                    if format == "%Y-%m-%d":
                        raise ValueError(f"{field_name} は日付形式（YYYY-MM-DD）である必要があります")
                    else:
                        display_format = format.replace("%Y", "YYYY").replace("%m", "MM").replace("%d", "DD")
                        raise ValueError(f"{field_name} は日付形式（{display_format}）である必要があります")
            elif isinstance(value, datetime):
                date_value = value.date()
            elif isinstance(value, date):
                date_value = value
            else:
                raise ValueError("Invalid date value")
                
            if min_date is not None and date_value < min_date:
                raise ValueError(f"{field_name} は {min_date.strftime('%Y-%m-%d')} 以降の日付である必要があります")
                
            if max_date is not None and date_value > max_date:
                raise ValueError(f"{field_name} は {max_date.strftime('%Y-%m-%d')} 以前の日付である必要があります")
                
            return date_value
                
        except ValueError as e:
            # 既に設定されたエラーメッセージをそのまま返す
            raise e
        except Exception as e:
            raise ValueError(f"{field_name} は有効な日付である必要があります")
            
