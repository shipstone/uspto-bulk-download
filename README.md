# USPTO Bulk Data Download Tool

A Python command-line tool for downloading bulk patent and trademark data from the USPTO Open Data Portal (ODP) API.

## Features

- **List Products**: Browse all 40+ available bulk data products
- **Search**: Filter products by title
- **Product Details**: View file listings, sizes, and dates
- **Download**: Download files with progress indication
- **No Dependencies**: Uses Python standard library only

## Requirements

- Python 3.7+
- USPTO API Key (free)

## Quick Start

### 1. Get an API Key

1. Go to https://data.uspto.gov/myodp/key-reveal
2. Sign in with your USPTO.gov account (or create one)
3. Copy your API key

### 2. Set Environment Variable (Recommended)

```bash
export USPTO_API_KEY="your-api-key-here"
```

### 3. Run the Tool

```bash
# List all available products
python3 uspto_bulk_download.py --list

# View product details
python3 uspto_bulk_download.py --product PTGRXML

# Download a file
python3 uspto_bulk_download.py --download PTGRXML --file ipg260113.zip
```

## Usage

### List All Products

```bash
python3 uspto_bulk_download.py --api-key YOUR_KEY --list
```

Output:
```
Found 40 products:

ID              Title                                                        Frequency  Files
----------------------------------------------------------------------------------------------------
PTGRXML         Patent Grant Full-Text Data (No Images) - XML                WEEKLY     1288
APPDT           Patent Application Full Text Data with Embedded TIFF Image   WEEKLY     1931
PTGRDT          Patent Grant Full Text Data with Embedded TIFF Images        WEEKLY     1606
...
```

### Search Products

```bash
python3 uspto_bulk_download.py --list --search "Patent Grant"
```

### View Product Details

```bash
python3 uspto_bulk_download.py --product PTGRXML
```

Output:
```
================================================================================
Product: Patent Grant Full-Text Data (No Images) - XML
================================================================================
ID:          PTGRXML
Description: Provides the bulk zip files that contains the concatenated full-text...
Frequency:   WEEKLY
Day:         TUESDAY
Date Range:  2002-01-01 to 2026-01-13
Total Size:  114.84 GB
File Count:  1288
MIME Types:  ASCII, XML
Last Update: 2026-01-13 01:00:36

Recent Files (showing 20 of 1278):
Filename                                      Size (MB)    Date
----------------------------------------------------------------------
ipg260113.zip                                 137.58       2026-01-13
ipg260106.zip                                 147.68       2026-01-06
...
```

### Download a File

```bash
python3 uspto_bulk_download.py --download PTGRXML --file ipg260113.zip --output ./downloads
```

Output:
```
Downloading: ipg260113.zip
Size: 137.58 MB
URL: https://api.uspto.gov/api/v1/datasets/products/files/PTGRXML/2026/ipg260113.zip
Downloading from: https://data.uspto.gov/files/PTGRXML/2026/ipg260113.zip?Expires=...
Saving to: downloads/ipg260113.zip
Progress: 100.0% (137.58 MB / 137.58 MB)

✓ Download complete: downloads/ipg260113.zip
```

### Output JSON

```bash
python3 uspto_bulk_download.py --product PTGRXML --json
```

## Available Products

| ID | Title | Frequency | Description |
|----|-------|-----------|-------------|
| **Patent Grants** |
| PTGRXML | Patent Grant Full-Text Data (No Images) - XML | WEEKLY | Full text of granted patents |
| PTGRDT | Patent Grant Full Text with TIFF Images | WEEKLY | Full text + embedded images |
| PTGRMP2 | Patent Grant Multi-page PDF Images | WEEKLY | PDF images of patents |
| PTBLXML | Patent Grant Bibliographic Data - XML | WEEKLY | Front page data only |
| **Patent Applications** |
| APPXML | Patent Application Full-Text Data (No Images) | WEEKLY | Published applications text |
| APPDT | Patent Application Full Text with TIFF Images | WEEKLY | Applications + images |
| APPBLXML | Patent Application Bibliographic Data | WEEKLY | Front page data only |
| **Patent File Wrappers** |
| PTFWPRE | Patent File Wrapper - Weekly | WEEKLY | Bulk bibliographic datasets |
| PTFWPRD | Patent File Wrapper - Daily | DAILY | Daily updates |
| **Patent Examination** |
| PEDSXML | Patent Examination Data System - XML | YEARLY | Examination records |
| PEDSJSON | Patent Examination Data System - JSON | YEARLY | Same data in JSON |
| **Assignments** |
| PASDL | Patent Assignment XML - Daily | DAILY | Ownership transfers |
| PASYR | Patent Assignment XML - Annual | YEARLY | Annual compilation |
| **Research Datasets** |
| ECOPAIR | Patent Examination Research Dataset | YEARLY | PatEx for researchers |
| ECOPATAI | AI Patent Dataset | YEARLY | AI-related patents |
| MOONSHOT | Cancer Moonshot Patent Data | YEARLY | Cancer research patents |

Run `--list` for all 40 products.

## API Technical Details

### Endpoints

| Endpoint | Description |
|----------|-------------|
| `GET /api/v1/datasets/products/search` | List/search products |
| `GET /api/v1/datasets/products/{id}` | Get product details |
| `GET /api/v1/datasets/products/files/{id}/{year}/{file}` | Download file |

### Authentication

- Header: `X-API-Key: your-key`
- Get key at: https://data.uspto.gov/myodp/key-reveal

### File Downloads

The API returns HTTP 302 redirects to CloudFront presigned URLs:
```
https://data.uspto.gov/files/{product}/{year}/{file}?Expires=...&Signature=...&Key-Pair-Id=...
```

## Command Reference

```
usage: uspto_bulk_download.py [-h] [--api-key API_KEY] [--list] [--search SEARCH]
                              [--product PRODUCT] [--download DOWNLOAD] [--file FILE]
                              [--output OUTPUT] [--json]

USPTO Open Data Portal Bulk Data Download Tool

optional arguments:
  -h, --help            show this help message and exit
  --api-key, -k         USPTO API key (or set USPTO_API_KEY env var)
  --list, -l            List available bulk data products
  --search, -s          Search term for filtering products
  --product, -p         Show details for a specific product ID
  --download, -d        Product ID to download from
  --file, -f            Filename to download (use with --download)
  --output, -o          Output directory (default: ./downloads)
  --json, -j            Output raw JSON (for product details)
```

## License

MIT License - See LICENSE file

## Links

- [USPTO Open Data Portal](https://data.uspto.gov)
- [API Documentation](https://data.uspto.gov/apis/bulk-data/search)
- [Get API Key](https://data.uspto.gov/myodp/key-reveal)
