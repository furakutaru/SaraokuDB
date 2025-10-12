"""
疾病情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, List, Optional

# 健康関連のキーワード
HEALTH_KEYWORDS = [
    '手術歴', '骨折', '皮膚病', '屈腱炎', '腫れ', '咽頭虚脱', '脱臼', '跛行', '打撲'
]

class DiseaseInfoExtractor:
    """疾病情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """
        初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.health_keywords = HEALTH_KEYWORDS
        self.logger = logger or logging.getLogger(__name__)
    
    def extract(self, comment: str) -> Dict[str, any]:
        """
        コメントから疾病情報を抽出する
        
        Args:
            comment: 抽出元のコメントテキスト
            
        Returns:
            Dict[str, any]: 抽出した疾病情報（キーワードとその有無）
        """
        if not comment:
            return {}
            
        result = {
            'diseases': [],
            'has_health_issues': False
        }
        
        try:
            # 各キーワードをチェック
            for keyword in self.health_keywords:
                if keyword in comment:
                    result['diseases'].append(keyword)
            
            # 健康問題の有無を設定
            result['has_health_issues'] = len(result['diseases']) > 0
            
            self.logger.debug(f'抽出した疾病情報: {result}')
            
        except Exception as e:
            self.logger.error(f'疾病情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            
        return result
    
    def extract_disease_tags(self, comment: str) -> str:
        """
        コメントから病気タグを抽出する（後方互換性のためのメソッド）
        
        Args:
            comment: 抽出元のコメントテキスト
            
        Returns:
            str: カンマ区切りの病気タグ。見つからない場合は空文字列を返します。
        """
        if not comment:
            return ""
            
        diseases = []
        for keyword in self.health_keywords:
            if keyword in comment:
                diseases.append(keyword)
                
        return ",".join(diseases) if diseases else ""
