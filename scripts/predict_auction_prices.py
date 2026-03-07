#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
楽天サラブレッドオークション落札価格予測ツール（本番稼働用）

提供された予測ロジックをベースに、スクレイピング機能と統合して
オークション開催時に自動実行されるツール
"""

import pandas as pd
import math
import json
import logging
import sys
import os
from datetime import datetime, date
from pathlib import Path
from typing import Dict, List, Tuple, Any

# スクリプトのルートディレクトリをパスに追加
sys.path.append(str(Path(__file__).parent))
sys.path.append(str(Path(__file__).parent.parent))

# 既存のスクレイパーをインポート
from improved_scraper import ImprovedRakutenScraper, ScraperConfig

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

# ==========================================
# 定数（CONST）定義 - 予測ロジックのコア部分（変更禁止）
# ==========================================
WEIGHT_MODIFIERS = {
    "超軽量": -0.15, "軽量_牡セ": -0.05, "軽量_牝": 0.0,
    "普通": 0.0, "大型": 0.05, "超大型": 0.10
}

DISEASE_CATEGORIES = {
    "致命的": ["屈腱炎", "繋靭帯炎", "腱損傷", "じん帯損傷", "腰フラ", "蹄葉炎", "神経麻痺", "腸捻転"],
    "重度_治療可": ["骨折", "ボーンシスト", "ウォブラー症候群", "OCD", "離断性骨軟骨炎"],
    "中程度": ["骨膜炎", "フレグモーネ", "骨片", "関節炎", "膝関節炎", "球節炎", "飛節炎", "前膝腱炎", "腱鞘炎", "跛行", "跛る", "肉離れ", "横紋筋融解症", "鶏跛", "喉鳴り", "軟口蓋の癒着", "喉頭蓋エントラップメント", "喉頭蓋炎", "鼻出血", "肺出血", "喘鳴症", "DDSP", "軟口蓋背側変位", "疝痛", "鼓腸症", "大腸炎", "裂蹄", "蹄中隔炎", "蹄の亀裂", "蹄内出血", "繋皸", "けいくん", "角膜炎"],
    "軽微": ["蟻洞", "骨瘤", "骨膜肥厚", "エクイロックス", "脚部不安", "脚元不安", "こり症", "筋肉痛", "筋肉炎", "コズミ", "挫跖", "ざせき", "旋回癖", "旋回症", "さく癖", "ゆう癖", "カケス", "気管支炎", "呼吸器不安", "上気道炎", "胃潰瘍", "下痢", "食欲不振", "風気疝", "ガス腹", "ロタウイルス感染症", "馬インフルエンザ", "皮膚糸状菌症", "感冒", "蹄不安", "蹄傷", "蹄底負傷", "蹄球損傷", "打撲", "擦過傷", "裂傷", "腫脹", "炎症", "創傷", "皮膚炎", "疥癬", "蕁麻疹", "結膜炎"]
}

DISEASE_PENALTIES = {"致命的": -0.60, "重度_治療可": -0.30, "中程度": -0.20, "軽微": -0.10}

# ==========================================
# 予測ロジック関数（変更禁止）
# ==========================================

def analyze_sires(df):
    """種牡馬の固有プレミアムを計算（過去データから）"""
    def get_rough_base(row):
        age = row.get('年齢', 4) if pd.notna(row.get('年齢')) else 4
        prize = row.get('落札時賞金', 0) if pd.notna(row.get('落札時賞金')) else 0
        sex = str(row.get('性別', '牡'))
        if age <= 3:
            if prize == 0 and sex in ['牝', 'セ']: base = 600000
            else: base = 800000
        else:
            prize_mult = 0.03
            if age >= 8: prize_mult = 0.015
            elif age >= 6: prize_mult = 0.02
            base = 500000 + (prize * prize_mult)
        if age >= 5:
            base *= (1.0 - min(0.50, (age - 4) * 0.10))
        return base
        
    df_calc = df[df['落札価格'] > 0].copy()
    df_calc['base_est'] = df_calc.apply(get_rough_base, axis=1)
    df_calc['prem_rate'] = (df_calc['落札価格'] / df_calc['base_est']) - 1.0
    stats = df_calc.groupby('父')['prem_rate'].agg(['median', 'count'])
    
    sire_multiplier = {}
    for sire, row in stats.iterrows():
        if row['count'] >= 3:
            sire_multiplier[sire] = max(-0.40, min(0.60, row['median']))
        else:
            sire_multiplier[sire] = 0.0
    return sire_multiplier

def extract_disease_severity(text):
    """病歴テキストから疾患の重症度を抽出（変更禁止）"""
    if not isinstance(text, str) or not text.strip(): return [], []
    found_severities = set()
    found_diseases = []
    for severity, keywords in DISEASE_CATEGORIES.items():
        for kw in keywords:
            if kw in text:
                found_severities.add(severity)
                found_diseases.append(kw)
    return list(found_severities), found_diseases

def estimate_horse_price(row, sire_ranks):
    """馬の価格を予測（変更禁止）"""
    points = []
    age = row.get('年齢', 4) if not pd.isna(row.get('年齢')) else 4
    sex = str(row.get('性別', '牡'))
    sire = str(row.get('父', ''))
    weight = row.get('馬体重', 450) if not pd.isna(row.get('馬体重')) else 450
    prize_money = row.get('落札時賞金', 0) if not pd.isna(row.get('落札時賞金')) else 0
    disease_text = str(row.get('病歴', '')) if not pd.isna(row.get('病歴')) else ''
    is_broodmare = (row.get('繁殖') == '○')

    auction_month = None
    if 'オークション日' in row and pd.notna(row['オークション日']):
        try: auction_month = pd.to_datetime(row['オークション日']).month
        except: pass

    severities, found_diseases = extract_disease_severity(disease_text)
    if found_diseases:
        points.append(f"検出疾病: {', '.join(found_diseases)}")

    # 【大改善】賞金評価の過剰ペナルティ（二重苦）を排除
    if age <= 3:
        if prize_money == 0 and sex in ['牝', 'セ']:
            base_price = 600000
            points.append(f"{int(age)}歳未勝利・牝/セ基準(60万)")
        else:
            base_price = 800000
            points.append(f"{int(age)}歳基準(80万)")
    else:
        prize_mult = 0.03
        if age >= 8:
            prize_mult = 0.015
            points.append("超高齢(8歳〜)賞金加算半減")
        elif age >= 6:
            prize_mult = 0.02
            points.append("高齢(6歳〜)賞金加算微減")
        else:
            points.append("実績馬(基本50万＋賞金加算)")
        base_price = 500000 + (prize_money * prize_mult)

    positive_mod = 0.0
    if weight <= 404:
        positive_mod += WEIGHT_MODIFIERS["超軽量"]
        points.append("超軽量(-15%)")
    elif 405 <= weight <= 449:
        if sex != "牝":
            positive_mod += WEIGHT_MODIFIERS["軽量_牡セ"]
            points.append("軽量牡/セ(-5%)")
    elif 494 <= weight <= 538:
        positive_mod += WEIGHT_MODIFIERS["大型"]
        points.append("大型馬(+5%)")
    elif weight >= 539:
        positive_mod += WEIGHT_MODIFIERS["超大型"]
        points.append("超大型馬(+10%)")

    sire_prem = sire_ranks.get(sire, 0.0)
    if sire_prem > 0:
        positive_mod += sire_prem
        points.append(f"種牡馬({sire})適正プレミアム(+{int(sire_prem*100)}%)")
    elif sire_prem < 0:
        positive_mod += sire_prem
        points.append(f"種牡馬({sire})ディスカウント({int(sire_prem*100)}%)")

    # 【大改善】高齢による実績プレミアム剥奪を撤廃。実績は永遠の箔。
    if prize_money >= 20000000:
        positive_mod += 0.30
        points.append("中央実績馬プレミアム(+30%)")
    elif prize_money >= 10000000:
        positive_mod += 0.20
        points.append("オープン馬/準実績馬評価(+20%)")
    elif prize_money >= 3000000:
        positive_mod += 0.10
        points.append("地方即戦力評価(+10%)")

    if auction_month:
        if age == 3 and auction_month in [8, 9]:
            positive_mod += 0.25
            points.append("秋季3歳中央未勝利落ちプレミアム(+25%)")
        elif age == 2 and auction_month in [11, 12]:
            positive_mod -= 0.20
            points.append("年末2歳見切り馬ディスカウント(-20%)")

    if sex == 'セ' and age >= 6 and prize_money < 30000000:
        positive_mod -= 0.10
        points.append("セン馬・高齢による繁殖無価値化(-10%)")

    disease_mod = 0.0
    if "致命的" in severities: disease_mod = DISEASE_PENALTIES["致命的"]
    elif "重度_治療可" in severities: disease_mod = DISEASE_PENALTIES["重度_治療可"]
    elif "中程度" in severities: disease_mod = DISEASE_PENALTIES["中程度"]
    elif "軽微" in severities: disease_mod = DISEASE_PENALTIES["軽微"]

    if disease_mod < 0:
        if age <= 3:
            disease_mod *= 0.50
            points.append("若駒将来性による疾病リスク半減")
        if positive_mod >= 0.40:
            disease_mod *= 0.50
            points.append("高期待値・名馬プレミアムによる疾病リスク半減")

    modifier_sum = positive_mod + disease_mod
    est_base = base_price * (1.0 + modifier_sum)

    min_factor = 0.55
    max_factor = 1.60
    
    if prize_money >= 50000000:
        min_factor = 0.30
        max_factor = 2.50
        points.append("超名馬ボラティリティ拡張(底値〜青天井許容)")
    elif prize_money >= 30000000:
        min_factor = 0.40
        max_factor = 2.00
        points.append("名馬ボラティリティ拡張(レンジ幅拡大)")

    if prize_money < 1000000:
        min_factor = min(min_factor, 0.40)
        points.append("未勝利・低賞金馬の下振れリスク許容")

    est_min = max(0, est_base * min_factor)
    est_max = max(0, est_base * max_factor)

    # 全体に対する年齢ペナルティは維持（ここで引くのでベースは引かなくて良い）
    if age >= 5:
        age_penalty = min(0.80, (age - 4) * 0.10)
        est_min *= (1.0 - age_penalty)
        est_max *= (1.0 - age_penalty)
        points.append(f"年齢減価(-{int(age_penalty*100)}%)")

    if sex == "牝" and is_broodmare:
        est_min = max(est_min, 200000)
        est_max = max(est_max, 500000)
        if "繁殖牝馬最低保障" not in points: points.append("繁殖牝馬最低保障")
    elif sex in ["牡", "セ"]:
        est_min = max(est_min, 100000)
        est_max = max(est_max, 100000)
        
    est_min_man = math.floor(est_min / 10000)
    est_max_man = math.floor(est_max / 10000)
    price_range_str = f"{est_min_man}万円" if est_min_man == est_max_man else f"{est_min_man}万円 〜 {est_max_man}万円"

    return est_min, est_max, price_range_str, " / ".join(points)

# ==========================================
# スクレイピングとデータ処理機能
# ==========================================

def scrape_current_auction_horses() -> pd.DataFrame:
    """今回のオークション出走馬をスクレイピング"""
    logger.info("今回のオークション出走馬をスクレイピング開始...")
    
    try:
        # スクレイパーの初期化
        config = ScraperConfig()
        scraper = ImprovedRakutenScraper(config)
        
        # 馬一覧をスクレイピング
        horse_list = scraper.scrape_horse_list(use_cache=True)
        logger.info(f"取得した馬リスト: {len(horse_list)}頭")
        
        if not horse_list:
            logger.warning("馬リストが空です")
            return pd.DataFrame()
        
        # スクレイピングデータを予測用DataFrameに変換
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

def format_hot_horses_for_twitter(hot_list: List[Dict[str, Any]]) -> str:
    """X（Twitter）投稿用のテキストを生成"""
    if not hot_list:
        return "今回のオークション出品馬はありません。"
    
    today = datetime.now().strftime('%Y/%m/%d')
    text = f"🌟楽天サラブレッドオークション注目馬リスト（{today}）\n\n"
    
    for i, horse in enumerate(hot_list, 1):
        text += f"{i}. {horse['馬名']}（{horse['性別']}{horse['年齢']}歳）\n"
        text += f"   父: {horse['父']} | 予想: {horse['予想価格レンジ']}\n"
        
        # 査定ポイントから主要な要因を抽出
        points = horse['査定ポイント'].split(' / ')[:3]  # 上位3つまで
        if points:
            text += f"   要因: {' / '.join(points)}\n"
        text += "\n"
    
    text += f"#楽天サラブレッドオークション #競馬 #競走馬"
    
    return text

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
    
    # X投稿用テキストを保存
    twitter_file = output_path / f'twitter_text_{timestamp}.txt'
    twitter_text = format_hot_horses_for_twitter(hot_list)
    with open(twitter_file, 'w', encoding='utf-8') as f:
        f.write(twitter_text)
    logger.info(f"X投稿用テキストを保存: {twitter_file}")
    
    return {
        'csv_file': str(csv_file),
        'json_file': str(json_file),
        'hot_file': str(hot_file),
        'twitter_file': str(twitter_file)
    }

# ==========================================
# メイン実行部
# ==========================================

def main():
    """メイン処理"""
    logger.info("=== 楽天サラブレッドオークション価格予測ツール起動 ===")
    
    try:
        # 1. 過去データを読み込み
        historical_df = load_historical_data()
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
