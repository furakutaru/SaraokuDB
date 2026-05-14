# -*- coding: utf-8 -*-
"""
落札価格予測（scripts/README_prediction.md の変更禁止コアと同一式）。

DB 由来の学習 DataFrame 生成と、当日モード用の馬→予測行マッピングのみ追加。
"""
from __future__ import annotations

import json
import logging
import math
import time
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd
from sqlalchemy import func
from sqlalchemy.orm import Session

from database.models import AuctionHistory, Horse
from services.auction_session import extract_latest_history_value

logger = logging.getLogger(__name__)

# ==========================================
# 定数（CONST）定義 - 予測ロジックのコア部分（変更禁止）
# ==========================================
WEIGHT_MODIFIERS = {
    "超軽量": -0.15,
    "軽量_牡セ": -0.05,
    "軽量_牝": 0.0,
    "普通": 0.0,
    "大型": 0.05,
    "超大型": 0.10,
}

DISEASE_CATEGORIES = {
    "致命的": ["屈腱炎", "繋靭帯炎", "腱損傷", "じん帯損傷", "腰フラ", "蹄葉炎", "神経麻痺", "腸捻転"],
    "重度_治療可": ["骨折", "ボーンシスト", "ウォブラー症候群", "OCD", "離断性骨軟骨炎"],
    "中程度": [
        "骨膜炎",
        "フレグモーネ",
        "骨片",
        "関節炎",
        "膝関節炎",
        "球節炎",
        "飛節炎",
        "前膝腱炎",
        "腱鞘炎",
        "跛行",
        "跛る",
        "肉離れ",
        "横紋筋融解症",
        "鶏跛",
        "喉鳴り",
        "軟口蓋の癒着",
        "喉頭蓋エントラップメント",
        "喉頭蓋炎",
        "鼻出血",
        "肺出血",
        "喘鳴症",
        "DDSP",
        "軟口蓋背側変位",
        "疝痛",
        "鼓腸症",
        "大腸炎",
        "裂蹄",
        "蹄中隔炎",
        "蹄の亀裂",
        "蹄内出血",
        "繋皸",
        "けいくん",
        "角膜炎",
    ],
    "軽微": [
        "蟻洞",
        "骨瘤",
        "骨膜肥厚",
        "エクイロックス",
        "脚部不安",
        "脚元不安",
        "こり症",
        "筋肉痛",
        "筋肉炎",
        "コズミ",
        "挫跖",
        "ざせき",
        "旋回癖",
        "旋回症",
        "さく癖",
        "ゆう癖",
        "カケス",
        "気管支炎",
        "呼吸器不安",
        "上気道炎",
        "胃潰瘍",
        "下痢",
        "食欲不振",
        "風気疝",
        "ガス腹",
        "ロタウイルス感染症",
        "馬インフルエンザ",
        "皮膚糸状菌症",
        "感冒",
        "蹄不安",
        "蹄傷",
        "蹄底負傷",
        "蹄球損傷",
        "打撲",
        "擦過傷",
        "裂傷",
        "腫脹",
        "炎症",
        "創傷",
        "皮膚炎",
        "疥癬",
        "蕁麻疹",
        "結膜炎",
    ],
}

DISEASE_PENALTIES = {"致命的": -0.60, "重度_治療可": -0.30, "中程度": -0.20, "軽微": -0.10}

# ==========================================
# 予測ロジック関数（変更禁止）
# ==========================================


def analyze_sires(df):
    """種牡馬の固有プレミアムを計算（過去データから）"""

    def get_rough_base(row):
        age = row.get("年齢", 4) if pd.notna(row.get("年齢")) else 4
        prize = row.get("落札時賞金", 0) if pd.notna(row.get("落札時賞金")) else 0
        sex = str(row.get("性別", "牡"))
        if age <= 3:
            if prize == 0 and sex in ["牝", "セ"]:
                base = 600000
            else:
                base = 800000
        else:
            prize_mult = 0.03
            if age >= 8:
                prize_mult = 0.015
            elif age >= 6:
                prize_mult = 0.02
            base = 500000 + (prize * prize_mult)
        if age >= 5:
            base *= 1.0 - min(0.50, (age - 4) * 0.10)
        return base

    if df is None or df.empty or "落札価格" not in df.columns:
        return {}
    df_calc = df[df["落札価格"] > 0].copy()
    if df_calc.empty:
        return {}
    df_calc["base_est"] = df_calc.apply(get_rough_base, axis=1)
    df_calc["prem_rate"] = (df_calc["落札価格"] / df_calc["base_est"]) - 1.0
    stats = df_calc.groupby("父")["prem_rate"].agg(["median", "count"])

    sire_multiplier = {}
    for sire, row in stats.iterrows():
        if row["count"] >= 3:
            sire_multiplier[sire] = max(-0.40, min(0.60, row["median"]))
        else:
            sire_multiplier[sire] = 0.0
    return sire_multiplier


