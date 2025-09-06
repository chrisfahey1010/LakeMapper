#!/usr/bin/env python3
"""
Test script for fish survey data fetching functionality.
"""

import sys
from pathlib import Path

# Add the lakemapper package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from lakemapper.fish_survey_fetcher import get_fish_survey_summary, batch_fetch_fish_surveys
from lakemapper.utils import setup_logging


def test_single_lake():
    """Test fetching fish survey data for a single lake."""
    print("Testing single lake fish survey fetch...")
    
    # Test with Pine Lake (DOWLKNUM 01000100)
    dowlknum = "01000100"
    survey_data = get_fish_survey_summary(dowlknum)
    
    if survey_data:
        print(f"✅ Successfully fetched fish survey data for lake {dowlknum}")
        print(f"   Survey date: {survey_data.get('survey_date')}")
        print(f"   Survey method: {survey_data.get('survey_method')}")
        print(f"   Survey type: {survey_data.get('survey_type')}")
        print(f"   Total fish caught: {survey_data.get('total_fish_caught')}")
        print(f"   Number of species: {len(survey_data.get('fish_species', []))}")
        
        # Show first few species
        for i, species in enumerate(survey_data.get('fish_species', [])[:3]):
            print(f"   Species {i+1}: {species.get('species_name')} - {species.get('count')} fish")
    else:
        print(f"❌ Failed to fetch fish survey data for lake {dowlknum}")


def test_batch_fetch():
    """Test batch fetching fish survey data for multiple lakes."""
    print("\nTesting batch fish survey fetch...")
    
    # Test with a few lakes
    test_lakes = ["01000100", "27013300", "48000200"]  # Pine Lake, Lake Minnetonka, Lake Mille Lacs
    
    survey_data = batch_fetch_fish_surveys(test_lakes, delay=1.0)
    
    print(f"Batch fetch results:")
    for dowlknum, data in survey_data.items():
        if data:
            print(f"  ✅ Lake {dowlknum}: {len(data.get('fish_species', []))} species, {data.get('total_fish_caught')} total fish")
        else:
            print(f"  ❌ Lake {dowlknum}: No data available")


def main():
    """Main test function."""
    # Set up logging
    setup_logging(level="INFO")
    
    print("LakeMapper Fish Survey Fetcher Test")
    print("=" * 50)
    
    # Test single lake fetch
    test_single_lake()
    
    # Test batch fetch
    test_batch_fetch()
    
    print("\nTest completed!")


if __name__ == "__main__":
    main() 