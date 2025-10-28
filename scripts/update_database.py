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
from typing import Dict, List, Optional, Any, Tuple
import json
import logging
import os
import sys
from datetime import datetime, timezone
from sqlalchemy import create_engine, Column, Integer, String, Float, Text, DateTime, Boolean, ForeignKey, func, or_
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session, relationship
from sqlalchemy.exc import SQLAlchemyError, IntegrityError
from dotenv import load_dotenv
import argparse
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent.parent))
from backend.database.models import Base, Horse, AuctionHistory

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_database.log')
    ]
)
logger = logging.getLogger(__name__)

def get_default_json_path() -> str:
    """デフォルトのJSONファイルのパスを取得する"""
    return os.path.join(
        os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
        "static-frontend", "public", "data", "horses.json"
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
        'is_unsold': False,  # デフォルトは落札済み
        'bid_count': 0,      # デフォルトの入札数は0
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
            'is_unsold': 'is_unsold',  # is_unsold フィールドをマッピング
            'bid_count': 'bid_count',   # bid_count フィールドをマッピング
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
            # bid_count フィールドは無視
            if dest_field == 'bid_count':
                continue
                
            if src_field in horse_data and horse_data[src_field] is not None:
                try:
                    if dest_field == 'race_record' and isinstance(horse_data[src_field], dict):
                        normalized[dest_field] = json.dumps(horse_data[src_field])
                    elif dest_field == 'is_unsold':
                        # is_unsold は必ずブール値に変換
                        normalized[dest_field] = bool(horse_data[src_field]) if horse_data[src_field] is not None else False
                    elif dest_field == 'bid_count':
                        # bid_count は整数に変換（Noneの場合は0）
                        normalized[dest_field] = int(horse_data[src_field]) if horse_data[src_field] is not None else 0
                    elif dest_field in ['auction_date', 'seller', 'comment']:
                        # 文字列のリストとして保存
                        normalized[dest_field] = json.dumps([str(horse_data[src_field])])
                    elif dest_field == 'sold_price':
                        # sold_price は文字列として保存
                        normalized[dest_field] = str(horse_data[src_field]) if horse_data[src_field] is not None else None
                    elif dest_field == 'image_url' and isinstance(horse_data[src_field], dict):
                        normalized[dest_field] = horse_data[src_field].get('image_url', '')
                    else:
                        # その他のフィールドはそのまま代入
                        normalized[dest_field] = horse_data[src_field]
                except (ValueError, TypeError) as e:
                    logger.warning(f"フィールド '{dest_field}' の値 '{horse_data[src_field]}' の変換に失敗しました: {str(e)}")
                    # デフォルト値を設定
                    if dest_field == 'is_unsold':
                        normalized[dest_field] = False
                    elif dest_field == 'bid_count':
                        normalized[dest_field] = 0
                    else:
                        normalized[dest_field] = None
        
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

def update_database(session, horses_data: List[Dict[str, Any]]) -> Tuple[int, int, int]:
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
    
    try:
        for i, horse_data in enumerate(horses_data, 1):
            try:
                # 馬データを正規化
                normalized = normalize_horse_data(horse_data)
                if not normalized:
                    logger.warning(f"馬データの正規化に失敗しました (インデックス: {i})")
                    error_count += 1
                    continue
                
                auction_id = normalized.get('auction_id')
                if not auction_id:
                    logger.warning(f"auction_id が見つかりません (インデックス: {i})")
                    error_count += 1
                    continue
                
                # 既存のレコードを検索
                existing_horse = session.query(Horse).filter_by(auction_id=auction_id).first()
                
                if existing_horse:
                    # 既存のレコードを更新
                    update_fields = {}
                    
                    for key, value in normalized.items():
                        # 主キーは更新しない
                        if key == 'id':
                            continue
                            
                        # フィールドが存在するか確認
                        if not hasattr(Horse, key):
                            logger.warning(f"フィールド '{key}' はモデルに存在しません")
                            continue
                            
                        try:
                            # 型に合わせて値を変換
                            if key == 'race_record' and isinstance(value, dict):
                                value = json.dumps(value, ensure_ascii=False)
                            elif key == 'is_unsold':
                                value = bool(value) if value is not None else False
                            
                            # bid_count は除外
                            if key == 'bid_count':
                                continue
                            
                            # 現在の値と異なる場合のみ更新対象に追加
                            current_value = getattr(existing_horse, key)
                            if current_value != value:
                                update_fields[key] = value
                                logger.debug(f"  - フィールド '{key}' を更新予定: {current_value} -> {value}")
                                
                        except Exception as e:
                            logger.error(f"フィールド '{key}' の更新に失敗しました: {str(e)}")
                            logger.debug(f"  - 値: {value} (型: {type(value)})")
                    
                    # 更新対象のフィールドがある場合のみ更新を実行
                    if update_fields:
                        try:
                            # 個別にフィールドを更新
                            for key, value in update_fields.items():
                                setattr(existing_horse, key, value)
                            
                            # 更新日時を設定
                            existing_horse.updated_at = datetime.now(timezone.utc)
                            
                            # 変更をコミット
                            session.commit()
                            updated_count += 1
                            logger.debug(f"  - 更新: {auction_id} (更新フィールド数: {len(update_fields)})")
                        except Exception as e:
                            logger.error(f"レコードの更新に失敗しました (auction_id: {auction_id}): {str(e)}")
                            logger.error(f"エラーの詳細: {str(e.__class__.__name__)}: {str(e)}", exc_info=True)
                            error_count += 1
                            session.rollback()
                            continue
                else:
                    # 新しいレコードを作成
                    # race_recordが辞書型の場合はJSON文字列に変換
                    if 'race_record' in normalized and isinstance(normalized['race_record'], dict):
                        try:
                            normalized['race_record'] = json.dumps(normalized['race_record'], ensure_ascii=False)
                        except Exception as e:
                            logger.error(f"新しいレコードのrace_recordのJSONシリアライズに失敗: {str(e)}")
                            normalized['race_record'] = None
                    
                    # 存在するフィールドのみを抽出
                    horse_attrs = {k: v for k, v in normalized.items() if hasattr(Horse, k)}
                    
                    try:
                        logger.debug(f"  - 新規作成: {auction_id}, データ: {horse_attrs}")
                        
                        # 必須フィールドを抽出
                        is_unsold = bool(horse_attrs.pop('is_unsold', False))
                        bid_count = int(horse_attrs.pop('bid_count', 0))
                        
                        try:
                            # 新しいHorseインスタンスを作成
                            new_horse = Horse()
                            
                            # オークション日付と販売者を取得
                            auction_date_list = json.loads(horse_attrs.get('auction_date', '[]'))
                            seller_list = json.loads(horse_attrs.get('seller', '[]'))
                            
                            # 新しいAuctionHistoryインスタンスを作成してis_unsoldを設定
                            auction_history = AuctionHistory(
                                horse_name=horse_attrs.get('name', ''),
                                auction_date=auction_date_list[0] if auction_date_list else None,
                                price=int(horse_attrs.get('sold_price', 0)) if not is_unsold else 0,
                                seller=seller_list[0] if seller_list else None,
                                is_unsold=is_unsold,
                                sire_name=horse_attrs.get('sire', ''),
                                dam_name=horse_attrs.get('dam', ''),
                                damsire_name=horse_attrs.get('dam_sire', '')
                            )
                            
                            # リレーションシップを設定
                            new_horse.latest_auction = auction_history
                            new_horse.auction_histories = [auction_history]
                            
                            logger.debug(f"    - オークション履歴を作成: is_unsold = {is_unsold}, bid_count = {bid_count}")
                        except Exception as e:
                            logger.error(f"オークション履歴の作成に失敗しました: {str(e)}")
                            raise
                        except Exception as e:
                            logger.error(f"bid_count の設定に失敗しました: {str(e)}")
                            raise
                        
                        # その他のフィールドを設定
                        for key, value in horse_attrs.items():
                            if hasattr(new_horse, key) and key not in ['is_unsold', 'bid_count']:
                                try:
                                    object.__setattr__(new_horse, key, value)
                                    logger.debug(f"    - フィールド設定: {key} = {value}")
                                except Exception as e:
                                    logger.error(f"フィールド '{key}' の設定に失敗しました: {str(e)}")
                                    raise
                        
                        session.add(new_horse)
                        session.flush()  # 即座にSQLを発行してエラーを検出
                        created_count += 1
                        logger.debug(f"  - 新規作成成功: {auction_id}")
                        
                    except Exception as e:
                        logger.error(f"レコードの作成に失敗しました (auction_id: {auction_id}): {str(e)}", exc_info=True)
                        logger.error(f"エラーのあるデータ: {horse_attrs}")
                        error_count += 1
                        session.rollback()
                        continue
                
                # バッチコミット（100件ごと）
                if i % 100 == 0:
                    session.commit()
                    logger.info(f"  - 進捗: {i}/{len(horses_data)} (作成: {created_count}, 更新: {updated_count}, エラー: {error_count})")
            
            except Exception as e:
                error_count += 1
                logger.error(f"馬データの処理中にエラーが発生しました (インデックス: {i}): {str(e)}")
                logger.debug(f"エラーが発生したデータ: {horse_data}")
                session.rollback()
                continue
        
        # 残りの変更をコミット
        session.commit()
        
        logger.info(f"データベースの更新が完了しました。")
        logger.info(f"  - 新規作成: {created_count}件")
        logger.info(f"  - 更新: {updated_count}件")
        if error_count > 0:
            logger.warning(f"  - エラー: {error_count}件")
        
        return created_count, updated_count, error_count
        
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
        created, updated, errors = update_database(session, data)
        
        logger.info(f"処理が完了しました。新規作成: {created}件, 更新: {updated}件, エラー: {errors}件")
        return 0
        
    except KeyboardInterrupt:
        logger.info("処理がユーザーによって中断されました")
        return 1
    except Exception as e:
        logger.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        return 1

if __name__ == '__main__':
    sys.exit(main())
