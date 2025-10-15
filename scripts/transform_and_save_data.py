import json
import os
import re
import uuid
from datetime import datetime
from typing import List, Dict, Any, Optional

def extract_seller_from_comment(comment: str) -> str:
    """Extract seller information from comment if available."""
    if not comment:
        return ""
    
    # Common patterns for seller information in comments
    patterns = [
        r'(?P<seller>.*?)[(（]?牧場[)）]?$',  # Ends with '牧場' or '（牧場）'
        r'[（(](?P<seller>.*?牧場)[)）]',  # Inside brackets with '牧場'
        r'[（(](?P<seller>.*?)[)）]',  # Any text inside brackets
    ]
    
    for pattern in patterns:
        match = re.search(pattern, comment)
        if match and 'seller' in match.groupdict():
            seller = match.group('seller').strip()
            if seller and len(seller) < 50:  # Sanity check for seller name length
                return seller
    
    return ""

def transform_horse_data(scraped_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """
    Transform the scraped horse data into the format expected by the frontend.
    
    Args:
        scraped_data: List of dictionaries containing scraped horse data
        
    Returns:
        List of transformed horse data dictionaries
    ""
    horses = []
    
    for horse in scraped_data:
        try:
            # Generate a stable UUID based on horse name and age if ID is not provided
            horse_id = horse.get("id") or str(uuid.uuid5(uuid.NAMESPACE_DNS, f"{horse.get('name', '')}-{horse.get('age', '')}"))
            
            # Extract seller from comment if available
            seller = horse.get("seller", "")
            if not seller and "comment" in horse:
                seller = extract_seller_from_comment(horse["comment"])
            
            # Get prize money, handling various formats
            prize_money = 0.0
            if "prize_money" in horse and isinstance(horse["prize_money"], dict):
                prize_str = str(horse["prize_money"].get("total_prize", "0.0"))
                prize_money = float(prize_str.replace("万円", "").replace(",", ""))
            
            # Create a new horse entry with required fields
            transformed_horse = {
                "id": horse_id,
                "name": horse.get("name", "不明"),
                "sex": horse.get("sex", "不明"),
                "age": int(horse.get("age", 0)) if str(horse.get("age", "0")).isdigit() else 0,
                "sire": horse.get("sire", "不明"),
                "dam": horse.get("dam", "不明"),
                "damsire": horse.get("damsire", "不明"),
                "image_url": horse.get("image_url", ""),
                "jbis_url": horse.get("jbis_url", ""),
                "auction_url": horse.get("detail_url", ""),
                "disease_tags": horse.get("disease_tags", []),
                "created_at": horse.get("created_at", datetime.now().isoformat()),
                "updated_at": datetime.now().isoformat()
            }
            
            # Add auction history
            auction_history = {
                "id": f"{horse_id}_{datetime.now().strftime('%Y%m%d')}",
                "horse_id": horse_id,
                "auction_date": horse.get("auction_date", datetime.now().strftime("%Y-%m-%d")),
                "sold_price": horse.get("sold_price"),
                "total_prize_start": prize_money,
                "total_prize_latest": prize_money,
                "weight": horse.get("weight"),
                "seller": seller,
                "is_unsold": horse.get("is_unsold", False),
                "comment": horse.get("comment", ""),
                "created_at": datetime.now().isoformat()
            }
            
            transformed_horse["auction_history"] = [auction_history]
            horses.append(transformed_horse)
            
        except Exception as e:
            print(f"Error processing horse data: {e}")
            continue
    
    return horses

def load_scraped_data(file_path: str) -> List[Dict[str, Any]]:
    """Load and validate scraped data from JSON file."""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            
        # Handle both list and dict with 'horses' key for backward compatibility
        if isinstance(data, dict) and 'horses' in data:
            return data['horses']
        elif isinstance(data, list):
            return data
        else:
            raise ValueError("Invalid data format: expected list or dict with 'horses' key")
            
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON file: {e}")
        raise
    except Exception as e:
        print(f"Error loading data: {e}")
        raise

def main():
    # Define file paths
    script_dir = os.path.dirname(os.path.abspath(__file__))
    scraped_data_path = os.path.join(script_dir, "../output/scraped_data.json")
    output_dir = os.path.join(script_dir, "../frontend/public/data")
    output_path = os.path.join(output_dir, "horses_history.json")
    
    # Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)
    
    try:
        print(f"Loading data from {scraped_data_path}...")
        scraped_data = load_scraped_data(scraped_data_path)
        
        if not scraped_data:
            raise ValueError("No data found in the scraped data file")
            
        print(f"Found {len(scraped_data)} horses to process")
        
        # Transform data
        print("Transforming data...")
        transformed_data = transform_horse_data(scraped_data)
        
        if not transformed_data:
            raise ValueError("No valid horse data after transformation")
            
        # Save to frontend directory
        print(f"Saving data to {output_path}...")
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(transformed_data, f, ensure_ascii=False, indent=2)
        
        print(f"\nSuccessfully transformed and saved data to {output_path}")
        print(f"Total horses processed: {len(transformed_data)}")
        
        # Print summary
        print("\nData Summary:")
        print(f"- Horses with missing sire: {sum(1 for h in transformed_data if h.get('sire') in [None, '', '不明'])}")
        print(f"- Horses with missing dam: {sum(1 for h in transformed_data if h.get('dam') in [None, '', '不明'])}")
        print(f"- Horses with missing damsire: {sum(1 for h in transformed_data if h.get('damsire') in [None, '', '不明'])}")
        print(f"- Horses with seller info: {sum(1 for h in transformed_data if h.get('auction_history', [{}])[0].get('seller', ''))}")
        
    except Exception as e:
        print(f"\nError: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        sys.exit(1)

if __name__ == "__main__":
    import sys
    main()
