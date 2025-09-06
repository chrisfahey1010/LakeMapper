#!/usr/bin/env python3
"""
Diagnostic script to inspect shapefile column names and data structure.
"""

import sys
from pathlib import Path

# Add the lakemapper package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import geopandas as gpd
from lakemapper.config import BATHYMETRY_FILE, FISH_SURVEY_FILE


def inspect_shapefile(file_path, name):
    """Inspect a shapefile and print its structure."""
    print(f"\n{'='*60}")
    print(f"INSPECTING {name.upper()} SHAPEFILE")
    print(f"{'='*60}")
    print(f"File: {file_path}")
    
    if not file_path.exists():
        print(f"ERROR: File not found!")
        return
    
    try:
        # Load the shapefile
        gdf = gpd.read_file(file_path)
        
        print(f"Successfully loaded {len(gdf)} records")
        print(f"CRS: {gdf.crs}")
        print(f"Geometry types: {gdf.geometry.geom_type.value_counts().to_dict()}")
        
        print(f"\nColumns ({len(gdf.columns)} total):")
        for i, col in enumerate(gdf.columns, 1):
            print(f"  {i:2d}. {col}")
        
        print(f"\nFirst 3 records:")
        for i, (idx, row) in enumerate(gdf.head(3).iterrows()):
            print(f"\nRecord {i+1} (index {idx}):")
            for col in gdf.columns:
                if col != 'geometry':
                    value = row[col]
                    # Truncate long values
                    if isinstance(value, str) and len(value) > 50:
                        value = value[:47] + "..."
                    print(f"  {col}: {value}")
        
        # Check for DOWLKNUM-like columns
        dowlknum_candidates = [col for col in gdf.columns if 'dowlknum' in col.lower() or 'dow' in col.lower()]
        if dowlknum_candidates:
            print(f"\nPotential DOWLKNUM columns: {dowlknum_candidates}")
        
        return gdf
        
    except Exception as e:
        print(f"ERROR loading shapefile: {e}")
        return None


def main():
    """Main function to inspect both shapefiles."""
    print("LakeMapper Data Inspection Tool")
    print("This will help identify the actual column names in your shapefiles.")
    
    # Inspect bathymetry data
    bathymetry_gdf = inspect_shapefile(BATHYMETRY_FILE, "bathymetry")
    
    # Inspect fish survey data
    fish_survey_gdf = inspect_shapefile(FISH_SURVEY_FILE, "fish survey")
    
    if bathymetry_gdf is not None and fish_survey_gdf is not None:
        print(f"\n{'='*60}")
        print("RECOMMENDATIONS")
        print(f"{'='*60}")
        
        # Find DOWLKNUM columns
        bath_dowlknum = [col for col in bathymetry_gdf.columns if 'dowlknum' in col.lower() or 'dow' in col.lower()]
        fish_dowlknum = [col for col in fish_survey_gdf.columns if 'dowlknum' in col.lower() or 'dow' in col.lower()]
        
        print(f"Bathymetry DOWLKNUM candidates: {bath_dowlknum}")
        print(f"Fish survey DOWLKNUM candidates: {fish_dowlknum}")
        
        # Check for other important fields
        print(f"\nBathymetry depth candidates: {[col for col in bathymetry_gdf.columns if 'depth' in col.lower()]}")
        print(f"Fish survey area candidates: {[col for col in fish_survey_gdf.columns if 'acre' in col.lower() or 'area' in col.lower()]}")
        print(f"Fish survey URL candidates: {[col for col in fish_survey_gdf.columns if 'url' in col.lower() or 'survey' in col.lower()]}")


if __name__ == "__main__":
    main() 