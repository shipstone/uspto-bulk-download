#!/usr/bin/env python3
"""
USPTO PTGRXML Download Functions

Maps patent numbers to weekly files and downloads them.
"""

import os
import re
import subprocess
from datetime import datetime
from typing import Dict, List, Tuple

# Patent number to grant date mapping (from IPTLpatents-complete.json)
PATENT_GRANT_DATES = {
    "US9294434B1": "2016-03-22",
    "US9391881B2": "2016-07-12", 
    "US9876757B2": "2018-01-23",
    "US10154005B2": "2018-12-11",
    "US10469444B2": "2019-11-05",
    "US10659430B2": "2020-05-19",
    "US11283790B2": "2022-03-22",
    "US11477276B2": "2022-10-18",
    "US11799690B2": "2023-10-24",
    "US12034799B2": "2024-07-09",
    "US12034800B2": "2024-07-09",
}


def grant_date_to_weekly_filename(grant_date: str) -> str:
    """
    Convert a grant date to the expected USPTO weekly filename.
    
    USPTO PTGRXML files are named: ipgYYMMDD.zip
    where YYMMDD is the Tuesday of that week (grant day).
    
    Args:
        grant_date: Date string in YYYY-MM-DD format
        
    Returns:
        Filename like "ipg160322.zip"
    """
    dt = datetime.strptime(grant_date, "%Y-%m-%d")
    # Format: ipgYYMMDD.zip
    return f"ipg{dt.strftime('%y%m%d')}.zip"


def get_required_files(patent_numbers: List[str]) -> Dict[str, List[str]]:
    """
    Get the set of weekly files needed for the given patents.
    
    Args:
        patent_numbers: List of patent numbers like "US9391881B2"
        
    Returns:
        Dict mapping filename to list of patent numbers in that file
    """
    files = {}
    for patent in patent_numbers:
        if patent not in PATENT_GRANT_DATES:
            print(f"Warning: No grant date for {patent}, skipping")
            continue
        
        grant_date = PATENT_GRANT_DATES[patent]
        filename = grant_date_to_weekly_filename(grant_date)
        
        if filename not in files:
            files[filename] = []
        files[filename].append(patent)
    
    return files


def download_file(filename: str, api_key: str, downloads_dir: str, 
                  script_path: str = "uspto_bulk_download.py") -> bool:
    """
    Download a specific USPTO PTGRXML file.
    
    Args:
        filename: File to download, e.g., "ipg160322.zip"
        api_key: USPTO API key
        downloads_dir: Directory to save downloads
        script_path: Path to the download script
        
    Returns:
        True if successful, False otherwise
    """
    os.makedirs(downloads_dir, exist_ok=True)
    
    output_path = os.path.join(downloads_dir, filename)
    if os.path.exists(output_path):
        print(f"  Already exists: {filename}")
        return True
    
    cmd = [
        "python3", script_path,
        "--api-key", api_key,
        "--download", "PTGRXML",
        "--file", filename,
        "--output", downloads_dir
    ]
    
    print(f"  Downloading: {filename}")
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=600)
        if result.returncode != 0:
            print(f"  Error: {result.stderr}")
            return False
        return os.path.exists(output_path)
    except subprocess.TimeoutExpired:
        print(f"  Timeout downloading {filename}")
        return False
    except Exception as e:
        print(f"  Exception: {e}")
        return False


def download_all_required(patent_numbers: List[str], api_key: str, 
                          downloads_dir: str, verbose: bool = False) -> Dict[str, str]:
    """
    Download all required USPTO weekly files for the given patents.
    
    Args:
        patent_numbers: List of patent numbers
        api_key: USPTO API key
        downloads_dir: Directory to save downloads
        verbose: Print detailed progress
        
    Returns:
        Dict mapping patent number to local file path
    """
    required_files = get_required_files(patent_numbers)
    
    print(f"Need to download {len(required_files)} USPTO weekly files:")
    for filename, patents in sorted(required_files.items()):
        print(f"  {filename}: {', '.join(patents)}")
    print()
    
    patent_to_file = {}
    
    for filename, patents in sorted(required_files.items()):
        success = download_file(filename, api_key, downloads_dir)
        if success:
            file_path = os.path.join(downloads_dir, filename)
            for patent in patents:
                patent_to_file[patent] = file_path
        else:
            print(f"  FAILED to download {filename}")
    
    return patent_to_file


def verify_downloads(patent_numbers: List[str], downloads_dir: str) -> Tuple[List[str], List[str]]:
    """
    Verify that all required files have been downloaded.
    
    Returns:
        Tuple of (found_patents, missing_patents)
    """
    required_files = get_required_files(patent_numbers)
    
    found = []
    missing = []
    
    for filename, patents in required_files.items():
        file_path = os.path.join(downloads_dir, filename)
        if os.path.exists(file_path):
            found.extend(patents)
        else:
            missing.extend(patents)
    
    return found, missing


if __name__ == "__main__":
    # Test the functions
    print("Testing USPTO download functions...")
    
    test_patents = list(PATENT_GRANT_DATES.keys())
    required = get_required_files(test_patents)
    
    print(f"\nRequired files for {len(test_patents)} patents:")
    for filename, patents in sorted(required.items()):
        print(f"  {filename}: {patents}")
    
    print(f"\nTotal unique files needed: {len(required)}")
