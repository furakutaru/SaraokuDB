#!/usr/bin/env python3
"""
既存のキャッシュファイルを使用してテストを実行するスクリプト
"""
import os
import sys
import logging
from pathlib import Path
from improved_scraper import ImprovedRakutenScraper

# ロギングの設定
logging.basicConfig(
    level=logging.DEBUG,  # DEBUGレベルで詳細なログを出力
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_cache.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)
# 依存ライブラリのログレベルをWARNINGに設定
logging.getLogger('urllib3').setLevel(logging.WARNING)
logging.getLogger('requests').setLevel(logging.WARNING)
logging.getLogger('selenium').setLevel(logging.WARNING)

def get_cache_key(url: str) -> str:
    """URLからキャッシュキーを生成する（ImprovedRakutenScraper._get_cache_keyと同一の実装）"""
    import hashlib
    import re
    
    # URLを安全なファイル名に変換
    clean_url = re.sub(r'[^a-zA-Z0-9]', '_', url)
    # ハッシュを追加して一意性を確保
    url_hash = hashlib.md5(url.encode('utf-8')).hexdigest()[:8]
    return f"{clean_url[:50]}_{url_hash}"

def setup_cache():
    """テスト用のキャッシュをセットアップ"""
    # テスト用キャッシュディレクトリ（絶対パスで指定）
    base_dir = Path(__file__).parent.absolute()
    cache_dir = base_dir / "test_cache"
    
    # キャッシュディレクトリをクリアして再作成
    import shutil
    if cache_dir.exists():
        shutil.rmtree(cache_dir)
    cache_dir.mkdir(exist_ok=True)
    
    # 元のキャッシュファイルが保存されているディレクトリ
    html_cache_dir = base_dir / "html_cache"
    
    # リストページのキャッシュをコピー
    list_url = "https://auction.keiba.rakuten.co.jp/list/"
    list_cache_key = get_cache_key(list_url)
    list_cache_file = None
    
    # キャッシュディレクトリの内容をログに出力
    logger.debug(f"HTMLキャッシュディレクトリの内容 ({html_cache_dir}):")
    for f in sorted(html_cache_dir.glob("*.html")):
        logger.debug(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    # キャッシュキーのハッシュ部分を取得
    hash_part = list_cache_key.split('_')[-1]
    logger.debug(f"リストページのキャッシュを検索中... 検索キー: {hash_part}")
    
    # ファイル名にハッシュ部分が含まれるファイルを検索
    for f in html_cache_dir.glob("*.html"):
        if hash_part in f.name and "list" in f.name.lower():
            list_cache_file = f
            logger.debug(f"リストページのキャッシュ候補を見つけました: {f.name} (サイズ: {f.stat().st_size} bytes)")
            break
    
    # 見つからなかった場合は、ハッシュ部分のみで再検索
    if list_cache_file is None:
        for f in html_cache_dir.glob("*.html"):
            if hash_part in f.name:
                list_cache_file = f
                logger.debug(f"リストページのキャッシュ候補（ハッシュ一致）: {f.name} (サイズ: {f.stat().st_size} bytes)")
                break
    
    # まだ見つからない場合は、最初に見つかった大きなHTMLファイルを使用
    if list_cache_file is None:
        for f in sorted(html_cache_dir.glob("*.html"), key=lambda x: x.stat().st_size, reverse=True):
            if f.stat().st_size > 50000:  # 50KB以上のファイルをリストページとみなす
                list_cache_file = f
                logger.warning(f"リストページのキャッシュとして使用: {f.name} (サイズ: {f.stat().st_size} bytes)")
                break
    
    if list_cache_file and list_cache_file.exists():
        # キャッシュファイルを保存（元のファイル名をそのまま使用）
        dest_file = cache_dir / list_cache_file.name
        shutil.copy2(list_cache_file, dest_file)
        logger.info(f"リストページのキャッシュをセットアップ: {dest_file}")
        logger.debug(f"URL: {list_url}, キャッシュキー: {list_cache_key}, ファイル: {list_cache_file.name}")
    else:
        logger.error(f"リストページのキャッシュが見つかりません。検索キー: {hash_part}")
        logger.error(f"キャッシュディレクトリの内容: {[f.name for f in html_cache_dir.glob('*.html')]}")
        raise FileNotFoundError("リストページのキャッシュファイルが見つかりません")
    
    # 詳細ページのキャッシュをコピー
    detail_urls = [
        "https://auction.keiba.rakuten.co.jp/item/14643",
        "https://auction.keiba.rakuten.co.jp/item/14644",
        "https://auction.keiba.rakuten.co.jp/item/14645"
    ]
    
    for detail_url in detail_urls:
        cache_key = get_cache_key(detail_url)
        src_file = None
        
        # キャッシュキーのハッシュ部分で検索
        hash_part = cache_key.split('_')[-1]
        for f in html_cache_dir.glob("*.html"):
            if hash_part in f.name:
                src_file = f
                logger.debug(f"詳細ページのキャッシュ候補を見つけました: {f.name} (URL: {detail_url})")
                break
            
        if src_file and src_file.exists():
            # キャッシュファイルを保存（元のファイル名をそのまま使用）
            dest_file = cache_dir / src_file.name
            shutil.copy2(src_file, dest_file)
            logger.info(f"詳細ページのキャッシュをセットアップ: {detail_url}")
            logger.debug(f"キャッシュキー: {cache_key}, ファイル: {src_file.name} -> {dest_file}")
        else:
            logger.warning(f"詳細ページのキャッシュが見つかりません: {detail_url} (検索パターン: *{hash_part}*.html)")
    
    # キャッシュディレクトリの内容をログに出力（デバッグ用）
    logger.debug("キャッシュディレクトリの内容:")
    for f in cache_dir.glob("*"):
        logger.debug(f"  - {f.name} ({f.stat().st_size} bytes)")
    
    return str(cache_dir)

def main():
    try:
        logger.info("テストを開始します...")
        
        # テスト用キャッシュをセットアップ
        cache_dir = setup_cache()
        
        # スクレイパーを初期化（テストモードで）
        logger.info(f"スクレイパーを初期化します。キャッシュディレクトリ: {cache_dir}")
        scraper = ImprovedRakutenScraper(
            test_mode=True, 
            cache_dir=cache_dir,
            timeout=30,
            max_retries=1  # テスト中はリトライを最小限に
        )
        
        # キャッシュディレクトリが正しく設定されているか確認
        logger.debug(f"スクレイパーのキャッシュディレクトリ: {getattr(scraper, 'cache_dir', '未設定')}")
        logger.debug(f"スクレイパーのテストモード: {getattr(scraper, 'test_mode', '未設定')}")
            
        # 馬の一覧を取得
        logger.info("馬の一覧を取得中...")
        horses = scraper.scrape_horse_list(use_cache=True)
            
        if not horses:
            logger.error("馬の一覧を取得できませんでした")
            return 1
                
        logger.info(f"{len(horses)}頭の馬の情報を取得しました")
        
        # 最初の馬の詳細を取得
        if horses:
            first_horse = horses[0]
            logger.info(f"最初の馬の情報: {first_horse.get('name', '不明')}")
            
            # 詳細ページのURLが取得できているか確認
            detail_url = first_horse.get('detail_url')
            if detail_url:
                logger.info(f"詳細ページのURL: {detail_url}")
                
                # 詳細ページをスクレイピング
                logger.info("詳細情報を取得中...")
                detail = scraper.scrape_horse_detail(detail_url, save_html=True)
                
                if detail:
                    logger.info("詳細情報の取得に成功しました")
                    logger.info(f"性別: {detail.get('sex', '不明')}")
                    logger.info(f"年齢: {detail.get('age', '不明')}歳")
                    logger.info(f"JBIS URL: {detail.get('jbis_url', '不明')}")
                else:
                    logger.warning("詳細情報の取得に失敗しました")
            else:
                logger.warning("詳細ページのURLが取得できませんでした")
        
        logger.info("テストが完了しました")
        return 0
        
    except Exception as e:
        logger.error(f"テスト中にエラーが発生しました: {str(e)}", exc_info=True)
        return 1

if __name__ == "__main__":
    sys.exit(main())
