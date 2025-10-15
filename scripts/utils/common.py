"""
共通ユーティリティ関数を提供するモジュール
"""
import json
import logging
import os
from pathlib import Path
from typing import Dict, List, Any, Optional, Union


def setup_logging(log_level: str = 'INFO', log_file: Optional[str] = None) -> logging.Logger:
    """ロギングの設定を行う
    
    Args:
        log_level: ログレベル（'DEBUG', 'INFO', 'WARNING', 'ERROR', 'CRITICAL'）
        log_file: ログファイルのパス（Noneの場合はコンソールのみに出力）
        
    Returns:
        logging.Logger: 設定済みのロガーインスタンス
    """
    logger = logging.getLogger()
    logger.setLevel(log_level)
    
    # 既存のハンドラをクリア
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # フォーマッタの設定
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # コンソールハンドラの設定
    console_handler = logging.StreamHandler()
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # ファイルハンドラの設定（log_fileが指定されている場合）
    if log_file:
        # ログディレクトリが存在しない場合は作成
        log_dir = os.path.dirname(log_file)
        if log_dir:
            os.makedirs(log_dir, exist_ok=True)
            
        file_handler = logging.FileHandler(log_file, encoding='utf-8')
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def save_to_json(data: Any, file_path: Union[str, Path], indent: int = 2) -> None:
    """データをJSONファイルに保存する
    
    Args:
        data: 保存するデータ（JSONシリアライズ可能なオブジェクト）
        file_path: 保存先のファイルパス
        indent: インデント幅（Noneの場合は圧縮形式）
    """
    file_path = Path(file_path)
    file_path.parent.mkdir(parents=True, exist_ok=True)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=indent)
    
    logging.info(f"データを {file_path} に保存しました")


def load_from_json(file_path: Union[str, Path]) -> Any:
    """JSONファイルからデータを読み込む
    
    Args:
        file_path: 読み込むJSONファイルのパス
        
    Returns:
        JSONから読み込まれたデータ
    """
    file_path = Path(file_path)
    if not file_path.exists():
        logging.warning(f"ファイルが見つかりません: {file_path}")
        return None
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except json.JSONDecodeError as e:
        logging.error(f"JSONのデコードに失敗しました: {file_path} - {e}")
        return None


def get_file_hash(file_path: Union[str, Path]) -> str:
    """ファイルのMD5ハッシュを計算する
    
    Args:
        file_path: ハッシュを計算するファイルのパス
        
    Returns:
        str: 16進数表記のMD5ハッシュ値
    """
    file_path = Path(file_path)
    if not file_path.exists():
        return ""
    
    import hashlib
    
    hash_md5 = hashlib.md5()
    with open(file_path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_md5.update(chunk)
    
    return hash_md5.hexdigest()


def ensure_directory(directory: Union[str, Path]) -> Path:
    """ディレクトリが存在することを確認し、存在しない場合は作成する
    
    Args:
        directory: 確認するディレクトリのパス
        
    Returns:
        Path: 確認/作成されたディレクトリのPathオブジェクト
    """
    directory = Path(directory)
    directory.mkdir(parents=True, exist_ok=True)
    return directory


# モジュールのテスト
if __name__ == "__main__":
    # ロギングのテスト
    logger = setup_logging('DEBUG', 'test.log')
    logger.info("これは情報メッセージです")
    logger.debug("これはデバッグメッセージです")
    
    # JSONの保存と読み込みのテスト
    test_data = {"key": "value", "list": [1, 2, 3]}
    test_file = "test_data.json"
    
    save_to_json(test_data, test_file)
    loaded_data = load_from_json(test_file)
    print(f"読み込まれたデータ: {loaded_data}")
    
    # ファイルハッシュのテスト
    file_hash = get_file_hash(test_file)
    print(f"ファイルのハッシュ: {file_hash}")
    
    # テストファイルの削除
    import os
    if os.path.exists(test_file):
        os.remove(test_file)
    if os.path.exists("test.log"):
        os.remove("test.log")
