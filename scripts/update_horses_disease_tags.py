#!/usr/bin/env python3
# -*- coding: utf-8 -*-

import os
import sys
import logging
from datetime import datetime
from typing import List, Dict, Any, Optional

import importlib.util
import sys
from pathlib import Path

# プロジェクトのルートディレクトリをパスに追加
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root))

# 環境変数の読み込み
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    print("[INFO] dotenv パッケージがインストールされていません。環境変数は手動で設定してください。")

# データベース接続の動的インポート
def import_database_modules():
    """データベース関連モジュールを動的にインポート"""
    try:
        import os
        
        # プロジェクトのルートディレクトリをパスに追加
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        backend_path = os.path.join(project_root, 'backend')
        
        # パスを追加（重複を避ける）
        if backend_path not in sys.path:
            sys.path.insert(0, backend_path)
        
        # モジュールを直接インポート
        from database import SessionLocal
        from database.models import Horse
        
        # Horse モデルのカラムを確認
        if not hasattr(Horse, 'comment'):
            print("[WARN] Horse モデルに 'comment' カラムが見つかりません。利用可能なカラム:")
            for attr in dir(Horse):
                if not attr.startswith('_') and not callable(getattr(Horse, attr)):
                    print(f"  - {attr}")
            
            # 代わりのカラムを探す
            for attr in ['history', 'memo', 'notes', 'description']:
                if hasattr(Horse, attr):
                    print(f"[INFO] 代わりに '{attr}' カラムを使用します")
                    # 動的に属性を追加
                    setattr(Horse, 'comment', getattr(Horse, attr))
                    break
        
        print("[INFO] データベースモジュールを正常に読み込みました")
        return SessionLocal, Horse
        
    except ImportError as e:
        print(f"[ERROR] データベースモジュールのインポートに失敗しました: {e}")
        print(f"[DEBUG] Pythonパス: {sys.path}")
        print("\n以下のいずれかの方法を試してください:")
        print("1. 仮想環境が有効化されていることを確認")
        print("2. 必要なパッケージがインストールされていることを確認")
        print("   pip install -r requirements.txt")
        print("3. 環境変数 DATABASE_URL が正しく設定されていることを確認")
        print("   例: postgresql://user:password@localhost/dbname")
        sys.exit(1)

# データベースモジュールをインポート
SessionLocal, Horse = import_database_modules()
from scripts.components.disease_info_extractor import DiseaseInfoExtractor

# ロギングの設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('update_disease_tags.log')
    ]
)
logger = logging.getLogger(__name__)

