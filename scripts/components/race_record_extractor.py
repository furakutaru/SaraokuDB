"""
レース実績情報を抽出するモジュール
"""
from typing import Dict, Any, List
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor

class RaceRecordExtractor(BaseExtractor):
    """レース実績情報を抽出するクラス"""
    
    def extract(self, html_content: str) -> tuple[Dict[str, Any], bool]:
        """
        馬の詳細ページからレース実績情報を抽出する
        
        Args:
            html_content (str): 馬の詳細ページのHTML
            
        Returns:
            tuple[Dict[str, Any], bool]: (レース実績情報を含む辞書, 抽出が成功したかどうか)
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            records = []
            
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
            
            # レコードが1つ以上あれば成功とみなす
            success = len(records) > 0
            return {'race_records': records}, success
            
        except Exception as e:
            self.logger.error(f'レース実績の抽出中にエラーが発生しました: {e}')
            return {'race_records': []}, False
