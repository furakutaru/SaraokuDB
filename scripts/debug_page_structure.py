import requests
import logging
from pathlib import Path

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_page_structure.log')
    ]
)
logger = logging.getLogger(__name__)

def save_html_content(url: str, output_file: str):
    """指定したURLのHTMLを保存する"""
    try:
        # ユーザーエージェントを設定（PC向け）
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        }
        
        logger.info(f"{url} にアクセス中...")
        response = requests.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # 文字コードを設定
        response.encoding = response.apparent_encoding
        
        # HTMLをファイルに保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logger.info(f"HTMLを {output_file} に保存しました。")
        
        # HTMLの構造を解析して表示
        from bs4 import BeautifulSoup
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # ページの基本情報を表示
        print("\n=== ページ情報 ===")
        print(f"タイトル: {soup.title.string if soup.title else 'N/A'}")
        
        # 馬の情報が含まれていそうな要素を探す
        print("\n=== 馬の情報が含まれていそうな要素 ===")
        horse_sections = []
        
        # 候補となるクラス名（実際のHTMLに合わせて調整が必要）
        candidate_classes = [
            'horse-card', 'auction-item', 'list-item', 'item-box',
            'auctionTableCard', 'auctionTableRow', 'horse-info'
        ]
        
        for class_name in candidate_classes:
            elements = soup.find_all(class_=class_name)
            if elements:
                print(f"\nクラス '{class_name}' で {len(elements)} 件の要素が見つかりました。")
                for i, elem in enumerate(elements[:2], 1):  # 最初の2つを表示
                    print(f"\n要素 {i} の内容:")
                    print(elem.prettify()[:500] + "..." if len(str(elem)) > 500 else elem.prettify())
        
        # 見つからなかった場合、すべての要素を確認
        if not any(soup.find_all(class_=class_name) for class_name in candidate_classes):
            print("\n一般的なクラス名では要素を見つけられませんでした。上位の構造を確認します。")
            
            # 主要なセクションを表示
            for tag in ['div', 'section', 'article', 'main']:
                elements = soup.find_all(tag, limit=5)
                if elements:
                    print(f"\nタグ '{tag}' の例 (最大5件):")
                    for i, elem in enumerate(elements, 1):
                        print(f"\n{tag} {i} のクラス: {elem.get('class', ['なし'])}")
                        print(f"ID: {elem.get('id', 'なし')}")
                        print(f"内容の一部: {str(elem.text[:100]).strip()}...")
        
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    # 楽天競馬オークションのURL
    url = "https://auction.keiba.rakuten.co.jp/"
    output_file = "rakuten_auction_page.html"
    
    save_html_content(url, output_file)
