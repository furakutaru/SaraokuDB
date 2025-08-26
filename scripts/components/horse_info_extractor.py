"""
馬の基本情報を抽出するためのコンポーネント
"""
import re
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup, Tag
import logging

class HorseInfoExtractor:
    """馬の基本情報を抽出するクラス"""
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス（指定がない場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, horse_element: Tag) -> Tuple[Dict[str, any], List[str]]:
        """
        馬の基本情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Dict[str, any], List[str]]: (馬情報の辞書, 不足している必須フィールドのリスト)
        """
        horse_info = {}
            
        # 馬名を抽出（必須）
        name = self._extract_name(horse_element)
        if name:
            horse_info['name'] = name
        
        # 性別・年齢を抽出（必須）
        sex_age = self._extract_sex_and_age(horse_element)
        if sex_age:
            horse_info.update(sex_age)
        
        # 不足している必須フィールドを確認
        missing_fields = self._check_required_fields(horse_info)
        
        return horse_info, missing_fields
    
    def _extract_name(self, horse_element: Tag) -> str:
        """馬名を抽出する"""
        name_elem = horse_element.select_one('.horse-name')
        if not name_elem:
            return ''
            
        # 馬名を取得してクリーンアップ
        name = name_elem.get_text(strip=True)
        return self._clean_horse_name(name)
    
    def _extract_sex_and_age(self, horse_element: Tag) -> Dict[str, any]:
        """
        性別と年齢を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Dict[str, any]: 性別と年齢を含む辞書
        """
        result = {}
        try:
            sex_age_elem = horse_element.select_one('.horse-info')
            if not sex_age_elem:
                return result
                
            sex_age = sex_age_elem.get_text(strip=True)
            if not sex_age:
                return result
            
            # 性別（最初の1文字）
            if len(sex_age) > 0:
                result['sex'] = sex_age[0]
            
            # 年齢（数字のみ抽出）
            age_match = re.search(r'\d+', sex_age[1:])
            if age_match:
                try:
                    age_str = age_match.group()
                    # 年齢が有効な場合のみ追加
                    if age_str.isdigit() and int(age_str) > 0:
                        result['age'] = int(age_str)
                    else:
                        self.logger.warning(f'無効な年齢です: {age_str}')
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'年齢の抽出に失敗しました: {sex_age}')
                    self.logger.debug(f'Error details: {str(e)}')
            else:
                # 数字が見つからない場合も警告を出力
                if len(sex_age) > 1:  # 性別の1文字目を除く
                    self.logger.warning(f'年齢の抽出に失敗しました（数字が見つかりません）: {sex_age}')
            
            return result
            
        except Exception as e:
            self.logger.error(f'性別・年齢の抽出中にエラーが発生しました: {str(e)}')
            return result
    
    def _clean_horse_name(self, name: str) -> str:
        """
        馬名をクリーンアップする
        
        Args:
            name: クリーンアップ前の馬名
            
        Returns:
            str: クリーンアップされた馬名
        """
        if not name:
            return ''
            
        # 文字列に変換（Noneや数値が渡された場合に対応）
        name = str(name)
            
        # 改行文字、タブ文字、エスケープされた改行文字を削除
        name = re.sub(r'[\n\t\r]|\\n|\\t|\\r', '', name)
        
        # 不要な文字列を削除
        for s in ["※", "登録抹消", "新馬", "未出走"]:
            name = name.replace(s, "")
            
        # 連続するスペースを1つにまとめてトリム
        return re.sub(r'\s+', ' ', name).strip()
    
    def extract(self, horse_element: Tag) -> Tuple[Dict[str, any], List[str]]:
        """
        馬の基本情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Dict[str, any], List[str]]: (馬情報の辞書, 不足している必須フィールドのリスト)
        """
        if not isinstance(horse_element, Tag):
            error_msg = "無効なHTML要素が渡されました"
            self.logger.error(error_msg)
            return {}, ['name', 'sex', 'age']  # 全必須フィールドを不足として返す
        
        horse_info = {}
        
        try:
            # 馬名を抽出（必須）
            name = self._extract_name(horse_element)
            if name:
                horse_info['name'] = name
            
            # 性別・年齢を抽出（必須）
            sex_age = self._extract_sex_and_age(horse_element)
            if sex_age:
                horse_info.update(sex_age)
                
            # 追加フィールド（あれば）
            sire_elem = horse_element.select_one('.sire-name')
            if sire_elem:
                horse_info['sire'] = sire_elem.get_text(strip=True)
                
            dam_elem = horse_element.select_one('.dam')
            if dam_elem:
                horse_info['dam'] = dam_elem.get_text(strip=True)
                
            damsire_elem = horse_element.select_one('.damsire')
            if damsire_elem:
                horse_info['damsire'] = damsire_elem.get_text(strip=True)
                
            # 不足している必須フィールドを確認
            missing_fields = self._check_required_fields(horse_info)
            
            if missing_fields:
                self.logger.warning(f"必須フィールドが不足しています: {', '.join(missing_fields)}")
                
            return horse_info, missing_fields
            
        except Exception as e:
            error_msg = f"馬情報の抽出中にエラーが発生しました: {str(e)}"
            self.logger.error(error_msg)
            return horse_info, self._check_required_fields(horse_info)
    
    def _check_required_fields(self, horse_info: Dict[str, any]) -> List[str]:
        """必須フィールドが不足しているか確認する"""
        required_fields = ['name', 'sex', 'age']
        return [field for field in required_fields if field not in horse_info]
