import os
import json
import re
import logging
import requests
from bs4 import BeautifulSoup
from datetime import datetime
from pathlib import Path
import time
from urllib.parse import urljoin, urlparse, parse_qs

# Set up logging
log_file = Path('horse_extraction.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file, encoding='utf-8'),
        logging.StreamHandler()
    ]
)

# Suppress BeautifulSoup warning
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module='bs4')

def download_detail_page(detail_url, output_dir, session_id, base_url="https://www.tb-selection.com/"):
    """Download and save detail page for a horse."""
    try:
        # Create details directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)
        
        # Extract horse ID from URL or generate a unique ID
        parsed_url = urlparse(detail_url)
        query_params = parse_qs(parsed_url.query)
        horse_id = query_params.get('id', [None])[0] or str(int(time.time()))
        
        # Generate filename
        filename = f"{session_id}_horse_{horse_id}.html"
        filepath = os.path.join(output_dir, filename)
        
        # Check if file already exists
        if os.path.exists(filepath):
            logging.info(f"Detail page already exists: {filepath}")
            return filename
        
        # Make the request
        headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36'
        }
        
        # Construct full URL if it's relative
        if not detail_url.startswith('http'):
            detail_url = urljoin(base_url, detail_url)
        
        response = requests.get(detail_url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Save the HTML content
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        logging.info(f"Downloaded detail page: {filename}")
        return filename
        
    except Exception as e:
        logging.error(f"Error downloading detail page {detail_url}: {str(e)}")
        return None

def extract_detail_links(html_file):
    """Extract detail page links from the list page."""
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        soup = BeautifulSoup(content, 'html.parser')
        links = []
        
        # Find all links that point to detail pages
        # This selector needs to be adjusted based on the actual HTML structure
        for link in soup.find_all('a', href=True):
            href = link['href']
            # Adjust this condition based on how detail page URLs are structured
            if 'detail' in href or 'horse' in href:
                links.append(href)
        
        return list(set(links))  # Remove duplicates
        
    except Exception as e:
        logging.error(f"Error extracting detail links: {str(e)}")
        return []

def extract_horse_info(html_file):
    """Extract horse information from the list page HTML."""
    logging.info(f"Starting extraction from {html_file}")
    
    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        logging.error(f"Error reading file {html_file}: {str(e)}")
        return []
    
    try:
        soup = BeautifulSoup(content, 'html.parser')
    except Exception as e:
        logging.error(f"Error parsing HTML: {str(e)}")
        return []
    
    horses = []
    
    # Find all horse entries - they seem to be in tables with specific styling
    horse_sections = []
    
    # Look for tables that contain horse information
    tables = soup.find_all('table')
    logging.info(f"Found {len(tables)} tables in the document")
    
    # The horse information is in tables with specific attributes
    for table in tables:
        # Look for tables with horse information
        if table.find('b') and table.find('pre'):
            horse_sections.append(table)
    
    logging.info(f"Found {len(horse_sections)} potential horse sections")
    
    for section in horse_sections:
        try:
            # Extract horse name (in bold)
            name_tag = section.find('b')
            if not name_tag:
                continue
                
            name = name_tag.get_text(strip=True)
            if not name or len(name) < 2:  # Skip if name is too short
                continue
            
            # Extract all text from the section
            details_text = section.get_text(separator='\n', strip=True)
            
            # Extract basic information using regex patterns
            horse_info = {
                'name': name,
                'extracted_at': datetime.now().isoformat(),
                'source_file': os.path.basename(html_file)
            }
            
            # Extract pedigree information
            pedigree_match = re.search(r'父：([^\s]+)\s*母：([^\s]+)\s*母の父：([^\n]+)', details_text)
            if pedigree_match:
                horse_info.update({
                    'sire': pedigree_match.group(1).strip(),
                    'dam': pedigree_match.group(2).strip(),
                    'damsire': pedigree_match.group(3).strip()
                })
            
            # Extract race record if available
            record_match = re.search(r'通算成績：([^\[]+)\[([^\]]+)\]', details_text)
            if record_match:
                horse_info['race_record'] = {
                    'summary': record_match.group(1).strip(),
                    'record': record_match.group(2).strip()
                }
            
            # Extract prize money
            prize_match = re.search(r'中央獲得賞金：([\d,.]+)万円', details_text)
            if prize_match:
                try:
                    horse_info['prize_money'] = float(prize_match.group(1).replace(',', ''))
                except (ValueError, TypeError):
                    pass
            
            # Extract auction date if available
            auction_match = re.search(r'※(\d{4}年\d{1,2}月\d{1,2}日)落札', details_text)
            if auction_match:
                horse_info['auction_date'] = auction_match.group(1)
            
            # Extract comments about the horse
            comment_section = re.search(r'本馬について[^\n]*\n(.*?)(?=\n\s*※|$)', details_text, re.DOTALL)
            if comment_section:
                horse_info['comments'] = comment_section.group(1).strip()
            
            logging.info(f"Extracted info for horse: {name}")
            horses.append(horse_info)
            
        except Exception as e:
            logging.error(f"Error processing horse section: {str(e)}", exc_info=True)
            continue
    
    logging.info(f"Successfully extracted {len(horses)} horses")
    return horses

def main():
    try:
        # Set up paths
        cache_dir = "/Users/yum.ishii/SaraokuDB/cache/202508161516"
        list_file = os.path.join(cache_dir, "list.html")
        output_file = os.path.join(cache_dir, "extracted_horses.json")
        details_dir = os.path.join(cache_dir, "details")
        metadata_file = os.path.join(cache_dir, "metadata.json")
        
        # Load or create metadata
        if os.path.exists(metadata_file):
            with open(metadata_file, 'r', encoding='utf-8') as f:
                metadata = json.load(f)
        else:
            metadata = {
                "session_id": os.path.basename(cache_dir),
                "start_time": datetime.now().isoformat(),
                "list_page": "list.html",
                "details": [],
                "last_updated": datetime.now().isoformat()
            }
        
        # Check if input file exists
        if not os.path.exists(list_file):
            logging.error(f"Input file not found: {list_file}")
            return
        
        # Clear previous log file if it exists
        if os.path.exists('horse_extraction.log'):
            os.remove('horse_extraction.log')
        
        # Create details directory if it doesn't exist
        os.makedirs(details_dir, exist_ok=True)
        
        # Extract detail page links and download them
        logging.info("Extracting detail page links...")
        detail_links = extract_detail_links(list_file)
        logging.info(f"Found {len(detail_links)} detail page links")
        
        # Download detail pages
        downloaded_files = []
        for i, link in enumerate(detail_links, 1):
            logging.info(f"Downloading detail page {i}/{len(detail_links)}: {link}")
            filename = download_detail_page(link, details_dir, metadata["session_id"])
            if filename:
                downloaded_files.append(filename)
                
                # Update metadata
                if filename not in metadata["details"]:
                    metadata["details"].append(filename)
                
                # Update metadata file after each download
                metadata["last_updated"] = datetime.now().isoformat()
                with open(metadata_file, 'w', encoding='utf-8') as f:
                    json.dump(metadata, f, ensure_ascii=False, indent=2)
                
                # Be nice to the server
                time.sleep(1)
        
        # Extract horse information
        logging.info(f"Starting extraction from {list_file}")
        horses = extract_horse_info(list_file)
        
        # Save the extracted data
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(horses, f, ensure_ascii=False, indent=2)
            
        # Update metadata with final information
        metadata["last_updated"] = datetime.now().isoformat()
        with open(metadata_file, 'w', encoding='utf-8') as f:
            json.dump(metadata, f, ensure_ascii=False, indent=2)
        
        # Print summary
        print("\n=== 抽出結果のサマリー ===")
        print(f"抽出された馬の数: {len(horses)}")
        print(f"出力ファイル: {output_file}")
        
        if horses:
            print("\n最初の数頭の情報:")
            for i, horse in enumerate(horses[:3], 1):
                print(f"\n{i}. 馬名: {horse.get('name', 'N/A')}")
                print(f"   父: {horse.get('sire', 'N/A')}")
                print(f"   母: {horse.get('dam', 'N/A')}")
                print(f"   母の父: {horse.get('damsire', 'N/A')}")
                if 'prize_money' in horse:
                    print(f"   獲得賞金: {horse['prize_money']:,.1f}万円")
        
        print(f"\n詳細なログは 'horse_extraction.log' を確認してください。")
        
    except Exception as e:
        logging.error(f"エラーが発生しました: {str(e)}", exc_info=True)
        print(f"\nエラーが発生しました。詳細はログファイルを確認してください: {os.path.abspath('horse_extraction.log')}")
        raise

if __name__ == "__main__":
    main()
