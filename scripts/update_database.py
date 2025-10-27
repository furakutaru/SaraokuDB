#!/usr/bin/env python3
"""
スクレイピング結果をデータベースに反映するスクリプト

使用方法:
    # デフォルトのパスで実行
    python update_database.py
    
    # カスタムパスを指定して実行
    python update_database.py --input /path/to/horses.json
    
    # デバッグモードで実行
    python update_database.py --debug
"""
import os
import sys
import json
import logging
import argparse
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, Optional, List, Tuple

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))
from backend.database.models import Base, Horse

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
    ]
)
logger = logging.getLogger(__name__)

def get_default_json_path() -> str:
    """デフォルトのJSONファイルのパスを取得する"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "frontend", "public", "data", "horses.json"
    )

def load_json_data(file_path: str) -> List[Dict[str, Any]]:
    """JSONファイルを読み込む
    
{{ ... }}
    Args:
        file_path: 読み込むJSONファイルのパス
        
    Returns:
        List[Dict[str, Any]]: 読み込んだJSONデータ
        
    Raises:
        FileNotFoundError: ファイルが存在しない場合
        json.JSONDecodeError: JSONの形式が不正な場合
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        if not isinstance(data, list):
            logger.warning("JSONデータがリスト形式ではありません。リストに変換します。")
            data = [data]
            
        return data
    except FileNotFoundError:
        logger.error(f"エラー: ファイルが見つかりません: {file_path}")
        raise
    except json.JSONDecodeError as e:
        logger.error(f"JSONのデコードに失敗しました: {str(e)}")
        raise

def init_db():
    """データベースを初期化する
    
    Returns:
        Session: SQLAlchemyセッション
        
    Raises:
        ValueError: DATABASE_URLが設定されていない場合
    """
    try:
        # 環境変数からデータベースURLを取得（必須）
        db_uri = os.environ.get('DATABASE_URL')
        
        if not db_uri:
            raise ValueError("環境変数DATABASE_URLが設定されていません。PostgreSQLデータベースの接続URLを設定してください。")
            
        # PostgreSQL (Neon) を使用
        logger.info("環境変数DATABASE_URLを使用してデータベースに接続します")
        if db_uri.startswith('postgres://'):
            # SQLAlchemy 1.4+ では postgres:// ではなく postgresql:// を使用する必要がある
            db_uri = db_uri.replace('postgres://', 'postgresql://', 1)
            
        engine = create_engine(db_uri, pool_pre_ping=True)
        
        # テーブルが存在しない場合は作成
        Base.metadata.create_all(engine)
        logger.info("テーブルの作成/確認が完了しました")
        
        # セッションを作成して返す
        Session = sessionmaker(bind=engine)
        session = Session()
        logger.info("データベースセッションを作成しました")
        return session
    except Exception as e:
        logger.error(f"データベースの初期化中にエラーが発生しました: {str(e)}", exc_info=True)
        raise

def get_default_horse_data(auction_id: str) -> Dict[str, Any]:
    """デフォルトの馬データを取得する
    
    Args:
        auction_id: オークションID
        
    Returns:
        Dict[str, Any]: デフォルト値が設定された馬データ
    """
    now = datetime.now(timezone.utc)
    return {
        'auction_id': auction_id,
        'name': '不明な馬名',
        'sex': json.dumps(['']),
        'age': None,
        'sire': '',
        'dam': '',
        'dam_sire': '',
        'race_record': json.dumps({}),
        'weight': None,
        'total_prize_start': 0.0,
        'total_prize_latest': 0.0,
        'sold_price': None,
        'auction_date': json.dumps([now.strftime('%Y-%m-%d')]),
        'seller': json.dumps(['']),
        'comment': json.dumps(['']),
        'image_url': '',
        'primary_image': '',
        'jbis_url': '',
        'detail_url': '',
        'created_at': now,
        'updated_at': now
    }

