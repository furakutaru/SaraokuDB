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
    
    def extract(self, html_content: str) -> Tuple[Dict[str, Any], bool]:
        """
        馬の詳細ページからレース実績情報を抽出する
        
        Args:
            html_content (str or BeautifulSoup): 馬の詳細ページのHTMLまたはBeautifulSoupオブジェクト
            
        Returns:
            Tuple[Dict[str, Any], bool]: (レース実績情報を含む辞書, 抽出が成功したかどうか)
        """
        try:
            # html_contentがBeautifulSoupオブジェクトの場合はそのまま使用
            if not isinstance(html_content, str):
                soup = html_content
            else:
                soup = BeautifulSoup(html_content, 'html.parser')
                
            records = []
            record_summary = {}
            
            # 通算成績を抽出
            record_summary = {}
            # preタグ内のテキストを検索
            pre_tag = soup.find('pre')
            if pre_tag:
                pre_text = pre_tag.get_text()
                self.logger.debug(f"pre_text: {pre_text}")
                
                # 未出走馬のチェック
                if '未出走' in pre_text:
                    self.logger.debug("未出走馬を検出しました")
                    return {'summary': {'status': 'unraced'}, 'races': []}, True
                
                # 通算成績：の後からスペースまでの文字列を取得
                start_markers = ['通算成績：', '通算成績:']
                record_text = None
                
                for marker in start_markers:
                    if marker in pre_text:
                        # 開始マーカーの直後から次のスペースまでを取得
                        start = pre_text.find(marker) + len(marker)
                        end = pre_text.find(' ', start)
                        if end == -1:  # スペースが見つからない場合は最後まで
                            end = len(pre_text)
                        record_text = pre_text[start:end].strip()
                        break
                
                if record_text:
                    self.logger.debug(f"Found record text: {record_text}")
                    # 例: "3戦0勝[0-0-0-3]" をパース
                    try:
                        # 数字とハイフン、カッコを抽出
                        import re
                        numbers = re.findall(r'\d+', record_text)
                        if len(numbers) >= 4:  # 最低限必要な数値が揃っているか確認
                            # サマリーを文字列で保存
                            record_summary = f"{numbers[0]}戦{numbers[1]}勝［{numbers[2]}-{numbers[3]}-{numbers[4] if len(numbers) > 4 else 0}-{numbers[5] if len(numbers) > 5 else 0}］"
                            
                            # 詳細な情報も辞書として保持
                            record_summary_dict = {
                                'status': 'active',  # 出走歴あり
                                'races': int(numbers[0]),  # 総出走回数
                                'wins': int(numbers[1]),   # 勝利回数
                                'first': int(numbers[2]) if len(numbers) > 2 else 0,  # 1着回数
                                'second': int(numbers[3]) if len(numbers) > 3 else 0, # 2着回数
                                'third': int(numbers[4]) if len(numbers) > 4 else 0,  # 3着回数
                                'other': int(numbers[5]) if len(numbers) > 5 else 0,  # その他の着順回数
                                'summary': f"{numbers[0]}戦{numbers[1]}勝［{numbers[2]}-{numbers[3]}-{numbers[4] if len(numbers) > 4 else 0}-{numbers[5] if len(numbers) > 5 else 0}］"
                            }
                            record_summary = record_summary_dict
                        self.logger.debug(f"Extracted record: {record_summary}")
                    except (IndexError, ValueError) as e:
                        self.logger.error(f"通算成績の抽出中にエラーが発生しました: {e}")
                        return {'summary': {}}, False
                else:
                    self.logger.debug("通算成績のパターンにマッチしませんでした")
                    return {'summary': {'summary': ''}}, True
            
            # 通算成績を返す（racesフィールドは削除）
            if isinstance(record_summary, dict) and 'summary' in record_summary:
                return {'summary': record_summary}, True
            return {'summary': {'summary': record_summary}}, True
            
        except Exception as e:
            self.logger.error(f"レース実績の抽出中にエラーが発生しました: {e}", exc_info=True)
            return {'summary': {}, 'races': []}, False
