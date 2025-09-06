#!/usr/bin/env python3
"""
Debug script to inspect Mille Lacs survey data structure in detail.
"""

import sys
import json
from pathlib import Path

# Add the lakemapper package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from lakemapper.config import REQUEST_TIMEOUT


def inspect_mille_lacs_surveys():
    """Inspect Mille Lacs survey data in detail."""
    print("Mille Lacs Survey Data Inspector")
    print("=" * 60)
    
    # Fetch Mille Lacs data
    base_url = "https://maps.dnr.state.mn.us/cgi-bin/lakefinder/detail.cgi"
    params = {
        'type': 'lake_survey',
        'id': '48000200'
    }
    
    try:
        response = requests.get(
            base_url,
            params=params,
            timeout=REQUEST_TIMEOUT,
            headers={
                'User-Agent': 'LakeMapper/1.0 (Minnesota DNR Lake Data Processing Tool)'
            }
        )
        
        if response.status_code == 200:
            data = response.json()
            result = data.get('result', {})
            
            print(f"Lake Name: {result.get('lakeName', 'Unknown')}")
            print(f"Area (acres): {result.get('areaAcres', 'Unknown')}")
            print(f"Max Depth (feet): {result.get('maxDepthFeet', 'Unknown')}")
            
            surveys = result.get('surveys', [])
            print(f"\nNumber of surveys: {len(surveys)}")
            
            for i, survey in enumerate(surveys):
                print(f"\n--- Survey {i+1} ---")
                print(f"Survey ID: {survey.get('surveyID', 'Unknown')}")
                print(f"Survey Date: {survey.get('surveyDate', 'Unknown')}")
                print(f"Survey Method: {survey.get('surveyMethod', 'Unknown')}")
                print(f"Survey Type: {survey.get('surveyType', 'Unknown')}")
                
                fish_summaries = survey.get('fishCatchSummaries', [])
                print(f"Fish catch summaries: {len(fish_summaries)}")
                
                if fish_summaries:
                    print("  Fish species found:")
                    for j, summary in enumerate(fish_summaries[:5]):  # Show first 5
                        print(f"    {j+1}. {summary.get('species', 'Unknown')} - {summary.get('totalCatch', 0)} fish")
                    if len(fish_summaries) > 5:
                        print(f"    ... and {len(fish_summaries) - 5} more species")
                else:
                    print("  No fish catch summaries found")
                
                # Show all keys in the survey
                print(f"  Survey keys: {list(survey.keys())}")
            
            # Look for any other fish-related data
            print(f"\n--- Other Result Keys ---")
            for key, value in result.items():
                if 'fish' in key.lower() or 'catch' in key.lower() or 'species' in key.lower():
                    print(f"{key}: {type(value)} - {str(value)[:100]}...")
                    
        else:
            print(f"Error: HTTP {response.status_code}")
            
    except Exception as e:
        print(f"Request failed: {e}")


if __name__ == "__main__":
    inspect_mille_lacs_surveys() 