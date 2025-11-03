"""
レース実績情報を抽出するモジュール
"""
import re
from typing import Dict, Any, List, Tuple
from bs4 import BeautifulSoup
from .base_extractor import BaseExtractor

class RaceRecordExtractor(BaseExtractor):
    """レース実績情報を抽出するクラス"""
    
    def extract(self, html_content: str) -> Tuple[Dict[str, Any], bool]:
        """
        馬の詳細ページからレース実績情報を抽出する
        
        Args:
            html_content (str): 馬の詳細ページのHTML
            
        Returns:
            Tuple[Dict[str, Any], bool]: (レース実績情報を含む辞書, 抽出が成功したかどうか)
        """
        try:
            self.logger.debug("レース実績の抽出を開始します")
            self.logger.debug(f"入力HTMLの先頭500文字: {html_content[:500]}...")
            
            # レース実績のサマリーを抽出（例: "62戦6勝［6-8-5-43］"）
            race_summary = {}
            
            # パターン1: 「X戦Y勝［A-B-C-D］」形式
            pattern1 = r'(\d+)戦(\d+)勝\s*\[(\d+)-(\d+)-(\d+)-(\d+)\]'
            # パターン2: 「X戦Y勝」形式（詳細なし）
            pattern2 = r'(\d+)戦(\d+)勝'
            
            # パターン1で検索
            match = re.search(pattern1, html_content)
            
            if match:
                # パターン1にマッチした場合
                race_summary = {
                    'total_races': int(match.group(1)),
                    'wins': int(match.group(2)),
                    'first_place': int(match.group(3)),
                    'second_place': int(match.group(4)),
                    'third_place': int(match.group(5)),
                    'other_place': int(match.group(6)),
                    'record_format': 'detailed'
                }
            else:
                # パターン1にマッチしなかった場合、パターン2を試す
                match = re.search(pattern2, html_content)
                if match:
                    race_summary = {
                        'total_races': int(match.group(1)),
                        'wins': int(match.group(2)),
                        'record_format': 'simple'
                    }
            
            if race_summary:
                # フォーマットを「X戦Y勝[A-B-C-D]」に整形
                if race_summary.get('record_format') == 'detailed':
                    formatted_record = (
                        f"{race_summary['total_races']}戦{race_summary['wins']}勝"
                        f"[{race_summary['first_place']}-{race_summary['second_place']}-{race_summary['third_place']}-{race_summary['other_place']}]"
                    )
                else:
                    # 詳細情報がない場合はシンプルな形式で返す
                    formatted_record = f"{race_summary['total_races']}戦{race_summary['wins']}勝"
                
                # 必要なフィールドのみを含む形式で返す
                result = {
                    'total_races': race_summary.get('total_races', 0),
                    'wins': race_summary.get('wins', 0),
                    'record_format': 'simple',
                    'formatted_record': f"{race_summary.get('total_races', 0)}戦{race_summary.get('wins', 0)}勝"
                }
                self.logger.debug(f"レース実績を抽出しました: {result}")
                return result, True
            else:
                # コメント内の戦績情報を探す
                soup = BeautifulSoup(html_content, 'html.parser')
                comment_elem = soup.find('div', class_=lambda c: c and 'comment' in c.lower())
                if comment_elem:
                    comment_text = comment_elem.get_text()
                    # コメント内で戦績情報を検索
                    match = re.search(r'(\d+)戦(\d+)勝', comment_text)
                    if match:
                        race_summary = {
                            'total_races': int(match.group(1)),
                            'wins': int(match.group(2)),
                            'record_format': 'simple',
                            'formatted_record': f"{int(match.group(1))}戦{int(match.group(2))}勝"
                        }
                        self.logger.debug(f"コメントからレース実績を抽出しました: {race_summary}")
                        return race_summary, True
                
                self.logger.warning("レース実績のパターンが見つかりませんでした")
                return {}, False
                
        except Exception as e:
            self.logger.error(f'レース実績の抽出中にエラーが発生しました: {e}', exc_info=True)
            return {}, False
