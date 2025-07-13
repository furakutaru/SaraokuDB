from fastapi import FastAPI, Depends, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime

from backend.database.models import get_db, Horse
from backend.services.horse_service import HorseService
from backend.scheduler.auction_scheduler import scheduler
from pydantic import BaseModel

app = FastAPI(title="サラブレッドオークション データベース", version="1.0.0")

# CORS設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Pydanticモデル
class HorseResponse(BaseModel):
    id: int
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    race_record: Optional[str] = None
    weight: Optional[int] = None
    total_prize_start: Optional[float] = None
    total_prize_latest: Optional[float] = None
    sold_price: Optional[int] = None
    auction_date: Optional[str] = None
    seller: Optional[str] = None
    disease_tags: Optional[str] = None
    comment: Optional[str] = None
    netkeiba_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True

class HorseCreate(BaseModel):
    name: str
    sex: Optional[str] = None
    age: Optional[int] = None
    sire: Optional[str] = None
    dam: Optional[str] = None
    dam_sire: Optional[str] = None
    race_record: Optional[str] = None
    weight: Optional[int] = None
    total_prize_start: Optional[float] = None
    total_prize_latest: Optional[float] = None
    sold_price: Optional[int] = None
    auction_date: Optional[str] = None
    seller: Optional[str] = None
    disease_tags: Optional[str] = None
    comment: Optional[str] = None
    netkeiba_url: Optional[str] = None
    image_url: Optional[str] = None

class StatisticsResponse(BaseModel):
    total_horses: int
    average_price: int
    average_growth_rate: float
    horses_with_growth_data: int

# サービスインスタンス
horse_service = HorseService()

@app.get("/")
async def root():
    return {"message": "サラブレッドオークション データベース API"}

@app.get("/horses/", response_model=List[HorseResponse])
async def get_horses(
    skip: int = 0,
    limit: int = 100,
    auction_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """馬データを取得"""
    if auction_date:
        horses = horse_service.get_horses_by_auction_date(db, auction_date)
    else:
        horses = horse_service.get_horses(db, skip=skip, limit=limit)
    return horses

@app.get("/horses/{horse_id}", response_model=HorseResponse)
async def get_horse(horse_id: int, db: Session = Depends(get_db)):
    """特定の馬データを取得"""
    horse = horse_service.get_horse_by_id(db, horse_id)
    if not horse:
        raise HTTPException(status_code=404, detail="馬が見つかりません")
    return horse

@app.post("/horses/", response_model=HorseResponse)
async def create_horse(horse_data: HorseCreate, db: Session = Depends(get_db)):
    """新しい馬データを作成"""
    horse = horse_service.create_horse(db, horse_data.dict())
    return horse

@app.put("/horses/{horse_id}", response_model=HorseResponse)
async def update_horse(
    horse_id: int,
    horse_data: HorseCreate,
    db: Session = Depends(get_db)
):
    """馬データを更新"""
    horse = horse_service.update_horse(db, horse_id, horse_data.dict())
    if not horse:
        raise HTTPException(status_code=404, detail="馬が見つかりません")
    return horse

@app.delete("/horses/{horse_id}")
async def delete_horse(horse_id: int, db: Session = Depends(get_db)):
    """馬データを削除"""
    success = horse_service.delete_horse(db, horse_id)
    if not success:
        raise HTTPException(status_code=404, detail="馬が見つかりません")
    return {"message": "削除されました"}

@app.post("/scrape/")
async def scrape_horses(
    background_tasks: BackgroundTasks,
    auction_date: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """スクレイピングを実行"""
    try:
        horses = horse_service.scrape_and_save_horses(db, auction_date)
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
        updated_count = horse_service.update_prize_money_for_all(db)
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

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000) 