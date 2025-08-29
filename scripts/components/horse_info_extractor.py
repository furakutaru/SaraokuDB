"""
馬の基本情報を抽出するためのコンポーネント
"""
import re
import traceback
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
        """
        馬名を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            str: 抽出された馬名。抽出に失敗した場合は空文字列
        """
        try:
            # デバッグ用に要素のHTMLをログに出力
            self.logger.debug(f'馬名抽出を開始: {str(horse_element)[:200]}...')
            
            # 新しいHTML構造に対応
            # まず、auctionTableCard__nameクラスを探す
            name_elem = horse_element.select_one('.auctionTableCard__name')
            
            if not name_elem:
                # 見つからない場合は、別のセレクタを試す
                name_elem = horse_element.select_one('.auctionTableCard__name .value')
            
            if not name_elem:
                self.logger.warning('馬名要素が見つかりませんでした')
                self.logger.debug(f'要素のHTML: {str(horse_element)[:500]}...')
                return ''
            
            # 馬名を取得
            name = name_elem.get_text(strip=True, separator=' ')
            
            if not name:
                self.logger.warning('馬名が空です')
                self.logger.debug(f'name_elemの内容: {str(name_elem)}')
                return ''
                
            cleaned_name = self._clean_horse_name(name)
            self.logger.debug(f'馬名を抽出しました: {cleaned_name}')
            return cleaned_name
            
        except Exception as e:
            self.logger.error(f'馬名の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            return ''
    
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
            # 性別を抽出
            sex_elem = horse_element.select_one('.horseLabelWrapper__horseSex')
            if not sex_elem:
                # 別のセレクタを試す
                sex_elem = horse_element.select_one('.auctionTableCard__sex')
                
            if sex_elem:
                sex = sex_elem.get_text(strip=True)
                # 性別を正規化（牡・牝・セに統一）
                if '牡' in sex or '牡馬' in sex:
                    result['sex'] = '牡'
                elif '牝' in sex or '牝馬' in sex:
                    result['sex'] = '牝'
                elif 'セ' in sex or 'せん' in sex or 'セン' in sex:
                    result['sex'] = 'セ'
                else:
                    result['sex'] = sex  # 不明な場合はそのまま保存
            
            # 年齢を抽出
            age_elem = horse_element.select_one('.horseLabelWrapper__horseAge')
            if not age_elem:
                # 別のセレクタを試す
                age_elem = horse_element.select_one('.auctionTableCard__age')
                
            if age_elem:
                age_text = age_elem.get_text(strip=True)
                # 数字のみを抽出
                age_match = re.search(r'(\d+)', age_text)
                if age_match:
                    try:
                        age = int(age_match.group(1))
                        if age > 0:
                            result['age'] = age
                        else:
                            self.logger.warning(f'無効な年齢です: {age_text}')
                    except (ValueError, TypeError) as e:
                        self.logger.warning(f'年齢の抽出に失敗しました: {age_text}')
                        self.logger.debug(f'Error details: {str(e)}')
            
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
    
    def _check_required_fields(self, horse_info: Dict[str, any]) -> List[str]:
        """
        必須フィールドが不足しているかチェック
        
        Args:
            horse_info: 馬情報の辞書
            
        Returns:
            List[str]: 不足している必須フィールドのリスト
        """
        required_fields = ['name', 'sex', 'age']
        return [field for field in required_fields if field not in horse_info]
        
    def extract_from_detail_page(self, detail_html: str) -> Dict[str, any]:
        """
        詳細ページのHTMLから性別と年齢を抽出する
        
        Args:
            detail_html: 詳細ページのHTML
            
        Returns:
            Dict[str, any]: 抽出した情報（sex, age）を含む辞書
        """
        result = {}
        try:
            soup = BeautifulSoup(detail_html, 'html.parser')
            
            # タイトル要素を取得
            title_elem = soup.select_one('#itemTitle span[itemprop="name"]')
            if not title_elem:
                return result
                
            title_text = title_elem.get_text(strip=True)
            
            # 性別を抽出（牝 or 牡）
            sex_match = re.search(r'([牡牝])', title_text)
            if sex_match:
                result['sex'] = sex_match.group(1)
            
            # 年齢を抽出（数字+「歳」のパターン）
            age_match = re.search(r'(\d+)歳', title_text)
            if age_match:
                result['age'] = int(age_match.group(1))
                
        except Exception as e:
            self.logger.error(f"詳細ページからの情報抽出中にエラーが発生しました: {e}")
            self.logger.debug(traceback.format_exc())
            
        return result
