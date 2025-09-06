"""
Utility functions for LakeMapper.

This module contains logging setup and other utility functions used throughout
the LakeMapper data processing pipeline.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from .config import LOG_LEVEL, LOG_FORMAT


def setup_logging(
    level: Optional[str] = None,
    log_file: Optional[Path] = None
) -> logging.Logger:
    """
    Set up logging configuration for the LakeMapper application.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        
    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger('lakemapper')
    logger.setLevel(level or LOG_LEVEL)
    
    # Clear any existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = logging.Formatter(LOG_FORMAT)
    
    # Create console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Create file handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger


def ensure_directories() -> None:
    """
    Ensure all required output directories exist.
    """
    from .config import OUTPUT_DIR, GEOJSON_DIR, RASTER_DIR, METADATA_DIR, CONTOURS_DIR
    
    for directory in [OUTPUT_DIR, GEOJSON_DIR, RASTER_DIR, METADATA_DIR, CONTOURS_DIR]:
        directory.mkdir(parents=True, exist_ok=True)


def validate_dowlknum(dowlknum: str) -> bool:
    """
    Validate that a DOWLKNUM is in the expected format.
    
    Args:
        dowlknum: The DOWLKNUM string to validate
        
    Returns:
        True if valid, False otherwise
    """
    if not dowlknum or not isinstance(dowlknum, str):
        return False
    
    # DOWLKNUM should be 8 digits
    return dowlknum.isdigit() and len(dowlknum) == 8


def format_lake_filename(dowlknum: str, extension: str = "geojson") -> str:
    """
    Generate a standardized filename for a lake based on its DOWLKNUM.
    
    Args:
        dowlknum: The lake's DOWLKNUM
        extension: File extension (without dot)
        
    Returns:
        Formatted filename
    """
    return f"lake_{dowlknum}.{extension}" 