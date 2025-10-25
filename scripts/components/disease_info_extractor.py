"""
疾病情報を抽出するモジュール
"""
import re
import logging
from typing import Dict, List, Optional, Any

# 健康関連のキーワード（フロントエンドと同期を取る）
HEALTH_KEYWORDS = [
    # 骨・関節系
    '骨折', '骨膜炎', '蟻洞', 'フレグモーネ', 'ボーンシスト', '骨瘤', '骨片', '骨膜肥厚',
    '関節炎', '膝関節炎', '球節炎', '飛節炎', 'ウォブラー症候群', 'OCD', 'エクイロックス',
    
    # 腱・靭帯系
    '屈腱炎', '繋靭帯炎', '前膝腱炎', '腱鞘炎', '腱損傷', 'じん帯損傷',
    
    # 脚部・運動器系
    '脚部不安', '脚元不安', '跛行', '跛る', 'こり症', '筋肉痛', '筋肉炎', '肉離れ', '横紋筋融解症',
    '腰フラ', '鶏跛', 'コズミ', '挫跖', '旋回癖', '旋回症', 'さく癖', 'ゆう癖',
    
    # 呼吸器系
    '喉鳴り', '軟口蓋の癒着', 'カケス', '喉頭蓋エントラップメント', '喉頭蓋炎', '鼻出血',
    '気管支炎', '肺出血', '呼吸器不安', '上気道炎', '喘鳴症', 'DDSP',
    
    # 消化器系
    '腸捻転', '鼓腸症', '胃潰瘍', '大腸炎', '下痢', '食欲不振', '疝痛', '風気疝', 'ガス腹',
    
    # 感染症・その他
    'ロタウイルス感染症', '馬インフルエンザ', '皮膚糸状菌症', '感冒',
    
    # 蹄・足部
    '裂蹄', '蹄葉炎', '蹄中隔炎', '蹄の亀裂', '蹄不安', '蹄傷', '蹄底負傷',
    '蹄球損傷', '蹄内出血', '繋皸',
    
    # 外傷・炎症
    '打撲', '擦過傷', '裂傷', '腫脹', '炎症', '創傷', '皮膚炎', '疥癬', '蕁麻疹',
    '角膜炎', '結膜炎', '神経麻痺'
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
    
    def _normalize_text(self, text: Any) -> str:
        """
        テキストを正規化する（全角・半角の統一など）
        
        Args:
            text: 正規化するテキスト（文字列または文字列のリスト）
            
        Returns:
            str: 正規化されたテキスト
        """
        # テキストがNoneの場合は空文字列を返す
        if text is None:
            return ""
            
        # リストが渡された場合は最初の要素を使用
        if isinstance(text, list):
            if not text:  # 空のリストの場合は空文字列を返す
                return ""
            text = text[0]  # 最初の要素を使用
            
        # 文字列に変換
        text = str(text)
            
        # 全角英数字を半角に
        try:
            text = text.translate(str.maketrans(
                '０１２３４５６７８９ＡＢＣＤＥＦＧＨＩＪＫＬＭＮＯＰＱＲＳＴＵＶＷＸＹＺａｂｃｄｅｆｇｈｉｊｋｌｍｎｏｐｑｒｓｔｕｖｗｘｙｚ',
                '0123456789ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz'
            ))
            # 全角スペースを半角に
            text = text.replace('　', ' ')
            # 連続するスペースを1つに
            text = ' '.join(text.split())
            return text
        except Exception as e:
            if self.logger:
                self.logger.error(f"テキストの正規化中にエラーが発生しました: {e}")
            return text  # エラーが発生した場合は元のテキストをそのまま返す
    
    def _find_keyword_variations(self, keyword: str, text: str) -> bool:
        """
        キーワードのバリエーションをチェック
        
        Args:
            keyword: 検索するキーワード
            text: 検索対象のテキスト
            
        Returns:
            bool: キーワードが見つかったかどうか
        """
        # 完全一致
        if keyword in text:
            return True
            
        # カッコ内の表記を考慮（例：「骨折（右前脚）」→「骨折」）
        if '(' in keyword and ')' in keyword:
            base_keyword = keyword.split('（')[0].split('(')[0]
            if base_keyword and base_keyword in text:
                return True
                
        # カタカナ・ひらがなの表記ゆれを考慮（例：「コズミ」と「こずみ」）
        if 'ー' in keyword:
            alt_keyword = keyword.replace('ー', '')
            if alt_keyword in text:
                return True
                
        return False
    
    def extract(self, comment: str) -> Dict[str, any]:
        """
        コメントから疾病情報を抽出する
        
        Args:
            comment: 抽出元のコメントテキスト
            
        Returns:
            Dict[str, any]: 抽出した疾病情報
                - diseases: 検出された疾病キーワードのリスト
                - has_health_issues: 健康問題があるかどうか
        """
        if not comment:
            return {'diseases': [], 'has_health_issues': False}
            
        # テキストを正規化
        normalized_comment = self._normalize_text(comment)
        found_keywords = set()
        
        # 結果を格納する辞書を初期化
        result = {
            'diseases': [],
            'has_health_issues': False
        }
        
        # デバッグログ
        if self.logger:
            self.logger.debug(f"[抽出前] コメント: {comment}")
            self.logger.debug(f"[正規化後] コメント: {normalized_comment}")
        
        try:
            # 各キーワードをチェック
            for keyword in self.health_keywords:
                # キーワードのバリエーションチェック
                if self._find_keyword_variations(keyword, normalized_comment):
                    # 重複を避けて追加
                    found_keywords.add(keyword)
                    if self.logger:
                        self.logger.debug(f"[マッチ] キーワード: {keyword}")
            
            # 見つかったキーワードをリストに変換してソート
            result['diseases'] = sorted(list(found_keywords))
            result['has_health_issues'] = len(found_keywords) > 0
            
            # ログに検出結果を記録（デバッグ用）
            if self.logger and result['diseases']:
                self.logger.debug(f"検出された疾病キーワード: {', '.join(result['diseases'])}")
                
            return result
            
        except Exception as e:
            error_msg = f"疾病情報の抽出中にエラーが発生しました: {str(e)}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            return {'diseases': [], 'has_health_issues': False}
    
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
            
        try:
            # 新しいextractメソッドを使用して疾病情報を取得
            result = self.extract(comment)
            
            # 疾病キーワードを取得し、重複を削除してソート
            diseases = sorted(list(set(result.get('diseases', []))))
            
            # カンマ区切りの文字列に変換して返す
            return ", ".join(diseases) if diseases else ""
            
        except Exception as e:
            error_msg = f"疾病タグの抽出中にエラーが発生しました: {str(e)}"
            if self.logger:
                self.logger.error(error_msg, exc_info=True)
            return ""
