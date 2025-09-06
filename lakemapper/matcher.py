"""
Data matching module for LakeMapper.

This module handles finding lakes that exist in both bathymetry and fish survey datasets
by comparing their DOWLKNUM values.
"""

import logging
from typing import List, Set, Tuple, Dict, Any

import geopandas as gpd
import pandas as pd

from .config import BATHYMETRY_FIELDS, FISH_SURVEY_FIELDS
from .utils import validate_dowlknum


logger = logging.getLogger(__name__)


def find_matching_lakes(
    bathymetry_gdf: gpd.GeoDataFrame,
    fish_survey_gdf: gpd.GeoDataFrame
) -> Tuple[Set[str], Dict[str, Any]]:
    """
    Find lakes that exist in both bathymetry and fish survey datasets.
    
    Args:
        bathymetry_gdf: GeoDataFrame containing bathymetry contour data
        fish_survey_gdf: GeoDataFrame containing fish survey lake data
        
    Returns:
        Tuple of (matching_dowlknums, matching_stats)
    """
    logger.info("Finding lakes that exist in both datasets...")
    
    # Extract DOWLKNUMs from both datasets
    bathymetry_dowlknums = set()
    fish_survey_dowlknums = set()
    
    # Get bathymetry DOWLKNUMs
    bathymetry_field = BATHYMETRY_FIELDS['dowlknum']
    for dowlknum in bathymetry_gdf[bathymetry_field]:
        if validate_dowlknum(str(dowlknum)):
            bathymetry_dowlknums.add(str(dowlknum))
    
    # Get fish survey DOWLKNUMs
    fish_survey_field = FISH_SURVEY_FIELDS['dowlknum']
    for dowlknum in fish_survey_gdf[fish_survey_field]:
        if validate_dowlknum(str(dowlknum)):
            fish_survey_dowlknums.add(str(dowlknum))
    
    # Find intersection
    matching_dowlknums = bathymetry_dowlknums.intersection(fish_survey_dowlknums)
    
    # Calculate statistics
    stats = {
        'total_bathymetry_lakes': len(bathymetry_dowlknums),
        'total_fish_survey_lakes': len(fish_survey_dowlknums),
        'matching_lakes': len(matching_dowlknums),
        'bathymetry_only': len(bathymetry_dowlknums - fish_survey_dowlknums),
        'fish_survey_only': len(fish_survey_dowlknums - bathymetry_dowlknums),
        'match_percentage': (len(matching_dowlknums) / len(fish_survey_dowlknums)) * 100 if fish_survey_dowlknums else 0
    }
    
    # Log results
    logger.info(f"Found {len(matching_dowlknums)} lakes in both datasets")
    logger.info(f"Bathymetry only: {stats['bathymetry_only']}")
    logger.info(f"Fish survey only: {stats['fish_survey_only']}")
    logger.info(f"Match percentage: {stats['match_percentage']:.1f}%")
    
    if len(matching_dowlknums) == 0:
        logger.warning("No matching lakes found! Check data quality and DOWLKNUM formats.")
    
    return matching_dowlknums, stats


def filter_datasets_by_matching_lakes(
    bathymetry_gdf: gpd.GeoDataFrame,
    fish_survey_gdf: gpd.GeoDataFrame,
    matching_dowlknums: Set[str]
) -> Tuple[gpd.GeoDataFrame, gpd.GeoDataFrame]:
    """
    Filter both datasets to only include lakes that exist in both.
    
    Args:
        bathymetry_gdf: GeoDataFrame containing bathymetry contour data
        fish_survey_gdf: GeoDataFrame containing fish survey lake data
        matching_dowlknums: Set of DOWLKNUMs that exist in both datasets
        
    Returns:
        Tuple of (filtered_bathymetry_gdf, filtered_fish_survey_gdf)
    """
    logger.info(f"Filtering datasets to {len(matching_dowlknums)} matching lakes...")
    
    # Filter bathymetry data
    bathymetry_field = BATHYMETRY_FIELDS['dowlknum']
    bathymetry_mask = bathymetry_gdf[bathymetry_field].astype(str).isin(matching_dowlknums)
    filtered_bathymetry = bathymetry_gdf[bathymetry_mask].copy()
    
    # Filter fish survey data
    fish_survey_field = FISH_SURVEY_FIELDS['dowlknum']
    fish_survey_mask = fish_survey_gdf[fish_survey_field].astype(str).isin(matching_dowlknums)
    filtered_fish_survey = fish_survey_gdf[fish_survey_mask].copy()
    
    logger.info(f"Filtered bathymetry: {len(filtered_bathymetry)} contours")
    logger.info(f"Filtered fish survey: {len(filtered_fish_survey)} lakes")
    
    return filtered_bathymetry, filtered_fish_survey


