"""
馬の基本情報抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトから馬の基本情報（馬名、性別、年齢）を抽出する機能を提供します。
"""

import re
import logging
from typing import Dict, Optional, Tuple

logger = logging.getLogger(__name__)

class HorseBasicInfoExtractor:
    """馬の基本情報を抽出するクラス"""
    
    @staticmethod
    def extract(soup) -> Dict[str, str]:
        """BeautifulSoupオブジェクトから馬の基本情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, str]: 抽出した基本情報（name, sex, age）を含む辞書
        """
        result = {'name': '', 'sex': '', 'age': None}
        
        try:
            # 馬名の抽出
            name_elem = soup.select_one('.horseName')
            if name_elem:
                result['name'] = name_elem.get_text(strip=True)
            
            # 性別と年齢の抽出（通常は「性齢」の形式で表示される）
            age_sex_elem = soup.select_one('.ageSex')
            if age_sex_elem:
                age_sex_text = age_sex_elem.get_text(strip=True)
                
                # 性別の抽出
                sex_match = re.search(r'[牡牝セ]', age_sex_text)
                if sex_match:
                    result['sex'] = sex_match.group(0)
                
                # 年齢の抽出
                age_match = re.search(r'(\d+)歳', age_sex_text)
                if age_match:
                    try:
                        result['age'] = int(age_match.group(1))
                    except (ValueError, TypeError):
                        logger.warning(f"年齢の変換に失敗しました: {age_match.group(1)}")
            
            logger.info(
                f"[BASIC_INFO] 抽出した基本情報: 馬名='{result['name']}', "
                f"性別='{result['sex']}', 年齢='{result['age']}'"
            )
            
        except Exception as e:
            logger.error(f"[BASIC_INFO_ERROR] 基本情報の抽出中にエラーが発生しました: {str(e)}", exc_info=True)
        
        return result
