#!/usr/bin/env python3
"""
Main orchestrator script for LakeMapper.

This script coordinates the entire data processing pipeline:
1. Load bathymetry and fish survey shapefiles
2. Find matching lakes between datasets
3. Merge bathymetry contours for each lake
4. Export results to various formats
"""

import sys
import time
from pathlib import Path

# Add the lakemapper package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lakemapper.utils import setup_logging, ensure_directories
from lakemapper.loader import load_all_data, inspect_data_sample
from lakemapper.matcher import (
    find_matching_lakes, 
    filter_datasets_by_matching_lakes,
    get_lake_summary,
    validate_matching_data
)
from lakemapper.merger import (
    merge_all_lakes,
    create_merged_geodataframe,
    validate_merged_geometries
)
from lakemapper.exporter import (
    export_all_lakes,
    export_merged_geodataframe,
    export_summary_report,
    create_lake_index,
    create_lake_index_json
)


def main():
    """Main execution function for the LakeMapper pipeline."""
    
    # Set up logging
    logger = setup_logging()
    logger.info("Starting LakeMapper data processing pipeline")
    
    # Ensure output directories exist
    ensure_directories()
    
    start_time = time.time()
    
    try:
        # Step 1: Load data
        logger.info("=" * 60)
        logger.info("STEP 1: Loading shapefile data")
        logger.info("=" * 60)
        
        bathymetry_gdf, fish_survey_gdf = load_all_data()
        
        # Inspect data samples
        inspect_data_sample(bathymetry_gdf, "Bathymetry", 3)
        inspect_data_sample(fish_survey_gdf, "Fish Survey", 3)
        
        # Step 2: Find matching lakes
        logger.info("=" * 60)
        logger.info("STEP 2: Finding matching lakes")
        logger.info("=" * 60)
        
        matching_dowlknums, matching_stats = find_matching_lakes(
            bathymetry_gdf, fish_survey_gdf
        )
        
        if len(matching_dowlknums) == 0:
            logger.error("No matching lakes found! Exiting.")
            return 1
        
        # Filter datasets to only include matching lakes
        filtered_bathymetry, filtered_fish_survey = filter_datasets_by_matching_lakes(
            bathymetry_gdf, fish_survey_gdf, matching_dowlknums
        )
        
        # Create lake summary
        lake_summary = get_lake_summary(fish_survey_gdf, matching_dowlknums)
        logger.info(f"\nTop 5 largest lakes:")
        for _, row in lake_summary.head().iterrows():
            logger.info(f"  {row['lake_name'] or 'Unknown'} ({row['dowlknum']}): {row['acres']:.1f} acres")
        
        # Validate matching data
        validation_results = validate_matching_data(
            filtered_bathymetry, filtered_fish_survey, matching_dowlknums
        )
        
        # Step 3: Merge bathymetry contours
        logger.info("=" * 60)
        logger.info("STEP 3: Merging bathymetry contours")
        logger.info("=" * 60)
        
        merged_lakes, processing_stats = merge_all_lakes(
            filtered_bathymetry, filtered_fish_survey, list(matching_dowlknums)
        )
        
        if len(merged_lakes) == 0:
            logger.error("No lakes were successfully merged! Exiting.")
            return 1
        
        # Validate merged geometries
        geometry_validation = validate_merged_geometries(merged_lakes)
        
        # Create merged GeoDataFrame
        merged_gdf = create_merged_geodataframe(merged_lakes, filtered_fish_survey)
        
        # Step 4: Export results
        logger.info("=" * 60)
        logger.info("STEP 4: Exporting results")
        logger.info("=" * 60)
        
        # Export individual lake files
        export_stats = export_all_lakes(
            merged_lakes,
            export_geojson=True,
            export_metadata=True,
            export_raster=False,
            export_contours=True,
            include_fish_surveys=True
        )
        
        # Export merged GeoDataFrame
        merged_gdf_path = export_merged_geodataframe(merged_gdf)
        
        # Export summary report
        summary_report_path = export_summary_report(
            merged_lakes, matching_stats, processing_stats, export_stats
        )
        
        # Create lake index
        lake_index_path = create_lake_index(merged_lakes)
        lake_index_json_path = create_lake_index_json(merged_lakes)
        
        # Final summary
        end_time = time.time()
        processing_time = end_time - start_time
        
        logger.info("=" * 60)
        logger.info("PIPELINE COMPLETED SUCCESSFULLY")
        logger.info("=" * 60)
        logger.info(f"Processing time: {processing_time:.2f} seconds")
        logger.info(f"Total lakes processed: {len(merged_lakes)}")
        logger.info(f"Success rate: {(len(merged_lakes) / len(matching_dowlknums)) * 100:.1f}%")
        logger.info(f"Files exported: {export_stats['geojson_exported']} GeoJSON, {export_stats['metadata_exported']} metadata")
        logger.info(f"Output files:")
        logger.info(f"  Merged GeoDataFrame: {merged_gdf_path}")
        logger.info(f"  Summary report: {summary_report_path}")
        logger.info(f"  Lake index: {lake_index_path}")
        logger.info(f"  Lake index (JSON): {lake_index_json_path}")
        logger.info(f"  Individual files: output/geojson/ and output/metadata/")
        
        return 0
        
    except Exception as e:
        logger.error(f"Pipeline failed with error: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
