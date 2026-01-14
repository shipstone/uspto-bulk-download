#!/usr/bin/env python3
"""
Google Patents Scraper

Scrapes enrichment data from Google Patents:
- forward_cites (count)
- top_citing_assignees
- simple_family_members
- expiration
- assignee_current
"""

import re
import time
import urllib.request
import urllib.error
from typing import Dict, List, Optional


def fetch_google_patents_page(patent_number: str) -> Optional[str]:
    """
    Fetch the Google Patents page for a patent.
    """
    url = f"https://patents.google.com/patent/{patent_number}/en"
    
    headers = {
        'User-Agent': 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36',
        'Accept': 'text/html,application/xhtml+xml',
        'Accept-Language': 'en-US,en;q=0.9',
    }
    
    try:
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=30) as response:
            return response.read().decode('utf-8', errors='replace')
    except urllib.error.HTTPError as e:
        print(f"  HTTP Error {e.code} for {patent_number}")
        return None
    except urllib.error.URLError as e:
        print(f"  URL Error for {patent_number}: {e.reason}")
        return None
    except Exception as e:
        print(f"  Error fetching {patent_number}: {e}")
        return None


def parse_google_patents_html(html: str, patent_number: str) -> Dict:
    """
    Parse Google Patents HTML to extract enrichment data.
    """
    result = {
        'forward_cites': 0,
        'top_citing_assignees': None,
        'simple_family_members': [],
        'expiration': None,
        'assignee_current': None
    }
    
    # 1. Extract forward citations 
    # Sum "Cited By (N)" sections + "Families Citing this family (N)"
    cited_by_counts = re.findall(r'<h2>Cited By \((\d+)\)</h2>', html)
    families_citing = re.search(r'Families Citing this family \((\d+)\)', html)
    
    total_cites = sum(int(c) for c in cited_by_counts)
    if families_citing:
        total_cites += int(families_citing.group(1))
    result['forward_cites'] = total_cites
    
    # 2. Extract expiration date (handles both Adjusted and Anticipated)
    exp_match = re.search(r'itemprop="expiration"[^>]*datetime="(\d{4}-\d{2}-\d{2})"', html)
    if not exp_match:
        exp_match = re.search(r'itemprop="ifiExpiration">(\d{4}-\d{2}-\d{2})<', html)
    if not exp_match:
        # Look for date in legal events before "Anticipated expiration" or "Adjusted expiration"
        # Pattern: <time itemprop="date" datetime="YYYY-MM-DD">...</time>\n...<span>Anticipated expiration
        exp_match = re.search(
            r'<time[^>]*datetime="(\d{4}-\d{2}-\d{2})"[^>]*>[^<]*</time>\s*\n?\s*<span[^>]*>(?:Anticipated|Adjusted) expiration',
            html
        )
    if exp_match:
        result['expiration'] = exp_match.group(1)
    
    # 3. Extract current assignee
    assignee_match = re.search(
        r'Current Assignee.*?<dd[^>]*>(.*?)</dd>',
        html, re.DOTALL | re.IGNORECASE
    )
    if assignee_match:
        assignee_html = assignee_match.group(1)
        assignee_clean = re.sub(r'<[^>]+>', ' ', assignee_html)
        assignee_clean = re.sub(r'The listed assignees.*', '', assignee_clean, flags=re.I)
        assignee_clean = re.sub(r'Google has not.*', '', assignee_clean, flags=re.I)
        assignee_clean = ' '.join(assignee_clean.split()).strip()
        if assignee_clean and len(assignee_clean) > 2:
            result['assignee_current'] = assignee_clean
    
    if not result['assignee_current']:
        alt_match = re.search(
            r'<span[^>]*itemprop="assigneeOriginal"[^>]*>([^<]+)</span>',
            html
        )
        if alt_match:
            result['assignee_current'] = alt_match.group(1).strip()
    
    # 4. Extract simple family members from multiple sections
    family_pubs = set()
    
    # Family Applications section
    family_match = re.search(
        r'<h2>Family Applications \(\d+\)</h2>(.*?)(?=<h2>|</section>)', 
        html, re.DOTALL
    )
    if family_match:
        pubs = re.findall(r'>(US\d{7,}[AB]\d?)<', family_match.group(1))
        family_pubs.update(pubs)
    
    # Also Published As section  
    also_match = re.search(
        r'<h2>Also Published As</h2>(.*?)(?=<h2>|</section>)', 
        html, re.DOTALL
    )
    if also_match:
        pubs = re.findall(r'>(US\d{7,}[AB]\d?)<', also_match.group(1))
        family_pubs.update(pubs)
    
    # Priority Applications section
    priority_match = re.search(
        r'<h2>Priority Applications \(\d+\)</h2>(.*?)(?=<h2>|</section>)', 
        html, re.DOTALL
    )
    if priority_match:
        pubs = re.findall(r'>(US\d{7,}[AB]\d?)<', priority_match.group(1))
        family_pubs.update(pubs)
    
    # Remove self from family
    family_pubs.discard(patent_number)
    result['simple_family_members'] = sorted(list(family_pubs))
    
    # 5. Extract top citing assignees from Cited By and Families Citing tables
    assignee_counts = {}
    
    # Get assignees from forwardReferences entries
    citing_entries = re.findall(
        r'itemprop="forward[Rr]eferences[^"]*".*?itemprop="assigneeOriginal"[^>]*>([^<]+)<',
        html, re.DOTALL
    )
    for assignee in citing_entries:
        assignee_clean = assignee.strip().upper()
        if assignee_clean and len(assignee_clean) > 3:
            assignee_counts[assignee_clean] = assignee_counts.get(assignee_clean, 0) + 1
    
    # Also get from Families Citing section
    families_citing_section = re.search(
        r'<h2>Families Citing this family.*?</h2>(.*?)(?=<h2>|</article>)',
        html, re.DOTALL
    )
    if families_citing_section:
        family_assignees = re.findall(
            r'itemprop="assigneeOriginal"[^>]*>([^<]+)<',
            families_citing_section.group(1)
        )
        for assignee in family_assignees:
            assignee_clean = assignee.strip().upper()
            if assignee_clean and len(assignee_clean) > 3:
                assignee_counts[assignee_clean] = assignee_counts.get(assignee_clean, 0) + 1
    
    if assignee_counts:
        sorted_assignees = sorted(assignee_counts.items(), key=lambda x: (-x[1], x[0]))
        result['top_citing_assignees'] = [
            f"{name} ({count})" for name, count in sorted_assignees[:7]
        ]
    
    return result


