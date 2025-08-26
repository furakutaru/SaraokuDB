from bs4 import BeautifulSoup
from typing import Optional

class ImageExtractor:
    """
    馬の画像URLを抽出するクラス
    """
    
    @staticmethod
    def extract(html_content: str) -> Optional[str]:
        """
        詳細ページのHTMLから馬の画像URLを抽出する
        
        Args:
            html_content (str): 詳細ページのHTMLコンテンツ
            
        Returns:
            Optional[str]: 画像のURL（見つからない場合はNone）
        """
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # カルーセルから最初の画像を取得
        big_image = soup.select_one('#itemphotoArea .bigImageWrap img#bigImage')
        
        if big_image and 'src' in big_image.attrs:
            return big_image['src']
            
        return None
