import os
import re
import time
import requests
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from pathlib import Path

def extract_horse_links(html_file):
    """Extract horse detail page links from the list page."""
    with open(html_file, 'r', encoding='utf-8') as f:
        content = f.read()
    
    # The links are in format: /horse/auction/2024/0001234567/
    pattern = r'href="(/horse/auction/\d+/\d+/)"'
    links = re.findall(pattern, content)
    
    # Make links absolute
    base_url = 'https://www.keiba.go.jp'
    return [urljoin(base_url, link) for link in links]

def download_horse_page(url, output_dir):
    """Download a single horse detail page and save it."""
    try:
        # Create a session to handle cookies
        session = requests.Session()
        
        # Set headers to mimic a browser
        headers = {
            'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
            'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8',
            'Accept-Language': 'en-US,en;q=0.5',
            'Referer': 'https://www.keiba.go.jp/'
        }
        
        # Make the request
        response = session.get(url, headers=headers, timeout=30)
        response.raise_for_status()
        
        # Extract horse ID from URL for filename
        horse_id = url.rstrip('/').split('/')[-1]
        output_file = os.path.join(output_dir, f"{horse_id}.html")
        
        # Save the HTML content
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(response.text)
        
        print(f"Downloaded: {url} -> {output_file}")
        return True
        
    except Exception as e:
        print(f"Error downloading {url}: {str(e)}")
        return False

def main():
    # Set up paths
    cache_dir = "/Users/yum.ishii/SaraokuDB/cache/202508161516"
    details_dir = os.path.join(cache_dir, "details")
    list_file = os.path.join(cache_dir, "list.html")
    
    # Create details directory if it doesn't exist
    os.makedirs(details_dir, exist_ok=True)
    
    # Extract horse detail page links
    print("Extracting horse detail page links...")
    horse_links = extract_horse_links(list_file)
    
    if not horse_links:
        print("No horse links found in the list page.")
        return
    
    print(f"Found {len(horse_links)} horse detail pages to download.")
    
    # Download each horse detail page with delay
    success_count = 0
    for i, link in enumerate(horse_links, 1):
        print(f"\n[{i}/{len(horse_links)}] Downloading: {link}")
        if download_horse_page(link, details_dir):
            success_count += 1
        
        # Be nice to the server - add a delay between requests
        if i < len(horse_links):
            time.sleep(2)  # 2 second delay between requests
    
    print(f"\nDownload complete. Successfully downloaded {success_count} of {len(horse_links)} pages.")

if __name__ == "__main__":
    main()