def extract_disease_severity(text):
    """病歴テキストから疾患の重症度を抽出（変更禁止）"""
    if not isinstance(text, str) or not text.strip():
        return [], []
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
    age = row.get("年齢", 4) if not pd.isna(row.get("年齢")) else 4
    sex = str(row.get("性別", "牡"))
    sire = str(row.get("父", ""))
    weight = row.get("馬体重", 450) if not pd.isna(row.get("馬体重")) else 450
    prize_money = row.get("落札時賞金", 0) if not pd.isna(row.get("落札時賞金")) else 0
    disease_text = str(row.get("病歴", "")) if not pd.isna(row.get("病歴")) else ""
    is_broodmare = row.get("繁殖") == "○"

    auction_month = None
    if "オークション日" in row and pd.notna(row["オークション日"]):
        try:
            auction_month = pd.to_datetime(row["オークション日"]).month
        except Exception:
            pass

    severities, found_diseases = extract_disease_severity(disease_text)
    if found_diseases:
        points.append(f"検出疾病: {', '.join(found_diseases)}")

    if age <= 3:
        if prize_money == 0 and sex in ["牝", "セ"]:
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
        points.append(f"種牡馬({sire})適正プレミアム(+{int(sire_prem * 100)}%)")
    elif sire_prem < 0:
        positive_mod += sire_prem
        points.append(f"種牡馬({sire})ディスカウント({int(sire_prem * 100)}%)")

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

    if sex == "セ" and age >= 6 and prize_money < 30000000:
        positive_mod -= 0.10
        points.append("セン馬・高齢による繁殖無価値化(-10%)")

    disease_mod = 0.0
    if "致命的" in severities:
        disease_mod = DISEASE_PENALTIES["致命的"]
    elif "重度_治療可" in severities:
        disease_mod = DISEASE_PENALTIES["重度_治療可"]
    elif "中程度" in severities:
        disease_mod = DISEASE_PENALTIES["中程度"]
    elif "軽微" in severities:
        disease_mod = DISEASE_PENALTIES["軽微"]

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

    if age >= 5:
        age_penalty = min(0.80, (age - 4) * 0.10)
        est_min *= 1.0 - age_penalty
        est_max *= 1.0 - age_penalty
        points.append(f"年齢減価(-{int(age_penalty * 100)}%)")

    if sex == "牝" and is_broodmare:
        est_min = max(est_min, 200000)
        est_max = max(est_max, 500000)
        if "繁殖牝馬最低保障" not in points:
            points.append("繁殖牝馬最低保障")
    elif sex in ["牡", "セ"]:
        est_min = max(est_min, 100000)
        est_max = max(est_max, 100000)

    est_min_man = math.floor(est_min / 10000)
    est_max_man = math.floor(est_max / 10000)
    price_range_str = f"{est_min_man}万円" if est_min_man == est_max_man else f"{est_min_man}万円 〜 {est_max_man}万円"

    return est_min, est_max, price_range_str, " / ".join(points)


# ==========================================
# DB / 当日モード用ヘルパー
# ==========================================

_sire_cache: Dict[str, Any] = {"t": 0.0, "key": None, "ranks": None}
SIRE_CACHE_TTL = 300.0


def total_prize_start_to_yen(total_prize_start: Any) -> int:
    """total_prize_start（通常は万円）を予測ロジック用の円に変換。"""
    if total_prize_start is None:
        return 0
    try:
        v = float(total_prize_start)
    except (TypeError, ValueError):
        return 0
    if v > 100_000:
        return int(v)
    return int(round(v * 10000))


