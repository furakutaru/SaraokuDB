#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Script to verify debug directory creation and file saving functionality.
"""
import os
import sys
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(),
        logging.FileHandler('debug_save_verification.log')
    ]
)
logger = logging.getLogger(__name__)

def verify_debug_save():
    """Verify debug directory creation and file saving."""
    try:
        # 1. Define paths
        project_root = Path(__file__).parent.parent
        debug_dir = project_root / 'debug'
        
        # 2. Create date-based subdirectories
        date_str = datetime.now().strftime("%Y%m%d")
        date_dir = debug_dir / date_str
        detail_dir = date_dir / 'detail'
        
        logger.info(f"Project root: {project_root}")
        logger.info(f"Debug directory: {debug_dir}")
        logger.info(f"Date directory: {date_dir}")
        logger.info(f"Detail directory: {detail_dir}")
        
        # 3. Create directories with explicit permissions
        for directory in [debug_dir, date_dir, detail_dir]:
            try:
                directory.mkdir(parents=True, exist_ok=True)
                # Set permissions explicitly (rwxr-xr-x)
                directory.chmod(0o755)
                logger.info(f"✓ Created/verified directory: {directory}")
                logger.info(f"  Permissions: {oct(directory.stat().st_mode)[-3:]}")
            except Exception as e:
                logger.error(f"✗ Failed to create directory {directory}: {e}")
                raise
        
        # 4. Test file writing
        test_content = f"Test content written at: {datetime.now()}"
        
        # Test list page file
        list_page_file = date_dir / 'test_horse_list.html'
        try:
            with open(list_page_file, 'w', encoding='utf-8') as f:
                f.write(f"<html><body>{test_content}</body></html>")
            logger.info(f"✓ Successfully wrote to: {list_page_file}")
        except Exception as e:
            logger.error(f"✗ Failed to write to {list_page_file}: {e}")
            raise
        
        # Test detail page file
        detail_file = detail_dir / 'test_detail_001.html'
        try:
            with open(detail_file, 'w', encoding='utf-8') as f:
                f.write(f"<html><body><h1>Test Detail Page</h1><p>{test_content}</p></body></html>")
            logger.info(f"✓ Successfully wrote to: {detail_file}")
        except Exception as e:
            logger.error(f"✗ Failed to write to {detail_file}: {e}")
            raise
        
        # Test card file
        card_file = detail_dir / 'test_card_001.html'
        try:
            with open(card_file, 'w', encoding='utf-8') as f:
                f.write(f"<div class='horse-card'><h2>Test Horse</h2><p>{test_content}</p></div>")
            logger.info(f"✓ Successfully wrote to: {card_file}")
        except Exception as e:
            logger.error(f"✗ Failed to write to {card_file}: {e}")
            raise
        
        # Verify file permissions
        for file_path in [list_page_file, detail_file, card_file]:
            try:
                file_stat = file_path.stat()
                logger.info(f"File: {file_path}")
                logger.info(f"  Size: {file_stat.st_size} bytes")
                logger.info(f"  Permissions: {oct(file_stat.st_mode)[-3:]}")
            except Exception as e:
                logger.error(f"Error getting file info for {file_path}: {e}")
        
        return True
        
    except Exception as e:
        logger.error(f"Verification failed: {e}")
        return False

if __name__ == "__main__":
    logger.info("=== Starting Debug Save Verification ===")
    try:
        success = verify_debug_save()
        if success:
            logger.info("✓ Debug save verification completed successfully!")
            sys.exit(0)
        else:
            logger.error("✗ Debug save verification failed!")
            sys.exit(1)
    except Exception as e:
        logger.error(f"✗ Unhandled exception: {e}", exc_info=True)
        sys.exit(1)
