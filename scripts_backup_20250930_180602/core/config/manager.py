"""
Configuration management for the scraper.

This module provides a centralized way to manage configuration settings,
with support for environment variable overrides and type validation.
"""
import os
import logging
from pathlib import Path
from typing import Any, Dict, Optional, Type, TypeVar, get_type_hints
from dataclasses import dataclass, field

from . import (
    BASE_DIR, CACHE_DIR, OUTPUT_DIR, LOG_DIR,
    DEFAULT_TIMEOUT, MAX_RETRIES, BACKOFF_FACTOR, MAX_WORKERS,
    LOG_LEVEL, LOG_FORMAT, LOG_FILE,
    HEALTH_KEYWORDS, DATABASE_CONFIG, SCRAPER_CONFIG, OUTPUT_CONFIG, CACHE_CONFIG
)

T = TypeVar('T', bound='Config')

@dataclass
class Config:
    """Base configuration class."""
    
    def __post_init__(self):
        """Initialize the configuration."""
        self._validate_types()
    
    def _validate_types(self):
        """Validate that all fields have the correct type."""
        type_hints = get_type_hints(self.__class__)
        for field_name, field_type in type_hints.items():
            value = getattr(self, field_name)
            if value is not None and not isinstance(value, field_type):
                try:
                    # Try to convert to the correct type
                    if field_type == Path and isinstance(value, str):
                        setattr(self, field_name, Path(value))
                    else:
                        setattr(self, field_name, field_type(value))
                except (TypeError, ValueError) as e:
                    raise TypeError(
                        f"Invalid type for {field_name}: "
                        f"expected {field_type.__name__}, got {type(value).__name__}"
                    ) from e

@dataclass
class DatabaseConfig(Config):
    """Database configuration."""
    host: str = "localhost"
    port: str = "5432"
    database: str = "horsedb"
    user: str = "postgres"
    password: str = "postgres"
    
    @property
    def connection_string(self) -> str:
        """Get the database connection string."""
        return f"postgresql://{self.user}:{self.password}@{self.host}:{self.port}/{self.database}"

@dataclass
class LoggingConfig(Config):
    """Logging configuration."""
    level: str = LOG_LEVEL
    format: str = LOG_FORMAT
    file: Path = LOG_FILE
    max_size: int = 10 * 1024 * 1024  # 10 MB
    backup_count: int = 5

@dataclass
class ScraperConfig(Config):
    """Scraper configuration."""
    use_cache: bool = True
    base_url: str = "https://auction.keiba.rakuten.co.jp/"
    timeout: int = DEFAULT_TIMEOUT
    max_retries: int = MAX_RETRIES
    backoff_factor: float = BACKOFF_FACTOR
    max_workers: int = MAX_WORKERS
    user_agent: str = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36"
    health_keywords: list = field(default_factory=lambda: HEALTH_KEYWORDS)

@dataclass
class CacheConfig(Config):
    """Cache configuration."""
    enabled: bool = True
    cache_dir: Path = CACHE_DIR
    expire_after: int = 60 * 60 * 24 * 7  # 1 week in seconds
    compress: bool = True

@dataclass
class OutputConfig(Config):
    """Output configuration."""
    output_dir: Path = OUTPUT_DIR
    output_file: Path = OUTPUT_DIR / 'horses.json'
    pretty_print: bool = True
    ensure_ascii: bool = False

class ConfigManager:
    """Configuration manager for the application."""
    
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
            
        # Load configurations
        self.database = DatabaseConfig(**DATABASE_CONFIG)
        self.logging = LoggingConfig()
        self.scraper = ScraperConfig(**SCRAPER_CONFIG)
        self.cache = CacheConfig(**CACHE_CONFIG)
        self.output = OutputConfig(**OUTPUT_CONFIG)
        
        # Apply environment variable overrides
        self._apply_env_overrides()
        
        # Ensure directories exist
        self._ensure_directories()
        
        self._initialized = True
    
    def _apply_env_overrides(self):
        """Apply environment variable overrides to the configuration."""
        # Database overrides
        if db_host := os.getenv('DB_HOST'):
            self.database.host = db_host
        if db_port := os.getenv('DB_PORT'):
            self.database.port = db_port
        if db_name := os.getenv('DB_NAME'):
            self.database.database = db_name
        if db_user := os.getenv('DB_USER'):
            self.database.user = db_user
        if db_password := os.getenv('DB_PASSWORD'):
            self.database.password = db_password
        
        # Logging overrides
        if log_level := os.getenv('LOG_LEVEL'):
            self.logging.level = log_level
        if log_file := os.getenv('LOG_FILE'):
            self.logging.file = Path(log_file)
        
        # Scraper overrides
        if timeout := os.getenv('SCRAPER_TIMEOUT'):
            self.scraper.timeout = int(timeout)
        if max_retries := os.getenv('SCRAPER_MAX_RETRIES'):
            self.scraper.max_retries = int(max_retries)
        if max_workers := os.getenv('SCRAPER_MAX_WORKERS'):
            self.scraper.max_workers = int(max_workers)
    
    def _ensure_directories(self):
        """Ensure that all required directories exist."""
        dirs = [
            self.logging.file.parent,
            self.cache.cache_dir,
            self.output.output_dir
        ]
        
        for directory in dirs:
            directory.mkdir(exist_ok=True, parents=True)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert the configuration to a dictionary."""
        return {
            'database': self.database.__dict__,
            'logging': self.logging.__dict__,
            'scraper': self.scraper.__dict__,
            'cache': self.cache.__dict__,
            'output': self.output.__dict__
        }

# Global configuration instance
config = ConfigManager()