class DiseaseTagUpdater:
    """馬の疾病タグを更新するクラス"""
    
    def __init__(self, batch_size: int = 100, dry_run: bool = False):
        """
        初期化メソッド
        
        Args:
            batch_size: 一度に処理するレコード数
            dry_run: 実際には更新せず、処理内容を表示するだけかどうか
        """
        self.batch_size = batch_size
        self.dry_run = dry_run
        self.extractor = DiseaseInfoExtractor(logger=logger)
        self.stats = {
            'total_processed': 0,
            'total_updated': 0,
            'total_horses': 0,
            'horses_with_diseases': 0,
            'errors': 0
        }
    
    def get_horses_batch(self, offset: int) -> List[dict]:
        """
        馬データをバッチで取得する
        
        Args:
            offset: オフセット
            
        Returns:
            List[dict]: 馬データの辞書のリスト
        """
        db = SessionLocal()
        try:
            # テーブルのカラムを動的に取得
            columns = [
                Horse.id,
                Horse.name,
            ]
            
            # コメントカラムを動的に追加
            text_column_name = None
            for col in ['comment', 'history', 'memo', 'notes', 'description']:
                if hasattr(Horse, col):
                    text_column_name = col
                    columns.append(getattr(Horse, col).label('text_content'))
                    break
                    
            if not text_column_name:
                raise AttributeError("テキストデータを取得するためのカラムが見つかりません")
                
            logger.info(f"使用するテキストカラム: {text_column_name}")
                
            # 疾病タグカラムがあれば追加
            if hasattr(Horse, 'disease_tags'):
                columns.append(Horse.disease_tags)
            
            # クエリを構築
            query = db.query(*columns)
            
            # テキストが存在するもののみをフィルタリング
            query = query.filter(getattr(Horse, text_column_name).isnot(None))
            
            # オフセットとリミットを適用
            results = query.offset(offset).limit(self.batch_size).all()
            logger.info(f"取得したレコード数: {len(results)}")
            return results
        except Exception as e:
            logger.error(f"馬データの取得中にエラーが発生しました: {e}", exc_info=True)
            return []
        finally:
            db.close()
    
    def update_horse_disease_tags(self, horse) -> bool:
        """
        馬の疾病タグを更新する
        
        Args:
            horse: 馬データ（名前付きタプル）
            
        Returns:
            bool: 更新が成功したかどうか
        """
        try:
            # テキストコンテンツを取得（動的な属性アクセス）
            text_content = getattr(horse, 'text_content', None)
            horse_id = getattr(horse, 'id', 'N/A')
            
            # テキストが空またはNoneの場合はスキップ
            if not text_content or str(text_content).strip() in ('[]', 'null', 'None', ''):
                logger.debug(f"[スキップ] 馬ID {horse_id} - テキストコンテンツが空です")
                return False
                
            # テキストの型と内容をデバッグログに出力
            logger.debug(f"[デバッグ] 馬ID {horse_id} - テキストの型: {type(text_content)}")
            logger.debug(f"[デバッグ] 馬ID {horse_id} - テキストの先頭100文字: {str(text_content)[:100]}")
            
            # テキストが辞書やリストの文字列表現の場合は、実際のオブジェクトに変換
            if isinstance(text_content, str) and (text_content.startswith('{') or text_content.startswith('[')):
                try:
                    import json
                    text_content = json.loads(text_content)
                    logger.debug(f"[デバッグ] 馬ID {horse_id} - JSONとしてパースしました: {type(text_content)}")
                except json.JSONDecodeError:
                    logger.debug(f"[デバッグ] 馬ID {horse_id} - JSONとしてパースできませんでした")
                    pass
                
            # テキストが長すぎる場合は切り詰めてログに記録
            preview = str(text_content)[:100] + ('...' if len(str(text_content)) > 100 else '')
            logger.debug(f"[処理中] 馬ID {horse_id} - テキスト: {preview}")
            
            # 疾病情報を抽出
            result = self.extractor.extract(text_content)
            diseases = result.get('diseases', [])
            
            # 疾病情報がなければスキップ
            if not diseases:
                logger.debug(f"[スキップ] 馬ID {horse_id} - 疾病情報が見つかりませんでした")
                return False
                
            # 疾病タグをカンマ区切りの文字列に変換
            disease_tags = ", ".join(diseases)
            
            # 現在のタグを取得（存在する場合）
            current_tags = getattr(horse, 'disease_tags', None)
            
            # タグが変更されていない場合はスキップ
            if current_tags == disease_tags:
                logger.debug(f"[スキップ] 馬ID {horse_id} - タグに変更がありません (現在: {current_tags}, 抽出: {disease_tags})")
                return False
                
            # 更新内容をログに記録
            logger.info(f"[更新] 馬ID: {horse.id}, 馬名: {horse.name}")
            logger.info(f"  テキスト: {text_content[:100]}...")
            logger.info(f"  抽出した疾病タグ: {disease_tags}")
            
            # ドライランの場合は更新しない
            if self.dry_run:
                return True
                
            # データベースを更新
            db = SessionLocal()
            try:
                db_horse = db.query(Horse).filter(Horse.id == horse.id).first()
                if db_horse:
                    db_horse.disease_tags = disease_tags
                    db.commit()
                    return True
                return False
            except Exception as e:
                db.rollback()
                logger.error(f"データベースの更新中にエラーが発生しました (馬ID: {horse.id}): {e}", exc_info=True)
                return False
            finally:
                db.close()
                
        except Exception as e:
            logger.error(f"馬ID {getattr(horse, 'id', 'N/A')} の処理中にエラーが発生しました: {e}", exc_info=True)
            self.stats['errors'] += 1
            return False
    
    def run(self):
        """バッチ処理を実行する"""
        logger.info("=== 馬の疾病タグ更新処理を開始します ===")
        logger.info(f"バッチサイズ: {self.batch_size}, ドライラン: {self.dry_run}")
        
        # 総馬数を取得
        db = SessionLocal()
        try:
            self.stats['total_horses'] = db.query(Horse.id).count()
            logger.info(f"処理対象の馬の総数: {self.stats['total_horses']}頭")
        except Exception as e:
            logger.error(f"総馬数の取得中にエラーが発生しました: {e}", exc_info=True)
            return
        finally:
            db.close()
        
        # バッチ処理の開始
        offset = 0
        while True:
            # バッチで馬データを取得
            horses = self.get_horses_batch(offset)
            if not horses:
                break
                
            logger.info(f"\n=== バッチ処理: {offset+1} - {offset + len(horses)} / {self.stats['total_horses']} ===")
            
            # 各馬の疾病タグを更新
            for horse in horses:
                self.stats['total_processed'] += 1
                
                # 進捗を表示
                if self.stats['total_processed'] % 10 == 0:
                    logger.info(f"処理中: {self.stats['total_processed']} / {self.stats['total_horses']}")
                
                # 疾病タグを更新
                try:
                    if self.update_horse_disease_tags(horse):
                        self.stats['total_updated'] += 1
                        self.stats['horses_with_diseases'] += 1
                except Exception as e:
                    logger.error(f"馬ID {horse.id} の処理中にエラーが発生しました: {e}", exc_info=True)
                    self.stats['errors'] += 1
            
            # 次のバッチに進む
            offset += self.batch_size
        
        # 処理結果を表示
        logger.info("\n=== 処理が完了しました ===")
        logger.info(f"総処理件数: {self.stats['total_processed']} 頭")
        logger.info(f"更新件数: {self.stats['total_updated']} 件")
        logger.info(f"疾病が検出された馬: {self.stats['horses_with_diseases']} 頭")
        logger.info(f"エラー件数: {self.stats['errors']} 件")
        
        if self.dry_run:
            logger.warning("※ ドライランモードのため、実際のデータは更新されていません。")


def main():
    """メイン関数"""
    import argparse
    
    # コマンドライン引数のパース
    parser = argparse.ArgumentParser(description='馬の疾病タグを更新します。')
    parser.add_argument('--batch-size', type=int, default=100, help='1回のバッチで処理するレコード数')
    parser.add_argument('--dry-run', action='store_true', help='実際には更新せず、処理内容を表示するだけ')
    
    args = parser.parse_args()
    
    # アップデーターを実行
    updater = DiseaseTagUpdater(
        batch_size=args.batch_size,
        dry_run=args.dry_run
    )
    updater.run()


if __name__ == "__main__":
    main()
