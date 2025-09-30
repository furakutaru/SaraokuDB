import re
import json
import logging
import requests
from datetime import datetime

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

class DirectAuctionScraper:
    def __init__(self, base_url="https://auction.keiba.rakuten.co.jp"):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'ja,en-US;q=0.7,en;q=0.3',
            'Connection': 'keep-alive',
            'Upgrade-Insecure-Requests': '1',
            'Cache-Control': 'max-age=0',
        })

    def fetch_page(self):
        try:
            response = self.session.get(self.base_url, timeout=30)
            response.raise_for_status()
            content = response.text
            # Save the raw HTML for debugging
            with open('auction_page_raw.html', 'w', encoding='utf-8') as f:
                f.write(content)
            logger.info("Saved raw HTML to auction_page_raw.html")
            return content
        except Exception as e:
            logger.error(f"Failed to fetch page: {e}")
            return None

    def _extract_javascript_variables(self, html_content):
        """Extract all JavaScript variables from the HTML content."""
        variables = {}
        
        # Pattern 1: var name = "value";
        var_patterns = [
            r'var\s+(\w+)\s*=\s*["\']([^"\']+)["\']',
            r'var\s+(\w+)\s*=\s*([^;\n]+?)(?=;|\n|$)',
            r'var\s+([a-z])\s*=\s*"([^"]+)"',
            r"var\s+([a-z])\s*=\s*'([^']+)'"
        ]
        
        for pattern in var_patterns:
            for var_name, var_value in re.findall(pattern, html_content):
                var_value = var_value.strip('\'"')
                if var_name and var_value:
                    variables[var_name] = var_value
        
        # Try to extract seller information from JavaScript objects
        seller_patterns = [
            r'var\s+sellers\s*=\s*(\[[^\]]+\])',
            r'var\s+sellerList\s*=\s*(\{[^}]+\})',
            r'var\s+([a-z])\s*=\s*"([^"]+)"',
            r'var\s+([a-z])\s*=\s*\{name:\s*"([^"]+)"'
        ]
        
        for pattern in seller_patterns:
            matches = re.findall(pattern, html_content)
            if matches:
                try:
                    if pattern == seller_patterns[0] or pattern == seller_patterns[1]:
                        for match in matches:
                            try:
                                sellers = json.loads(re.sub(r'\s*\/\*.*?\*\/\s*', '', match))
                                if isinstance(sellers, dict):
                                    variables.update(sellers)
                                elif isinstance(sellers, list):
                                    for i, seller in enumerate(sellers):
                                        if seller:
                                            variables[chr(97 + i)] = seller
                            except json.JSONDecodeError:
                                pass
                    else:
                        for var_name, var_value in matches:
                            if var_name and var_value:
                                variables[var_name] = var_value.strip('\'"')
                except Exception as e:
                    logger.warning(f"Error extracting sellers with pattern {pattern}: {e}")
        
        return variables
        
    def extract_horse_data(self, html_content):
        """Extract horse data directly from JavaScript variables."""
        try:
            # Extract all JavaScript variables first
            variables = self._extract_javascript_variables(html_content)
            
            # Look for the main data structure containing horse information
            pattern = r'var\s+\w+\s*=\s*(\[\s*\{.*?\}\s*\])'
            matches = re.search(pattern, html_content, re.DOTALL)
            
            if not matches:
                logger.error("Could not find horse data array in JavaScript")
                return []
                
            try:
                # Extract and parse the JSON array
                data_str = matches.group(1)
                # Clean up the string to make it valid JSON
                data_str = re.sub(r'\s+', ' ', data_str)  # Normalize whitespace
                data_str = re.sub(r',\s*\}', '}', data_str)  # Remove trailing commas
                data_str = re.sub(r',\s*\]', ']', data_str)  # Remove trailing commas before array end
                
                # Parse the JSON data
                horses_data = json.loads(data_str)
                
                horses = []
                for item in horses_data:
                    try:
                        # Resolve seller name if it's a variable reference
                        seller = str(item.get('offererName', ''))
                        if seller in variables:
                            seller = variables[seller]
                        
                        # Clean up URLs
                        jbis_url = item.get('basicInfoUrl', '').replace('\\', '')
                        jbis_url = jbis_url.encode().decode('unicode_escape')
                        
                        horse = {
                            'name': item.get('topItemName', ''),
                            'seller': seller,
                            'jbis_url': jbis_url,
                            'image_url': item.get('image', '').replace('\\', ''),
                            'price': item.get('price', ''),
                            'sex': self._convert_sex(item.get('sex', '')),
                            'age': self._standardize_age(item.get('age', ''))
                        }
                        horses.append(horse)
                    except Exception as e:
                        logger.error(f"Error processing horse item: {e}")
                
                logger.info(f"Successfully extracted data for {len(horses)} horses")
                return horses
                
            except json.JSONDecodeError as e:
                logger.error(f"Failed to parse JSON data: {e}")
                logger.debug(f"Problematic JSON string: {data_str[:500]}...")
                return []
                
        except Exception as e:
            logger.error(f"Error in extract_horse_data: {e}")
            return []
            
        except Exception as e:
            logger.error(f"Error extracting horse data: {e}")
            return []

    def _convert_sex(self, sex_code):
        """Convert sex code to Japanese text (牡/牝/騸)."""
        if not sex_code:
            return '不明'
            
        # Clean the sex code
        sex_code = str(sex_code).strip('"\'').lower()
        
        # Basic Japanese characters
        if '牡' in sex_code or '♂' in sex_code or '雄' in sex_code:
            return '牡'
        elif '牝' in sex_code or '♀' in sex_code or '雌' in sex_code:
            return '牝'
        elif '騸' in sex_code or '去勢' in sex_code or 'せん' in sex_code:
            return '騸'
            
        # Single letter codes
        if sex_code in ['c', 'b', 'm', 'h']:
            return '牡'
        elif sex_code in ['f', 'q', 'z']:
            return '牝'
        elif sex_code in ['d', 'g', 's']:
            return '騸'
            
        return '不明'
    
    def _standardize_age(self, age):
        """Standardize age values to 歳 format."""
        if not age:
            return '不明'
            
        # Convert to string and clean
        age = str(age).strip('\'" ')
        
        # If it's already in 歳 format, return as is
        if '歳' in age:
            return age
            
        # Extract numbers
        numbers = re.findall(r'\d+', age)
        if numbers:
            age_num = int(numbers[0])
            if 0 <= age_num <= 30:  # 0-30歳の範囲
                return f"{age_num}歳"
                
        return '不明'

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
    logger.info("Starting direct auction scraper...")
    
    scraper = DirectAuctionScraper()
    
    # Fetch the auction page
    logger.info("Fetching auction page...")
    html_content = scraper.fetch_page()
    
    if not html_content:
        logger.error("Failed to fetch the auction page")
        return
    
    # Save the HTML for debugging
    with open('auction_page.html', 'w', encoding='utf-8') as f:
        f.write(html_content)
    logger.info("Saved raw HTML to auction_page.html")
    
    # Extract horse data
    logger.info("Extracting horse data...")
    horses = scraper.extract_horse_data(html_content)
    
    if not horses:
        logger.warning("No horse data found on the page")
        return
    
    logger.info(f"Extracted data for {len(horses)} horses")
    
    # Print the extracted data
    print(f"\n=== オークション情報 ({len(horses)}頭) ===\n")
    for i, horse in enumerate(horses[:20], 1):  # Print first 20 to avoid too much output
        print(f"【{i}頭目】")
        print(f"名前: {horse['name']}")
        print(f"性別: {horse['sex']}")
        print(f"年齢: {horse['age']}")
        print(f"売主: {horse['seller']}")
        print(f"価格: {horse['price']}")
        print(f"JBIS: {horse['jbis_url']}")
        print(f"画像: {horse['image_url']}")
        print()
    
    if len(horses) > 20:
        print(f"... and {len(horses) - 20} more horses")
    
    # Save to JSON file
    output_file = scraper.save_to_json(horses)
    if output_file:
        print(f"\nデータを {output_file} に保存しました")

if __name__ == "__main__":
    main()
