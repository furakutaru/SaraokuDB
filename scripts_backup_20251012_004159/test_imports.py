import sys
import os
import logging

# ロギング設定
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # 相対インポートを試みる
    from .components.horse_info_extractor import HorseInfoExtractor
    logger.info("HorseInfoExtractor のインポートに成功しました")
except ImportError as e:
    logger.error(f"HorseInfoExtractor のインポートに失敗しました: {e}")
    
    # 絶対パスを試す
    try:
        sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        from scripts.components.horse_info_extractor import HorseInfoExtractor
        logger.info("絶対パスでのインポートに成功しました")
    except ImportError as e2:
        logger.error(f"絶対パスでのインポートにも失敗しました: {e2}")
        
        # モジュールの存在確認
        components_dir = os.path.join(os.path.dirname(__file__), 'components')
        if os.path.exists(components_dir):
            logger.info(f"components ディレクトリの内容: {os.listdir(components_dir)}")
        else:
            logger.error(f"components ディレクトリが見つかりません: {components_dir}")
