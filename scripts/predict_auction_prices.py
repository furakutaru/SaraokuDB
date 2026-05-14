#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天サラブレッドオークション落札価格予測ツール（本番稼働用）

提供された予測ロジックをベースに、スクレイピング機能と統合して
オークション開催時に自動実行されるツール
"""

import pandas as pd
import json
import logging
import sys
import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Tuple, Any

REPO_ROOT = Path(__file__).resolve().parent.parent
BACKEND_ROOT = REPO_ROOT / "backend"
sys.path.insert(0, str(REPO_ROOT))
sys.path.insert(0, str(BACKEND_ROOT))
sys.path.append(str(Path(__file__).parent))

# 既存のスクレイパーをインポート
from improved_scraper import ImprovedRakutenScraper, ScraperConfig

from services.auction_price_prediction import (
    analyze_sires,
    estimate_horse_price,
    load_training_dataframe_from_db,
)

# ロギング設定
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('predict_auction_prices.log', encoding='utf-8')
    ]
)
logger = logging.getLogger(__name__)


def load_historical_data_with_db_fallback() -> pd.DataFrame:
    """DB の成約履歴を優先し、空なら CSV にフォールバック。"""
    if os.environ.get("DATABASE_URL"):
        try:
            from database import SessionLocal

            db = SessionLocal()
            try:
                df = load_training_dataframe_from_db(db)
                if not df.empty:
                    logger.info("過去データをDBから読み込みました (%s 件)", len(df))
                    return df
            finally:
                db.close()
        except Exception as e:
            logger.warning("DBからの学習データ読み込みに失敗: %s", e)
    return load_historical_data()


def scrape_current_auction_horses() -> pd.DataFrame:
    """今回のオークション出走馬をスクレイピング"""
    logger.info("今回のオークション出走馬をスクレイピング開始...")

    try:
        config = ScraperConfig()
        scraper = ImprovedRakutenScraper(config)

        horse_list = scraper.scrape_horse_list(use_cache=True)
        logger.info(f"取得した馬リスト: {len(horse_list)}頭")

        if not horse_list:
            logger.warning("馬リストが空です")
            return pd.DataFrame()

        df_current = convert_scraped_data_to_dataframe(horse_list)
        logger.info(f"変換したDataFrame: {len(df_current)}頭")

        return df_current

    except Exception as e:
        logger.error(f"スクレイピング中にエラーが発生しました: {str(e)}")
        import traceback

        logger.error(traceback.format_exc())
        return pd.DataFrame()


def convert_scraped_data_to_dataframe(horse_list: List[Dict[str, Any]]) -> pd.DataFrame:
    """スクレイピングデータを予測用DataFrameに変換"""
    converted_data = []
    
    for horse in horse_list:
        try:
            # 必要なカラムにデータをマッピング
            row_data = {
                '馬名': horse.get('name', ''),
                '性別': horse.get('sex', ''),
                '年齢': horse.get('age', 0),
                '父': horse.get('sire', ''),
                '馬体重': horse.get('weight', 0),
                '落札時賞金': extract_prize_money(horse),
                '病歴': extract_disease_info(horse),
                '繁殖': '○' if horse.get('is_broodmare', False) else '',
                'オークション日': extract_auction_date(horse)
            }
            
            converted_data.append(row_data)
            
        except Exception as e:
            logger.warning(f"馬データの変換中にエラー: {horse.get('name', 'Unknown')} - {str(e)}")
            continue
    
    return pd.DataFrame(converted_data)

def extract_prize_money(horse: Dict[str, Any]) -> int:
    """馬データから賞金情報を抽出"""
    prize_money = 0
    
    # race_recordから賞金を抽出
    if 'race_record' in horse and horse['race_record']:
        try:
            if isinstance(horse['race_record'], str):
                race_record = json.loads(horse['race_record'])
            else:
                race_record = horse['race_record']
            
            # total_prize_latestやtotal_prize_startを確認
            if 'total_prize_latest' in race_record:
                prize_money = int(race_record['total_prize_latest'] or 0)
            elif 'total_prize_start' in race_record:
                prize_money = int(race_record['total_prize_start'] or 0)
                
        except (json.JSONDecodeError, ValueError, KeyError):
            pass
    
    # prize_moneyフィールドも確認
    if 'prize_money' in horse and horse['prize_money']:
        try:
            prize_money = int(horse['prize_money'] or 0)
        except (ValueError, TypeError):
            pass
    
    return prize_money

def extract_disease_info(horse: Dict[str, Any]) -> str:
    """馬データから病歴情報を抽出"""
    disease_info = ""
    
    # commentから病名を抽出
    if 'comment' in horse and horse['comment']:
        disease_info = horse['comment']
    
    # disease_tagsも確認
    if 'disease_tags' in horse and horse['disease_tags']:
        if disease_info:
            disease_info += " " + str(horse['disease_tags'])
        else:
            disease_info = str(horse['disease_tags'])
    
    return disease_info

def extract_auction_date(horse: Dict[str, Any]) -> str:
    """馬データからオークション日を抽出"""
    if 'auction_date' in horse and horse['auction_date']:
        return horse['auction_date']
    
    # デフォルトで今日の日付を返す
    return datetime.now().strftime('%Y-%m-%d')

def load_historical_data() -> pd.DataFrame:
    """過去の全落札データを読み込み"""
    logger.info("過去の落札データを読み込み中...")
    
    # 複数の可能性のあるCSVファイルを試行
    csv_files = [
        'horses_data.csv',
        'horses_export.csv', 
        'horses_all.csv'
    ]
    
    for csv_file in csv_files:
        csv_path = Path(__file__).parent.parent / csv_file
        if csv_path.exists():
            try:
                df = pd.read_csv(csv_path)
                logger.info(f"過去データを読み込みました: {csv_file} ({len(df)}件)")
                
                # 予測に必要なカラムが存在するか確認
                required_cols = ['落札価格', '父', '年齢', '性別', '落札時賞金']
                missing_cols = [col for col in required_cols if col not in df.columns]
                
                if missing_cols:
                    logger.warning(f"必要なカラムが不足しています: {missing_cols}")
                
                # カラム名のマッピングを試行
                df = map_column_names(df)
                
                # データ型変換とクリーニング
                df = clean_and_convert_data(df)
                
                return df
                
            except Exception as e:
                logger.warning(f"{csv_file}の読み込みに失敗: {str(e)}")
                continue
    
    logger.error("過去データファイルが見つかりません")
    return pd.DataFrame()

def map_column_names(df: pd.DataFrame) -> pd.DataFrame:
    """カラム名を予測ロジック用にマッピング"""
    column_mapping = {
        'sold_price': '落札価格',
        'total_prize_latest': '落札時賞金',
        'total_prize_start': '落札時賞金',
        'prize_money': '落札時賞金',
        'name': '馬名',
        'sex': '性別', 
        'age': '年齢',
        'sire': '父',
        'weight': '馬体重',
        'auction_date': 'オークション日'
    }
    
    df_mapped = df.copy()
    for old_name, new_name in column_mapping.items():
        if old_name in df.columns and new_name not in df.columns:
            df_mapped[new_name] = df_mapped[old_name]
    
    return df_mapped

def clean_and_convert_data(df: pd.DataFrame) -> pd.DataFrame:
    """データ型変換とクリーニング"""
    df_clean = df.copy()
    
    # 落札価格を数値に変換
    if '落札価格' in df_clean.columns:
        # 文字列の場合（JSON形式など）を処理
        df_clean['落札価格'] = df_clean['落札価格'].astype(str)
        df_clean['落札価格'] = df_clean['落札価格'].str.replace(r'[\[\]]', '', regex=True)
        df_clean['落札価格'] = pd.to_numeric(df_clean['落札価格'], errors='coerce').fillna(0)
    
    # 落札時賞金を数値に変換
    if '落札時賞金' in df_clean.columns:
        df_clean['落札時賞金'] = pd.to_numeric(df_clean['落札時賞金'], errors='coerce').fillna(0)
    
    # 年齢を数値に変換
    if '年齢' in df_clean.columns:
        df_clean['年齢'] = pd.to_numeric(df_clean['年齢'], errors='coerce').fillna(0)
    
    # 馬体重を数値に変換
    if '馬体重' in df_clean.columns:
        df_clean['馬体重'] = pd.to_numeric(df_clean['馬体重'], errors='coerce').fillna(0)
    
    return df_clean

def generate_predictions(current_horses: pd.DataFrame, sire_ranks: Dict[str, float]) -> pd.DataFrame:
    """今回の出品馬の予測を生成"""
    logger.info("予測を開始...")
    
    predictions = []
    
    for idx, row in current_horses.iterrows():
        try:
            est_min, est_max, price_range_str, valuation = estimate_horse_price(row, sire_ranks)
            
            prediction = {
                '馬名': row.get('馬名', ''),
                '性別': row.get('性別', ''),
                '年齢': row.get('年齢', 0),
                '父': row.get('父', ''),
                '馬体重': row.get('馬体重', 0),
                '落札時賞金': row.get('落札時賞金', 0),
                '病歴': row.get('病歴', ''),
                '繁殖': row.get('繁殖', ''),
                'オークション日': row.get('オークション日', ''),
                '予想価格(最小)': est_min,
                '予想価格(最大)': est_max,
                '予想価格レンジ': price_range_str,
                '査定ポイント': valuation
            }
            
            predictions.append(prediction)
            
        except Exception as e:
            logger.error(f"予測中にエラー: {row.get('馬名', 'Unknown')} - {str(e)}")
            continue
    
    return pd.DataFrame(predictions)

def generate_hot_horses_list(predictions_df: pd.DataFrame, top_n: int = 10) -> List[Dict[str, Any]]:
    """🌟HOT注目馬リストを生成"""
    # 予想価格(最大)でソート
    hot_horses = predictions_df.sort_values('予想価格(最大)', ascending=False).head(top_n)
    
    hot_list = []
    for _, row in hot_horses.iterrows():
        hot_horse = {
            '馬名': row['馬名'],
            '性別': row['性別'],
            '年齢': int(row['年齢']),
            '父': row['父'],
            '予想価格レンジ': row['予想価格レンジ'],
            '査定ポイント': row['査定ポイント']
        }
        hot_list.append(hot_horse)
    
    return hot_list


def save_results(predictions_df: pd.DataFrame, hot_list: List[Dict[str, Any]], output_dir: str = None):
    """結果を保存"""
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / 'prediction_results'
    
    output_path = Path(output_dir)
    output_path.mkdir(exist_ok=True)
    
    timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
    
    # CSV形式で全予測結果を保存
    csv_file = output_path / f'predictions_{timestamp}.csv'
    predictions_df.to_csv(csv_file, index=False, encoding='utf-8-sig')
    logger.info(f"予測結果を保存: {csv_file}")
    
    # JSON形式でも保存
    json_file = output_path / f'predictions_{timestamp}.json'
    predictions_df.to_json(json_file, orient='records', force_ascii=False, indent=2)
    logger.info(f"予測結果を保存: {json_file}")
    
    # HOT注目馬リストを保存
    hot_file = output_path / f'hot_horses_{timestamp}.json'
    with open(hot_file, 'w', encoding='utf-8') as f:
        json.dump(hot_list, f, ensure_ascii=False, indent=2)
    logger.info(f"HOT注目馬リストを保存: {hot_file}")

    return {
        'csv_file': str(csv_file),
        'json_file': str(json_file),
        'hot_file': str(hot_file),
    }

# ==========================================
# メイン実行部
# ==========================================

def main():
    """メイン処理"""
    logger.info("=== 楽天サラブレッドオークション価格予測ツール起動 ===")
    
    try:
        # 1. 過去データを読み込み
        historical_df = load_historical_data_with_db_fallback()
        if historical_df.empty:
            logger.error("過去データが読み込めませんでした。処理を中断します。")
            return
        
        # 2. 種牡馬のプレミアムを計算
        logger.info("種牡馬の固有プレミアムを計算中...")
        sire_ranks = analyze_sires(historical_df)
        logger.info(f"種牡馬プレミアムを計算完了: {len(sire_ranks)}頭")
        
        # 3. 今回のオークション出走馬をスクレイピング
        current_horses = scrape_current_auction_horses()
        if current_horses.empty:
            logger.error("今回の出走馬データが取得できませんでした。処理を中断します。")
            return
        
        logger.info(f"今回の出走馬: {len(current_horses)}頭")
        
        # 4. 予測を実行
        predictions_df = generate_predictions(current_horses, sire_ranks)
        logger.info(f"予測完了: {len(predictions_df)}頭")
        
        # 5. HOT注目馬リストを生成
        hot_list = generate_hot_horses_list(predictions_df, top_n=10)
        
        # 6. 結果を保存
        saved_files = save_results(predictions_df, hot_list)
        
        # 7. 結果のサマリーを表示
        print("\n" + "="*60)
        print("🌟 楽天サラブレッドオークション 価格予測結果")
        print("="*60)
        print(f"予測対象馬: {len(predictions_df)}頭")
        print(f"予測時刻: {datetime.now().strftime('%Y/%m/%d %H:%M')}")
        print()
        
        print("🔥 TOP 5 注目馬:")
        for i, horse in enumerate(hot_list[:5], 1):
            print(f"{i}. {horse['馬名']}（{horse['性別']}{horse['年齢']}歳）")
            print(f"   父: {horse['父']} | 予想: {horse['予想価格レンジ']}")
            print()
        
        print("📁 保存ファイル:")
        for key, filepath in saved_files.items():
            print(f"  {key}: {filepath}")
        
        print("\n✅ 予測処理が完了しました！")
        
    except Exception as e:
        logger.error(f"メイン処理中にエラーが発生しました: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        raise

if __name__ == "__main__":
    main()
