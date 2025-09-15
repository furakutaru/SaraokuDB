import os
import sys
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

import uvicorn
from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks, status
from fastapi.responses import JSONResponse
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, inspect, text
from typing import List, Optional, Union, Dict, Any
from datetime import datetime
import os
import sys
import json
import traceback
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent
if str(project_root) not in sys.path:
    sys.path.insert(0, str(project_root))

# Import services and models
from database.models import Base, engine, get_db, Horse
from services.horse_service import HorseService

# Initialize services
horse_service = HorseService()
from scheduler.auction_scheduler import scheduler
from pydantic import BaseModel
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session
from typing import Optional, List, Dict, Any

app = FastAPI(
    title="サラブレッドオークション データベース",
    version="1.0.0",
    docs_url="/docs",
    redoc_url=None
)

# データベース接続を確認する関数
def check_db_connection():
    try:
        with engine.connect() as conn:
            conn.execute(text("SELECT 1"))
        return True
    except Exception as e:
        print(f"データベース接続エラー: {str(e)}")
        return False

# アプリケーション起動時にデータベース接続を確認
@app.on_event("startup")
async def startup_event():
    print("\n=== アプリケーション起動中 ===")
    if not check_db_connection():
        print("警告: データベースに接続できません。テーブルが存在しないか、データベースファイルが存在しません。")
        try:
            # テーブルが存在しない場合は作成を試みる
            Base.metadata.create_all(bind=engine)
            print("テーブルを作成しました。")
        except Exception as e:
            print(f"テーブル作成中にエラーが発生しました: {str(e)}")

    # スケジューラーを開始
    try:
        if not scheduler.running:
            scheduler.start()
            print("スケジューラーを開始しました。")
    except Exception as e:
        print(f"スケジューラーの開始中にエラーが発生しました: {str(e)}")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydanticモデル
class RaceRecordSummary(BaseModel):
    status: Optional[str] = None  # 'active', 'unraced', or 'broodmare'
    races: Optional[int] = None
    wins: Optional[int] = None
    first: Optional[int] = None
    second: Optional[int] = None
    third: Optional[int] = None
    other: Optional[int] = None
    summary: Optional[str] = None  # For backward compatibility

class HorseResponse(BaseModel):
    id: int
    auction_id: Optional[str] = None  # オークションサイトの数値ID
    name: str
    sex: Optional[List[str]] = None
    age: Optional[List[Union[int, str]]] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    race_record: Optional[Union[RaceRecordSummary, str]] = None
    weight: Optional[int] = None
    total_prize_start: Optional[float] = None
    total_prize_latest: Optional[float] = None
    sold_price: Optional[List[Union[int, str]]] = None
    auction_date: Optional[List[str]] = None
    seller: Optional[List[str]] = None
    disease_tags: Optional[str] = None
    comment: Optional[List[str]] = None
    image_url: Optional[str] = None
    unsold_count: Optional[int] = None  # 主取り回数
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
        json_encoders = {
            'dict': lambda v: v  # Handle dictionary serialization
        }

class HorseCreate(BaseModel):
    name: str
    auction_id: Optional[str] = None  # オークションサイトの数値ID
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    race_record: Optional[Union[RaceRecordSummary, str]] = None
    weight: Optional[int] = None
    total_prize_start: Optional[float] = None
    total_prize_latest: Optional[float] = None
    sold_price: Optional[int] = None
    auction_date: Optional[str] = None
    seller: Optional[str] = None
    disease_tags: Optional[str] = None
    comment: Optional[str] = None
    image_url: Optional[str] = None

class HorseUpdate(BaseModel):
    total_prize_latest: Optional[float] = None
    jbis_url: Optional[str] = None

class StatisticsResponse(BaseModel):
    total_horses: int
    average_price: int
    average_growth_rate: float
    horses_with_growth_data: int

# サービスインスタンス（必要に応じて後で追加）

