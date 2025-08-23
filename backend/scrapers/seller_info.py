"""
販売者情報を取得するモジュール
"""
from typing import Dict, Optional, Tuple


def extract_seller_info(card) -> Tuple[Optional[Dict[str, str]], bool]:
    """
    馬のカードから販売者情報を抽出する
    
    Args:
        card: BeautifulSoupのカード要素
        
    Returns:
        Tuple[Optional[Dict[str, str]], bool]: 
            - 抽出した販売者情報の辞書（失敗時はNone）
            - 成功可否（True: 成功, False: 失敗）
    """
    try:
        # 販売者情報を取得
        seller_elem = card.select_one('.auctionTableCard__farm, .seller-info, [data-testid="seller"]')
        if not seller_elem:
            return None, False
            
        # 販売者名を取得
        seller = seller_elem.get_text(strip=True)
        
        # 不要なテキストを削除
        seller = _clean_seller_name(seller)
        
        return {
            'seller': seller
        }, True
        
    except Exception as e:
        return None, False


def _clean_seller_name(seller: str) -> str:
    """販売者名をクリーンアップする"""
    if not seller:
        return ""
    
    # 不要なテキストを削除
    seller = re.sub(r'\s*[\[\]\(\)\{\}]\s*', ' ', seller)  # 括弧類を削除
    seller = re.sub(r'\s+', ' ', seller).strip()  # 連続するスペースを1つに
    
    # 不要な接頭辞・接尾辞を削除
    seller = re.sub(r'^[\s\-\*\+\=\~_…]+', '', seller)  # 先頭の記号
    seller = re.sub(r'[\-\*\+\=\~_…]+$', '', seller)  # 末尾の記号
    
    return seller
