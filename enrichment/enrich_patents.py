#!/usr/bin/env python3
"""
Patent Data Enrichment Tool

Populates patent portfolio JSON templates with data from:
1. USPTO PTGRXML bulk data (primary source)
2. Google Patents (enrichment: citations, family, expiration)

Usage:
    python3 enrichment/enrich_patents.py --template examples/IPTLpatents-template.json --output examples/IPTLpatents-enriched.json
"""

import argparse
import json
import os
import sys
from datetime import date

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from enrichment import uspto_download
from enrichment import xml_parser
from enrichment import google_patents

# Configuration
DEFAULT_TEMPLATE = "examples/IPTLpatents-template.json"
DEFAULT_OUTPUT = "examples/IPTLpatents-enriched.json"
DOWNLOADS_DIR = "downloads"
USPTO_API_KEY_ENV = "USPTO_API_KEY"


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Enrich patent portfolio JSON with USPTO and Google Patents data",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s --template examples/IPTLpatents-template.json
  %(prog)s --template input.json --output enriched.json
  %(prog)s --download-only  # Just download USPTO files
  %(prog)s --scrape-only    # Just scrape Google Patents (skip USPTO download)
        """
    )
    
    parser.add_argument(
        "--template", "-t",
        default=DEFAULT_TEMPLATE,
        help=f"Input template JSON file (default: {DEFAULT_TEMPLATE})"
    )
    
    parser.add_argument(
        "--output", "-o",
        default=DEFAULT_OUTPUT,
        help=f"Output enriched JSON file (default: {DEFAULT_OUTPUT})"
    )
    
    parser.add_argument(
        "--downloads-dir", "-d",
        default=DOWNLOADS_DIR,
        help=f"Directory for USPTO downloads (default: {DOWNLOADS_DIR})"
    )
    
    parser.add_argument(
        "--api-key", "-k",
        default=os.environ.get(USPTO_API_KEY_ENV),
        help=f"USPTO API key (or set {USPTO_API_KEY_ENV} env var)"
    )
    
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Only download USPTO files, don't process"
    )
    
    parser.add_argument(
        "--scrape-only",
        action="store_true",
        help="Only scrape Google Patents, skip USPTO download"
    )
    
    parser.add_argument(
        "--skip-google",
        action="store_true",
        help="Skip Google Patents scraping"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Verbose output"
    )
    
    return parser.parse_args()


def load_template(template_path):
    """Load the patent template JSON file."""
    with open(template_path, 'r') as f:
        return json.load(f)


def get_patent_numbers(template_data):
    """Extract patent numbers from template."""
    return [p['number'] for p in template_data.get('patents', [])]


def build_patent_to_file_mapping(patent_numbers, downloads_dir):
    """Build mapping of patent numbers to their ZIP file paths."""
    patent_to_file = {}
    for patent_num in patent_numbers:
        if patent_num in uspto_download.PATENT_GRANT_DATES:
            grant_date = uspto_download.PATENT_GRANT_DATES[patent_num]
            filename = uspto_download.grant_date_to_weekly_filename(grant_date)
            patent_to_file[patent_num] = os.path.join(downloads_dir, filename)
    return patent_to_file


def merge_patent_data(uspto_data, google_data, patent_number):
    """
    Merge USPTO and Google Patents data for a single patent.
    
    Returns a dict matching the target JSON schema.
    """
    result = {
        "number": patent_number,
        "title": None,
        "grant_date": None,
        "priority_date": None,
        "expiration": None,
        "application_number": None,
        "assignee_original": None,
        "assignee_current": None,
        "forward_cites": 0,
        "top_citing_assignees": None,
        "abstract": None,
        "independent_claims": [],
        "application_family_members": [],
        "simple_family_members": []
    }
    
    # From USPTO XML
    if uspto_data:
        result["title"] = uspto_data.get("title")
        result["grant_date"] = uspto_data.get("grant_date")
        result["priority_date"] = uspto_data.get("priority_date")
        result["application_number"] = uspto_data.get("application_number")
        result["assignee_original"] = uspto_data.get("assignee_original")
        result["abstract"] = uspto_data.get("abstract")
        result["independent_claims"] = uspto_data.get("independent_claims", [])
        result["application_family_members"] = uspto_data.get("application_family_members", [])
    
    # From Google Patents (enrichment)
    if google_data:
        result["forward_cites"] = google_data.get("forward_cites", 0)
        result["top_citing_assignees"] = google_data.get("top_citing_assignees")
        result["simple_family_members"] = google_data.get("simple_family_members", [])
        result["expiration"] = google_data.get("expiration")
        # Use Google's assignee_current, fall back to USPTO original
        result["assignee_current"] = google_data.get("assignee_current") or result["assignee_original"]
    else:
        # No Google data - use USPTO assignee as current
        result["assignee_current"] = result["assignee_original"]
    
    return result


def generate_output(template_data, uspto_results, google_results):
    """
    Generate the final enriched JSON structure.
    """
    output = {
        "portfolio": {
            "assignee": None,
            "patent_count": 0,
            "generated": date.today().isoformat()
        },
        "patents": []
    }
    
    # Process each patent from template
    for template_patent in template_data.get("patents", []):
        patent_num = template_patent["number"]
        
        uspto_data = uspto_results.get(patent_num, {})
        google_data = google_results.get(patent_num, {})
        
        merged = merge_patent_data(uspto_data, google_data, patent_num)
        output["patents"].append(merged)
    
    # Set portfolio metadata
    output["portfolio"]["patent_count"] = len(output["patents"])
    
    # Get assignee from first patent with one
    for patent in output["patents"]:
        if patent.get("assignee_original"):
            output["portfolio"]["assignee"] = patent["assignee_original"]
            break
    
    return output


def main():
    """Main entry point."""
    args = parse_args()
    
    print(f"USPTO Patent Data Enrichment Tool")
    print(f"==================================")
    print(f"Template: {args.template}")
    print(f"Output:   {args.output}")
    print(f"Downloads: {args.downloads_dir}")
    print()
    
    # Load template
    if not os.path.exists(args.template):
        print(f"Error: Template file not found: {args.template}")
        return 1
    
    template_data = load_template(args.template)
    patent_numbers = get_patent_numbers(template_data)
    
    print(f"Found {len(patent_numbers)} patents in template:")
    for num in patent_numbers:
        print(f"  - {num}")
    print()
    
    # Phase 2: Download USPTO files (if needed)
    if not args.scrape_only:
        if not args.api_key:
            print(f"Warning: No USPTO API key. Assuming files already downloaded.")
        else:
            print("Phase 2: Downloading USPTO PTGRXML files...")
            patent_to_file = uspto_download.download_all_required(
                patent_numbers, 
                args.api_key, 
                args.downloads_dir,
                verbose=args.verbose
            )
        
        found, missing = uspto_download.verify_downloads(patent_numbers, args.downloads_dir)
        print(f"\nDownload summary: {len(found)} found, {len(missing)} missing")
        if missing:
            print(f"Missing patents: {missing}")
            if not args.download_only:
                return 1
        
        if args.download_only:
            print("\n--download-only specified, stopping here.")
            return 0
    
    # Phase 3-4: Parse USPTO XML
    print("\nPhase 3-4: Parsing USPTO XML files...")
    patent_to_file = build_patent_to_file_mapping(patent_numbers, args.downloads_dir)
    
    uspto_results = xml_parser.extract_all_patents(patent_to_file, verbose=args.verbose)
    print(f"  Extracted {len(uspto_results)}/{len(patent_numbers)} patents from USPTO XML")
    
    # Phase 5-6: Scrape Google Patents (if not skipped)
    google_results = {}
    if not args.skip_google:
        print("\nPhase 5-6: Scraping Google Patents for enrichment data...")
        google_results = google_patents.scrape_all_patents(
            patent_numbers, 
            delay=1.0, 
            verbose=args.verbose
        )
        print(f"  Scraped {len(google_results)}/{len(patent_numbers)} patents from Google Patents")
    else:
        print("\nSkipping Google Patents scraping (--skip-google)")
    
    # Phase 7: Generate output JSON
    print("\nPhase 7: Generating enriched JSON output...")
    output_data = generate_output(template_data, uspto_results, google_results)
    
    # Write output file
    with open(args.output, 'w') as f:
        json.dump(output_data, f, indent=2)
    
    print(f"  Wrote enriched data to: {args.output}")
    
    # Summary
    print("\n" + "=" * 60)
    print("ENRICHMENT COMPLETE")
    print("=" * 60)
    print(f"Portfolio: {output_data['portfolio']['assignee']}")
    print(f"Patents:   {output_data['portfolio']['patent_count']}")
    print(f"Generated: {output_data['portfolio']['generated']}")
    print()
    
    for patent in output_data['patents']:
        title = (patent.get('title') or 'NO TITLE')[:50]
        claims = len(patent.get('independent_claims', []))
        cites = patent.get('forward_cites', 0)
        exp = patent.get('expiration', 'N/A')
        print(f"  {patent['number']}: {title}...")
        print(f"      claims: {claims}, cites: {cites}, exp: {exp}")
    
    return 0


if __name__ == "__main__":
    sys.exit(main())
