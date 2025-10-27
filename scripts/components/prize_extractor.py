"""
賞金情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, Optional, Union
from bs4 import BeautifulSoup, Tag

# ロガーの設定
logger = logging.getLogger(__name__)

class PrizeExtractor:
    """賞金情報を抽出するクラス"""
    
    def extract(self, element) -> Dict[str, Union[int, str, Dict]]:
        """賞金情報を抽出する
        
        Args:
            element: BeautifulSoup要素
            
        Returns:
            Dict: 賞金情報を含む辞書
            {
                'total_prize': int,  # 総賞金（円）
                'original_text': str,  # 元のテキスト
                'pattern_used': str,   # 使用されたパターン
                'central_prize': int,  # 中央賞金（円）
                'local_prize': int     # 地方賞金（円）
            }
        """
        default_return = {
            'total_prize': 0,
            'original_text': '賞金なし',
            'pattern_used': 'デフォルト（0円）',
            'central_prize': 0,
            'local_prize': 0
        }
        
        try:
            # 詳細ページからの取得（BeautifulSoup要素の場合）
            if hasattr(element, 'find_all'):
                # 中央・地方の賞金を個別に取得
                central_prize = 0
                local_prize = 0
                text = element.get_text(' ', strip=True)
                
                # 中央賞金の抽出
                central_match = re.search(r'中央獲得賞金[：: ]*([\d,.]+)', text)
                if central_match:
                    try:
                        central_prize = int(float(central_match.group(1).replace(',', '')) * 10000)
                    except (ValueError, AttributeError) as e:
                        logger.debug(f"中央賞金の数値変換に失敗: {e}")
                
                # 地方賞金の抽出
                local_match = re.search(r'地方獲得賞金[：: ]*([\d,.]+)', text)
                if local_match:
                    try:
                        local_prize = int(float(local_match.group(1).replace(',', '')) * 10000)
                    except (ValueError, AttributeError) as e:
                        logger.debug(f"地方賞金の数値変換に失敗: {e}")
                
                total_prize = central_prize + local_prize
                
                if total_prize > 0:
                    return {
                        'total_prize': total_prize,
                        'original_text': f"中央:{central_prize//10000}万円 地方:{local_prize//10000}万円",
                        'pattern_used': '詳細ページ賞金',
                        'central_prize': central_prize,
                        'local_prize': local_prize
                    }
            
            # テキストベースのフォールバック
            text = element.get_text(' ', strip=True) if hasattr(element, 'get_text') else str(element)
            
            # 賞金パターン（旧方式との互換性のため保持）
            prize_patterns = [
                (r'総賞金[：: ]*([\d,.]+)(?:\s*万円)?', '総賞金パターン'),
                (r'獲得賞金[：: ]*([\d,.]+)(?:\s*万円)?', '獲得賞金パターン'),
                (r'([\d,.]+)\s*万円', '単純な万円パターン')
            ]
            
            for pattern, pattern_name in prize_patterns:
                match = re.search(pattern, text)
                if match:
                    try:
                        prize_str = match.group(1).replace(',', '').strip()
                        prize_value = float(prize_str)
                        return {
                            'total_prize': int(prize_value * 10000),
                            'original_text': match.group(0).strip(),
                            'pattern_used': pattern_name,
                            'central_prize': 0,
                            'local_prize': 0
                        }
                    except (ValueError, IndexError) as e:
                        logger.debug(f"賞金の数値変換に失敗しました: {e}")
                        continue
            
            return default_return
                
        except Exception as e:
            logger.error(f"賞金情報の抽出中にエラーが発生しました: {e}", exc_info=True)
            return default_return
