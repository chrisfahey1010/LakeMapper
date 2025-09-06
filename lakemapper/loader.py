"""
Data loader module for LakeMapper.

This module handles loading and basic validation of the Minnesota DNR shapefiles.
"""

import logging
from pathlib import Path
from typing import Tuple, Optional

import geopandas as gpd
import pandas as pd

from .config import (
    BATHYMETRY_FILE, FISH_SURVEY_FILE, CRS_EPSG,
    BATHYMETRY_FIELDS, FISH_SURVEY_FIELDS,
    MIN_LAKE_AREA_ACRES, MAX_LAKE_AREA_ACRES
)
from .utils import validate_dowlknum


logger = logging.getLogger(__name__)


def load_bathymetry_data() -> gpd.GeoDataFrame:
    """
    Load and validate bathymetry contours shapefile.
    
    Returns:
        GeoDataFrame containing bathymetry contour data
        
    Raises:
        FileNotFoundError: If bathymetry file doesn't exist
        ValueError: If required fields are missing or data is invalid
    """
    logger.info(f"Loading bathymetry data from {BATHYMETRY_FILE}")
    
    if not BATHYMETRY_FILE.exists():
        raise FileNotFoundError(f"Bathymetry file not found: {BATHYMETRY_FILE}")
    
    # Load the shapefile
    gdf = gpd.read_file(BATHYMETRY_FILE)
    
    # Log basic info
    logger.info(f"Loaded {len(gdf)} bathymetry contours")
    logger.info(f"CRS: {gdf.crs}")
    logger.info(f"Columns: {list(gdf.columns)}")
    
    # Validate required fields
    required_fields = list(BATHYMETRY_FIELDS.values())
    missing_fields = [field for field in required_fields if field not in gdf.columns]
    if missing_fields:
        raise ValueError(f"Missing required fields in bathymetry data: {missing_fields}")
    
    # Validate DOWLKNUM format
    invalid_dowlknums = []
    for idx, dowlknum in enumerate(gdf[BATHYMETRY_FIELDS['dowlknum']]):
        if not validate_dowlknum(str(dowlknum)):
            invalid_dowlknums.append((idx, dowlknum))
    
    if invalid_dowlknums:
        logger.warning(f"Found {len(invalid_dowlknums)} invalid DOWLKNUMs in bathymetry data")
        for idx, dowlknum in invalid_dowlknums[:5]:  # Log first 5
            logger.warning(f"  Row {idx}: {dowlknum}")
    
    # Ensure CRS is set correctly
    if gdf.crs is None:
        logger.warning("No CRS found in bathymetry data, assuming EPSG:26915")
        gdf.set_crs(epsg=CRS_EPSG, inplace=True)
    elif gdf.crs.to_epsg() != CRS_EPSG:
        logger.info(f"Reprojecting bathymetry data from {gdf.crs} to EPSG:{CRS_EPSG}")
        gdf = gdf.to_crs(epsg=CRS_EPSG)
    
    # Basic data validation
    logger.info(f"Bathymetry data bounds: {gdf.total_bounds}")
    logger.info(f"Depth range: {gdf[BATHYMETRY_FIELDS['depth']].min()} to {gdf[BATHYMETRY_FIELDS['depth']].max()}")
    
    return gdf


