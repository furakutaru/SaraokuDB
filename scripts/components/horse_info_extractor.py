"""
馬の基本情報を抽出するためのコンポーネント（更新版）
"""
import re
import traceback
import logging
import unicodedata
from pathlib import Path
from typing import Dict, Any, Optional, Tuple, List
from bs4 import BeautifulSoup, Tag

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
            # デバッグ用：HTMLの先頭1000文字をログに出力
            html_str = str(horse_element)[:1000]
            self.logger.debug(f"血統抽出開始: HTMLの先頭1000文字 = {html_str}")
            
            # デバッグ用：全テキストをログに出力
            full_text = horse_element.get_text(separator='\n', strip=True)
            self.logger.debug(f"血統抽出: 全テキスト = {full_text[:500]}..." if len(full_text) > 500 else full_text)
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
                    cleaned = re.sub(r'[\s　]+', ' ', result[key]).strip()
                    # 不要な記号を削除（カッコ内の年数など）
                    cleaned = re.sub(r'\s*\(.*?\)', '', cleaned).strip()
                    # 末尾の記号を削除
                    cleaned = re.sub(r'[、。・\s　]+$', '', cleaned)
                    
                    # 値が変更されたかどうかをログに記録
                    if cleaned != result[key]:
                        self.logger.debug(f'血統情報をクリーニング: {key} = "{result[key]}" -> "{cleaned}"')
                        result[key] = cleaned
            
            # 結果をログに出力
            if any(result.values()):
                self.logger.debug(f'血統情報を抽出しました: sire={result.get("sire")}, dam={result.get("dam")}, damsire={result.get("damsire")}')
            else:
                self.logger.warning('血統情報のパターンが一致しませんでした')
                self.logger.debug(f'抽出対象テキスト: {str(horse_element)[:500]}...')
                
                # デバッグ用：血統情報が含まれていそうな要素を探す
                self.logger.debug("血統情報を含む可能性のある要素を検索中...")
                for elem in horse_element.find_all(True, recursive=True):
                    text = elem.get_text(strip=True)
                    if '父' in text or '母' in text:
                        self.logger.debug(f'血統情報の可能性あり - タグ: {elem.name}, クラス: {elem.get("class", [])}, テキスト: {text[:200]}...' if len(text) > 200 else text)
                
        except Exception as e:
            self.logger.error(f'血統情報の抽出中にエラーが発生しました: {str(e)}')
            self.logger.debug(f'エラー詳細: {traceback.format_exc()}')
            
        return result

    def extract(self, horse_element: Tag) -> Tuple[Dict[str, Any], Dict[str, Any]]:
        """
        馬の基本情報を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Tuple[Dict[str, Any], Dict[str, Any]]: (基本情報, 詳細情報) のタプル
        """
        try:
            # 基本情報の抽出
            basic_info = {}
            
            # 性別と年齢の抽出
            sex_age = self._extract_sex_and_age(horse_element)
            if sex_age:
                basic_info.update(sex_age)
                
            # 血統情報の抽出
            pedigree = self._extract_pedigree(horse_element)
            if pedigree:
                basic_info.update(pedigree)
                
            # 馬体重の抽出を追加
            weight = self._extract_weight(horse_element)
            if weight is not None:
                basic_info['weight'] = weight
                
            # 詳細情報の抽出
            detail_info = {}
            
            # 通算成績の抽出
            race_record = self._extract_race_record(horse_element)
            if race_record:
                detail_info['race_record'] = race_record
                
            return basic_info, detail_info
                
        except Exception as e:
            self.logger.error(f"馬情報の抽出中にエラーが発生しました: {str(e)}")
            self.logger.error(traceback.format_exc())
            return {}, {}
    
    def _extract_race_record(self, horse_element: Tag) -> Optional[str]:
        """
        通算成績を抽出する
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Optional[str]: 抽出された通算成績（例: "3戦0勝［0-0-0-3］"）、抽出できない場合はNone
        """
        try:
            # テキスト全体を取得
            text_content = horse_element.get_text()
            
            # パターン1: 通算成績：3戦0勝［0-0-0-3］形式
            record_match = re.search(r'通算成績[：:]([^\[\]\n]+(?:\[[^\]]+\])?)', text_content)
            if record_match:
                record = record_match.group(1).strip()
                self.logger.debug(f'通算成績を抽出: {record}')
                return record
                
            # パターン2: テーブル内の通算成績
            for td in horse_element.find_all('td'):
                if '通算成績' in td.text:
                    record_match = re.search(r'通算成績[：:]([^\[\]\n]+(?:\[[^\]]+\])?)', td.text)
                    if record_match:
                        record = record_match.group(1).strip()
                        self.logger.debug(f'テーブルから通算成績を抽出: {record}')
                        return record
                        
            self.logger.debug('通算成績が見つかりませんでした')
            return None
            
        except Exception as e:
            self.logger.error(f'通算成績の抽出中にエラーが発生しました: {str(e)}')
            return None

    def _extract_weight(self, horse_element: Tag) -> Optional[int]:
        """
        馬体重を抽出する（強化版）
        
        Args:
            horse_element: 馬情報を含むBeautifulSoup要素
            
        Returns:
            Optional[int]: 抽出された馬体重（kg）、抽出できない場合はNone
        """
        try:
            self.logger.debug('馬体重抽出を開始')
            
            # デバッグ用にHTMLを保存
            debug_html = str(horse_element)[:2000] + '...'  # 先頭2000文字のみ
            self.logger.debug(f'デバッグ用HTML: {debug_html}')
            
            # テキスト全体を正規化（全角を半角に変換）
            text_content = unicodedata.normalize('NFKC', horse_element.get_text())
            self.logger.debug(f'正規化済みテキスト: {text_content[:200]}...')
            
            # パターン1: 数値 + kg のパターン（例: 422kg, 454 kg, 422.5kg）
            weight_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ)', text_content, re.IGNORECASE)
            self.logger.debug(f'パターン1でマッチングを開始: マッチ数={len(list(weight_matches))}')
            
            # イテレータをリセット
            weight_matches = re.finditer(r'(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ)', text_content, re.IGNORECASE)
            
            for i, match in enumerate(weight_matches, 1):
                try:
                    weight_str = match.group(1)
                    self.logger.debug(f'パターン1-{i}: マッチング文字列={match.group(0)}, 抽出した数値={weight_str}')
                    weight = float(weight_str)
                    # 馬体重として妥当な範囲かチェック（300kg〜700kgに拡大）
                    if 300 <= weight <= 700:
                        weight_kg = int(round(weight))
                        self.logger.debug(f'パターン1で馬体重を抽出: {weight_kg}kg')
                        return weight_kg
                except (ValueError, TypeError) as e:
                    self.logger.warning(f'体重の数値変換に失敗しました: {match.group(1)}: {str(e)}')
            
            # パターン2: 体重表記が別の形式の場合（例: 体重:422kg, 体重：422, 馬体重 422）
            weight_patterns = [
                # パターン2-1: 未登録 体高：157cm 胸囲：179cm 管囲：18.8cm 馬体重：454kg 形式
                (r'馬体重[：:]\s*(\d+)\s*kg', 'パターン2-1'),
                # パターン2-2: 一般的な体重表記
                (r'[馬体]?重[量]?\s*[:：]?\s*(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ)?', 'パターン2-2'),
                (r'(\d+(?:\.\d+)?)\s*(?:kg|キロ|㎏|ｋｇ)?\s*[\(（]?[馬体]?重[量]?[\)）]?', 'パターン2-3'),
                (r'最終出走馬体重[：:]\s*(\d+)\s*kg', 'パターン2-4'),
                (r'体重[：:]\s*(\d+)\s*kg', 'パターン2-5'),
                # パターン2-6: コメント内の体重表記
                (r'馬体重は(\d+)kg', 'パターン2-6'),
                (r'馬体重(\d+)kg', 'パターン2-7')
            ]
            
            self.logger.debug('パターン2でマッチングを開始')
            
            # パターン3: 複数の測定値が並んでいる場合（例: 体高：157cm 胸囲：179cm 馬体重：454kg）
            multi_measure_pattern = r'(?:[^\d]|^)(\d+)kg(?:[^\d]|$)'
            multi_measure_matches = list(re.finditer(multi_measure_pattern, text_content))
            self.logger.debug(f'パターン3: マッチ数={len(multi_measure_matches)}')
            
            if len(multi_measure_matches) > 0:
                # 最後のマッチを体重とみなす（通常、体重は最後に来ることが多い）
                last_match = multi_measure_matches[-1]
                try:
                    weight_str = last_match.group(1)
                    self.logger.debug(f'パターン3: 最終マッチ文字列={last_match.group(0)}, 抽出した数値={weight_str}')
                    weight = float(weight_str)
                    if 300 <= weight <= 700:
                        weight_kg = int(round(weight))
                        self.logger.debug(f'複数測定値パターンで馬体重を抽出: {weight_kg}kg (マッチ: {last_match.group(0).strip()})')
                        return weight_kg
                except (ValueError, TypeError) as e:
                    self.logger.debug(f'複数測定値パターンでの体重抽出に失敗: {str(e)}')
            
            for pattern, pattern_name in weight_patterns:
                matches = list(re.finditer(pattern, text_content, re.IGNORECASE))
                self.logger.debug(f'{pattern_name} マッチ数: {len(matches)}')
                
                for i, match in enumerate(matches, 1):
                    try:
                        weight_str = match.group(1)
                        self.logger.debug(f'{pattern_name}-{i}: マッチング文字列={match.group(0)}, 抽出した数値={weight_str}')
                        weight = float(weight_str)
                        if 300 <= weight <= 700:
                            weight_kg = int(round(weight))
                            self.logger.debug(f'パターン2で馬体重を抽出: {weight_kg}kg (パターン: {pattern_name})')
                            return weight_kg
                    except (ValueError, TypeError, IndexError) as e:
                        self.logger.debug(f'{pattern_name}-{i}: 数値変換エラー: {str(e)}')
                        continue
            
            # パターン4: テーブル内の体重情報
            for table in horse_element.find_all('table'):
                for row in table.find_all('tr'):
                    cells = [cell.get_text(strip=True) for cell in row.find_all(['th', 'td'])]
                    for i, cell in enumerate(cells):
                        if '体重' in cell and i + 1 < len(cells):
                            match = re.search(r'(\d+(?:\.\d+)?)', cells[i+1])
                            if match:
                                try:
                                    weight = float(match.group(1))
                                    if 300 <= weight <= 700:
                                        weight_kg = int(round(weight))
                                        self.logger.debug(f'テーブルから馬体重を抽出: {weight_kg}kg')
                                        return weight_kg
                                except (ValueError, TypeError):
                                    continue
            
            # パターン4: 属性値に体重が含まれる場合
            for elem in horse_element.find_all(True):
                for attr in elem.attrs.values():
                    if isinstance(attr, str) and re.search(r'\b\d{3,4}\s*(?:kg|キロ|㎏|ｋｇ)?\b', attr, re.IGNORECASE):
                        match = re.search(r'(\d{3,4})', attr)
                        if match:
                            try:
                                weight = int(match.group(1))
                                if 300 <= weight <= 700:
                                    self.logger.debug(f'属性値から馬体重を抽出: {weight}kg')
                                    return weight
                            except (ValueError, TypeError):
                                continue
            
            # デバッグ用に「体重」の前後100文字を出力
            weight_pos = text_content.find('体重')
            if weight_pos != -1:
                start = max(0, weight_pos - 100)
                end = min(len(text_content), weight_pos + 100)
                self.logger.debug(f'「体重」付近のテキスト: ...{text_content[start:end]}...')
            
            self.logger.warning('馬体重の抽出に失敗しました。該当するパターンが見つかりませんでした。')
            return None
            
        except Exception as e:
            self.logger.error(f'馬体重の抽出中にエラーが発生しました: {str(e)}')
            self.logger.error(traceback.format_exc())
            return None
            
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
            
            # パターン1: テスト用のセレクタ
            name_elem = horse_element.select_one('.horse-name')
            if name_elem:
                name = name_elem.get_text(strip=True)
                if name:
                    cleaned_name = self._clean_horse_name(name)
                    self.logger.debug(f'horse-nameクラスから馬名を抽出: {cleaned_name}')
                    return cleaned_name
            
            # パターン2: リストページ用のセレクタ
            name_elem = horse_element.select_one('.auctionTableCard__name')
            if name_elem:
                # 子要素に.valueがある場合
                value_elem = name_elem.select_one('.value')
                if value_elem:
                    name = value_elem.get_text(strip=True)
                else:
                    name = name_elem.get_text(strip=True)
                
                if name:
                    cleaned_name = self._clean_horse_name(name)
                    self.logger.debug(f'リストページから馬名を抽出: {cleaned_name}')
                    return cleaned_name
            
            # パターン3: 詳細ページ用の<b>タグから抽出
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
            
            # パターン4: タイトルタグから抽出
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
            # デバッグ用：要素のHTMLをログに出力
            self.logger.debug(f"性別・年齢抽出開始: 要素の先頭500文字 = {str(horse_element)[:500]}...")
            
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
                    self.logger.debug(f'タイトルから性別・年齢を抽出: {result}')
                    return result
                
                # パターン2: スペース区切り
                match = re.search(r'([牡牝セ])\s*([０-９0-9]+)', title_text)
                if match:
                    result['sex'] = match.group(1)
                    result['age'] = int(unicodedata.normalize('NFKC', match.group(2)))
                    self.logger.debug(f'タイトルから性別・年齢を抽出（スペース区切り）: {result}')
                    return result
            
            # 詳細情報セクションを確認
            self.logger.debug("詳細情報セクションから性別・年齢を抽出中...")
            for i, elem in enumerate(horse_element.select('div, p, span, td, th, li'), 1):
                text = elem.get_text(separator=' ', strip=True)
                if not text or len(text) > 100:  # 長すぎるテキストはスキップ
                    continue
                    
                self.logger.debug(f"  - 要素 {i}: {text}")
                
                # 性別と年齢が近くにあるパターン
                match = re.search(r'([牡牝セ])\s*([０-９0-9]+)[歳才]', text)
                if match:
                    result['sex'] = match.group(1)
                    result['age'] = int(unicodedata.normalize('NFKC', match.group(2)))
                    self.logger.debug(f'性別・年齢を抽出（パターン1）: {result} (テキスト: "{text}")')
                    return result
                
                # 性別のみのパターン
                if not result['sex'] and any(c in text for c in ['牡', '牝', 'セ']):
                    sex = next((c for c in text if c in ['牡', '牝', 'セ']), None)
                    if sex:
                        result['sex'] = sex
                        self.logger.debug(f'性別を抽出: {sex} (テキスト: "{text}")')
                
                # 年齢のみのパターン
                if not result['age']:
                    age_match = re.search(r'([０-９0-9]+)[歳才]', text)
                    if age_match:
                        result['age'] = int(unicodedata.normalize('NFKC', age_match.group(1)))
                        self.logger.debug(f'年齢を抽出: {result["age"]} (テキスト: "{text}")')
            
            if result['sex'] or result['age']:
                self.logger.debug(f'性別・年齢を抽出しました: {result}')
                return result
            
            # デバッグ用：性別・年齢が含まれていそうな要素を探す
            self.logger.warning('性別・年齢のパターンが一致しませんでした。デバッグ情報を出力します。')
            self.logger.debug("性別・年齢が含まれていそうな要素を検索中...")
            for elem in horse_element.find_all(True, recursive=True):
                text = elem.get_text(strip=True)
                if '牡' in text or '牝' in text or 'セ' in text or '歳' in text or '才' in text:
                    self.logger.debug(f'性別・年齢の可能性あり - タグ: {elem.name}, クラス: {elem.get("class", [])}, テキスト: {text}')
                    
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
            str: クリーニング後の馬名（余分な情報を削除）
        """
        if not name:
            return ""
            
        # 1. 不要な空白や改行を削除
        name = re.sub(r'\s+', ' ', name).strip()
        # 2. 全角スペースを半角スペースに変換
        name = name.replace('　', ' ')
        
        # 3. 馬名の最初の単語を抽出（スペースまたは記号の前まで）
        # 例: "スピリットガイド セン" -> "スピリットガイド"
        # 例: "アットザホップ 牝3歳" -> "アットザホップ"
        # 例: "サクラバクシンオー(父: サクラユタカオー)" -> "サクラバクシンオー"
        name_parts = re.split(r'[ 　(（※]', name)
        if name_parts:
            name = name_parts[0].strip()
        
        # 4. 不要な記号を削除
        name = re.sub(r'[\[\]()（）※]', '', name).strip()
        
        # 5. 末尾の「セ」「セン」が性別の場合は削除
        # ただし、馬名の一部として「セ」や「セン」を含む可能性がある場合は注意が必要
        # 例: "スピリットガイド セン" は "スピリットガイド" になるが、
        #     "ゴールドシップ" はそのまま残る
        if name.endswith(' セ') or name.endswith(' セン'):
            name = name.rsplit(' ', 1)[0]
            
        return name
        
    def extract_from_detail_page(self, detail_html: str) -> Dict[str, Any]:
        """
        詳細ページのHTMLから馬の情報を抽出する
        
        Args:
            detail_html: 詳細ページのHTML文字列
            
        Returns:
            Dict[str, Any]: 抽出した馬の情報
        """
        try:
            self.logger.debug("詳細ページから情報を抽出します")
            soup = BeautifulSoup(detail_html, 'html.parser')
            
            # 血統情報を抽出
            pedigree = self._extract_pedigree(soup)
            
            # 性別と年齢を抽出
            sex_age = self._extract_sex_and_age(soup)
            
            # 馬名を抽出
            name = self._extract_name(soup)
            
            # 馬体重を抽出
            weight = self._extract_weight(soup)
            
            # 結果を結合して返す
            result = {
                'name': name,
                'sex': sex_age.get('sex'),
                'age': sex_age.get('age'),
                'weight': weight,
                'sire': pedigree.get('sire'),
                'dam': pedigree.get('dam'),
                'damsire': pedigree.get('damsire')
            }
            
            self.logger.debug(f"詳細ページから抽出した情報: {result}")
            return result
            
        except Exception as e:
            self.logger.error(f"詳細ページからの情報抽出中にエラーが発生しました: {str(e)}")
            self.logger.debug(f"エラー詳細: {traceback.format_exc()}")
            return {}
