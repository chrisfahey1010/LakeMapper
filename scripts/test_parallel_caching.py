#!/usr/bin/env python3
"""
Test script for parallel processing and caching of fish survey data.

This script tests the enhanced fish survey fetcher with parallel processing
and caching capabilities.
"""

import sys
import time
import logging
from pathlib import Path

# Add the project root to the Python path
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from lakemapper.fish_survey_fetcher import (
    batch_fetch_fish_surveys, 
    clear_cache, 
    get_cache_stats
)
from lakemapper.utils import setup_logging

def test_parallel_caching():
    """Test parallel processing and caching functionality."""
    
    # Setup logging
    setup_logging()
    logger = logging.getLogger(__name__)
    
    # Test lakes (mix of lakes we know have data and some that might not)
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
    
    logger.info("=== Testing Parallel Processing and Caching ===")
    
    # Clear cache first
    logger.info("Clearing existing cache...")
    clear_cache()
    
    # Test 1: First run (should fetch from API)
    logger.info("\n--- Test 1: First run (API calls) ---")
    start_time = time.time()
    
    results1 = batch_fetch_fish_surveys(
        dowlknums=test_lakes,
        use_parallel=True,
        max_workers=5,
        use_cache=True
    )
    
    elapsed1 = time.time() - start_time
    successful1 = sum(1 for data in results1.values() if data is not None)
    
    logger.info(f"First run completed in {elapsed1:.2f} seconds")
    logger.info(f"Successful fetches: {successful1}/{len(test_lakes)}")
    
    # Check cache stats
    cache_stats = get_cache_stats()
    logger.info(f"Cache stats after first run: {cache_stats}")
    
    # Test 2: Second run (should use cache)
    logger.info("\n--- Test 2: Second run (should use cache) ---")
    start_time = time.time()
    
    results2 = batch_fetch_fish_surveys(
        dowlknums=test_lakes,
        use_parallel=True,
        max_workers=5,
        use_cache=True
    )
    
    elapsed2 = time.time() - start_time
    successful2 = sum(1 for data in results2.values() if data is not None)
    
    logger.info(f"Second run completed in {elapsed2:.2f} seconds")
    logger.info(f"Successful fetches: {successful2}/{len(test_lakes)}")
    
    # Test 3: Sequential run for comparison
    logger.info("\n--- Test 3: Sequential run (no parallel, no cache) ---")
    start_time = time.time()
    
    results3 = batch_fetch_fish_surveys(
        dowlknums=test_lakes[:5],  # Use fewer lakes for sequential test
        use_parallel=False,
        use_cache=False
    )
    
    elapsed3 = time.time() - start_time
    successful3 = sum(1 for data in results3.values() if data is not None)
    
    logger.info(f"Sequential run completed in {elapsed3:.2f} seconds")
    logger.info(f"Successful fetches: {successful3}/5")
    
    # Summary
    logger.info("\n=== Performance Summary ===")
    logger.info(f"Parallel with cache (first run): {elapsed1:.2f}s")
    logger.info(f"Parallel with cache (second run): {elapsed2:.2f}s")
    logger.info(f"Sequential without cache: {elapsed3:.2f}s")
    
    if elapsed1 > 0:
        speedup = elapsed3 / elapsed1
        logger.info(f"Parallel speedup over sequential: {speedup:.2f}x")
    
    if elapsed2 > 0:
        cache_speedup = elapsed1 / elapsed2
        logger.info(f"Cache speedup: {cache_speedup:.2f}x")
    
    # Show some sample data
    logger.info("\n=== Sample Data ===")
    for dowlknum, data in list(results1.items())[:3]:
        if data:
            logger.info(f"Lake {dowlknum}: {data.get('lake_name', 'Unknown')}")
            logger.info(f"  Fish species: {len(data.get('fish_species', []))}")
            logger.info(f"  Total fish count: {data.get('total_fish_count', 0)}")
        else:
            logger.info(f"Lake {dowlknum}: No data available")

if __name__ == "__main__":
    test_parallel_caching() 