import json
from bs4 import BeautifulSoup
import logging

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('analyze_horse_structure.log')
    ]
)
logger = logging.getLogger(__name__)

def analyze_horse_card(card, index):
    """馬のカードの構造を分析する"""
    result = {
        'index': index,
        'text': card.get_text(separator=' ', strip=True)[:200],
        'classes': card.get('class', []),
        'attrs': {k: v for k, v in card.attrs.items() if k != 'class'},
        'children': []
    }
    
    # 最初の数レベルの子要素を確認
    for i, child in enumerate(card.children):
        if hasattr(child, 'name') and child.name is not None:
            result['children'].append({
                'tag': child.name,
                'classes': child.get('class', []),
                'attrs': {k: v for k, v in child.attrs.items() if k != 'class'},
                'text': child.get_text(separator=' ', strip=True)[:100]
            })
    
    return result

def main():
    # 保存したHTMLファイルを読み込む
    html_file = "rakuten_auction_page.html"
    output_file = "horse_structure_analysis.json"
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            html_content = f.read()
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # 馬のカード要素を取得
        horse_cards = soup.select('div.auctionTableCard')
        
        if not horse_cards:
            logger.warning("馬のカード要素が見つかりませんでした。")
            return
        
        # 最初の3つのカードを詳細に分析
        analysis_results = []
        for i, card in enumerate(horse_cards[:3], 1):
            logger.info(f"カード {i} を分析中...")
            analysis = analyze_horse_card(card, i)
            analysis_results.append(analysis)
        
        # 結果をJSONファイルに保存
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(analysis_results, f, ensure_ascii=False, indent=2)
        
        # コンソールに結果を表示
        print("\n=== 馬のカード構造分析結果 ===\n")
        for i, result in enumerate(analysis_results, 1):
            print(f"カード {i}:")
            print(f"  クラス: {', '.join(result['classes'])}")
            print(f"  属性: {result['attrs']}")
            print(f"  テキストの先頭: {result['text']}")
            print("  主な子要素:")
            for child in result['children'][:5]:  # 最初の5つの子要素のみ表示
                print(f"    - {child['tag']} (クラス: {', '.join(child['classes'])})")
                print(f"      テキスト: {child['text']}")
            print("\n" + "-"*80 + "\n")
        
        logger.info(f"分析結果を {output_file} に保存しました。")
        
    except FileNotFoundError:
        logger.error(f"ファイルが見つかりません: {html_file}")
    except Exception as e:
        logger.error(f"エラーが発生しました: {e}", exc_info=True)

if __name__ == "__main__":
    main()
