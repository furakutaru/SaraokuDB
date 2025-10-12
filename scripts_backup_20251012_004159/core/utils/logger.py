"""
Logging configuration and utilities.

This module provides a centralized way to configure logging for the application.
"""
import logging
import logging.handlers
import os
from pathlib import Path
from typing import Optional, Union

from ..config.manager import config

class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log levels."""
    
    # ANSI color codes
    COLORS = {
        'DEBUG': '\033[0;36m',    # Cyan
        'INFO': '\033[0;32m',     # Green
        'WARNING': '\033[0;33m',  # Yellow
        'ERROR': '\033[0;31m',    # Red
        'CRITICAL': '\033[1;31m', # Bold Red
        'RESET': '\033[0m'        # Reset
    }
    
    def format(self, record):
        """Format the specified record with colors."""
        levelname = record.levelname
        if levelname in self.COLORS:
            record.levelname = f"{self.COLORS[levelname]}{levelname}{self.COLORS['RESET']}"
            record.msg = f"{self.COLORS[levelname]}{record.msg}{self.COLORS['RESET']}"
        return super().format(record)

def setup_logger(
    name: str = 'scraper',
    level: Optional[Union[int, str]] = None,
    log_file: Optional[Union[str, Path]] = None,
    console: bool = True,
    max_bytes: int = 10 * 1024 * 1024,  # 10 MB
    backup_count: int = 5
) -> logging.Logger:
    """Set up a logger with file and console handlers.
    
    Args:
        name: Name of the logger
        level: Logging level (default: from config)
        log_file: Path to the log file (default: from config)
        console: Whether to log to console
        max_bytes: Maximum size of log file before rotation
        backup_count: Number of backup log files to keep
        
    Returns:
        Configured logger instance
    """
    # Use config values if not provided
    if level is None:
        level = config.logging.level
    if log_file is None:
        log_file = config.logging.file
    
    # Convert string level to logging level
    if isinstance(level, str):
        level = getattr(logging, level.upper(), logging.INFO)
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(level)
    
    # Clear existing handlers to avoid duplicate logs
    logger.handlers = []
    
    # Create formatters
    file_formatter = logging.Formatter(
        fmt=config.logging.format,
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    console_formatter = ColoredFormatter(
        fmt=f"%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # File handler
    if log_file:
        # Ensure log directory exists
        log_file = Path(log_file)
        log_file.parent.mkdir(exist_ok=True, parents=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            filename=log_file,
            maxBytes=max_bytes,
            backupCount=backup_count,
            encoding='utf-8'
        )
        file_handler.setLevel(level)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
    
    # Console handler
    if console:
        console_handler = logging.StreamHandler()
        console_handler.setLevel(level)
        console_handler.setFormatter(console_formatter)
        logger.addHandler(console_handler)
    
    return logger

# Default logger for the application
logger = setup_logger()

def get_logger(name: str = None) -> logging.Logger:
    """Get a logger with the given name.
    
    Args:
        name: Name of the logger (default: root logger)
        
    Returns:
        Configured logger instance
    """
    if not name:
        return logger
    return logging.getLogger(name)
