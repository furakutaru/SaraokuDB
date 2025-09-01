#!/usr/bin/env python3
"""
Test script to verify the extraction of horse weight information from cache files.
"""
import os
import sys
import re
import logging
from pathlib import Path
from bs4 import BeautifulSoup
import sys

# Add the project root to the path
sys.path.append(str(Path(__file__).parent.parent))

# Import the extractor class
from scripts.components.horse_info_extractor import HorseInfoExtractor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('test_weight_extraction.log', 'w', 'utf-8')
    ]
)
logger = logging.getLogger(__name__)

def test_weight_extraction():
    """Test weight extraction from cache files."""
    # Get all HTML files from the cache directories using absolute paths
    project_root = Path(__file__).parent.parent
    cache_dirs = [
        project_root / "cache",
        project_root / "cache" / "details"
    ]
    
    # Find all HTML files
    html_files = []
    for cache_dir in cache_dirs:
        if cache_dir.exists() and cache_dir.is_dir():
            html_files.extend(list(cache_dir.glob("*.html")))
    
    if not html_files:
        logger.error("No HTML files found in cache directories")
        return
    
    logger.info(f"Found {len(html_files)} HTML files to process")
    
    # Initialize the extractor
    extractor = HorseInfoExtractor()
    
    # Process each file
    for file_path in html_files:
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            # Parse the HTML
            soup = BeautifulSoup(content, 'html.parser')
            
            # Try to find horse elements
            horse_elements = soup.select('div.horseInfo, div.horse-info, div.horse')
            if not horse_elements:
                # If no specific horse elements found, use the whole document
                horse_elements = [soup]
            
            for idx, element in enumerate(horse_elements):
                weight = extractor._extract_weight(element)
                if weight is not None:
                    logger.info(f"File: {file_path} - Horse {idx+1} - Weight: {weight}kg")
                    break  # Stop after first successful extraction
            else:
                logger.debug(f"No weight found in {file_path}")
                
        except Exception as e:
            logger.error(f"Error processing {file_path}: {str(e)}")
            continue

if __name__ == "__main__":
    logger.info("Starting weight extraction test...")
    test_weight_extraction()
    logger.info("Test completed")