def scrape_patent_enrichment(patent_number: str) -> Optional[Dict]:
    """
    Scrape enrichment data for a single patent from Google Patents.
    """
    html = fetch_google_patents_page(patent_number)
    if html is None:
        return None
    
    return parse_google_patents_html(html, patent_number)


def scrape_all_patents(patent_numbers: List[str], delay: float = 1.0, 
                       verbose: bool = False) -> Dict[str, Dict]:
    """
    Scrape enrichment data for all patents with rate limiting.
    """
    results = {}
    
    for i, patent_num in enumerate(patent_numbers):
        if verbose:
            print(f"  [{i+1}/{len(patent_numbers)}] Scraping {patent_num}...")
        
        data = scrape_patent_enrichment(patent_num)
        if data:
            results[patent_num] = data
            if verbose:
                print(f"      forward_cites: {data['forward_cites']}, expiration: {data['expiration']}")
        else:
            print(f"  WARNING: Failed to scrape {patent_num}")
            results[patent_num] = {
                'forward_cites': 0,
                'top_citing_assignees': None,
                'simple_family_members': [],
                'expiration': None,
                'assignee_current': None
            }
        
        if i < len(patent_numbers) - 1:
            time.sleep(delay)
    
    return results


if __name__ == "__main__":
    import json
    
    test_patent = "US9391881B2"
    
    print(f"Testing Google Patents scraper with {test_patent}")
    print("=" * 60)
    
    data = scrape_patent_enrichment(test_patent)
    
    if data:
        print(json.dumps(data, indent=2))
        print()
        print("=" * 60)
        print("Verification:")
        print(f"  forward_cites: {data['forward_cites']} (expected ~16: 3 direct + 13 family)")
        print(f"  expiration: {data['expiration']} (expected: 2034-05-25)")
        print(f"  assignee_current: {data['assignee_current']}")
        print(f"  simple_family_members: {len(data['simple_family_members'])} patents")
        print(f"  top_citing_assignees: {len(data['top_citing_assignees'] or [])} assignees")
        
        passed = True
        if data['expiration'] != '2034-05-25':
            print("  FAIL: expiration mismatch")
            passed = False
        if not data['assignee_current']:
            print("  FAIL: no assignee found")
            passed = False
        if data['forward_cites'] < 10:
            print("  WARNING: forward_cites lower than expected")
        if len(data['simple_family_members']) < 5:
            print("  WARNING: few family members found")
            
        print()
        print("TEST PASSED" if passed else "TEST FAILED")
    else:
        print("FAILED to scrape patent data")
