"""販売者情報を抽出するモジュール"""
from typing import Dict, Optional, Tuple
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup


class SellerInfoExtractor:
    """販売者情報を抽出するクラス"""
    
    def __init__(self, logger: logging.Logger = None):
        """初期化メソッド
        
        Args:
            logger: ロガーインスタンス（Noneの場合は新規作成）
        """
        self.logger = logger or logging.getLogger(__name__)
        
    def _extract_seller_from_element(self, element) -> Optional[Dict[str, str]]:
        """指定された要素から販売者情報を抽出するヘルパーメソッド
        
        Args:
            element: BeautifulSoup要素または文字列
            
        Returns:
            Optional[Dict[str, str]]: 販売者情報を含む辞書、見つからない場合はNone
        """
        if not element:
            return None
            
        # 要素が文字列の場合はそのまま使用、そうでなければテキストを抽出
        if isinstance(element, str):
            element_text = element
        else:
            # 要素内のテキストを結合
            element_text = ' '.join(element.stripped_strings)
        
        # デバッグ用に要素の最初の200文字をログに出力
        self.logger.debug(f'要素のテキスト（先頭200文字）: {element_text[:200]}...')
        
        # 正規表現で「販売申込者：」の後を抽出（改行や括弧を含む場合も考慮）
        seller_match = re.search(r'販売申込者[：:]([^\n\r<（]+(?:（[^）]*）)?)', element_text)
        
        if seller_match:
            seller_name = seller_match.group(1).strip()
            self.logger.debug(f'販売者名を抽出: {seller_name}')
            
            # URLがあれば取得（「販売申込者」というテキストを含むリンクを探す）
            seller_url = None
            if not isinstance(element, str):
                seller_links = element.find_all('a', href=True)
                for link in seller_links:
                    if link.string and '販売申込者' in link.string and link.get('href'):
                        seller_url = link['href']
                        self.logger.debug(f'販売者URLを抽出: {seller_url}')
                        break
            
            seller_info = {'seller': seller_name}
            if seller_url:
                seller_info['seller_url'] = seller_url
                
            return seller_info
            
        return None
        
    def extract(self, card_or_soup) -> Tuple[Optional[Dict[str, str]], bool]:
        """馬の詳細ページから販売者情報を抽出する
        
        Args:
            card_or_soup: BeautifulSoupオブジェクトまたはカード要素
            
        Returns:
            Tuple[Optional[Dict[str, str]], bool]: 
                (販売者情報を含む辞書, 成功したかどうか)
        """
        try:
            self.logger.info('販売者情報の抽出を開始します')
            
            # デバッグ用にHTMLをファイルに保存
            debug_dir = Path('debug_html')
            debug_dir.mkdir(exist_ok=True)
            debug_file = debug_dir / 'seller_debug.html'
            
            # 文字列の場合はBeautifulSoupオブジェクトに変換
            if isinstance(card_or_soup, str):
                html_str = card_or_soup
                soup = BeautifulSoup(html_str, 'html.parser')
            else:
                soup = card_or_soup
                html_str = str(card_or_soup)
                
            # デバッグ用にHTMLを保存
            with open(debug_file, 'w', encoding='utf-8') as f:
                f.write(html_str)
            self.logger.info(f'デバッグ用HTMLを保存しました: {debug_file}')
            
            # 1. まずは「販売申込者」というテキストを含む要素を探す
            seller_elements = soup.find_all(string=re.compile(r'販売申込者[：:]?'))
            
            if seller_elements:
                for element in seller_elements:
                    # 親要素を取得して解析
                    parent = element.parent
                    seller_info = self._extract_seller_from_element(parent)
                    if seller_info:
                        self.logger.info(f'販売者情報を抽出しました: {seller_info}')
                        return seller_info, True
            
            # 2. 見つからない場合は、テキスト全体から正規表現で探す
            full_text = soup.get_text(separator=' ', strip=True)
            if '販売申込者' in full_text:
                self.logger.info('テキスト内に「販売申込者」を検出しました')
                match = re.search(r'販売申込者[：:]([^<\n]+)', full_text)
                if match:
                    seller_name = match.group(1).strip()
                    self.logger.info(f'正規表現で抽出した販売者名: {seller_name}')
                    return {'seller': seller_name}, True
            
            self.logger.warning('販売者情報を検出できませんでした')
            return None, False
            
        except Exception as e:
            self.logger.error(f'販売者情報の抽出中にエラーが発生しました: {e}', exc_info=True)
            return None, False
            
    def _extract_seller_name(self, text: str) -> str:
        """販売者情報のテキストから販売者名を抽出する
        
        Args:
            text: 販売者情報を含むテキスト（例: "販売申込者：国本 哲秀（インボイス登録あり）"）
            
        Returns:
            str: 抽出された販売者名（例: "国本 哲秀"）
        """
        try:
            # "販売申込者："の後のテキストを取得
            seller = text.split('販売申込者：', 1)[1].strip()
            
            # カッコがあればその前までを販売者名とする
            if '（' in seller:
                seller = seller.split('（', 1)[0].strip()
                
            return seller
            
        except Exception as e:
            self.logger.error(f'販売者名の抽出に失敗しました: {e}', exc_info=True)
            return ""
    
    def _clean_seller_name(self, seller: str) -> str:
        """販売者名をクリーンアップする
        
        Args:
            seller: クリーンアップ前の販売者名
            
        Returns:
            str: クリーンアップされた販売者名
        """
        if not seller:
            return ""
            
        # 不要な空白と改行を削除
        seller = ' '.join(seller.split())
        
        # 販売者名から不要なテキストを削除
        patterns = [
            r'^[\s\u3000]*(出品者|販売者|セラー|売主)[\s\u3000]*[:：]?[\s\u3000]*',  # 接頭辞
            r'[\s\u3000]*$',  # 末尾の空白
            r'[\r\n\t]+',  # 改行やタブ
            r'\s{2,}',  # 連続する空白
            r'^\s+|\s+$'  # 先頭と末尾の空白
        ]
        
        for pattern in patterns:
            seller = re.sub(pattern, ' ', seller)
            
        return seller.strip()
        
    def _get_text_from_element(self, element) -> str:
        """要素からテキストを取得し、正規化する"""
        if not element:
            return ""
            
        # テキストを取得し、正規化
        text = element.get_text(' ', strip=True)
        return ' '.join(text.split())