def disease_text_from_horse(horse: Horse) -> str:
    parts: List[str] = []
    com = extract_latest_history_value(horse.comment)
    if com:
        parts.append(str(com))
    dt = horse.disease_tags
    if not dt:
        return " ".join(parts)
    if isinstance(dt, str):
        stripped = dt.strip()
        if stripped.startswith("["):
            try:
                arr = json.loads(stripped)
                if isinstance(arr, list):
                    parts.append(" ".join(str(x) for x in arr))
                else:
                    parts.append(stripped)
            except json.JSONDecodeError:
                parts.append(stripped)
        else:
            parts.append(stripped)
    else:
        parts.append(str(dt))
    return " ".join(parts)


def coerce_age_for_row(horse: Horse) -> int:
    raw = extract_latest_history_value(horse.age)
    if raw is None:
        return 4
    try:
        return int(float(raw))
    except (TypeError, ValueError):
        return 4


def horse_to_prediction_row(horse: Horse, session_auction_date: str) -> Dict[str, Any]:
    """DB の Horse を estimate_horse_price 用の dict に変換。"""
    sex = str(extract_latest_history_value(horse.sex) or "牡")
    sire = str(horse.sire or "")
    age = coerce_age_for_row(horse)
    w = horse.weight
    try:
        weight = int(w) if w is not None else 450
    except (TypeError, ValueError):
        weight = 450
    prize_yen = total_prize_start_to_yen(horse.total_prize_start)
    disease_text = disease_text_from_horse(horse)
    brood = "○" if horse.is_broodmare else ""
    return {
        "馬名": horse.name or "",
        "性別": sex,
        "年齢": age,
        "父": sire,
        "馬体重": weight,
        "落札時賞金": prize_yen,
        "病歴": disease_text,
        "繁殖": brood,
        "オークション日": session_auction_date,
    }


def load_training_dataframe_from_db(db: Session) -> pd.DataFrame:
    """auction_histories の成約行から学習用 DataFrame を構築。"""
    rows: List[Dict[str, Any]] = []
    q = (
        db.query(AuctionHistory, Horse)
        .join(Horse, Horse.id == AuctionHistory.horse_id)
        .filter(AuctionHistory.price > 0, AuctionHistory.is_unsold.is_(False))
    )
    for ah, horse in q.all():
        try:
            price = int(ah.price)
        except (TypeError, ValueError):
            continue
        if price <= 0:
            continue
        sire = (ah.sire_name or horse.sire or "").strip() or "（父不明）"
        age = coerce_age_for_row(horse)
        sex = str(extract_latest_history_value(horse.sex) or "牡")
        prize_yen = total_prize_start_to_yen(horse.total_prize_start)
        auction_day = str(ah.auction_date)[:10] if ah.auction_date else ""
        rows.append(
            {
                "落札価格": price,
                "父": sire,
                "年齢": age,
                "性別": sex,
                "落札時賞金": prize_yen,
                "オークション日": auction_day,
            }
        )
    return pd.DataFrame(rows)


def get_sire_ranks_cached(db: Session) -> Dict[str, float]:
    """analyze_sires 結果を短 TTL でキャッシュ。"""
    global _sire_cache
    m = db.query(func.max(Horse.updated_at)).scalar()
    key = str(m)
    now = time.time()
    if (
        _sire_cache["ranks"] is not None
        and _sire_cache["key"] == key
        and now - _sire_cache["t"] < SIRE_CACHE_TTL
    ):
        return _sire_cache["ranks"]
    df = load_training_dataframe_from_db(db)
    ranks = analyze_sires(df) if not df.empty else {}
    _sire_cache = {"t": now, "key": key, "ranks": ranks}
    return ranks


def predict_for_horse(horse: Horse, session_auction_date: str, sire_ranks: Dict[str, float]) -> Tuple[int, int, str, str]:
    row = horse_to_prediction_row(horse, session_auction_date)
    est_min, est_max, range_str, valuation = estimate_horse_price(row, sire_ranks)
    return int(est_min), int(est_max), range_str, valuation


def parse_sold_price_latest(horse: Horse) -> Optional[float]:
    v = extract_latest_history_value(horse.sold_price)
    if v is None:
        return None
    if isinstance(v, (int, float)):
        return float(v)
    s = str(v).strip().replace(",", "")
    s = "".join(c for c in s if c.isdigit() or c == ".")
    if not s:
        return None
    try:
        return float(s)
    except ValueError:
        return None
