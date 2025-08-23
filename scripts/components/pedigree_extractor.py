"""
血統情報抽出コンポーネント

このモジュールは、BeautifulSoupオブジェクトから馬の血統情報を抽出する機能を提供します。
"""

import re
import time
import logging
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)

class PedigreeExtractor:
    """馬の血統情報を抽出するクラス"""
    
    @staticmethod
    def extract(soup) -> Dict[str, str]:
        """BeautifulSoupオブジェクトから血統情報を抽出する
        
        Args:
            soup: BeautifulSoupオブジェクト
            
        Returns:
            Dict[str, str]: 抽出した血統情報（sire, dam, damsire）を含む辞書
        """
        pedigree_info = {}
        
        try:
            # 血統テーブルから直接抽出を試みる
            pedigree_table = soup.select_one('.pedigreeTable')
            if pedigree_table:
                # 父馬を抽出
                sire_elem = pedigree_table.select_one('.sire .name')
                if sire_elem:
                    pedigree_info['sire'] = sire_elem.get_text(strip=True)
                
                # 母馬を抽出
                dam_elem = pedigree_table.select_one('.dam .name')
                if dam_elem:
                    pedigree_info['dam'] = dam_elem.get_text(strip=True)
                
                # 母父を抽出
                damsire_elem = pedigree_table.select_one('.damsire .name')
                if damsire_elem:
                    pedigree_info['damsire'] = damsire_elem.get_text(strip=True)
            
            # テーブルから取得できなかった場合は、テキストベースで抽出を試みる
            if not all(key in pedigree_info for key in ['sire', 'dam', 'damsire']):
                for elem in soup.find_all(string=re.compile(r'父[：:]|母[：:]|母[のの]?父[：:]')):
                    parent_text = elem.parent.get_text(' ', strip=True)
                    logger.debug(f"[PEDIGREE_DEBUG] 親要素テキスト: {parent_text}")
                    
                    if 'sire' not in pedigree_info and '父' in parent_text:
                        sire_match = re.search(r'父[：:]([^\s　\n\r\f\v]+)', parent_text)
                        if sire_match:
                            pedigree_info['sire'] = sire_match.group(1).strip()
                    
                    if 'dam' not in pedigree_info and '母' in parent_text and '父' not in parent_text:
                        dam_match = re.search(r'母[：:]([^\s　\n\r\f\v]+)', parent_text)
                        if dam_match:
                            pedigree_info['dam'] = dam_match.group(1).strip()
                    
                    if 'damsire' not in pedigree_info and any(x in parent_text for x in ['母父', '母の父']):
                        damsire_match = re.search(r'母[のの]?父[：:]([^\s　\n\r\f\v]+)', parent_text)
                        if damsire_match:
                            pedigree_info['damsire'] = damsire_match.group(1).strip()
            
            # デバッグ出力
            logger.info(f"[PEDIGREE_RESULT] 抽出した血統情報: 父='{pedigree_info.get('sire', 'N/A')}', "
                      f"母='{pedigree_info.get('dam', 'N/A')}', "
                      f"母父='{pedigree_info.get('damsire', 'N/A')}")
            
            # 血統情報が1つも見つからなかった場合のデバッグ情報
            if not any(pedigree_info.values()):
                logger.warning("[PEDIGREE_DEBUG] 血統情報が見つかりませんでした。HTML構造を確認してください。")
                # デバッグ用にHTMLを保存
                PedigreeExtractor._save_debug_html(soup, "pedigree_debug")
                
        except Exception as e:
            logger.error(f"[PEDIGREE_ERROR] 血統情報の抽出中にエラーが発生しました: {str(e)}", exc_info=True)
            # エラーが発生した場合もデバッグ情報を保存
            PedigreeExtractor._save_debug_html(soup, "pedigree_error")
        
        return pedigree_info
    
    @staticmethod
    def _save_debug_html(soup, prefix: str) -> Optional[Path]:
        """デバッグ用にHTMLを保存する
        
        Args:
            soup: BeautifulSoupオブジェクト
            prefix: ファイル名のプレフィックス
            
        Returns:
            Optional[Path]: 保存したファイルのパス。失敗した場合はNone
        """
        try:
            debug_dir = Path('debug_pedigree')
            debug_dir.mkdir(exist_ok=True)
            debug_file = debug_dir / f"{prefix}_{int(time.time())}.html"
            
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(str(soup))
                
            logger.warning(f"[PEDIGREE_DEBUG] デバッグ用HTMLを保存しました: {debug_file}")
            return debug_file
            
        except Exception as e:
            logger.error(f"[PEDIGREE_ERROR] デバッグ用HTMLの保存に失敗しました: {str(e)}", exc_info=True)
            return None