def get_lake_summary(
    fish_survey_gdf: gpd.GeoDataFrame,
    matching_dowlknums: Set[str]
) -> pd.DataFrame:
    """
    Create a summary DataFrame of the matching lakes with key metadata.
    
    Args:
        fish_survey_gdf: GeoDataFrame containing fish survey lake data
        matching_dowlknums: Set of DOWLKNUMs that exist in both datasets
        
    Returns:
        DataFrame with lake summary information
    """
    logger.info("Creating lake summary...")
    
    # Filter to matching lakes
    fish_survey_field = FISH_SURVEY_FIELDS['dowlknum']
    mask = fish_survey_gdf[fish_survey_field].astype(str).isin(matching_dowlknums)
    matching_lakes = fish_survey_gdf[mask].copy()
    
    # Create summary DataFrame with available fields
    summary_columns = {
        'dowlknum': FISH_SURVEY_FIELDS['dowlknum'],
        'acres': FISH_SURVEY_FIELDS['acres'],
        'city_name': FISH_SURVEY_FIELDS['city_name'],
        'survey_url': FISH_SURVEY_FIELDS['survey_url']
    }
    
    # Add lake name if available, otherwise use basin name
    if 'PW_BASIN_N' in matching_lakes.columns:
        summary_columns['lake_name'] = 'PW_BASIN_N'
    elif 'LAKE_NAME' in matching_lakes.columns:
        summary_columns['lake_name'] = 'LAKE_NAME'
    else:
        summary_columns['lake_name'] = 'PW_BASIN_N'  # Default fallback
    
    summary_df = matching_lakes[list(summary_columns.values())].copy()
    summary_df.columns = list(summary_columns.keys())
    
    # Sort by lake area (largest first)
    summary_df = summary_df.sort_values('acres', ascending=False)
    
    logger.info(f"Created summary for {len(summary_df)} lakes")
    logger.info(f"Largest lake: {summary_df.iloc[0]['acres']:.1f} acres")
    logger.info(f"Smallest lake: {summary_df.iloc[-1]['acres']:.1f} acres")
    
    return summary_df


def validate_matching_data(
    bathymetry_gdf: gpd.GeoDataFrame,
    fish_survey_gdf: gpd.GeoDataFrame,
    matching_dowlknums: Set[str]
) -> Dict[str, Any]:
    """
    Perform validation checks on the matched data.
    
    Args:
        bathymetry_gdf: GeoDataFrame containing bathymetry contour data
        fish_survey_gdf: GeoDataFrame containing fish survey lake data
        matching_dowlknums: Set of DOWLKNUMs that exist in both datasets
        
    Returns:
        Dictionary containing validation results
    """
    logger.info("Validating matched data...")
    
    validation_results = {
        'total_matching_lakes': len(matching_dowlknums),
        'bathymetry_contours_per_lake': {},
        'geometry_types': {},
        'data_quality_issues': []
    }
    
    # Check bathymetry contours per lake
    bathymetry_field = BATHYMETRY_FIELDS['dowlknum']
    for dowlknum in matching_dowlknums:
        mask = bathymetry_gdf[bathymetry_field].astype(str) == dowlknum
        contour_count = mask.sum()
        validation_results['bathymetry_contours_per_lake'][dowlknum] = contour_count
        
        if contour_count == 0:
            validation_results['data_quality_issues'].append(
                f"Lake {dowlknum} has no bathymetry contours"
            )
    
    # Check geometry types
    validation_results['geometry_types']['bathymetry'] = dict(
        bathymetry_gdf.geometry.geom_type.value_counts()
    )
    validation_results['geometry_types']['fish_survey'] = dict(
        fish_survey_gdf.geometry.geom_type.value_counts()
    )
    
    # Log validation results
    logger.info(f"Validation complete for {len(matching_dowlknums)} lakes")
    logger.info(f"Bathymetry geometry types: {validation_results['geometry_types']['bathymetry']}")
    logger.info(f"Fish survey geometry types: {validation_results['geometry_types']['fish_survey']}")
    
    if validation_results['data_quality_issues']:
        logger.warning(f"Found {len(validation_results['data_quality_issues'])} data quality issues")
        for issue in validation_results['data_quality_issues'][:5]:  # Log first 5
            logger.warning(f"  {issue}")
    
    return validation_results 