"""
レース実績情報を抽出するモジュール
"""
from typing import Dict, Any, List, Tuple, Optional
import re
from bs4 import BeautifulSoup
from bs4.element import Tag
import logging

class RaceRecordExtractor:
    """レース実績情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def _parse_race_record(self, record_text: str) -> Optional[Dict[str, str]]:
        """戦績テキストからレース記録をパースする
        
        Args:
            record_text: 戦績テキスト（例: "23戦1勝［1-0-1-21］"）
            
        Returns:
            パースされたレコードの辞書、またはパースできない場合はNone
        """
        try:
            # 戦績テキストから各数値を抽出
            match = re.search(r'(\d+)戦(\d+)勝\s*\[(\d+)-(\d+)-(\d+)-(\d+)\]', record_text)
            if not match:
                return None
                
            return {
                'races': int(match.group(1)),  # 総出走回数
                'wins': int(match.group(2)),   # 勝利回数
                'first': int(match.group(3)),  # 1着回数
                'second': int(match.group(4)), # 2着回数
                'third': int(match.group(5)),  # 3着回数
                'other': int(match.group(6))   # その他の着順回数
            }
        except (ValueError, IndexError, AttributeError) as e:
            self.logger.warning(f"戦績テキストのパースに失敗しました: {record_text}, エラー: {e}")
            return None
    
    def extract(self, html_content: str) -> Tuple[Dict[str, Any], bool]:
        """
        馬の詳細ページからレース実績情報を抽出する
        
        Args:
            html_content (str): 馬の詳細ページのHTML
            
        Returns:
            Tuple[Dict[str, Any], bool]: (レース実績情報を含む辞書, 抽出が成功したかどうか)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            records = []
            
            # 戦績テキストを抽出
            record_summary = {}
            record_div = soup.find('div', class_='record')
            if record_div:
                record_text = record_div.get_text(strip=True)
                record_summary = self._parse_race_record(record_text) or {}
            
            # レース実績テーブルを検索
            race_table = soup.find('table', class_='raceTable')
            if race_table:
                # ヘッダー行をスキップして各行を処理
                rows = race_table.find_all('tr')[1:]  # ヘッダー行をスキップ
                
                for row in rows:
                    cols = row.find_all('td')
                    if len(cols) >= 8:  # 必要な列数があることを確認
                        record = {
                            'date': cols[0].get_text(strip=True) if cols[0] else '',
                            'race_name': cols[1].get_text(strip=True) if cols[1] else '',
                            'track': cols[2].get_text(strip=True) if cols[2] else '',
                            'distance': cols[3].get_text(strip=True) if cols[3] else '',
                            'track_condition': cols[4].get_text(strip=True) if cols[4] else '',
                            'position': cols[5].get_text(strip=True) if cols[5] else '',
                            'time': cols[6].get_text(strip=True) if cols[6] else '',
                            'jockey': cols[7].get_text(strip=True) if cols[7] else ''
                        }
                        records.append(record)
            
            # 戦績サマリーと詳細を結合
            result = {
                'summary': record_summary,
                'races': records
            }
            
            # レコードが0件でも成功とみなす（データが存在しない場合は空のリストを返す）
            return result, True
            
        except Exception as e:
            self.logger.error(f'レース実績の抽出中にエラーが発生しました: {e}', exc_info=True)
            return {'summary': {}, 'races': []}, False
