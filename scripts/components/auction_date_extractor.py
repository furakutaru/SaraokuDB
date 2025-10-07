"""
Auction Date Extractor Module

This module provides functionality to extract auction dates from auction pages.
"""
import logging
from datetime import datetime
from typing import Optional
from bs4 import BeautifulSoup

class AuctionDateExtractor:
    """
    A class to handle extraction of auction dates from auction pages.
    """
    
    def __init__(self, logger: Optional[logging.Logger] = None):
        """
        Initialize the AuctionDateExtractor.
        
        Args:
            logger: Optional logger instance. If not provided, a new one will be created.
        """
        self.logger = logger or logging.getLogger(__name__)
    
    def extract_from_html(self, html_content: str) -> Optional[str]:
        """
        Extract auction date from HTML content.
        
        Args:
            html_content: The HTML content of the auction page
            
        Returns:
            str: The extracted auction date in YYYY-MM-DD format, or None if not found
        """
        try:
            soup = BeautifulSoup(html_content, 'html.parser')
            
            # Look for the date element with class 'date'
            date_elem = soup.find('div', class_='date')
            
            if date_elem:
                date_str = date_elem.text.strip()
                # Convert from YYYY/MM/DD to YYYY-MM-DD format
                try:
                    date_obj = datetime.strptime(date_str, '%Y/%m/%d')
                    return date_obj.strftime('%Y-%m-%d')
                except ValueError as e:
                    self.logger.warning(f"Failed to parse date '{date_str}': {e}")
                    return None
            
            self.logger.debug("No date element found in the HTML content")
            return None
            
        except Exception as e:
            self.logger.error(f"Error extracting auction date: {e}", exc_info=True)
            return None
    
    def get_auction_date(self, html_content: str) -> Optional[str]:
        """
        Alias for extract_from_html for backward compatibility.
        """
        return self.extract_from_html(html_content)

# For backward compatibility
get_auction_date = AuctionDateExtractor().get_auction_date
