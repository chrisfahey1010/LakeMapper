"""
Fish survey data fetcher module for LakeMapper.

This module handles fetching fish survey data from the Minnesota DNR's JSON API
endpoints for each lake.
"""

import json
import logging
import time
import os
from typing import Dict, List, Optional, Any
from urllib.parse import urljoin
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import requests

from .config import REQUEST_TIMEOUT, MAX_RETRIES, MAX_WORKERS, CACHE_DIR


logger = logging.getLogger(__name__)


def fetch_fish_survey_data(dowlknum: str) -> Optional[Dict[str, Any]]:
    """
    Fetch fish survey data for a specific lake from the DNR API.
    
    Args:
        dowlknum: The DOWLKNUM identifier for the lake
        
    Returns:
        Dictionary containing fish survey data or None if fetch failed
    """
    # Construct the API URL
    base_url = "https://maps.dnr.state.mn.us/cgi-bin/lakefinder/detail.cgi"
    params = {
        'type': 'lake_survey',
        'id': dowlknum
    }
    
    logger.debug(f"Fetching fish survey data for lake {dowlknum}")
    
    for attempt in range(MAX_RETRIES):
        try:
            response = requests.get(
                base_url,
                params=params,
                timeout=REQUEST_TIMEOUT,
                headers={
                    'User-Agent': 'LakeMapper/1.0 (Minnesota DNR Lake Data Processing Tool)'
                }
            )
            
            # Check if request was successful
            if response.status_code == 200:
                try:
                    data = response.json()
                    logger.debug(f"Successfully fetched fish survey data for lake {dowlknum}")
                    return data
                except json.JSONDecodeError as e:
                    logger.warning(f"Invalid JSON response for lake {dowlknum}: {e}")
                    return None
            
            elif response.status_code == 404:
                logger.debug(f"No fish survey data available for lake {dowlknum}")
                return None
            
            else:
                logger.warning(f"HTTP {response.status_code} for lake {dowlknum}")
                if attempt < MAX_RETRIES - 1:
                    time.sleep(1)  # Brief delay before retry
                    continue
                return None
                
        except requests.exceptions.Timeout:
            logger.warning(f"Timeout fetching fish survey data for lake {dowlknum}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(2)  # Longer delay for timeout
                continue
            return None
            
        except requests.exceptions.RequestException as e:
            logger.warning(f"Request error for lake {dowlknum}: {e}")
            if attempt < MAX_RETRIES - 1:
                time.sleep(1)
                continue
            return None
    
    logger.error(f"Failed to fetch fish survey data for lake {dowlknum} after {MAX_RETRIES} attempts")
    return None


def parse_fish_survey_data(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """
    Parse and extract relevant fish survey data from the raw API response.
    
    Args:
        raw_data: Raw JSON data from the DNR API
        
    Returns:
        Dictionary containing parsed fish survey data
    """
    parsed_data = {
        'survey_date': None,
        'survey_method': None,
        'survey_type': None,
        'fish_species': [],
        'total_fish_caught': 0
    }
    
    try:
        # The API response has the structure: {"status": "SUCCESS", "result": {...}}
        if 'result' not in raw_data:
            logger.warning("No 'result' key found in API response")
            return parsed_data
        
        result = raw_data['result']
        
        # Check if result is a dictionary (some lakes return None or string for result)
        if not isinstance(result, dict):
            logger.warning(f"Result is not a dictionary (type: {type(result)}) - lake may not have fish survey data")
            return parsed_data
        
        # Extract survey data from the 'surveys' array
        if 'surveys' in result and result['surveys']:
            surveys = result['surveys']
            
            # Find the best survey to use
            selected_survey = None
            
            # First, try to find the most recent Standard Survey with fish data
            standard_surveys = [
                s for s in surveys 
                if s.get('surveyType') == 'Standard Survey' 
                and s.get('fishCatchSummaries') 
                and len(s.get('fishCatchSummaries', [])) > 0
            ]
            
            if standard_surveys:
                # Sort by date (most recent first) and take the first one
                standard_surveys.sort(key=lambda x: x.get('surveyDate', ''), reverse=True)
                selected_survey = standard_surveys[0]
                logger.debug(f"Selected Standard Survey from {selected_survey.get('surveyDate')}")
            
            # If no Standard Survey with fish data, try Targeted Surveys
            if not selected_survey:
                targeted_surveys = [
                    s for s in surveys 
                    if s.get('surveyType') == 'Targeted Survey' 
                    and s.get('fishCatchSummaries') 
                    and len(s.get('fishCatchSummaries', [])) > 0
                ]
                
                if targeted_surveys:
                    # Sort by date (most recent first) and take the first one
                    targeted_surveys.sort(key=lambda x: x.get('surveyDate', ''), reverse=True)
                    selected_survey = targeted_surveys[0]
                    logger.debug(f"Selected Targeted Survey from {selected_survey.get('surveyDate')}")
            
            # If still no survey, just take the first survey with any fish data
            if not selected_survey:
                for survey in surveys:
                    if survey.get('fishCatchSummaries') and len(survey.get('fishCatchSummaries', [])) > 0:
                        selected_survey = survey
                        logger.debug(f"Selected fallback survey from {survey.get('surveyDate')}")
                        break
            
            if selected_survey:
                parsed_data['survey_date'] = selected_survey.get('surveyDate')
                parsed_data['survey_method'] = selected_survey.get('surveyMethod')
                parsed_data['survey_type'] = selected_survey.get('surveyType')
                
                # Extract fish catch summaries
                if 'fishCatchSummaries' in selected_survey:
                    total_fish = 0
                    
                    for catch_summary in selected_survey['fishCatchSummaries']:
                        species_info = {
                            'species_name': catch_summary.get('species', 'Unknown'),
                            'count': catch_summary.get('totalCatch', 0),
                            'length_stats': {
                                'average': None,  # Not provided in this API
                                'minimum': None,  # Not provided in this API
                                'maximum': None   # Not provided in this API
                            },
                            'weight_stats': {
                                'average': catch_summary.get('averageWeight'),
                                'total': catch_summary.get('totalWeight'),
                                'quartile': catch_summary.get('quartileWeight')
                            },
                            'gear': catch_summary.get('gear', 'Unknown'),
                            'cpue': catch_summary.get('CPUE')  # Catch per unit effort
                        }
                        
                        # Convert weight values to float if they exist
                        for key in ['average', 'total']:
                            value = species_info['weight_stats'][key]
                            if value is not None:
                                try:
                                    species_info['weight_stats'][key] = float(value)
                                except (ValueError, TypeError):
                                    species_info['weight_stats'][key] = None
                        
                        # Convert CPUE to float if it exists
                        cpue_value = species_info['cpue']
                        if cpue_value is not None:
                            try:
                                species_info['cpue'] = float(cpue_value)
                            except (ValueError, TypeError):
                                species_info['cpue'] = None
                        
                        parsed_data['fish_species'].append(species_info)
                        total_fish += species_info['count']
                    
                    parsed_data['total_fish_caught'] = total_fish
            else:
                logger.warning("No surveys with fish data found")
        else:
            logger.debug("No surveys found in result")
        
        logger.debug(f"Parsed fish survey data: {len(parsed_data['fish_species'])} species, {parsed_data['total_fish_caught']} total fish")
        
    except Exception as e:
        logger.error(f"Error parsing fish survey data: {e}")
        return {
            'survey_date': None,
            'survey_method': None,
            'survey_type': None,
            'fish_species': [],
            'total_fish_caught': 0,
            'parse_error': str(e)
        }
    
    return parsed_data


def get_fish_survey_summary(dowlknum: str, use_cache: bool = True) -> Optional[Dict[str, Any]]:
    """
    Get fish survey summary data for a lake by DOWLKNUM.
    
    Args:
        dowlknum: DOWLKNUM identifier (e.g., "27000100")
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary with fish survey summary data or None if not found/error
    """
    # Check cache first if enabled
    if use_cache:
        cached_data = _load_from_cache(dowlknum)
        if cached_data is not None:
            return cached_data
    
    # Fetch from API
    raw_data = fetch_fish_survey_data(dowlknum)
    
    if raw_data is None:
        # Return a default structure for lakes without fish survey data
        default_data = {
            'dowlknum': dowlknum,
            'survey_date': None,
            'survey_method': None,
            'survey_type': None,
            'fish_species': [],
            'total_fish_caught': 0,
            'fetch_timestamp': time.time(),
            'no_data_available': True
        }
        
        # Cache the default data to avoid repeated API calls
        if use_cache:
            _save_to_cache(dowlknum, default_data)
        
        return default_data
    
    survey_data = parse_fish_survey_data(raw_data)
    
    # Add metadata
    survey_data['dowlknum'] = dowlknum
    survey_data['fetch_timestamp'] = time.time()
    
    # Cache the result if we got data
    if use_cache and survey_data is not None:
        _save_to_cache(dowlknum, survey_data)
    
    return survey_data


def batch_fetch_fish_surveys_parallel(
    dowlknums: List[str], 
    max_workers: Optional[int] = None,
    delay: float = 0.1,
    use_cache: bool = True
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch fish survey data for multiple lakes using parallel processing.
    
    Args:
        dowlknums: List of DOWLKNUM identifiers
        max_workers: Maximum number of worker threads (defaults to config value)
        delay: Delay between requests in seconds (reduced for parallel processing)
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary mapping DOWLKNUM to fish survey data (or None if failed)
    """
    logger.info(f"Fetching fish survey data for {len(dowlknums)} lakes using parallel processing...")
    
    max_workers = max_workers or MAX_WORKERS
    results = {}
    
    def fetch_single_lake(dowlknum: str) -> tuple[str, Optional[Dict[str, Any]]]:
        """Fetch data for a single lake with delay."""
        time.sleep(delay)  # Rate limiting
        survey_data = get_fish_survey_summary(dowlknum, use_cache=use_cache)
        return dowlknum, survey_data
    
    # Use ThreadPoolExecutor for parallel processing
    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        # Submit all tasks
        future_to_dowlknum = {
            executor.submit(fetch_single_lake, dowlknum): dowlknum 
            for dowlknum in dowlknums
        }
        
        # Process completed tasks
        completed = 0
        for future in as_completed(future_to_dowlknum):
            try:
                dowlknum, survey_data = future.result()
                results[dowlknum] = survey_data
                completed += 1
                
                if completed % 50 == 0:
                    logger.info(f"Completed {completed}/{len(dowlknums)} lakes...")
                    
            except Exception as e:
                dowlknum = future_to_dowlknum[future]
                logger.error(f"Error fetching data for lake {dowlknum}: {e}")
                results[dowlknum] = None
    
    # Log summary
    successful_fetches = sum(1 for data in results.values() if data is not None)
    logger.info(f"Parallel fish survey fetch complete: {successful_fetches}/{len(dowlknums)} successful")
    
    return results


def batch_fetch_fish_surveys(
    dowlknums: List[str], 
    delay: float = 0.5,
    use_parallel: bool = True,
    max_workers: Optional[int] = None,
    use_cache: bool = True
) -> Dict[str, Optional[Dict[str, Any]]]:
    """
    Fetch fish survey data for multiple lakes with optional parallel processing and caching.
    
    Args:
        dowlknums: List of DOWLKNUM identifiers
        delay: Delay between requests in seconds
        use_parallel: Whether to use parallel processing
        max_workers: Maximum number of worker threads (for parallel processing)
        use_cache: Whether to use cached data if available
        
    Returns:
        Dictionary mapping DOWLKNUM to fish survey data (or None if failed)
    """
    if use_cache:
        cache_stats = get_cache_stats()
        logger.info(f"Cache stats: {cache_stats['fresh_files']} fresh, {cache_stats['expired_files']} expired files")
    
    if use_parallel and len(dowlknums) > 1:
        return batch_fetch_fish_surveys_parallel(dowlknums, max_workers, delay, use_cache)
    else:
        # Fall back to sequential processing for small batches or when parallel is disabled
        logger.info(f"Fetching fish survey data for {len(dowlknums)} lakes...")
        
        results = {}
        
        for i, dowlknum in enumerate(dowlknums):
            if (i + 1) % 50 == 0:
                logger.info(f"Fetched fish survey data for {i + 1}/{len(dowlknums)} lakes...")
            
            survey_data = get_fish_survey_summary(dowlknum, use_cache=use_cache)
            results[dowlknum] = survey_data
            
            # Rate limiting
            if i < len(dowlknums) - 1:  # Don't delay after the last request
                time.sleep(delay)
        
        # Log summary
        successful_fetches = sum(1 for data in results.values() if data is not None)
        logger.info(f"Fish survey fetch complete: {successful_fetches}/{len(dowlknums)} successful")
        
        return results


# Ensure cache directory exists
def _ensure_cache_dir():
    """Ensure the cache directory exists."""
    cache_path = Path(CACHE_DIR)
    cache_path.mkdir(exist_ok=True)
    return cache_path

def _get_cache_file_path(dowlknum: str) -> Path:
    """Get the cache file path for a given DOWLKNUM."""
    cache_dir = _ensure_cache_dir()
    return cache_dir / f"fish_survey_{dowlknum}.json"

def _load_from_cache(dowlknum: str) -> Optional[Dict[str, Any]]:
    """
    Load fish survey data from cache if available and not expired.
    
    Args:
        dowlknum: DOWLKNUM identifier
        
    Returns:
        Cached data if available and fresh, None otherwise
    """
    cache_file = _get_cache_file_path(dowlknum)
    
    if not cache_file.exists():
        return None
    
    try:
        # Check if cache is fresh (less than 24 hours old)
        cache_age = time.time() - cache_file.stat().st_mtime
        if cache_age > 24 * 60 * 60:  # 24 hours in seconds
            logger.debug(f"Cache for lake {dowlknum} is expired, will refetch")
            return None
        
        with open(cache_file, 'r') as f:
            data = json.load(f)
            logger.debug(f"Loaded fish survey data for lake {dowlknum} from cache")
            return data
            
    except (json.JSONDecodeError, IOError) as e:
        logger.warning(f"Error reading cache for lake {dowlknum}: {e}")
        return None

def _save_to_cache(dowlknum: str, data: Dict[str, Any]) -> None:
    """
    Save fish survey data to cache.
    
    Args:
        dowlknum: DOWLKNUM identifier
        data: Fish survey data to cache
    """
    if data is None:
        return
    
    cache_file = _get_cache_file_path(dowlknum)
    
    try:
        with open(cache_file, 'w') as f:
            json.dump(data, f, indent=2)
        logger.debug(f"Saved fish survey data for lake {dowlknum} to cache")
    except IOError as e:
        logger.warning(f"Error saving cache for lake {dowlknum}: {e}")

def clear_cache() -> None:
    """Clear all cached fish survey data."""
    cache_dir = _ensure_cache_dir()
    cache_files = list(cache_dir.glob("fish_survey_*.json"))
    
    for cache_file in cache_files:
        try:
            cache_file.unlink()
            logger.debug(f"Deleted cache file: {cache_file}")
        except IOError as e:
            logger.warning(f"Error deleting cache file {cache_file}: {e}")
    
    logger.info(f"Cleared {len(cache_files)} cached fish survey files")

def get_cache_stats() -> Dict[str, int]:
    """Get statistics about the cache."""
    cache_dir = _ensure_cache_dir()
    cache_files = list(cache_dir.glob("fish_survey_*.json"))
    
    total_files = len(cache_files)
    fresh_files = 0
    
    current_time = time.time()
    for cache_file in cache_files:
        cache_age = current_time - cache_file.stat().st_mtime
        if cache_age <= 24 * 60 * 60:  # 24 hours
            fresh_files += 1
    
    return {
        "total_files": total_files,
        "fresh_files": fresh_files,
        "expired_files": total_files - fresh_files
    } 