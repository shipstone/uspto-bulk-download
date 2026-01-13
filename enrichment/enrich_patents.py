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

# Add parent directory to path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

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
    
    # TODO: Phase 2 - Download USPTO files
    # TODO: Phase 3-4 - Parse USPTO XML
    # TODO: Phase 5-6 - Scrape Google Patents
    # TODO: Phase 7 - Generate output JSON
    
    print()
    print("Enrichment complete (stub - phases not yet implemented)")
    return 0


if __name__ == "__main__":
    sys.exit(main())
