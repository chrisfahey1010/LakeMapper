"""
Data merger module for LakeMapper.

This module handles merging bathymetry contours for each lake using spatial operations
and buffering to create unified lake geometries.
"""

import logging
from typing import Dict, List, Tuple, Optional, Any

import geopandas as gpd
import pandas as pd
from shapely.geometry import Polygon, MultiPolygon
from shapely.ops import unary_union

from .config import BUFFER_DISTANCE_METERS, BATHYMETRY_FIELDS, FISH_SURVEY_FIELDS


logger = logging.getLogger(__name__)


def merge_bathymetry_for_lake(
    bathymetry_gdf: gpd.GeoDataFrame,
    fish_survey_geometry: Polygon,
    dowlknum: str
) -> Optional[Dict[str, Any]]:
    """
    Merge bathymetry contours for a single lake.
    
    Args:
        bathymetry_gdf: GeoDataFrame containing bathymetry contour data
        fish_survey_geometry: Polygon geometry of the fish survey lake outline
        dowlknum: DOWLKNUM of the lake to process
        
    Returns:
        Dictionary containing merged lake data or None if no contours found
    """
    logger.debug(f"Merging bathymetry for lake {dowlknum}")
    
    # Filter bathymetry data for this lake
    bathymetry_field = BATHYMETRY_FIELDS['dowlknum']
    lake_mask = bathymetry_gdf[bathymetry_field].astype(str) == dowlknum
    lake_bathymetry = bathymetry_gdf[lake_mask].copy()
    
    if len(lake_bathymetry) == 0:
        logger.warning(f"No bathymetry contours found for lake {dowlknum}")
        return None
    
    # Buffer the fish survey geometry to capture nearby contours
    buffered_geometry = fish_survey_geometry.buffer(BUFFER_DISTANCE_METERS)
    
    # Find contours that intersect with the buffered area
    intersecting_mask = lake_bathymetry.geometry.intersects(buffered_geometry)
    intersecting_contours = lake_bathymetry[intersecting_mask].copy()
    
    if len(intersecting_contours) == 0:
        logger.warning(f"No intersecting bathymetry contours found for lake {dowlknum}")
        return None
    
    # Merge all intersecting contours
    try:
        merged_geometry = unary_union(intersecting_contours.geometry.tolist())
        
        # Ensure we have a valid geometry
        if merged_geometry.is_empty:
            logger.warning(f"Merged geometry is empty for lake {dowlknum}")
            return None
        
        # Convert to MultiPolygon if it's a single Polygon
        if isinstance(merged_geometry, Polygon):
            merged_geometry = MultiPolygon([merged_geometry])
        
        # Create merged lake data
        merged_lake_data = {
            'dowlknum': dowlknum,
            'geometry': merged_geometry,
            'contour_count': len(intersecting_contours),
            'depth_range': {
                'min': float(intersecting_contours[BATHYMETRY_FIELDS['depth']].min()),
                'max': float(intersecting_contours[BATHYMETRY_FIELDS['depth']].max())
            },
            'lake_name': intersecting_contours[BATHYMETRY_FIELDS['lake_name']].iloc[0] if len(intersecting_contours) > 0 and BATHYMETRY_FIELDS['lake_name'] in intersecting_contours.columns else None,
            'original_contours': intersecting_contours
        }
        
        logger.debug(f"Successfully merged {len(intersecting_contours)} contours for lake {dowlknum}")
        return merged_lake_data
        
    except Exception as e:
        logger.error(f"Error merging bathymetry for lake {dowlknum}: {e}")
        return None


def merge_all_lakes(
    bathymetry_gdf: gpd.GeoDataFrame,
    fish_survey_gdf: gpd.GeoDataFrame,
    matching_dowlknums: List[str]
) -> Tuple[List[Dict[str, Any]], Dict[str, Any]]:
    """
    Merge bathymetry contours for all matching lakes.
    
    Args:
        bathymetry_gdf: GeoDataFrame containing bathymetry contour data
        fish_survey_gdf: GeoDataFrame containing fish survey lake data
        matching_dowlknums: List of DOWLKNUMs to process
        
    Returns:
        Tuple of (merged_lakes, processing_stats)
    """
    logger.info(f"Starting bathymetry merging for {len(matching_dowlknums)} lakes...")
    
    merged_lakes = []
    processing_stats = {
        'total_lakes': len(matching_dowlknums),
        'successful_merges': 0,
        'failed_merges': 0,
        'lakes_with_no_contours': 0,
        'lakes_with_no_intersection': 0,
        'error_details': []
    }
    
    # Process each lake
    for i, dowlknum in enumerate(matching_dowlknums):
        if (i + 1) % 100 == 0:
            logger.info(f"Processed {i + 1}/{len(matching_dowlknums)} lakes...")
        
        try:
            # Get fish survey geometry for this lake
            fish_survey_field = FISH_SURVEY_FIELDS['dowlknum']
            lake_mask = fish_survey_gdf[fish_survey_field].astype(str) == dowlknum
            lake_fish_survey = fish_survey_gdf[lake_mask]
            
            if len(lake_fish_survey) == 0:
                logger.warning(f"No fish survey data found for lake {dowlknum}")
                processing_stats['failed_merges'] += 1
                processing_stats['error_details'].append(f"Lake {dowlknum}: No fish survey data")
                continue
            
            fish_survey_geometry = lake_fish_survey.geometry.iloc[0]
            
            # Merge bathymetry for this lake
            merged_lake_data = merge_bathymetry_for_lake(
                bathymetry_gdf, fish_survey_geometry, dowlknum
            )
            
            if merged_lake_data is None:
                processing_stats['failed_merges'] += 1
                continue
            
            # Add fish survey metadata to the merged lake data
            merged_lake_data.update({
                'acres': lake_fish_survey[FISH_SURVEY_FIELDS['acres']].iloc[0],
                'city_name': lake_fish_survey[FISH_SURVEY_FIELDS['city_name']].iloc[0],
                'survey_url': lake_fish_survey[FISH_SURVEY_FIELDS['survey_url']].iloc[0]
            })
            
            # Add lake name from fish survey if not available from bathymetry
            if not merged_lake_data.get('lake_name') and 'PW_BASIN_N' in lake_fish_survey.columns:
                merged_lake_data['lake_name'] = lake_fish_survey['PW_BASIN_N'].iloc[0]
            
            merged_lakes.append(merged_lake_data)
            processing_stats['successful_merges'] += 1
            
        except Exception as e:
            logger.error(f"Error processing lake {dowlknum}: {e}")
            processing_stats['failed_merges'] += 1
            processing_stats['error_details'].append(f"Lake {dowlknum}: {str(e)}")
    
    # Log final statistics
    logger.info(f"Merging completed:")
    logger.info(f"  Successful: {processing_stats['successful_merges']}")
    logger.info(f"  Failed: {processing_stats['failed_merges']}")
    logger.info(f"  Success rate: {(processing_stats['successful_merges'] / len(matching_dowlknums)) * 100:.1f}%")
    
    return merged_lakes, processing_stats


