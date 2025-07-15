import json
from datetime import datetime

INPUT_PATH = "static-frontend/public/horses.json"
OUTPUT_PATH = "static-frontend/public/horses.json.new"

def convert():
    with open(INPUT_PATH, encoding="utf-8") as f:
        data = json.load(f)
    horses = data.get("horses", [])
    new_horses = []
    for idx, horse in enumerate(horses, 1):
        # auction_history
        auction_history = [
            {
                "date": horse.get("auction_date"),
                "price": horse.get("sold_price"),
                "seller": horse.get("seller")
            }
        ]
        # prize_history
        prize_history = []
        if horse.get("total_prize_start") is not None:
            prize_history.append({
                "date": horse.get("auction_date"),
                "total_prize": horse.get("total_prize_start")
            })
        if horse.get("total_prize_latest") is not None and horse.get("total_prize_latest") != horse.get("total_prize_start"):
            prize_history.append({
                "date": horse.get("updated_at"),
                "total_prize": horse.get("total_prize_latest")
            })
        # comment_history
        comment_history = []
        if horse.get("comment"):
            comment_history.append({
                "date": horse.get("updated_at"),
                "comment": horse.get("comment")
            })
        # weight_history
        weight_history = []
        if horse.get("weight"):
            weight_history.append({
                "date": horse.get("updated_at"),
                "weight": horse.get("weight")
            })
        # images
        images = []
        if horse.get("primary_image"):
            images.append(horse["primary_image"])
        # disease_history
        disease_history = []
        if horse.get("disease_tags"):
            disease_history.append({
                "date": horse.get("updated_at"),
                "tags": [tag.strip() for tag in horse["disease_tags"].split(",") if tag.strip()]
            })
        new_horses.append({
            "id": idx,
            "name": horse.get("name"),
            "sex": horse.get("sex"),
            "age": horse.get("age"),
            "auction_history": auction_history,
            "prize_history": prize_history,
            "sire": horse.get("sire"),
            "dam": horse.get("dam"),
            "dam_sire": horse.get("dam_sire"),
            "comment_history": comment_history,
            "weight_history": weight_history,
            "race_record": horse.get("race_record"),
            "images": images,
            "disease_history": disease_history,
            "netkeiba_url": horse.get("netkeiba_url"),
            "created_at": horse.get("created_at"),
            "updated_at": horse.get("updated_at")
        })
    # metadataはそのまま
    new_data = {
        "metadata": data.get("metadata", {}),
        "horses": new_horses
    }
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(new_data, f, ensure_ascii=False, indent=2)
    print(f"変換完了: {OUTPUT_PATH}")

if __name__ == "__main__":
    convert() 