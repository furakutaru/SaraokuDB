"""
馬の基本情報を抽出するためのコンポーネント（更新版）
"""
import re
import traceback
import logging
import unicodedata
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
    
    def _extract_pedigree(self, horse_element: Tag) -> Dict[str, str]:
        """
        血統情報を抽出する（新しいHTML構造用に更新）
        
        [2025-08-31 確定] 本番環境での動作を確認済み
        - テーブル形式とテキスト形式の両方の血統情報に対応
        - 父・母・母父の情報を正確に抽出可能
        - 全角/半角、記号の違いを吸収
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Dict[str, str]: 抽出した血統情報（sire, dam, damsire）を含む辞書
        """
        result = {'sire': None, 'dam': None, 'damsire': None}
        
        try:
            # タイトルから馬名を取得（デバッグ用）
            title_elem = horse_element.select_one('title')
            title_text = title_elem.get_text(strip=True) if title_elem else 'タイトルなし'
            self.logger.debug(f'血統抽出開始: {title_text}')
            
            # 1. まずテーブル形式の血統情報を探す
            table = horse_element.find('table', class_=re.compile(r'(pedigree|bloodline|blood|血統)'))
            if table:
                rows = table.find_all('tr')
                for row in rows:
                    th = row.find('th')
                    td = row.find('td')
                    if th and td:
                        label = th.get_text(strip=True)
                        value = td.get_text(strip=True)
                        if '父' in label and not result['sire']:
                            result['sire'] = value
                        elif '母' in label and '父' not in label and not result['dam']:
                            result['dam'] = value
                        elif '母父' in label or '母の父' in label and not result['damsire']:
                            result['damsire'] = value
            
            # 2. テーブルが見つからないか不完全な場合は、テキストベースで検索
            if not all(result.values()):
                text = horse_element.get_text(separator='\n', strip=True)
                
                # 血統情報が含まれていそうなセクションを探す
                for line in text.split('\n'):
                    line = line.strip()
                    if not line:
                        continue
                        
                    # パターン1: 性別・年齢 + 血統情報
                    patterns = [
                        # 父: サンデーサイレンス 母: ウインドインハーヘア 母父: アラジ
                        r'父[:：]\s*([^\n\r]+?)\s+母[:：]\s*([^\n\r]+?)\s+母の?父[:：]\s*([^\n\r]+)',
                        # 父: サンデーサイレンス 母: ウインドインハーヘア (アラジ)
                        r'父[:：]\s*([^\n\r]+?)\s+母[:：]\s*([^\n\r]+?)\s*\(([^)]+?)\)',
                        # 父: サンデーサイレンス 母: ウインドインハーヘア アラジ
                        r'父[:：]\s*([^\s　\n\r]+?)[\s　]+母[:：]\s*([^\s　\n\r]+?)[\s　]+([^\s　\d\n\r]+)',
                    ]
                    
                    for pattern in patterns:
                        match = re.search(pattern, line)
                        if match:
                            if not result['sire']:
                                result['sire'] = match.group(1).strip()
                            if not result['dam']:
                                result['dam'] = match.group(2).strip()
                            if not result['damsire'] and match.lastindex >= 3:
                                result['damsire'] = match.group(3).strip()
            
            # 3. 個別の要素を検索（最後の手段）
            if not all(result.values()):
                for elem in horse_element.find_all(['div', 'p', 'span', 'b']):
                    text = elem.get_text(separator=' ', strip=True)
                    if not text or len(text) > 100:  # 長すぎるテキストはスキップ
                        continue
                        
                    # 父馬のパターン
                    if not result['sire'] and ('父:' in text or '父：' in text):
                        name = re.sub(r'^.*[父:：]\s*', '', text)
                        if name and name != text:
                            result['sire'] = name.strip()
                    
                    # 母馬のパターン
                    if not result['dam'] and ('母:' in text or '母：' in text) and '母父' not in text:
                        name = re.sub(r'^.*[母:：]\s*', '', text)
                        if name and name != text:
                            result['dam'] = name.strip()
                    
                    # 母父のパターン
                    if not result['damsire'] and ('母父:' in text or '母父：' in text or '母の父:' in text or '母の父：' in text):
                        name = re.sub(r'^.*(?:母父|母の父)[:：]\s*', '', text)
                        if name and name != text:
                            result['damsire'] = name.strip()
            
            # 抽出した情報をクリーニング
            for key in ['sire', 'dam', 'damsire']:
                if result[key]:
                    # 不要な空白や改行を削除
                    result[key] = re.sub(r'[\s　]+', ' ', result[key]).strip()
                    # 不要な記号を削除（カッコ内の年数など）
                    result[key] = re.sub(r'\s*\(.*?\)', '', result[key]).strip()
                    # 末尾の記号を削除
                    result[key] = re.sub(r'[、。・\s　]+$', '', result[key])
            
            # 結果をログに出力
            if any(result.values()):
                self.logger.debug(f'血統情報を抽出しました: sire={result.get("sire")}, dam={result.get("dam")}, damsire={result.get("damsire")}')
            else:
                self.logger.warning('血統情報のパターンが一致しませんでした')
                self.logger.debug(f'抽出対象テキスト: {str(horse_element)[:500]}...')
                
        except Exception as e:
            self.logger.error(f'血統情報の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            
        return result

    # 他のメソッドはそのまま残します
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
            
        # 血統情報を抽出
        pedigree = self._extract_pedigree(horse_element)
        if pedigree:
            horse_info.update(pedigree)
        
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
            
            # パターン1: リストページ用のセレクタ
            name_elem = horse_element.select_one('.auctionTableCard__name')
            if name_elem:
                # 子要素に.valueがある場合（テストケース2）
                value_elem = name_elem.select_one('.value')
                if value_elem:
                    name = value_elem.get_text(strip=True)
                else:
                    name = name_elem.get_text(strip=True)
                
                if name:
                    cleaned_name = self._clean_horse_name(name)
                    self.logger.debug(f'リストページから馬名を抽出: {cleaned_name}')
                    return cleaned_name
            
            # パターン2: 詳細ページ用の<b>タグから抽出
            b_tag = horse_element.find('b')
            if b_tag:
                text = b_tag.get_text(strip=True, separator=' ')
                # 最初の連続する日本語とアルファベットの組み合わせを馬名とみなす
                match = re.search(r'^([^\s]+(?:\s+[^\s]+)*?)\s+[A-Za-z]', text)
                if match:
                    name = match.group(1).strip()
                    cleaned_name = self._clean_horse_name(name)
                    self.logger.debug(f'<b>タグから馬名を抽出: {cleaned_name}')
                    return cleaned_name
            
            # パターン3: タイトルタグから抽出
            title_tag = horse_element.find('title')
            if title_tag:
                title_text = title_tag.get_text(strip=True)
                # タイトルから馬名を抽出（例: 「グランダイトの情報」→「グランダイト」）
                match = re.search(r'^(.+?)(?:の情報|の血統|の競走馬データ|\s*\|)', title_text)
                if match:
                    name = match.group(1).strip()
                    cleaned_name = self._clean_horse_name(name)
                    self.logger.debug(f'タイトルタグから馬名を抽出: {cleaned_name}')
                    return cleaned_name
            
            self.logger.warning('馬名要素が見つかりませんでした')
            self.logger.debug(f'要素のHTML: {str(horse_element)[:500]}...')
            return ''
            
        except Exception as e:
            self.logger.error(f'馬名の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            return ''

    def _extract_sex_and_age(self, horse_element):
        """
        馬の性別と年齢を抽出する（新しいHTML構造用に更新）
        
        Args:
            horse_element: 馬の情報が含まれるBeautifulSoup要素
            
        Returns:
            dict: 性別(sex)と年齢(age)を含む辞書
        """
        result = {'sex': None, 'age': None}
        
        try:
            # タイトルから性別と年齢を抽出
            title_elem = horse_element.select_one('title')
            if title_elem:
                title_text = title_elem.get_text(strip=True)
                self.logger.debug(f"タイトルテキスト: {title_text}")
                
                # パターン1: 「馬名　　牝４歳　　※...」のような形式
                match = re.search(r'([牡牝セ])([０-９0-9]+)歳', title_text)
                if match:
                    result['sex'] = match.group(1)
                    result['age'] = int(unicodedata.normalize('NFKC', match.group(2)))
                    return result
                
                # パターン2: スペース区切り
                match = re.search(r'([牡牝セ])\s*([０-９0-9]+)', title_text)
                if match:
                    result['sex'] = match.group(1)
                    result['age'] = int(unicodedata.normalize('NFKC', match.group(2)))
                    return result
            
            # 詳細情報セクションを確認
            for elem in horse_element.select('div, p, span'):
                text = elem.get_text(separator=' ', strip=True)
                
                # 性別と年齢が近くにあるパターン
                match = re.search(r'([牡牝セ])\s*([０-９0-9]+)[歳才]', text)
                if match:
                    result['sex'] = match.group(1)
                    result['age'] = int(unicodedata.normalize('NFKC', match.group(2)))
                    return result
                
                # 性別のみのパターン
                if not result['sex'] and any(c in text for c in ['牡', '牝', 'セ']):
                    result['sex'] = next((c for c in text if c in ['牡', '牝', 'セ']), None)
                
                # 年齢のみのパターン
                if not result['age']:
                    age_match = re.search(r'([０-９0-9]+)[歳才]', text)
                    if age_match:
                        result['age'] = int(unicodedata.normalize('NFKC', age_match.group(1)))
            
            if result['sex'] or result['age']:
                self.logger.debug(f'性別・年齢を抽出しました: {result}')
                return result
            
            self.logger.warning('性別・年齢のパターンが一致しませんでした')
                    
        except Exception as e:
            self.logger.error(f'性別・年齢の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            
        return result

    def _check_required_fields(self, horse_info: Dict[str, any]) -> List[str]:
        """
        必須フィールドが存在するか確認する
        
        Args:
            horse_info: 抽出した馬情報
            
        Returns:
            List[str]: 不足している必須フィールドのリスト
        """
        required_fields = ['name', 'sex', 'age']
        return [field for field in required_fields if field not in horse_info]

    def _clean_horse_name(self, name: str) -> str:
        """
        馬名をクリーニングする
        
        Args:
            name: クリーニング前の馬名
            
        Returns:
            str: クリーニング後の馬名
        """
        # 不要な空白や改行を削除
        name = re.sub(r'\s+', ' ', name).strip()
        # 全角スペースを半角スペースに変換
        name = name.replace('　', ' ')
        return name
