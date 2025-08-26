from dataclasses import dataclass
from enum import Enum
from typing import Optional

class Sex(Enum):
    MALE = "牡"
    FEMALE = "牝"
    GELDING = "セン"

@dataclass
class Horse:
    """馬の基本情報を表すデータクラス"""
    name: str  # 馬名
    sex: Sex  # 性別
    age: int  # 年齢
    sire: str  # 父
    dam: str  # 母
    damsire: str  # 母父
    total_prize: Optional[float] = None  # 総賞金（万円）
    race_record: Optional[str] = None  # 戦績
    comment: Optional[str] = None  # コメント
    
    def to_dict(self) -> dict:
        """辞書形式に変換"""
        return {
            "name": self.name,
            "sex": self.sex.value,
            "age": self.age,
            "sire": self.sire,
            "dam": self.dam,
            "damsire": self.damsire,
            "total_prize": self.total_prize,
            "race_record": self.race_record,
            "comment": self.comment
        }
    
    @classmethod
    def from_dict(cls, data: dict) -> 'Horse':
        """辞書からインスタンスを生成"""
        return cls(
            name=data["name"],
            sex=Sex(data["sex"]),
            age=data["age"],
            sire=data["sire"],
            dam=data["dam"],
            damsire=data["damsire"],
            total_prize=data.get("total_prize"),
            race_record=data.get("race_record"),
            comment=data.get("comment")
        )