@app.get("/")
async def root():
    return {"message": "サラブレッドオークション データベース API"}

@app.get("/horses/")
async def get_horses(
    skip: int = 0,
    limit: int = 100,
    auction_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """
    馬の一覧を取得するエンドポイント
    """
    print("\n=== /horses/ エンドポイントが呼び出されました ===")
    print(f"パラメータ: skip={skip}, limit={limit}, auction_date={auction_date}")
    
    try:
        # データベース接続を確認
        if not check_db_connection():
            return JSONResponse(
                status_code=500,
                content={
                    "status": "error",
                    "message": "データベースに接続できません"
                }
            )
        
        # クエリの構築
        query = db.query(Horse)
        
        # オークション日でフィルタリング
        if auction_date:
            query = query.filter(Horse.auction_date.contains(f'"{auction_date}"'))
        
        # ページネーションを適用
        total_count = query.count()
        horses = query.offset(skip).limit(limit).all()
        
        # 結果をシリアライズ
        result = []
        for horse in horses:
            horse_dict = {}
            for column in Horse.__table__.columns.keys():
                value = getattr(horse, column, None)
                
                # 日付フィールドの処理
                if column in ['created_at', 'updated_at', 'auction_date'] and value is not None:
                    if hasattr(value, 'isoformat'):
                        value = value.isoformat()
                    elif isinstance(value, str):
                        try:
                            # ISO形式の日付文字列をそのまま使用
                            if 'T' in value and '-' in value and ':' in value:
                                pass
                            else:
                                # 不正な形式の場合はNoneに設定
                                value = None
                        except Exception:
                            value = None
                
                # JSON文字列をデコード
                if column in ['sex', 'age', 'sold_price', 'auction_date', 'seller', 'comment', 'disease_tags'] and value is not None:
                    try:
                        # 主取り（unsold）フラグを取得
                        unsold_count = getattr(horse, 'unsold_count', 0)
                        is_unsold = unsold_count > 0 or getattr(horse, 'unsold', False) or getattr(horse, 'is_unsold', False)
                        
                        # sold_priceが配列の場合は最初の要素を取得
                        if column == 'sold_price' and isinstance(value, str) and value.startswith('[') and value.endswith(']'):
                            try:
                                parsed = json.loads(value)
                                if isinstance(parsed, list) and len(parsed) > 0:
                                    value = parsed[0]
                                else:
                                    value = None
                            except json.JSONDecodeError:
                                value = None
                        
                        if isinstance(value, str):
                            # 既にJSON形式の文字列かどうかをチェック
                            if (value.startswith('[') and value.endswith(']')) or (value.startswith('{') and value.endswith('}')):
                                parsed_value = json.loads(value)
                                # sold_priceの特別な処理
                                if column == 'sold_price':
                                    if is_unsold:
                                        # 主取りの場合は常にNoneを返す
                                        value = None
                                    elif isinstance(parsed_value, list):
                                        # 空の配列または[0]の場合は未落札とみなす
                                        if not parsed_value or parsed_value == [0] or parsed_value == ['0']:
                                            value = None
                                        else:
                                            # 数値に変換可能な最初の要素を取得
                                            for item in parsed_value:
                                                try:
                                                    price = int(item) if item is not None else 0
                                                    value = price if price > 0 else None
                                                    break
                                                except (ValueError, TypeError):
                                                    continue
                                            else:
                                                value = None
                                    else:
                                        # 単一の値の場合はそのまま使用
                                        try:
                                            value = int(parsed_value) if parsed_value and parsed_value != '0' else None
                                        except (ValueError, TypeError):
                                            value = None
                                else:
                                    # 配列で1要素の場合はその要素を返す
                                    if isinstance(parsed_value, list) and len(parsed_value) == 1:
                                        value = parsed_value[0] if parsed_value[0] is not None else None
                                    else:
                                        value = parsed_value
                            else:
                                # 単一の値の場合はそのまま使用
                                if column == 'sold_price':
                                    if is_unsold:
                                        value = None  # 主取りの場合は常にNone
                                    else:
                                        try:
                                            value = int(value) if value and value != '0' else None
                                        except (ValueError, TypeError):
                                            value = None
                        elif column == 'sold_price' and value is not None:
                            # 主取りの場合は常にNoneを返す
                            if is_unsold:
                                value = None
                            # 既にリストでない場合はそのまま使用
                            elif isinstance(value, list):
                                if not value or value == [0] or value == ['0']:
                                    value = None
                                else:
                                    # 数値に変換可能な最初の要素を取得
                                    for item in value:
                                        try:
                                            price = int(item) if item is not None else 0
                                            value = price if price > 0 else None
                                            break
                                        except (ValueError, TypeError):
                                            continue
                                    else:
                                        value = None
                            else:
                                try:
                                    value = int(value) if value != 0 and value != '0' else None
                                except (ValueError, TypeError):
                                    value = None
                    except (json.JSONDecodeError, TypeError) as e:
                        # パースに失敗した場合は未落札とみなす
                        if column == 'sold_price':
                            value = None
                        print(f"JSONデコードエラー (カラム: {column}): {str(e)}")
                
                # 日付型を文字列に変換
                if column in ['created_at', 'updated_at', 'auction_date'] and value is not None:
                    try:
                        if hasattr(value, 'isoformat'):
                            value = value.isoformat()
                        elif isinstance(value, str):
                            # ISO形式の日付文字列をそのまま使用
                            if 'T' in value and '-' in value and ':' in value:
                                # 既にISO形式の場合はそのまま使用
                                pass
                            else:
                                try:
                                    # 日付文字列をパースしてからフォーマット
                                    from datetime import datetime
                                    dt = datetime.fromisoformat(value.replace('Z', '+00:00'))
                                    value = dt.isoformat()
                                except (ValueError, AttributeError):
                                    # パースできない場合はNoneに設定
                                    value = None
                        # リストの場合は各要素を処理
                        elif isinstance(value, list):
                            formatted_dates = []
                            for date_val in value:
                                if hasattr(date_val, 'isoformat'):
                                    formatted_dates.append(date_val.isoformat())
                                elif isinstance(date_val, str):
                                    try:
                                        dt = datetime.fromisoformat(date_val.replace('Z', '+00:00'))
                                        formatted_dates.append(dt.isoformat())
                                    except (ValueError, AttributeError):
                                        formatted_dates.append(None)
                            value = formatted_dates
                    except Exception as e:
                        print(f"日付変換エラー (カラム: {column}): {str(e)}")
                        value = None
                
                horse_dict[column] = value
            
            result.append(horse_dict)
        
        return {
            "status": "success",
            "data": result,
            "pagination": {
                "total": total_count,
                "skip": skip,
                "limit": limit
            }
        }
        
    except Exception as e:
        print(f"エラーが発生しました: {str(e)}")
        print(traceback.format_exc())
        
        return JSONResponse(
            status_code=500,
            content={
                "status": "error",
                "message": "馬データの取得中にエラーが発生しました",
                "error": str(e)
            }
        )

@app.get("/horses/auction/{auction_id}", response_model=HorseResponse)
async def get_horse_by_auction_id(auction_id: str, db: Session = Depends(get_db)):
    """オークションIDで馬データを取得
    
    Args:
        auction_id: オークションサイトの数値ID
        db: データベースセッション
        
    Returns:
        HorseResponse: 馬データ
        
    Raises:
        HTTPException: 馬が見つからない場合
    """
    horse = horse_service.get_horse_by_auction_id(db, auction_id)
    if not horse:
        raise HTTPException(status_code=404, detail=f"Auction ID {auction_id} の馬が見つかりません")
    
    # レスポンスモデルに合わせてデータを整形
    return horse

@app.get("/horses/{horse_id}", response_model=HorseResponse)
async def get_horse(horse_id: int, db: Session = Depends(get_db)):
    """特定の馬データを取得（履歴カラムは配列で返す）"""
    horse = horse_service.get_horse_by_id(db, horse_id)
    if not horse:
        raise HTTPException(status_code=404, detail="馬が見つかりません")
    
    def parse_race_record(record):
        if not record:
            return None
        try:
            if isinstance(record, str):
                # 文字列の場合はJSONとしてパースを試みる
                try:
                    record = json.loads(record)
                except json.JSONDecodeError:
                    # JSONとしてパースできない場合はそのまま返す
                    return record
            
            # 辞書型の場合はRaceRecordSummaryに変換
            if isinstance(record, dict):
                return RaceRecordSummary(**record)
            return record
        except Exception as e:
            print(f"Error parsing race record: {e}")
            return record
    
    # 通常のJSONフィールドをパース
    for field in ['sex', 'age', 'sold_price', 'auction_date', 'seller', 'comment']:
        if field in horse and horse[field] and isinstance(horse[field], str):
            try:
                horse[field] = json.loads(horse[field])
            except json.JSONDecodeError:
                pass
    
    # レースレコードを処理
    if 'race_record' in horse:
        horse['race_record'] = parse_race_record(horse['race_record'])
    
    return horse

@app.post("/horses/", response_model=HorseResponse)
async def create_horse(horse_data: HorseCreate, db: Session = Depends(get_db)):
    """新しい馬データを作成"""
    try:
        print(f"[DEBUG] 受信データ: {horse_data}")
        
        # Pydanticモデルを辞書に変換
        horse_dict = horse_data.dict()
        print(f"[DEBUG] 変換後データ: {horse_dict}")
        
        # レースレコードがRaceRecordSummary型の場合は辞書に変換
        if isinstance(horse_dict.get('race_record'), RaceRecordSummary):
            horse_dict['race_record'] = horse_dict['race_record'].dict()
        
        print(f"[DEBUG] サービスに渡すデータ: {horse_dict}")
        horse = horse_service.create_horse(db, horse_dict)
        print(f"[DEBUG] 保存された馬データ: {horse}")
        return horse
        
    except Exception as e:
        import traceback
        error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        print(f"[ERROR] {error_msg}")
        raise HTTPException(status_code=500, detail=error_msg)

@app.put("/horses/{horse_id}", response_model=HorseResponse)
async def update_horse(
    horse_id: int,
    horse_data: HorseCreate,
    db: Session = Depends(get_db)
):
    """馬データを更新"""
    # Pydanticモデルを辞書に変換
    horse_dict = horse_data.dict()
    
    # レースレコードがRaceRecordSummary型の場合は辞書に変換
    if isinstance(horse_dict.get('race_record'), RaceRecordSummary):
        horse_dict['race_record'] = horse_dict['race_record'].dict()
    
    updated_horse = horse_service.update_horse(db, horse_id, horse_dict)
    if not updated_horse:
        raise HTTPException(status_code=404, detail="馬が見つかりません")
    
    # 更新後のデータを取得して返す
    return await get_horse(horse_id, db)

@app.post("/scrape/")
async def scrape_horses(
    background_tasks: BackgroundTasks,
    auction_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """スクレイピングを実行"""
    try:
        horses = horse_service.scrape_and_save_horses(db, auction_date=auction_date)
        return {
            "message": f"{len(horses)}頭の馬データを取得・保存しました",
            "count": len(horses)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"スクレイピングに失敗: {str(e)}")

@app.post("/update-prize-money/")
async def update_prize_money(db: Session = Depends(get_db)):
    """全馬の賞金情報を更新"""
    try:
        updated_count = horse_service.update_all_prize_money(db)
        return {
            "message": f"{updated_count}頭の馬の賞金情報を更新しました",
            "updated_count": updated_count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"賞金更新に失敗: {str(e)}")

@app.get("/statistics/", response_model=StatisticsResponse)
async def get_statistics(db: Session = Depends(get_db)):
    """統計情報を取得"""
    return horse_service.get_statistics(db)

@app.get("/auction-dates/")
async def get_auction_dates(db: Session = Depends(get_db)):
    """開催日の一覧を取得"""
    dates = db.query(Horse.auction_date).distinct().all()
    return [date[0] for date in dates if date[0]]

@app.post("/scheduler/start")
async def start_scheduler():
    """スケジューラーを開始"""
    scheduler.start()
    return {"message": "スケジューラーを開始しました"}

@app.post("/scheduler/stop")
async def stop_scheduler():
    """スケジューラーを停止"""
    scheduler.stop()
    return {"message": "スケジューラーを停止しました"}

@app.get("/scheduler/status")
async def get_scheduler_status():
    """スケジューラーの状態を取得"""
    return scheduler.get_status()

@app.on_event("startup")
async def startup_event():
    """アプリケーション起動時にスケジューラーを開始"""
    scheduler.start()

@app.on_event("shutdown")
async def shutdown_event():
    """アプリケーション終了時にスケジューラーを停止"""
    scheduler.stop()

@app.get("/api/test/horses", response_model=dict)
async def get_horses_data():
    """
    テスト用の馬データをJSONファイルから取得するエンドポイント
    """
    try:
        # ファイルパスを絶対パスに変更
        file_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "static-frontend", "public", "data", "horses_history.json"
        )
        
        print(f"\n=== ファイル読み込み開始 ===")
        print(f"ファイルパス: {file_path}")
        
        if not os.path.exists(file_path):
            error_msg = f"ファイルが見つかりません: {file_path}"
            print(error_msg)
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=error_msg
            )
        
        # ファイルサイズを確認
        file_size = os.path.getsize(file_path)
        print(f"ファイルサイズ: {file_size / 1024 / 1024:.2f} MB")
            
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        print("\n=== データ構造の確認 ===")
        print(f"データの型: {type(data)}")
        
        # 常にhorsesキーを持つ辞書を返す
        response_data = {
            "horses": [],
            "metadata": {}
        }
        
        # データの構造を確認して適切な形式で返す
        if isinstance(data, dict):
            print(f"辞書型のキー: {list(data.keys())}")
            if 'horses' in data and isinstance(data['horses'], list):
                print(f"'horses'キーを発見。馬の数: {len(data['horses'])}")
                response_data['horses'] = data['horses']
                if 'metadata' in data:
                    response_data['metadata'] = data['metadata']
                if len(data['horses']) > 0:
                    print(f"最初の馬のデータ: {json.dumps(data['horses'][0], ensure_ascii=False, indent=2)[:200]}...")
            else:
                print("'horses'キーが存在しないか、配列ではありません")
                response_data['horses'] = [data]  # 単一の馬データを配列でラップ
        elif isinstance(data, list):
            print(f"配列型のデータを検出。要素数: {len(data)}")
            response_data['horses'] = data
            if len(data) > 0:
                print(f"最初の要素の型: {type(data[0])}")
                print(f"最初の要素: {json.dumps(data[0], ensure_ascii=False, indent=2)[:200]}...")
        else:
            error_msg = f"無効なデータ形式です。辞書または配列が必要です。受信したデータの型: {type(data)}"
            print(error_msg)
            raise ValueError(error_msg)
        
        print(f"\n=== レスポンスデータの形式 ===")
        print(f"返却するデータのキー: {list(response_data.keys())}")
        print(f"馬の数: {len(response_data['horses'])}")
        
        return response_data
            
    except json.JSONDecodeError as e:
        error_msg = f"JSONの解析に失敗しました: {str(e)}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=error_msg
        )
    except Exception as e:
        import traceback
        error_msg = f"エラーが発生しました: {str(e)}\n{traceback.format_exc()}"
        print(error_msg)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Error reading data file: {str(e)}"
        )

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)