import json
import os
from datetime import datetime
from pathlib import Path
from uuid import uuid4

def update_horse_fields(input_file, output_file=None):
    """
    Update field names in the processed_horses_updated.json to match horses_history.json format
    """
    # If output_file is not provided, overwrite the input file
    if output_file is None:
        output_file = input_file
    
    # Read the input file
    with open(input_file, 'r', encoding='utf-8') as f:
        data = json.load(f)
    
    # Process each horse
    updated_horses = []
    for horse in data:
        # Create a new horse dictionary with updated fields
        updated_horse = {}
        
        # 1. Add required fields with default values if missing
        updated_horse['id'] = str(uuid4())  # Generate new UUID
        updated_horse['created_at'] = datetime.now().isoformat()
        updated_horse['updated_at'] = datetime.now().isoformat()
        updated_horse['history'] = []  # Initialize empty history array
        
        # 2. Copy all existing fields
        for key, value in horse.items():
            # Skip fields we want to remove
            if key in ['auction_prize', 'current_prize', 'data_source', 'extracted_at', 'source_file']:
                continue
                
            # Rename image_url to primary_image
            if key == 'image_url':
                updated_horse['primary_image'] = value
            # Ensure disease_tags has a default value of 'なし' if empty
            elif key == 'disease_tags' and (value is None or value == ''):
                updated_horse[key] = 'なし'
            # Keep all other fields as is
            else:
                updated_horse[key] = value
        
        # Move jbis_links to history if it exists
        if 'jbis_links' in horse and horse['jbis_links']:
            history_entry = {
                'jbis_links': horse['jbis_links'],
                'updated_at': datetime.now().isoformat()
            }
            updated_horse['history'].append(history_entry)
        
        updated_horses.append(updated_horse)
    
    # Write the updated data to the output file
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(updated_horses, f, ensure_ascii=False, indent=2)
    
    print(f"Successfully updated {len(updated_horses)} horses in {output_file}")

if __name__ == "__main__":
    input_file = "/Users/yum.ishii/SaraokuDB/cache/20250818/processed_horses_updated.json"
    output_file = "/Users/yum.ishii/SaraokuDB/cache/20250818/processed_horses_final.json"
    
    # Make a backup of the original file
    import shutil
    backup_file = input_file.replace('.json', '.json.bak')
    shutil.copy2(input_file, backup_file)
    print(f"Created backup at {backup_file}")
    
    # Update the fields
    update_horse_fields(input_file, output_file)
    
    print(f"\nProcessing complete. Updated data saved to {output_file}")
    print("Please review the changes before using the updated file.")