def create_merged_geodataframe(
    merged_lakes: List[Dict[str, Any]],
    fish_survey_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Create a GeoDataFrame from the merged lake data.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        fish_survey_gdf: Original fish survey GeoDataFrame for additional metadata
        
    Returns:
        GeoDataFrame containing merged lake geometries and metadata
    """
    logger.info(f"Creating GeoDataFrame from {len(merged_lakes)} merged lakes...")
    
    # Prepare data for GeoDataFrame
    data = []
    for lake_data in merged_lakes:
        # Get additional metadata from fish survey data
        fish_survey_field = FISH_SURVEY_FIELDS['dowlknum']
        lake_mask = fish_survey_gdf[fish_survey_field].astype(str) == lake_data['dowlknum']
        fish_survey_row = fish_survey_gdf[lake_mask]
        
        if len(fish_survey_row) > 0:
            # Get lake name from fish survey data if available
            lake_name = lake_data.get('lake_name')
            if not lake_name and 'PW_BASIN_N' in fish_survey_row.columns:
                lake_name = fish_survey_row['PW_BASIN_N'].iloc[0]
            
            row_data = {
                'dowlknum': lake_data['dowlknum'],
                'geometry': lake_data['geometry'],
                'lake_name': lake_name,
                'contour_count': lake_data['contour_count'],
                'min_depth': lake_data['depth_range']['min'],
                'max_depth': lake_data['depth_range']['max'],
                'acres': lake_data['acres'],
                'city_name': lake_data['city_name'],
                'survey_url': lake_data['survey_url']
            }
            data.append(row_data)
    
    # Create GeoDataFrame
    if data:
        merged_gdf = gpd.GeoDataFrame(data, crs=fish_survey_gdf.crs)
        logger.info(f"Created GeoDataFrame with {len(merged_gdf)} lakes")
        return merged_gdf
    else:
        logger.warning("No data to create GeoDataFrame")
        return gpd.GeoDataFrame()


def validate_merged_geometries(
    merged_lakes: List[Dict[str, Any]]
) -> Dict[str, Any]:
    """
    Validate the merged lake geometries.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        
    Returns:
        Dictionary containing validation results
    """
    logger.info("Validating merged geometries...")
    
    validation_results = {
        'total_lakes': len(merged_lakes),
        'valid_geometries': 0,
        'invalid_geometries': 0,
        'empty_geometries': 0,
        'geometry_types': {},
        'area_statistics': {
            'min_area': float('inf'),
            'max_area': 0,
            'total_area': 0
        },
        'issues': []
    }
    
    for lake_data in merged_lakes:
        geometry = lake_data['geometry']
        
        # Check if geometry is valid
        if geometry.is_valid:
            validation_results['valid_geometries'] += 1
        else:
            validation_results['invalid_geometries'] += 1
            validation_results['issues'].append(
                f"Lake {lake_data['dowlknum']}: Invalid geometry"
            )
        
        # Check if geometry is empty
        if geometry.is_empty:
            validation_results['empty_geometries'] += 1
            validation_results['issues'].append(
                f"Lake {lake_data['dowlknum']}: Empty geometry"
            )
        
        # Record geometry type
        geom_type = geometry.geom_type
        validation_results['geometry_types'][geom_type] = validation_results['geometry_types'].get(geom_type, 0) + 1
        
        # Calculate area statistics
        area = geometry.area
        validation_results['area_statistics']['min_area'] = min(
            validation_results['area_statistics']['min_area'], area
        )
        validation_results['area_statistics']['max_area'] = max(
            validation_results['area_statistics']['max_area'], area
        )
        validation_results['area_statistics']['total_area'] += area
    
    # Handle case where no valid geometries were found
    if validation_results['area_statistics']['min_area'] == float('inf'):
        validation_results['area_statistics']['min_area'] = 0
    
    # Log validation results
    logger.info(f"Geometry validation complete:")
    logger.info(f"  Valid: {validation_results['valid_geometries']}")
    logger.info(f"  Invalid: {validation_results['invalid_geometries']}")
    logger.info(f"  Empty: {validation_results['empty_geometries']}")
    logger.info(f"  Geometry types: {validation_results['geometry_types']}")
    
    if validation_results['issues']:
        logger.warning(f"Found {len(validation_results['issues'])} geometry issues")
        for issue in validation_results['issues'][:5]:  # Log first 5
            logger.warning(f"  {issue}")
    
    return validation_results 