def normalize_horse_data(horse_data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """馬データを正規化する
    
    Args:
        horse_data: 入力となる馬データ
        
    Returns:
        Optional[Dict[str, Any]]: 正規化された馬データ（エラーの場合はNone）
    """
    try:
        auction_id = str(horse_data.get('id') or horse_data.get('auction_id', ''))
        if not auction_id:
            logger.warning("auction_idが見つからないため、スキップします")
            return None
            
        # デフォルト値で初期化
        normalized = get_default_horse_data(auction_id)
        
        # フィールドマッピング (入力フィールド名 -> 正規化済みフィールド名)
        field_mapping = {
            'name': 'name',
            'sex': 'sex',
            'age': 'age',
            'sire': 'sire',
            'dam': 'dam',
            'damsire': 'dam_sire',
            'dam_sire': 'dam_sire',
            'race_record': 'race_record',
            'race_records': 'race_record',
            'weight': 'weight',
            'total_prize_start': 'total_prize_start',
            'total_prize_latest': 'total_prize_latest',
            'sold_price': 'sold_price',
            'auction_date': 'auction_date',
            'seller': 'seller',
            'comment': 'comment',
            'image_url': 'image_url',
            'primary_image': 'primary_image',
            'jbis_url': 'jbis_url',
            'detail_url': 'detail_url',
            'url': 'detail_url'  # 念のため 'url' でもマッピング
        }
        
        # フィールドをマッピングに従ってコピー
        for src_field, dest_field in field_mapping.items():
            if src_field in horse_data and horse_data[src_field] is not None:
                if dest_field == 'race_record' and isinstance(horse_data[src_field], dict):
                    normalized[dest_field] = json.dumps(horse_data[src_field])
                elif dest_field in ['sold_price', 'auction_date', 'seller', 'comment']:
                    normalized[dest_field] = json.dumps([horse_data[src_field]])
                elif dest_field == 'image_url' and isinstance(horse_data[src_field], dict):
                    normalized[dest_field] = horse_data[src_field].get('image_url', '')
                else:
                    normalized[dest_field] = horse_data[src_field]
        
        # 数値フィールドの型変換
        try:
            if 'weight' in normalized and normalized['weight'] is not None:
                normalized['weight'] = int(normalized['weight'])
            if 'total_prize_start' in normalized and normalized['total_prize_start'] is not None:
                normalized['total_prize_start'] = float(normalized['total_prize_start'])
            if 'total_prize_latest' in normalized and normalized['total_prize_latest'] is not None:
                normalized['total_prize_latest'] = float(normalized['total_prize_latest'])
        except (ValueError, TypeError) as e:
            logger.warning(f"数値変換エラー (ID: {auction_id}): {str(e)}")
        
        return normalized
        
    except Exception as e:
        logger.error(f"馬データの正規化中にエラーが発生しました: {str(e)}")
        return None

def update_database(session, horses_data: List[Dict[str, Any]]) -> Tuple[int, int]:
    """データベースを更新する
    
    Args:
        session: SQLAlchemyセッション
        horses_data: 更新する馬データのリスト
        
    Returns:
        Tuple[int, int]: (作成件数, 更新件数)
    """
    created_count = 0
    updated_count = 0
    error_count = 0
    
    if not horses_data:
        logger.warning("更新するデータがありません")
        return 0, 0
    
    try:
        logger.info(f"データベース更新を開始します。合計{len(horses_data)}件の馬データを処理します。")
        
        for i, raw_horse_data in enumerate(horses_data, 1):
            try:
                # データの正規化
                horse_data = normalize_horse_data(raw_horse_data)
                if not horse_data:
                    error_count += 1
                    continue
                
                auction_id = horse_data['auction_id']
                logger.debug(f"[{i}/{len(horses_data)}] 処理中: ID={auction_id}, 馬名={horse_data.get('name', '不明')}")
                
                # 既存のデータを検索（auction_id で検索）
                horse = session.query(Horse).filter_by(auction_id=auction_id).first()
                
                if horse:
                    # 既存のデータを更新
                    for key, value in horse_data.items():
                        if key != 'created_at':  # created_atは更新しない
                            setattr(horse, key, value)
                    updated_count += 1
                    logger.debug(f"  - 更新: {auction_id}")
                else:
                    # 新しいデータを作成
                    horse = Horse(**horse_data)
                    session.add(horse)
                    created_count += 1
                    logger.debug(f"  - 新規作成: {auction_id}")
                
                # バッチコミット（100件ごと）
                if i % 100 == 0:
                    session.commit()
                    logger.info(f"  - 進捗: {i}/{len(horses_data)} (作成: {created_count}, 更新: {updated_count}, エラー: {error_count})")
            
            except Exception as e:
                error_count += 1
                logger.error(f"馬データの処理中にエラーが発生しました (インデックス: {i}): {str(e)}")
                logger.debug(f"エラーが発生したデータ: {raw_horse_data}")
                session.rollback()
                continue
        
        # 残りの変更をコミット
        session.commit()
        
        logger.info(f"データベースの更新が完了しました。")
        logger.info(f"  - 新規作成: {created_count}件")
        logger.info(f"  - 更新: {updated_count}件")
        if error_count > 0:
            logger.warning(f"  - エラー: {error_count}件")
        
        return created_count, updated_count
        
    except Exception as e:
        session.rollback()
        logger.error(f"データベースの更新中に予期しないエラーが発生しました: {str(e)}", exc_info=True)
        raise

def main() -> int:
    """メイン処理
    
    Returns:
        int: 終了コード (0: 成功, 1: エラー)
    """
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='スクレイピング結果をデータベースに反映')
    parser.add_argument(
        '--input', 
        type=str, 
        help=f'入力JSONファイルのパス (デフォルト: {get_default_json_path()})',
        default=str(get_default_json_path())
    )
    parser.add_argument(
        '--debug', 
        action='store_true',
        help='デバッグモードで実行 (より詳細なログを出力)'
    )
    args = parser.parse_args()
    
    # ログレベルを設定
    if args.debug:
        logger.setLevel(logging.DEBUG)
    
    try:
        json_path = Path(args.input).resolve()
        logger.info(f"入力ファイル: {json_path}")
        
        # ファイルの存在確認
        if not json_path.exists():
            logger.error(f"エラー: ファイルが見つかりません: {json_path}")
            return 1
        
        # JSONデータを読み込む
        logger.info("JSONファイルを読み込んでいます...")
        data = load_json_data(json_path)
        
        if not data:
            logger.warning("警告: 有効なデータが含まれていません")
            return 0
        
        logger.info(f"{len(data)}件の馬データを読み込みました")
        
        # データベースを初期化
        logger.info("データベースに接続しています...")
        session = init_db()
        
        # データベースを更新
        logger.info("データベースを更新しています...")
        created, updated = update_database(session, data)
        
        logger.info(f"処理が完了しました。新規作成: {created}件, 更新: {updated}件")
        return 0
        
    except KeyboardInterrupt:
        logger.info("処理がユーザーによって中断されました")
        return 1
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
