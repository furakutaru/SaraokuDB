import re
import json
import logging
import requests
from datetime import datetime
from pathlib import Path
from urllib.parse import unquote

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('auction_scraper.log')
    ]
)
logger = logging.getLogger(__name__)

class AuctionScraper:
    def __init__(self, base_url="https://auction.keiba.rakuten.co.jp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        })

    def fetch_page(self):
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            return response.text
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return None

    def extract_horse_data(self, html_content):
        """Extract horse data from the embedded JavaScript in the page."""
        try:
            # Look for the JavaScript data structure containing horse information
            pattern = r'umaList:\[(.*?)\]}'
            matches = re.search(pattern, html_content, re.DOTALL)
            
            if not matches:
                logger.warning("Could not find horse data in the page")
                return []
            
            # The actual data is in a JavaScript object, we'll need to parse it carefully
            # First, find the entire window.__NUXT__ object
            nuxt_pattern = r'window\.__NUXT__=(.*?);</script>'
            nuxt_match = re.search(nuxt_pattern, html_content, re.DOTALL)
            
            if not nuxt_match:
                logger.warning("Could not find NUXT data in the page")
                return []
            
            # The data we want is in the state.auction object
            auction_pattern = r'state:\s*{\s*auction:\s*({.*?})\s*},'
            auction_match = re.search(auction_pattern, nuxt_match.group(1), re.DOTALL)
            
            if not auction_match:
                logger.warning("Could not find auction data in NUXT state")
                return []
            
            # Try to parse the auction data as JSON
            try:
                # Clean up the JSON string
                json_str = auction_match.group(1)
                # Fix common JSON issues
                json_str = json_str.replace("'", '"')
                json_str = re.sub(r'(\w+):', r'"\1":', json_str)  # Add quotes around keys
                json_str = json_str.replace('\n', ' ').replace('\r', '')
                
                # Try to parse the JSON
                auction_data = json.loads('{' + json_str + '}')
                
                # Extract horses from the data structure
                horses = []
                for group in auction_data.get('umaList', []):
                    for item in group.get('list', []):
                        horse = {
                            'name': item.get('topItemName', ''),
                            'seller': item.get('offererName', ''),
                            'jbis_url': item.get('basicInfoUrl', '').replace('\\', ''),
                            'price': item.get('price', '').replace('\\', ''),
                            'sex': self._convert_sex(item.get('sex', '')),
                            'age': item.get('age', ''),
                            'image_url': item.get('image', '').replace('\\', '')
                        }
                        horses.append(horse)
                
                return horses
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {e}")
                return []
                
        except Exception as e:
            logger.error(f"Error extracting horse data: {e}")
            return []

    def _convert_sex(self, sex_code):
        """Convert sex code to Japanese text."""
        sex_map = {
            'c': '牡',
            'f': '牝',
            'd': '騸',
            'b': '牡',
            'q': '牝',
            'z': '牝'
        }
        return sex_map.get(sex_code.lower(), sex_code)

    def save_to_json(self, data, filename_prefix='auction_data'):
        """Save the extracted data to a JSON file."""
        try:
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"{filename_prefix}_{timestamp}.json"
            
            with open(filename, 'w', encoding='utf-8') as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
                
            logger.info(f"Data saved to {filename}")
            return filename
            
        except Exception as e:
            logger.error(f"Failed to save data to JSON: {e}")
            return None

def main():
    logger.info("Starting auction scraper...")
    
    scraper = AuctionScraper()
    
    # Fetch the auction page
    logger.info("Fetching auction page...")
    html_content = scraper.fetch_page()
    
    if not html_content:
        logger.error("Failed to fetch the auction page")
        return
    
    # Extract horse data
    logger.info("Extracting horse data...")
    horses = scraper.extract_horse_data(html_content)
    
    if not horses:
        logger.warning("No horse data found on the page")
        return
    
    logger.info(f"Extracted data for {len(horses)} horses")
    
    # Print the extracted data
    print(f"\n=== オークション情報 ({len(horses)}頭) ===\n")
    for i, horse in enumerate(horses, 1):
        print(f"【{i}頭目】")
        print(f"名前: {horse['name']}")
        print(f"性別: {horse['sex']}")
        print(f"年齢: {horse['age']}")
        print(f"売主: {horse['seller']}")
        print(f"価格: {horse['price']}")
        print(f"JBIS: {horse['jbis_url']}")
        print()
    
    # Save to JSON file
    output_file = scraper.save_to_json(horses)
    if output_file:
        print(f"\nデータを {output_file} に保存しました")

if __name__ == "__main__":
    main()
