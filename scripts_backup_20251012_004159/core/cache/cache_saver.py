"""
Cache Saver Module

Provides functionality to save and manage cached HTML content with proper directory structure
and metadata tracking.
"""

import logging
import time
from pathlib import Path
from typing import Optional, Dict, Any, Tuple
from urllib.parse import urlparse
from datetime import datetime
import json

logger = logging.getLogger(__name__)

class CacheSaver:
    """Handles saving and organizing cached HTML content with metadata."""
    
    def __init__(self, base_dir: Path, session_id: str = None):
        """Initialize the CacheSaver.
        
        Args:
            base_dir: Base directory for cache storage
            session_id: Optional session ID (generated from timestamp if not provided)
        """
        self.base_dir = Path(base_dir)
        self.session_id = session_id or self._generate_session_id()
        self.session_dir = self.base_dir / self.session_id
        self.metadata: Dict[str, Any] = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'files': {}
        }
        self._setup_directories()
    
    def _generate_session_id(self) -> str:
        """Generate a unique session ID based on timestamp."""
        return datetime.now().strftime('%Y%m%d_%H%M%S')
    
    def _setup_directories(self) -> None:
        """Create necessary directories for the cache session."""
        self.details_dir = self.session_dir / 'details'
        self.session_dir.mkdir(parents=True, exist_ok=True)
        self.details_dir.mkdir(exist_ok=True)
        logger.info(f"Cache session started: {self.session_dir}")
        logger.info(f"List pages will be saved to: {self.session_dir}")
        logger.info(f"Detail pages will be saved to: {self.details_dir}")
    
    def save_html(self, url: str, content: str) -> Optional[Path]:
        """Save HTML content to cache with proper organization.
        
        Args:
            url: Source URL of the content
            content: HTML content to save
            
        Returns:
            Path to the saved file, or None if save failed
        """
        try:
            # Determine if this is a detail page or list page
            is_detail = self._is_detail_page(url)
            
            # Get appropriate save path
            if is_detail:
                filename = self._generate_detail_filename(url)
                save_path = self.details_dir / filename
                file_type = 'detail'
            else:
                # For list pages, save directly in the session directory (not in details folder)
                filename = 'list.html'
                save_path = self.session_dir / filename
                file_type = 'list'
            
            # Save the content
            save_path.write_text(content, encoding='utf-8')
            
            # Update metadata
            self._update_metadata(url, str(save_path), file_type)
            
            logger.debug(f"Saved {file_type} to cache: {save_path}")
            return save_path
            
        except Exception as e:
            logger.error(f"Failed to save HTML to cache: {e}", exc_info=True)
            return None
    
    def _is_detail_page(self, url: str) -> bool:
        """Determine if a URL points to a detail page."""
        path = urlparse(url).path.lower()
        return any(x in path for x in ['item', 'detail', 'horse'])
    
    def _generate_detail_filename(self, url: str) -> str:
        """Generate a filename for a detail page based on URL."""
        # Extract ID from URL
        path_parts = [p for p in urlparse(url).path.split('/') if p]
        if path_parts:
            # Extract numeric ID from URL (e.g., 'item/12345' -> '12345.html')
            last_part = path_parts[-1]
            if last_part.isdigit():
                return f"{last_part}.html"
            # If the last part is not a number, try to find a number in the path
            for part in reversed(path_parts):
                if part.isdigit():
                    return f"{part}.html"
        # Fallback to timestamp if no ID found
        return f"detail_{int(time.time())}.html"
    
    def _update_metadata(self, url: str, filepath: str, file_type: str) -> None:
        """Update the metadata for the cache session."""
        self.metadata['files'][url] = {
            'path': filepath,
            'type': file_type,
            'saved_at': datetime.now().isoformat()
        }
        self._save_metadata()
    
    def _save_metadata(self) -> None:
        """Save the metadata to a JSON file."""
        metadata_path = self.session_dir / 'metadata.json'
        with open(metadata_path, 'w', encoding='utf-8') as f:
            json.dump(self.metadata, f, ensure_ascii=False, indent=2)
    
    def cleanup(self) -> None:
        """Clean up the cache session and finalize metadata."""
        self.metadata['end_time'] = datetime.now().isoformat()
        self._save_metadata()
        logger.info(f"Cache session completed: {self.session_dir}")


def get_cache_session(base_dir: str = 'cache') -> CacheSaver:
    """Helper function to create a new cache session."""
    base_path = Path(base_dir)
    base_path.mkdir(parents=True, exist_ok=True)
    return CacheSaver(base_path)
