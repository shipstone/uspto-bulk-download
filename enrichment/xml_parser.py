#!/usr/bin/env python3
"""
USPTO PTGRXML Parser

Parses USPTO patent grant XML files to extract patent data.
"""

import os
import re
import zipfile
import xml.etree.ElementTree as ET
from typing import Dict, List, Optional, Tuple
from io import BytesIO


def normalize_patent_number(patent_num: str) -> str:
    """
    Normalize patent number for matching.
    US9391881B2 -> 09391881
    """
    # Remove country prefix and kind code
    match = re.match(r'US(\d+)[A-Z]\d*', patent_num)
    if match:
        num = match.group(1)
        # Pad to 8 digits
        return num.zfill(8)
    return patent_num


def find_patent_in_xml(xml_content: bytes, patent_number: str) -> Optional[str]:
    """
    Find a specific patent's XML block within a weekly file.
    
    The USPTO XML files concatenate multiple patents, each starting with:
    <us-patent-grant ...>
    
    Returns the XML string for just that patent, or None if not found.
    """
    normalized = normalize_patent_number(patent_number)
    
    # Convert bytes to string for searching
    content = xml_content.decode('utf-8', errors='replace')
    
    # Find the start of this patent's block
    # Pattern: <us-patent-grant ... file="USxxxxxxxx-...
    pattern = f'<us-patent-grant[^>]+file="US{normalized}'
    
    match = re.search(pattern, content)
    if not match:
        return None
    
    start_pos = match.start()
    
    # Find the end of this patent block (next us-patent-grant or end)
    end_match = re.search(r'</us-patent-grant>', content[start_pos:])
    if end_match:
        end_pos = start_pos + end_match.end()
    else:
        end_pos = len(content)
    
    return content[start_pos:end_pos]


def extract_patent_xml(zip_path: str, patent_number: str) -> Optional[str]:
    """
    Extract a specific patent's XML from a weekly ZIP file.
    """
    with zipfile.ZipFile(zip_path, 'r') as zf:
        # Get the XML file name (should be only one .xml file)
        xml_files = [n for n in zf.namelist() if n.endswith('.xml')]
        if not xml_files:
            print(f"No XML files found in {zip_path}")
            return None
        
        xml_name = xml_files[0]
        with zf.open(xml_name) as f:
            content = f.read()
            return find_patent_in_xml(content, patent_number)


