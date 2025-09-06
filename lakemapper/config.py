"""
Configuration settings for LakeMapper.

This module contains all configuration constants and settings used throughout
the LakeMapper data processing pipeline.
"""

import os
from pathlib import Path

# Project paths
PROJECT_ROOT = Path(__file__).parent.parent
DATA_DIR = PROJECT_ROOT / "data"
RAW_DATA_DIR = DATA_DIR / "raw"
OUTPUT_DIR = PROJECT_ROOT / "output"
CACHE_DIR = "cache"  # Directory for caching fish survey data

# Input file paths
BATHYMETRY_FILE = RAW_DATA_DIR / "bathymetry_contours.shp"
FISH_SURVEY_FILE = RAW_DATA_DIR / "fish_survey.shp"

# Output directory structure
GEOJSON_DIR = OUTPUT_DIR / "geojson"
RASTER_DIR = OUTPUT_DIR / "raster"
METADATA_DIR = OUTPUT_DIR / "metadata"
CONTOURS_DIR = OUTPUT_DIR / "contours"

# Geometry processing settings
BUFFER_DISTANCE_METERS = 10.0  # Buffer distance for merging bathymetry contours
CRS_EPSG = 26915  # UTM Zone 15N (Minnesota) - NAD83

# Field mappings
BATHYMETRY_FIELDS = {
    'dowlknum': 'DOWLKNUM',
    'depth': 'DEPTH',
    'abs_depth': 'abs_depth',
    'shape_leng': 'Shape_Leng',
    'lake_name': 'LAKE_NAME'
}

FISH_SURVEY_FIELDS = {
    'dowlknum': 'DOWLKNUM',
    'acres': 'ACRES',
    'city_name': 'CTY_NAME',
    'survey_url': 'SURVEY_URL',
    'shape_leng': 'SHAPE_Leng',
    'shape_area': 'SHAPE_Area'
}

# Logging configuration
LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Processing settings
BATCH_SIZE = 100  # Number of lakes to process in each batch for progress reporting
MAX_WORKERS = 10  # Maximum number of concurrent threads for parallel processing

# Validation settings
MIN_LAKE_AREA_ACRES = 1.0  # Minimum lake area to include in processing
MAX_LAKE_AREA_ACRES = 1000000.0  # Maximum lake area (sanity check)

# Web scraping settings (for future fish survey data extraction)
REQUEST_TIMEOUT = 30  # seconds
MAX_RETRIES = 3 