#!/usr/bin/env python3
"""
USPTO Open Data Portal Bulk Data Download Script

This script interfaces with the USPTO ODP API to:
1. Search/list available bulk data products
2. Get product details and file listings
3. Download bulk data files

API Documentation: https://data.uspto.gov/apis/bulk-data/search
Requires: API Key from https://data.uspto.gov/myodp/key-reveal

Usage:
    python uspto_bulk_download.py --list                    # List all products
    python uspto_bulk_download.py --product PTGRXML         # Show product details
    python uspto_bulk_download.py --download PTGRXML --file ipg260113.zip --output ./downloads
"""

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Optional
import urllib.request
import urllib.error
from urllib.parse import urlparse, quote

# Configuration
API_BASE_URL = "https://api.uspto.gov/api/v1/datasets/products"
DEFAULT_API_KEY = os.environ.get("USPTO_API_KEY", "")


def make_request(url: str, api_key: str) -> dict:
    """Make authenticated request to USPTO API."""
    headers = {
        "X-API-Key": api_key,
        "Accept": "application/json",
        "User-Agent": "USPTO-Bulk-Downloader/1.0"
    }
    
    req = urllib.request.Request(url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=60) as response:
            return json.loads(response.read().decode('utf-8'))
    except urllib.error.HTTPError as e:
        print(f"HTTP Error {e.code}: {e.reason}", file=sys.stderr)
        if e.code == 403:
            print("Access denied. Check your API key.", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"URL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def list_products(api_key: str, search_term: Optional[str] = None) -> None:
    """List all available bulk data products."""
    url = f"{API_BASE_URL}/search"
    if search_term:
        url += f"?productTitle={quote(search_term)}"
    
    data = make_request(url, api_key)
    
    print(f"\nFound {data['count']} products:\n")
    print(f"{'ID':<15} {'Title':<60} {'Frequency':<10} {'Files':<8}")
    print("-" * 100)
    
    for product in data.get('bulkDataProductBag', []):
        prod_id = product.get('productIdentifier', 'N/A')
        title = product.get('productTitleText', 'N/A')[:58]
        freq = product.get('productFrequencyText', 'N/A')
        file_count = product.get('productFileTotalQuantity', 0)
        print(f"{prod_id:<15} {title:<60} {freq:<10} {file_count:<8}")


def get_product_details(api_key: str, product_id: str, show_files: bool = True) -> dict:
    """Get details for a specific product."""
    url = f"{API_BASE_URL}/{product_id}"
    data = make_request(url, api_key)
    
    if not data.get('bulkDataProductBag'):
        print(f"Product '{product_id}' not found.", file=sys.stderr)
        sys.exit(1)
    
    product = data['bulkDataProductBag'][0]
    
    print(f"\n{'='*80}")
    print(f"Product: {product.get('productTitleText', 'N/A')}")
    print(f"{'='*80}")
    print(f"ID:          {product.get('productIdentifier')}")
    print(f"Description: {product.get('productDescriptionText', 'N/A')[:200]}...")
    print(f"Frequency:   {product.get('productFrequencyText', 'N/A')}")
    print(f"Day:         {product.get('daysOfWeekText', 'N/A')}")
    print(f"Date Range:  {product.get('productFromDate')} to {product.get('productToDate')}")
    print(f"Total Size:  {product.get('productTotalFileSize', 0) / (1024**3):.2f} GB")
    print(f"File Count:  {product.get('productFileTotalQuantity', 0)}")
    print(f"MIME Types:  {', '.join(product.get('mimeTypeIdentifierArrayText', []))}")
    print(f"Last Update: {product.get('lastModifiedDateTime', 'N/A')}")
    
    if show_files and product.get('productFileBag'):
        file_bag = product['productFileBag']
        files = file_bag.get('fileDataBag', [])[:20]  # Show first 20 files
        
        print(f"\nRecent Files (showing {len(files)} of {file_bag.get('count', 0)}):")
        print(f"{'Filename':<45} {'Size (MB)':<12} {'Date':<12}")
        print("-" * 70)
        
        for f in files:
            name = f.get('fileName', 'N/A')[:43]
            size = f.get('fileSize', 0) / (1024**2)
            date = f.get('fileDataFromDate', 'N/A')
            print(f"{name:<45} {size:<12.2f} {date:<12}")
    
    return product


def format_size(size_bytes: int) -> str:
    """Format bytes to human readable string."""
    for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
        if size_bytes < 1024:
            return f"{size_bytes:.2f} {unit}"
        size_bytes /= 1024
    return f"{size_bytes:.2f} PB"


def download_file(api_key: str, product_id: str, filename: str, output_dir: str) -> None:
    """Download a specific file from a product."""
    # First get the product to find the exact download URL
    url = f"{API_BASE_URL}/{product_id}"
    data = make_request(url, api_key)
    
    if not data.get('bulkDataProductBag'):
        print(f"Product '{product_id}' not found.", file=sys.stderr)
        sys.exit(1)
    
    product = data['bulkDataProductBag'][0]
    file_bag = product.get('productFileBag', {})
    files = file_bag.get('fileDataBag', [])
    
    # Find the file
    target_file = None
    for f in files:
        if f.get('fileName') == filename:
            target_file = f
            break
    
    if not target_file:
        print(f"File '{filename}' not found in product '{product_id}'.", file=sys.stderr)
        print(f"Available files (first 10):", file=sys.stderr)
        for f in files[:10]:
            print(f"  - {f.get('fileName')}", file=sys.stderr)
        sys.exit(1)
    
    download_url = target_file.get('fileDownloadURI')
    file_size = target_file.get('fileSize', 0)
    
    print(f"\nDownloading: {filename}")
    print(f"Size: {format_size(file_size)}")
    print(f"URL: {download_url}")
    
    # Create output directory
    output_path = Path(output_dir)
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / filename
    
    # Download with progress - the API returns a redirect to a presigned CloudFront URL
    headers = {
        "X-API-Key": api_key,
        "User-Agent": "USPTO-Bulk-Downloader/1.0"
    }
    
    # URL-encode the download URL (handle spaces and special chars in filenames)
    parsed = urlparse(download_url)
    encoded_path = quote(parsed.path, safe='/')
    encoded_url = f"{parsed.scheme}://{parsed.netloc}{encoded_path}"
    
    req = urllib.request.Request(encoded_url, headers=headers)
    
    try:
        with urllib.request.urlopen(req, timeout=300) as response:
            # Get final URL (after redirect)
            final_url = response.geturl()
            total_size = int(response.headers.get('content-length', file_size))
            
            print(f"Downloading from: {final_url[:80]}...")
            print(f"Saving to: {output_file}")
            
            downloaded = 0
            chunk_size = 1024 * 1024  # 1MB chunks
            
            with open(output_file, 'wb') as f:
                while True:
                    chunk = response.read(chunk_size)
                    if not chunk:
                        break
                    f.write(chunk)
                    downloaded += len(chunk)
                    
                    # Progress indicator
                    if total_size > 0:
                        pct = (downloaded / total_size) * 100
                        print(f"\rProgress: {pct:.1f}% ({format_size(downloaded)} / {format_size(total_size)})", end='', flush=True)
            
            print(f"\n\n✓ Download complete: {output_file}")
            
    except urllib.error.HTTPError as e:
        print(f"\nHTTP Error {e.code}: {e.reason}", file=sys.stderr)
        sys.exit(1)
    except urllib.error.URLError as e:
        print(f"\nURL Error: {e.reason}", file=sys.stderr)
        sys.exit(1)


def main():
    parser = argparse.ArgumentParser(
        description="USPTO Open Data Portal Bulk Data Download Tool",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --list                                      # List all available products
  %(prog)s --list --search "Patent Grant"              # Search for specific products
  %(prog)s --product PTGRXML                           # Show product details and recent files
  %(prog)s --download PTGRXML --file ipg260113.zip     # Download a specific file
  
Environment:
  USPTO_API_KEY    Set your API key (or use --api-key)
  
Get an API key at: https://data.uspto.gov/myodp/key-reveal
        """
    )
    
    parser.add_argument('--api-key', '-k', 
                        default=DEFAULT_API_KEY,
                        help='USPTO API key (or set USPTO_API_KEY env var)')
    
    parser.add_argument('--list', '-l', 
                        action='store_true',
                        help='List available bulk data products')
    
    parser.add_argument('--search', '-s',
                        help='Search term for filtering products (use with --list)')
    
    parser.add_argument('--product', '-p',
                        help='Show details for a specific product ID')
    
    parser.add_argument('--download', '-d',
                        help='Product ID to download from')
    
    parser.add_argument('--file', '-f',
                        help='Filename to download (use with --download)')
    
    parser.add_argument('--output', '-o',
                        default='./downloads',
                        help='Output directory for downloads (default: ./downloads)')
    
    parser.add_argument('--json', '-j',
                        action='store_true',
                        help='Output raw JSON (for product details)')
    
    args = parser.parse_args()
    
    # Validate API key
    if not args.api_key:
        print("Error: API key required. Set USPTO_API_KEY or use --api-key", file=sys.stderr)
        print("Get an API key at: https://data.uspto.gov/myodp/key-reveal", file=sys.stderr)
        sys.exit(1)
    
    # Handle commands
    if args.list:
        list_products(args.api_key, args.search)
    
    elif args.product:
        product = get_product_details(args.api_key, args.product)
        if args.json:
            print(json.dumps(product, indent=2))
    
    elif args.download:
        if not args.file:
            print("Error: --file required with --download", file=sys.stderr)
            sys.exit(1)
        download_file(args.api_key, args.download, args.file, args.output)
    
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
