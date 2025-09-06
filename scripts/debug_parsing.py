#!/usr/bin/env python3
"""
Debug script to investigate fish survey parsing issues.
"""

import sys
import json
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lakemapper.fish_survey_fetcher import fetch_fish_survey_data, parse_fish_survey_data
from lakemapper.utils import setup_logging

def debug_parsing():
    """Debug the fish survey parsing issue."""
    
    # Setup logging
    setup_logging()
    
    # Test with a known lake that should have data
    test_lake = "27000100"  # Mille Lacs
    
    print(f"Fetching data for lake {test_lake}...")
    raw_data = fetch_fish_survey_data(test_lake)
    
    print(f"Raw data type: {type(raw_data)}")
    if raw_data is None:
        print("Raw data is None")
        return
    
    print(f"Raw data keys: {list(raw_data.keys()) if isinstance(raw_data, dict) else 'Not a dict'}")
    
    if isinstance(raw_data, dict):
        print(f"Raw data structure:")
        print(json.dumps(raw_data, indent=2)[:1000] + "..." if len(json.dumps(raw_data)) > 1000 else json.dumps(raw_data, indent=2))
    
    print("\nAttempting to parse...")
    try:
        parsed_data = parse_fish_survey_data(raw_data)
        print(f"Parsed successfully: {parsed_data}")
    except Exception as e:
        print(f"Parsing failed: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_parsing() 