#!/usr/bin/env python3
"""
Debug script to test multiple lakes and identify parsing issues.
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lakemapper.fish_survey_fetcher import fetch_fish_survey_data, parse_fish_survey_data
from lakemapper.utils import setup_logging

def debug_multiple_lakes():
    """Debug fish survey parsing for multiple lakes."""
    
    # Setup logging
    setup_logging()
    
    # Test lakes from our parallel test
    test_lakes = [
        "27000100",  # Mille Lacs Lake
        "27000200",  # Lake of the Woods
        "27000300",  # Leech Lake
        "27000400",  # Winnibigoshish
        "27000500",  # Vermilion
        "27000600",  # Rainy Lake
        "27000700",  # Kabetogama
        "27000800",  # Namakan
        "27000900",  # Sand Point
        "27001000",  # Crane Lake
    ]
    
    for i, dowlknum in enumerate(test_lakes):
        print(f"\n{'='*60}")
        print(f"Testing lake {i+1}/{len(test_lakes)}: {dowlknum}")
        print(f"{'='*60}")
        
        try:
            # Fetch raw data
            print(f"Fetching data for lake {dowlknum}...")
            raw_data = fetch_fish_survey_data(dowlknum)
            
            print(f"Raw data type: {type(raw_data)}")
            if raw_data is None:
                print("Raw data is None - lake has no fish survey data")
                continue
            
            print(f"Raw data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
            
            # Check if result exists
            if isinstance(raw_data, dict) and 'result' in raw_data:
                result = raw_data['result']
                print(f"Result keys: {list(result.keys()) if isinstance(result, dict) else 'Result is not a dict'}")
                
                if isinstance(result, dict) and 'surveys' in result:
                    surveys = result['surveys']
                    print(f"Surveys type: {type(surveys)}")
                    if surveys is None:
                        print("Surveys is None - this is likely the issue!")
                    elif isinstance(surveys, list):
                        print(f"Number of surveys: {len(surveys)}")
                        if len(surveys) > 0:
                            print(f"First survey keys: {list(surveys[0].keys()) if isinstance(surveys[0], dict) else 'First survey is not a dict'}")
                else:
                    print("No 'surveys' key in result")
            else:
                print("No 'result' key in raw data")
            
            # Try to parse
            print(f"\nAttempting to parse...")
            parsed_data = parse_fish_survey_data(raw_data)
            print(f"Parsed successfully: {len(parsed_data.get('fish_species', []))} species, {parsed_data.get('total_fish_caught', 0)} total fish")
            
        except Exception as e:
            print(f"Error processing lake {dowlknum}: {e}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    debug_multiple_lakes() 