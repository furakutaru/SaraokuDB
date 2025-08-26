"""
データバリデーションのユニットテスト
"""
import unittest
from datetime import datetime

from core.models.horse import Sex
from core.utils.data_validator import Validator

class TestDataValidator(unittest.TestCase):
    """データバリデーションのテスト"""
    
    def setUp(self):
        """テストの前処理"""
        self.validator = Validator()
    
    def test_validate_required(self):
        """必須チェックのテスト"""
        # 正常ケース
        self.assertTrue(self.validator.validate_required("test", "Test Field"))
        
        # エラーケース
        with self.assertRaises(ValueError) as context:
            self.validator.validate_required("", "Test Field")
        self.assertIn("Test Field は必須です", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.validator.validate_required(None, "Test Field")
        self.assertIn("Test Field は必須です", str(context.exception))
        
        with self.assertRaises(ValueError) as context:
            self.validator.validate_required(" ", "Test Field")
        self.assertIn("Test Field は必須です", str(context.exception))
    
    def test_validate_string(self):
        """文字列バリデーションのテスト"""
        # 正常ケース
        self.assertEqual(self.validator.validate_string("test", "Test Field"), "test")
        
        # 前後の空白をトリム
        self.assertEqual(self.validator.validate_string("  test  ", "Test Field"), "test")
        
        # None許容
        self.assertIsNone(self.validator.validate_string(None, "Test Field", required=False))
        
        # 空文字許容
        self.assertEqual(self.validator.validate_string("", "Test Field", required=False), "")
        
        # エラーケース
        with self.assertRaises(ValueError) as context:
            self.validator.validate_string(123, "Test Field")
        self.assertIn("Test Field は文字列である必要があります", str(context.exception))
    
    def test_validate_integer(self):
        """整数バリデーションのテスト"""
        # 正常ケース（文字列から変換）
        self.assertEqual(self.validator.validate_integer("123", "Test Field"), 123)
        
        # 正常ケース（整数）
        self.assertEqual(self.validator.validate_integer(123, "Test Field"), 123)
        
        # None許容
        self.assertIsNone(self.validator.validate_integer(None, "Test Field", required=False))
        
        # 空文字許容
        self.assertIsNone(self.validator.validate_integer("", "Test Field", required=False))
        
        # エラーケース（無効な形式）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_integer("abc", "Test Field")
        self.assertIn("Test Field は整数である必要があります", str(context.exception))
        
        # 最小値チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_integer("10", "Test Field", min_value=20)
        self.assertIn("Test Field は 20 以上である必要があります", str(context.exception))
        
        # 最大値チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_integer("30", "Test Field", max_value=20)
        self.assertIn("Test Field は 20 以下である必要があります", str(context.exception))
    
    def test_validate_float(self):
        """浮動小数点数バリデーションのテスト"""
        # 正常ケース（文字列から変換）
        self.assertEqual(self.validator.validate_float("123.45", "Test Field"), 123.45)
        
        # 正常ケース（浮動小数点数）
        self.assertEqual(self.validator.validate_float(123.45, "Test Field"), 123.45)
        
        # None許容
        self.assertIsNone(self.validator.validate_float(None, "Test Field", required=False))
        
        # 空文字許容
        self.assertIsNone(self.validator.validate_float("", "Test Field", required=False))
        
        # エラーケース（無効な形式）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_float("abc", "Test Field")
        self.assertIn("Test Field は数値である必要があります", str(context.exception))
        
        # 最小値チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_float("10.5", "Test Field", min_value=20.0)
        self.assertIn("Test Field は 20.0 以上である必要があります", str(context.exception))
        
        # 最大値チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_float("30.5", "Test Field", max_value=20.0)
        self.assertIn("Test Field は 20.0 以下である必要があります", str(context.exception))
    
    def test_validate_boolean(self):
        """真偽値バリデーションのテスト"""
        # 正常ケース（真）
        self.assertTrue(self.validator.validate_boolean(True, "Test Field"))
        self.assertTrue(self.validator.validate_boolean("true", "Test Field"))
        self.assertTrue(self.validator.validate_boolean("True", "Test Field"))
        self.assertTrue(self.validator.validate_boolean("1", "Test Field"))
        self.assertTrue(self.validator.validate_boolean(1, "Test Field"))
        
        # 正常ケース（偽）
        self.assertFalse(self.validator.validate_boolean(False, "Test Field"))
        self.assertFalse(self.validator.validate_boolean("false", "Test Field"))
        self.assertFalse(self.validator.validate_boolean("False", "Test Field"))
        self.assertFalse(self.validator.validate_boolean("0", "Test Field"))
        self.assertFalse(self.validator.validate_boolean(0, "Test Field"))
        
        # None許容
        self.assertIsNone(self.validator.validate_boolean(None, "Test Field", required=False))
        
        # 空文字許容
        self.assertIsNone(self.validator.validate_boolean("", "Test Field", required=False))
        
        # エラーケース（無効な形式）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_boolean("invalid", "Test Field")
        self.assertIn("Test Field は真偽値である必要があります", str(context.exception))
    
    def test_validate_date(self):
        """日付バリデーションのテスト"""
        # 正常ケース（文字列から変換）
        expected_date = datetime(2023, 1, 1).date()
        self.assertEqual(self.validator.validate_date("2023-01-01", "Test Field"), expected_date)
        
        # 正常ケース（日付オブジェクト）
        self.assertEqual(self.validator.validate_date(expected_date, "Test Field"), expected_date)
        
        # フォーマット指定
        self.assertEqual(
            self.validator.validate_date("01/01/2023", "Test Field", format="%d/%m/%Y"),
            expected_date
        )
        
        # None許容
        self.assertIsNone(self.validator.validate_date(None, "Test Field", required=False))
        
        # 空文字許容
        self.assertIsNone(self.validator.validate_date("", "Test Field", required=False))
        
        # エラーケース（無効な形式）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_date("2023-13-01", "Test Field")
        self.assertIn("Test Field は日付形式（YYYY-MM-DD）である必要があります", str(context.exception))
        
        # 最小日付チェック
        with self.assertRaises(ValueError) as context:
            min_date = datetime(2023, 1, 1).date()
            self.validator.validate_date("2022-12-31", "Test Field", min_date=min_date)
        self.assertIn("Test Field は 2023-01-01 以降の日付である必要があります", str(context.exception))
        
        # 最大日付チェック
        with self.assertRaises(ValueError) as context:
            max_date = datetime(2023, 12, 31).date()
            self.validator.validate_date("2024-01-01", "Test Field", max_date=max_date)
        self.assertIn("Test Field は 2023-12-31 以前の日付である必要があります", str(context.exception))
    
    def test_validate_enum(self):
        """列挙型バリデーションのテスト"""
        # 正常ケース（列挙値）
        self.assertEqual(
            self.validator.validate_enum(Sex.MALE, "Test Field", Sex),
            Sex.MALE
        )
        
        # 正常ケース（文字列から変換）
        self.assertEqual(
            self.validator.validate_enum("牡", "Test Field", Sex),
            Sex.MALE
        )
        
        # None許容
        self.assertIsNone(self.validator.validate_enum(None, "Test Field", Sex, required=False))
        
        # 空文字許容
        self.assertIsNone(self.validator.validate_enum("", "Test Field", Sex, required=False))
        
        # エラーケース（無効な値）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_enum("Invalid", "Test Field", Sex)
        self.assertIn("Test Field は ['牡', '牝', 'セン'] のいずれかである必要があります", str(context.exception))
        
        # エラーケース（無効な型）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_enum(123, "Test Field", Sex)
        self.assertIn("Test Field は文字列または列挙型である必要があります", str(context.exception))
    
    def test_validate_dict(self):
        """辞書バリデーションのテスト"""
        # 正常ケース
        test_dict = {"key1": "value1", "key2": 123}
        self.assertEqual(
            self.validator.validate_dict(test_dict, "Test Field"),
            test_dict
        )
        
        # None許容
        self.assertIsNone(self.validator.validate_dict(None, "Test Field", required=False))
        
        # 空辞書許容
        self.assertEqual(self.validator.validate_dict({}, "Test Field"), {})
        
        # エラーケース（無効な型）
        with self.assertRaises(ValueError) as context:
            self.validator.validate_dict("not a dict", "Test Field")
        self.assertIn("Test Field は辞書である必要があります", str(context.exception))
    
    def test_validate_list(self):
        """リストバリデーションのテスト"""
        # 正常ケース
        test_list = [1, 2, 3]
        self.assertEqual(
            self.validator.validate_list(test_list, "Test Field"),
            test_list
        )
        
        # None許容
        self.assertIsNone(self.validator.validate_list(None, "Test Field", required=False))
        
        # 空リスト許容
        self.assertEqual(self.validator.validate_list([], "Test Field"), [])
        
        # 最小長チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_list([1, 2], "Test Field", min_length=3)
        self.assertIn("Test Field は 3 個以上の要素が必要です", str(context.exception))
        
        # 最大長チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_list([1, 2, 3, 4], "Test Field", max_length=3)
        self.assertIn("Test Field は 3 個以下の要素である必要があります", str(context.exception))
        
        # 要素の型チェック
        with self.assertRaises(ValueError) as context:
            self.validator.validate_list([1, "2", 3], "Test Field", element_type=int)
        self.assertIn("Test Field の要素は整数型である必要があります", str(context.exception))

if __name__ == '__main__':
    unittest.main()