def load_fish_survey_data() -> gpd.GeoDataFrame:
    """
    Load and validate fish survey lake outlines shapefile.
    
    Returns:
        GeoDataFrame containing fish survey lake data
        
    Raises:
        FileNotFoundError: If fish survey file doesn't exist
        ValueError: If required fields are missing or data is invalid
    """
    logger.info(f"Loading fish survey data from {FISH_SURVEY_FILE}")
    
    if not FISH_SURVEY_FILE.exists():
        raise FileNotFoundError(f"Fish survey file not found: {FISH_SURVEY_FILE}")
    
    # Load the shapefile
    gdf = gpd.read_file(FISH_SURVEY_FILE)
    
    # Log basic info
    logger.info(f"Loaded {len(gdf)} fish survey lakes")
    logger.info(f"CRS: {gdf.crs}")
    logger.info(f"Columns: {list(gdf.columns)}")
    
    # Validate required fields
    required_fields = list(FISH_SURVEY_FIELDS.values())
    missing_fields = [field for field in required_fields if field not in gdf.columns]
    if missing_fields:
        raise ValueError(f"Missing required fields in fish survey data: {missing_fields}")
    
    # Validate DOWLKNUM format
    invalid_dowlknums = []
    for idx, dowlknum in enumerate(gdf[FISH_SURVEY_FIELDS['dowlknum']]):
        if not validate_dowlknum(str(dowlknum)):
            invalid_dowlknums.append((idx, dowlknum))
    
    if invalid_dowlknums:
        logger.warning(f"Found {len(invalid_dowlknums)} invalid DOWLKNUMs in fish survey data")
        for idx, dowlknum in invalid_dowlknums[:5]:  # Log first 5
            logger.warning(f"  Row {idx}: {dowlknum}")
    
    # Filter by lake area
    area_field = FISH_SURVEY_FIELDS['acres']
    original_count = len(gdf)
    
    gdf = gdf[
        (gdf[area_field] >= MIN_LAKE_AREA_ACRES) & 
        (gdf[area_field] <= MAX_LAKE_AREA_ACRES)
    ]
    
    filtered_count = len(gdf)
    if filtered_count < original_count:
        logger.info(f"Filtered out {original_count - filtered_count} lakes outside area range")
    
    # Ensure CRS is set correctly
    if gdf.crs is None:
        logger.warning("No CRS found in fish survey data, assuming EPSG:26915")
        gdf.set_crs(epsg=CRS_EPSG, inplace=True)
    elif gdf.crs.to_epsg() != CRS_EPSG:
        logger.info(f"Reprojecting fish survey data from {gdf.crs} to EPSG:{CRS_EPSG}")
        gdf = gdf.to_crs(epsg=CRS_EPSG)  # type: ignore
    
    # Basic data validation
    logger.info(f"Fish survey data bounds: {gdf.total_bounds}")
    logger.info(f"Lake area range: {gdf[area_field].min():.1f} to {gdf[area_field].max():.1f} acres")
    
    return gdf


def load_all_data() -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Load both bathymetry and fish survey datasets.
    
    Returns:
        Tuple of (bathymetry_gdf, fish_survey_gdf)
        
    Raises:
        FileNotFoundError: If either file doesn't exist
        ValueError: If required fields are missing or data is invalid
    """
    logger.info("Loading all shapefile data...")
    
    bathymetry_gdf = load_bathymetry_data()
    fish_survey_gdf = load_fish_survey_data()
    
    logger.info("Data loading completed successfully")
    logger.info(f"Bathymetry contours: {len(bathymetry_gdf)}")
    logger.info(f"Fish survey lakes: {len(fish_survey_gdf)}")
    
    return bathymetry_gdf, fish_survey_gdf


def inspect_data_sample(gdf: gpd.GeoDataFrame, name: str, sample_size: int = 3) -> None:
    """
    Log a sample of the data for inspection.
    
    Args:
        gdf: GeoDataFrame to inspect
        name: Name of the dataset for logging
        sample_size: Number of rows to show
    """
    logger.info(f"\n{name} data sample (first {sample_size} rows):")
    logger.info(f"Columns: {list(gdf.columns)}")
    
    # Show sample data (excluding geometry column)
    sample_data = gdf.head(sample_size).drop(columns=['geometry'])
    for idx, row in sample_data.iterrows():
        logger.info(f"Row {idx}: {dict(row)}")
    
    # Show geometry types
    geom_types = gdf.geometry.geom_type.value_counts()
    logger.info(f"Geometry types: {dict(geom_types)}")
