"""
Data exporter module for LakeMapper.

This module handles exporting merged lake data to various formats including
GeoJSON, metadata JSON, and raster formats.
"""

import json
import logging
from pathlib import Path
from typing import Dict, List, Any, Optional

import geopandas as gpd
import pandas as pd
import numpy as np

from .config import GEOJSON_DIR, METADATA_DIR, RASTER_DIR, CONTOURS_DIR
from .utils import format_lake_filename, ensure_directories


logger = logging.getLogger(__name__)


def export_lake_geojson(
    lake_data: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Path:
    """
    Export a single lake to GeoJSON format.
    
    Args:
        lake_data: Dictionary containing lake data with geometry and metadata
        output_dir: Optional output directory (defaults to GEOJSON_DIR)
        
    Returns:
        Path to the exported GeoJSON file
    """
    ensure_directories()
    output_dir = output_dir or GEOJSON_DIR
    
    dowlknum = lake_data['dowlknum']
    filename = format_lake_filename(dowlknum, "geojson")
    output_path = output_dir / filename
    
    # Create GeoDataFrame for this lake and reproject to WGS84 for web maps
    lake_gdf = gpd.GeoDataFrame([lake_data], crs="EPSG:26915")
    lake_gdf_wgs84 = lake_gdf.to_crs(epsg=4326)
    
    # Export to GeoJSON
    lake_gdf_wgs84.to_file(output_path, driver="GeoJSON")
    
    logger.debug(f"Exported lake {dowlknum} to {output_path}")
    return output_path


def export_lake_contours_geojson(
    lake_data: Dict[str, Any],
    output_dir: Optional[Path] = None
) -> Optional[Path]:
    """
    Export the original bathymetry contours for a single lake as GeoJSON.
    
    Args:
        lake_data: Dictionary containing lake data with 'original_contours' GeoDataFrame
        output_dir: Optional output directory (defaults to CONTOURS_DIR)
        
    Returns:
        Path to the exported GeoJSON file, or None if no contours are available
    """
    ensure_directories()
    output_dir = output_dir or CONTOURS_DIR
    dowlknum = lake_data['dowlknum']
    contours_gdf = lake_data.get('original_contours')
    
    if contours_gdf is None or len(contours_gdf) == 0:
        logger.debug(f"No original contours to export for lake {dowlknum}")
        return None
    
    # Filename pattern distinct from merged polygons
    filename = f"contours_{dowlknum}.geojson"
    output_path = output_dir / filename
    
    try:
        # Ensure CRS is set for export
        if contours_gdf.crs is None:
            contours_gdf.set_crs("EPSG:26915", inplace=True)
        contours_wgs84 = contours_gdf.to_crs(epsg=4326)
        contours_wgs84.to_file(output_path, driver="GeoJSON")
        logger.debug(f"Exported contours for lake {dowlknum} to {output_path}")
        return output_path
    except Exception as e:
        logger.error(f"Failed to export contours for lake {dowlknum}: {e}")
        return None


def export_lake_metadata(
    lake_data: Dict[str, Any],
    fish_survey_data: Optional[Dict[str, Any]] = None,
    output_dir: Optional[Path] = None
) -> Path:
    """
    Export lake metadata to JSON format.
    
    Args:
        lake_data: Dictionary containing lake data
        fish_survey_data: Optional fish survey data from DNR API
        output_dir: Optional output directory (defaults to METADATA_DIR)
        
    Returns:
        Path to the exported JSON file
    """
    ensure_directories()
    output_dir = output_dir or METADATA_DIR
    
    dowlknum = lake_data['dowlknum']
    filename = format_lake_filename(dowlknum, "json")
    output_path = output_dir / filename
    
    # Prepare metadata (exclude geometry and large objects)
    geometry = lake_data.get('geometry')
    metadata = {
        'dowlknum': lake_data['dowlknum'],
        'lake_name': lake_data.get('lake_name'),
        'contour_count': lake_data.get('contour_count'),
        'depth_range': lake_data.get('depth_range'),
        'acres': lake_data.get('acres'),
        'city_name': lake_data.get('city_name'),
        'survey_url': lake_data.get('survey_url'),
        'geometry_type': geometry.geom_type if geometry else None,
        'area_sq_meters': float(geometry.area) if geometry else None,
        'export_timestamp': pd.Timestamp.now().isoformat()
    }
    
    # Add fish survey data if available
    if fish_survey_data:
        metadata['fish_survey'] = fish_survey_data
    else:
        metadata['fish_survey'] = None
    
    # Export to JSON
    with open(output_path, 'w') as f:
        json.dump(metadata, f, indent=2)
    
    logger.debug(f"Exported metadata for lake {dowlknum} to {output_path}")
    return output_path


def export_all_lakes(
    merged_lakes: List[Dict[str, Any]],
    export_geojson: bool = True,
    export_metadata: bool = True,
    export_raster: bool = False,
    export_contours: bool = True,
    include_fish_surveys: bool = True
) -> Dict[str, Any]:
    """
    Export all merged lakes to the specified formats.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        export_geojson: Whether to export GeoJSON files
        export_metadata: Whether to export metadata JSON files
        export_raster: Whether to export raster files (not implemented yet)
        include_fish_surveys: Whether to fetch and include fish survey data
        
    Returns:
        Dictionary containing export statistics
    """
    logger.info(f"Starting export of {len(merged_lakes)} lakes...")
    
    ensure_directories()
    
    # Fetch fish survey data if requested
    fish_survey_data = {}
    if include_fish_surveys and export_metadata:
        logger.info("Fetching fish survey data from DNR API with parallel processing and caching...")
        from .fish_survey_fetcher import batch_fetch_fish_surveys, get_cache_stats
        
        dowlknums = [lake_data['dowlknum'] for lake_data in merged_lakes]
        
        # Use enhanced batch fetching with parallel processing and caching
        fish_survey_data = batch_fetch_fish_surveys(
            dowlknums=dowlknums,
            use_parallel=True,
            max_workers=10,  # Use more workers for faster processing
            use_cache=True,
            delay=0.1  # Reduced delay for parallel processing
        )
        
        # Log cache statistics
        cache_stats = get_cache_stats()
        logger.info(f"Fish survey cache stats: {cache_stats['fresh_files']} fresh, {cache_stats['expired_files']} expired files")
    
    export_stats = {
        'total_lakes': len(merged_lakes),
        'geojson_exported': 0,
        'metadata_exported': 0,
        'raster_exported': 0,
        'contours_exported': 0,
        'failed_exports': 0,
        'fish_surveys_fetched': len([data for data in fish_survey_data.values() if data is not None]),
        'exported_files': []
    }
    
    for i, lake_data in enumerate(merged_lakes):
        if (i + 1) % 50 == 0:
            logger.info(f"Exported {i + 1}/{len(merged_lakes)} lakes...")
        
        try:
            dowlknum = lake_data['dowlknum']
            
            # Export GeoJSON
            if export_geojson:
                try:
                    geojson_path = export_lake_geojson(lake_data)
                    export_stats['geojson_exported'] += 1
                    export_stats['exported_files'].append(str(geojson_path))
                except Exception as e:
                    logger.error(f"Failed to export GeoJSON for lake {dowlknum}: {e}")
                    export_stats['failed_exports'] += 1
            
            # Export metadata
            if export_metadata:
                try:
                    # Get fish survey data for this lake
                    lake_fish_survey = fish_survey_data.get(dowlknum)
                    metadata_path = export_lake_metadata(lake_data, lake_fish_survey)
                    export_stats['metadata_exported'] += 1
                    export_stats['exported_files'].append(str(metadata_path))
                except Exception as e:
                    logger.error(f"Failed to export metadata for lake {dowlknum}: {e}")
                    export_stats['failed_exports'] += 1
            
            # Export original contours GeoJSON for UI mapping
            if export_contours:
                try:
                    contours_path = export_lake_contours_geojson(lake_data)
                    if contours_path is not None:
                        export_stats['contours_exported'] += 1
                        export_stats['exported_files'].append(str(contours_path))
                except Exception as e:
                    logger.error(f"Failed to export contours for lake {dowlknum}: {e}")
                    export_stats['failed_exports'] += 1
            
            # Export raster (placeholder for future implementation)
            if export_raster:
                logger.warning("Raster export not yet implemented")
                export_stats['raster_exported'] += 0  # Placeholder
                
        except Exception as e:
            logger.error(f"Failed to export lake {lake_data.get('dowlknum', 'unknown')}: {e}")
            export_stats['failed_exports'] += 1
    
    # Log final statistics
    logger.info(f"Export completed:")
    logger.info(f"  GeoJSON: {export_stats['geojson_exported']}")
    logger.info(f"  Metadata: {export_stats['metadata_exported']}")
    logger.info(f"  Raster: {export_stats['raster_exported']}")
    logger.info(f"  Contours: {export_stats['contours_exported']}")
    logger.info(f"  Fish surveys: {export_stats['fish_surveys_fetched']}")
    logger.info(f"  Failed: {export_stats['failed_exports']}")
    
    return export_stats


def export_merged_geodataframe(
    merged_gdf: gpd.GeoDataFrame,
    output_path: Optional[Path] = None
) -> Path:
    """
    Export the complete merged GeoDataFrame to a single file.
    
    Args:
        merged_gdf: GeoDataFrame containing all merged lakes
        output_path: Optional output path (defaults to output/merged_lakes.geojson)
        
    Returns:
        Path to the exported file
    """
    ensure_directories()
    
    if output_path is None:
        output_path = Path("output") / "merged_lakes.geojson"
    
    logger.info(f"Exporting merged GeoDataFrame to {output_path}")
    
    # Reproject to WGS84 for web maps and export to GeoJSON
    merged_wgs84 = merged_gdf.to_crs(epsg=4326)
    merged_wgs84.to_file(output_path, driver="GeoJSON")
    
    logger.info(f"Successfully exported {len(merged_gdf)} lakes to {output_path}")
    return output_path


def export_summary_report(
    merged_lakes: List[Dict[str, Any]],
    matching_stats: Dict[str, Any],
    processing_stats: Dict[str, Any],
    export_stats: Dict[str, Any],
    output_path: Optional[Path] = None
) -> Path:
    """
    Export a comprehensive summary report of the processing pipeline.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        matching_stats: Statistics from the matching process
        processing_stats: Statistics from the merging process
        export_stats: Statistics from the export process
        output_path: Optional output path (defaults to output/summary_report.json)
        
    Returns:
        Path to the exported report
    """
    ensure_directories()
    
    if output_path is None:
        output_path = Path("output") / "summary_report.json"
    
    logger.info(f"Exporting summary report to {output_path}")
    
    # Calculate additional statistics
    lake_areas = [lake_data.get('geometry', {}).area for lake_data in merged_lakes if lake_data.get('geometry')]
    depth_ranges = [lake_data.get('depth_range', {}) for lake_data in merged_lakes if lake_data.get('depth_range')]
    
    summary_report = {
        'pipeline_summary': {
            'total_processing_time': None,  # Would be calculated if timing was implemented
            'total_lakes_processed': len(merged_lakes),
            'success_rate': (len(merged_lakes) / matching_stats.get('matching_lakes', 1)) * 100
        },
        'matching_statistics': matching_stats,
        'processing_statistics': processing_stats,
        'export_statistics': export_stats,
        'lake_statistics': {
            'total_lakes': len(merged_lakes),
            'area_statistics': {
                'min_area_sq_meters': min(lake_areas) if lake_areas else 0,
                'max_area_sq_meters': max(lake_areas) if lake_areas else 0,
                'mean_area_sq_meters': np.mean(lake_areas) if lake_areas else 0,
                'total_area_sq_meters': sum(lake_areas) if lake_areas else 0
            },
            'depth_statistics': {
                'min_depth': min([dr.get('min', float('inf')) for dr in depth_ranges]) if depth_ranges else 0,
                'max_depth': max([dr.get('max', 0) for dr in depth_ranges]) if depth_ranges else 0,
                'mean_min_depth': np.mean([dr.get('min', 0) for dr in depth_ranges]) if depth_ranges else 0,
                'mean_max_depth': np.mean([dr.get('max', 0) for dr in depth_ranges]) if depth_ranges else 0
            },
            'contour_statistics': {
                'min_contours': min([lake_data.get('contour_count', 0) for lake_data in merged_lakes]) if merged_lakes else 0,
                'max_contours': max([lake_data.get('contour_count', 0) for lake_data in merged_lakes]) if merged_lakes else 0,
                'mean_contours': np.mean([lake_data.get('contour_count', 0) for lake_data in merged_lakes]) if merged_lakes else 0
            }
        },
        'export_timestamp': pd.Timestamp.now().isoformat(),
        'lake_list': [
            {
                'dowlknum': lake_data['dowlknum'],
                'lake_name': lake_data.get('lake_name'),
                'acres': lake_data.get('acres'),
                'city_name': lake_data.get('city_name'),
                'contour_count': lake_data.get('contour_count'),
                'depth_range': lake_data.get('depth_range')
            }
            for lake_data in merged_lakes
        ]
    }
    
    # Export to JSON
    with open(output_path, 'w') as f:
        json.dump(summary_report, f, indent=2)
    
    logger.info(f"Successfully exported summary report to {output_path}")
    return output_path


def create_lake_index(
    merged_lakes: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a simple index file listing all processed lakes.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        output_path: Optional output path (defaults to output/lake_index.csv)
        
    Returns:
        Path to the exported index file
    """
    ensure_directories()
    
    if output_path is None:
        output_path = Path("output") / "lake_index.csv"
    
    logger.info(f"Creating lake index at {output_path}")
    
    # Create index data
    index_data = []
    for lake_data in merged_lakes:
        index_data.append({
            'dowlknum': lake_data['dowlknum'],
            'lake_name': lake_data.get('lake_name', 'Unknown'),
            'acres': lake_data.get('acres', 0.0),
            'city_name': lake_data.get('city_name', 'Unknown'),
            'contour_count': lake_data.get('contour_count', 0),
            'min_depth': lake_data.get('depth_range', {}).get('min', 0.0),
            'max_depth': lake_data.get('depth_range', {}).get('max', 0.0),
            'geojson_file': format_lake_filename(lake_data['dowlknum'], "geojson"),
            'metadata_file': format_lake_filename(lake_data['dowlknum'], "json"),
            'contours_file': f"contours_{lake_data['dowlknum']}.geojson"
        })
    
    # Create DataFrame and export
    index_df = pd.DataFrame(index_data)
    index_df = index_df.sort_values('acres', ascending=False)
    index_df.to_csv(output_path, index=False)
    
    logger.info(f"Successfully created lake index with {len(index_df)} lakes")
    return output_path 


def create_lake_index_json(
    merged_lakes: List[Dict[str, Any]],
    output_path: Optional[Path] = None
) -> Path:
    """
    Create a JSON index listing all processed lakes for frontend consumption.
    
    Args:
        merged_lakes: List of merged lake data dictionaries
        output_path: Optional output path (defaults to output/lake_index.json)
        
    Returns:
        Path to the exported JSON file
    """
    ensure_directories()
    
    if output_path is None:
        output_path = Path("output") / "lake_index.json"
    
    logger.info(f"Creating lake index JSON at {output_path}")
    
    index_records: List[Dict[str, Any]] = []
    for lake_data in merged_lakes:
        index_records.append({
            'dowlknum': lake_data['dowlknum'],
            'lake_name': lake_data.get('lake_name', 'Unknown'),
            'acres': lake_data.get('acres', 0.0),
            'city_name': lake_data.get('city_name', 'Unknown'),
            'contour_count': lake_data.get('contour_count', 0),
            'min_depth': lake_data.get('depth_range', {}).get('min', 0.0),
            'max_depth': lake_data.get('depth_range', {}).get('max', 0.0),
            'geojson_file': format_lake_filename(lake_data['dowlknum'], "geojson"),
            'metadata_file': format_lake_filename(lake_data['dowlknum'], "json"),
            'contours_file': f"contours_{lake_data['dowlknum']}.geojson"
        })
    
    # Sort by acres descending
    index_records.sort(key=lambda r: r.get('acres', 0.0), reverse=True)
    
    with open(output_path, 'w') as f:
        json.dump(index_records, f, indent=2)
    
    logger.info(f"Successfully created JSON lake index with {len(index_records)} lakes")
    return output_path