def parse_patent_xml(xml_string: str) -> Dict:
    """
    Parse a single patent's XML and extract relevant fields.
    
    Returns dict with:
    - title
    - abstract
    - grant_date
    - priority_date
    - application_number
    - assignee_original
    - independent_claims
    - application_family_members
    """
    result = {
        'title': None,
        'abstract': None,
        'grant_date': None,
        'priority_date': None,
        'application_number': None,
        'assignee_original': None,
        'independent_claims': [],
        'application_family_members': []
    }
    
    # Wrap in a root element to handle DTD issues
    # Remove DOCTYPE declaration which causes parsing issues
    xml_clean = re.sub(r'<!DOCTYPE[^>]+>', '', xml_string)
    
    try:
        root = ET.fromstring(xml_clean)
    except ET.ParseError as e:
        print(f"XML Parse Error: {e}")
        return result
    
    # Title
    title_elem = root.find('.//invention-title')
    if title_elem is not None:
        result['title'] = title_elem.text
    
    # Abstract
    abstract_elem = root.find('.//abstract/p')
    if abstract_elem is not None:
        # Get all text including nested elements
        result['abstract'] = ''.join(abstract_elem.itertext()).strip()
    
    # Grant date (publication date)
    pub_date = root.find('.//publication-reference/document-id/date')
    if pub_date is not None:
        # Format: YYYYMMDD -> YYYY-MM-DD
        d = pub_date.text
        if d and len(d) == 8:
            result['grant_date'] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    
    # Application number
    app_num = root.find('.//application-reference/document-id/doc-number')
    if app_num is not None:
        num = app_num.text
        # Format as XX/XXXXXX
        if num and len(num) >= 8:
            result['application_number'] = f"{num[:2]}/{num[2:]}"
        else:
            result['application_number'] = num
    
    # Application date (filing date) - can be used as fallback priority
    app_date = root.find('.//application-reference/document-id/date')
    filing_date = None
    if app_date is not None:
        d = app_date.text
        if d and len(d) == 8:
            filing_date = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    
    # Priority date - check provisional applications first
    prov_date = root.find('.//us-provisional-application/document-id/date')
    if prov_date is not None:
        d = prov_date.text
        if d and len(d) == 8:
            result['priority_date'] = f"{d[:4]}-{d[4:6]}-{d[6:8]}"
    elif filing_date:
        result['priority_date'] = filing_date
    
    # Assignee (original)
    assignee_org = root.find('.//assignees/assignee/addressbook/orgname')
    if assignee_org is not None:
        result['assignee_original'] = assignee_org.text
    else:
        # Try individual inventor as assignee
        last_name = root.find('.//assignees/assignee/addressbook/last-name')
        first_name = root.find('.//assignees/assignee/addressbook/first-name')
        if last_name is not None and first_name is not None:
            result['assignee_original'] = f"{first_name.text} {last_name.text}"
    
    # Related documents (family members)
    family_members = []
    
    # Related publications (pre-grant pub)
    for rel_pub in root.findall('.//related-publication/document-id'):
        country = rel_pub.find('country')
        doc_num = rel_pub.find('doc-number')
        kind = rel_pub.find('kind')
        if country is not None and doc_num is not None:
            member = f"{country.text}{doc_num.text}"
            if kind is not None:
                member += kind.text
            family_members.append(member)
    
    result['application_family_members'] = family_members
    
    # Claims - extract independent claims
    claims = root.findall('.//claim')
    for claim in claims:
        claim_id = claim.get('id', '')
        claim_num = claim.get('num', '')
        
        # Get direct child claim-text elements only (not nested)
        claim_texts = claim.findall('./claim-text')
        if not claim_texts:
            continue
        
        # First claim-text element usually has the preamble
        first_text = claim_texts[0]
        
        # Check if this is a dependent claim (references another claim)
        claim_ref = first_text.find('.//claim-ref')
        if claim_ref is not None:
            # This is a dependent claim, skip
            continue
        
        # Get all text from the first (top-level) claim-text including nested
        full_text = ''.join(first_text.itertext()).strip()
        
        # Check for dependency by looking at text pattern
        if re.search(r'of claim \d+|according to claim \d+', full_text, re.IGNORECASE):
            continue
        
        # This appears to be an independent claim
        full_claim_text = full_text
        
        # Determine claim type
        claim_type = 'method'  # default
        if re.match(r'\d+\.\s*A (system|apparatus|device)', full_claim_text, re.IGNORECASE):
            claim_type = 'system'
        elif re.match(r'\d+\.\s*A (method|process)', full_claim_text, re.IGNORECASE):
            claim_type = 'method'
        elif re.match(r'\d+\.\s*(A |An )?(non-transitory )?computer.{0,20}(medium|storage)', full_claim_text, re.IGNORECASE):
            claim_type = 'medium'
        
        claim_number = int(claim_num) if claim_num.isdigit() else 0
        
        result['independent_claims'].append({
            'number': claim_number,
            'type': claim_type,
            'text': full_claim_text
        })
    
    return result


def extract_patent_data(zip_path: str, patent_number: str) -> Optional[Dict]:
    """
    Extract all data for a patent from a weekly ZIP file.
    """
    xml_string = extract_patent_xml(zip_path, patent_number)
    if xml_string is None:
        print(f"Could not find {patent_number} in {zip_path}")
        return None
    
    return parse_patent_xml(xml_string)


if __name__ == "__main__":
    # Test with US9391881B2
    import json
    
    test_patent = "US9391881B2"
    test_zip = "downloads/ipg160712.zip"
    
    print(f"Testing extraction of {test_patent} from {test_zip}")
    print("=" * 60)
    
    data = extract_patent_data(test_zip, test_patent)
    
    if data:
        print(json.dumps(data, indent=2))
    else:
        print("Failed to extract patent data")
