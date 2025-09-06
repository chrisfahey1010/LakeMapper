"""
LakeMapper - Minnesota DNR Lake Data Processing Tool

A Python-based data processing tool designed to convert Minnesota DNR lake shapefiles
into game-ready formats for a browser-based fishing simulation game.

This package provides functionality to:
- Load and validate bathymetry and fish survey shapefiles
- Match lakes between datasets using DOWLKNUM identifiers
- Merge bathymetry contours for unified lake geometries
- Export processed data to GeoJSON, metadata JSON, and other formats
"""

__version__ = "0.1.0"
__author__ = "LakeMapper Development Team"

from .loader import load_all_data, load_bathymetry_data, load_fish_survey_data
from .matcher import find_matching_lakes, get_lake_summary
from .merger import merge_all_lakes, create_merged_geodataframe
from .exporter import export_all_lakes, export_merged_geodataframe
from .fish_survey_fetcher import get_fish_survey_summary, batch_fetch_fish_surveys
from .utils import setup_logging, ensure_directories

__all__ = [
    # Core functions
    'load_all_data',
    'load_bathymetry_data', 
    'load_fish_survey_data',
    'find_matching_lakes',
    'get_lake_summary',
    'merge_all_lakes',
    'create_merged_geodataframe',
    'export_all_lakes',
    'export_merged_geodataframe',
    
    # Fish survey functions
    'get_fish_survey_summary',
    'batch_fetch_fish_surveys',
    
    # Utilities
    'setup_logging',
    'ensure_directories',
] 