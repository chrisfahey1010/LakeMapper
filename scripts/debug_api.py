#!/usr/bin/env python3
"""
Debug script to inspect the actual API response structure from DNR fish survey endpoints.
"""

import sys
import json
from pathlib import Path

# Add the lakemapper package to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

import requests
from lakemapper.config import REQUEST_TIMEOUT


def inspect_api_response(dowlknum: str):
    """Inspect the raw API response for a lake."""
    print(f"\n{'='*60}")
    print(f"INSPECTING API RESPONSE FOR LAKE {dowlknum}")
    print(f"{'='*60}")
    
    # Construct the API URL
    base_url = "https://maps.dnr.state.mn.us/cgi-bin/lakefinder/detail.cgi"
    params = {
        'type': 'lake_survey',
        'id': dowlknum
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
        
        print(f"URL: {response.url}")
        print(f"Status Code: {response.status_code}")
        print(f"Content Type: {response.headers.get('content-type', 'Unknown')}")
        print(f"Content Length: {len(response.content)} bytes")
        
        if response.status_code == 200:
            try:
                data = response.json()
                print(f"\nJSON Response Structure:")
                print(f"Top-level keys: {list(data.keys())}")
                
                # Show the full response (truncated if too long)
                response_text = json.dumps(data, indent=2)
                if len(response_text) > 2000:
                    print(f"Response (first 2000 chars):")
                    print(response_text[:2000] + "...")
                else:
                    print(f"Full Response:")
                    print(response_text)
                    
            except json.JSONDecodeError as e:
                print(f"Not JSON response: {e}")
                print(f"Raw response (first 500 chars):")
                print(response.text[:500])
        else:
            print(f"Error response: {response.text}")
            
    except Exception as e:
        print(f"Request failed: {e}")


def main():
    """Main function to inspect API responses."""
    print("DNR Fish Survey API Inspector")
    print("This will show the actual structure of the API responses.")
    
    # Test with the lakes you mentioned
    test_lakes = ["01000100", "27013300", "48000200"]
    
    for dowlknum in test_lakes:
        inspect_api_response(dowlknum)
    
    print(f"\n{'='*60}")
    print("INSPECTION COMPLETE")
    print(f"{'='*60}")


if __name__ == "__main__":
    main() 