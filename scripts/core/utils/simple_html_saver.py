"""
Simple HTML Saver

A lightweight utility for saving HTML content to disk with basic organization.
"""

import logging
from pathlib import Path
from typing import Optional
from urllib.parse import urlparse
from datetime import datetime

logger = logging.getLogger(__name__)

class SimpleHTMLSaver:
    """Simple HTML saver that organizes files by date and type."""
    
    def __init__(self, base_dir: Path):
        """Initialize the HTML saver.
        
        Args:
            base_dir: Base directory for saving HTML files
        """
        self.base_dir = Path(base_dir)
        self.base_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"HTML saver initialized at: {self.base_dir}")
    
    def save(self, url: str, content: str) -> Optional[Path]:
        """Save HTML content to a file.
        
        Args:
            url: Source URL of the content
            content: HTML content to save
            
        Returns:
            Path to the saved file, or None if save failed
        """
        try:
            # Create dated subdirectory
            date_dir = datetime.now().strftime('%Y%m%d')
            save_dir = self.base_dir / date_dir
            save_dir.mkdir(exist_ok=True)
            
            # Generate filename from URL
            filename = self._generate_filename(url)
            filepath = save_dir / filename
            
            # Save the content
            filepath.write_text(content, encoding='utf-8')
            
            logger.debug(f"Saved HTML to: {filepath}")
            return filepath
            
        except Exception as e:
            logger.error(f"Failed to save HTML: {e}", exc_info=True)
            return None
    
    def _generate_filename(self, url: str) -> str:
        """Generate a filename from a URL."""
        # Extract the last path component or use timestamp
        path_parts = [p for p in urlparse(url).path.split('/') if p]
        if path_parts:
            return f"{path_parts[-1]}.html"
        return f"page_{int(datetime.now().timestamp())}.html"
