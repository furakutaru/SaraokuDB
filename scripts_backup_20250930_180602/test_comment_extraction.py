import sys
import json
import logging
import requests
from pathlib import Path
from datetime import datetime
from bs4 import BeautifulSoup

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))

from scripts.components.comment_extractor import CommentExtractor

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('comment_extraction_test.log')
    ]
)
logger = logging.getLogger(__name__)

def fetch_page(url):
    """シンプルにrequestsでページを取得"""
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
        'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
    }
    response = requests.get(url, headers=headers, timeout=30)
    response.raise_for_status()
    return response.text

def test_comment_extraction():
    # テスト対象の馬のURLリスト（コメントが取得できていない馬）
    test_urls = [
        {"name": "アローロ", "url": "https://auction.keiba.rakuten.co.jp/item/14601"},
        {"name": "ウエスタンタマヤ", "url": "https://auction.keiba.rakuten.co.jp/item/14602"},
        {"name": "ジャスマン", "url": "https://auction.keiba.rakuten.co.jp/item/14603"},
    ]

    # コメント抽出器を初期化
    comment_extractor = CommentExtractor(logger=logger)
    results = []

    for horse in test_urls:
        print(f"\n=== テスト中: {horse['name']} ===")
        print(f"URL: {horse['url']}")
        
        try:
            # ページを取得
            logger.info(f"ページを取得中: {horse['name']}")
            html_content = fetch_page(horse['url'])
            
            # BeautifulSoupでパース
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # コメントを抽出
            logger.info("コメントを抽出中...")
            result, success = comment_extractor.extract(soup)
            
            # 結果を保存
            if success and result and 'comment' in result:
                comment = result['comment']
                result_data = {
                    "name": horse['name'],
                    "status": "success",
                    "comment_length": len(comment),
                    "comment_preview": comment[:200] + "..." if len(comment) > 200 else comment,
                    "comment_extracted": True
                }
                logger.info(f"コメントを抽出しました: {len(comment)}文字")
            else:
                result_data = {
                    "name": horse['name'],
                    "status": "success",
                    "comment_length": 0,
                    "comment_preview": "",
                    "comment_extracted": False,
                    "error": "コメントが見つかりませんでした"
                }
                logger.warning(f"コメントの抽出に失敗しました: {horse['name']}")
                
                # デバッグ用にHTMLを保存
                debug_file = f"debug_{horse['name']}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup))
                logger.info(f"デバッグ用にHTMLを保存しました: {debug_file}")
            results.append(result_data)
            logger.info(f"テスト完了: {horse['name']}")
            
        except Exception as e:
            logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
            results.append({
                "name": horse['name'], 
                "status": "error", 
                "message": str(e),
                "comment_extracted": False
            })
            
            # エラーが発生した場合もHTMLを保存
            try:
                debug_file = f"error_{horse['name']}.html"
                with open(debug_file, 'w', encoding='utf-8') as f:
                    f.write(str(soup) if 'soup' in locals() else 'No HTML content')
                logger.info(f"エラー詳細を {debug_file} に保存しました。")
            except Exception as e2:
                logger.error(f"エラー詳細の保存に失敗しました: {str(e2)}", exc_info=True)
    
    # 結果を保存
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    output_file = f"comment_extraction_test_results_{timestamp}.json"
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    
    # サマリーを表示
    success_count = len([r for r in results if r['status'] == 'success'])
    error_count = len([r for r in results if r['status'] == 'error'])
    comments_found = len([r for r in results if r.get('comment_extracted', False)])
    
    summary = f"""
    ===== テスト結果サマリー =====
    テスト日時: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
    -----------------------------
    総テストケース: {len(results)}
    成功: {success_count}
    エラー: {error_count}
    コメント抽出成功: {comments_found}/{len(results)}
    =============================
    詳細は {output_file} を確認してください。
    """
    
    logger.info(summary)
    print(summary)
    
    print(f"\n=== テスト完了 ===")
    print(f"結果は {output_file} に保存されました")
    print(f"コメントの抽出に失敗: {len(test_urls) - comments_found}頭")

if __name__ == "__main__":
    test_comment_extraction()
