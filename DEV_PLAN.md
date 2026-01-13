# USPTO Patent Data Enrichment Tool - Development Plan

## Overview
Build a tool to populate the IPTLpatents-template.json with data from:
1. USPTO PTGRXML bulk data (primary source for patent text/claims)
2. Google Patents (enrichment: forward citations, family members, expiration)

## Target Patents (11 total)
| Patent | Grant Date | Weekly File |
|--------|------------|-------------|
| US9294434B1 | 2016-03-22 | ipg160322.zip |
| US9391881B2 | 2016-07-12 | ipg160712.zip |
| US9876757B2 | 2018-01-23 | ipg180123.zip |
| US10154005B2 | 2018-12-11 | ipg181211.zip |
| US10469444B2 | 2019-11-05 | ipg191105.zip |
| US10659430B2 | 2020-05-19 | ipg200519.zip |
| US11283790B2 | 2022-03-22 | ipg220322.zip |
| US11477276B2 | 2022-10-18 | ipg221018.zip |
| US11799690B2 | 2023-10-24 | ipg231024.zip |
| US12034799B2 | 2024-07-09 | ipg240709.zip |
| US12034800B2 | 2024-07-09 | ipg240709.zip |

## Data Field Mapping

### From USPTO PTGRXML:
- title
- abstract
- grant_date
- priority_date
- application_number
- assignee_original
- independent_claims (number, type, text)
- application_family_members

### From Google Patents:
- forward_cites (count)
- top_citing_assignees (list with counts)
- simple_family_members
- expiration (calculated with adjustments)
- assignee_current

### Calculated:
- portfolio.assignee (from first patent)
- portfolio.patent_count (count of patents array)
- portfolio.generated (current date)

---

## Phases

### Phase 1: Project Setup
**Goal:** Create project structure and utility functions

**Tasks:**
- [ ] Create enrichment/ subdirectory
- [ ] Create enrich_patents.py with argument parsing
- [ ] Create config for API key and paths
- [ ] Add to .gitignore: downloads/, *.xml, __pycache__/

**Test:** Run `python3 enrichment/enrich_patents.py --help` successfully

**Status:** NOT STARTED

---

### Phase 2: USPTO XML Download
**Goal:** Download required PTGRXML files

**Tasks:**
- [ ] Create function to map patent numbers to weekly filenames
- [ ] Create function to download specific weekly files using existing uspto_bulk_download.py
- [ ] Download all 10 required weekly files to downloads/

**Test:** Verify all 10 zip files exist in downloads/ with correct sizes

**Status:** NOT STARTED

---

### Phase 3: XML Parsing - Single Patent
**Goal:** Extract data from USPTO XML for one patent

**Tasks:**
- [ ] Unzip and locate patent XML within weekly file
- [ ] Parse XML structure to understand schema
- [ ] Extract: title, abstract, grant_date, priority_date, application_number
- [ ] Extract: assignee_original
- [ ] Extract: independent_claims (identify claim type: system/method/medium)
- [ ] Extract: application_family_members

**Test:** Parse US9391881B2 and print extracted fields, verify against Google Patents

**Status:** NOT STARTED

---

### Phase 4: XML Parsing - All Patents
**Goal:** Extract data for all 11 patents

**Tasks:**
- [ ] Loop through all patent numbers
- [ ] Handle case where 2 patents share same weekly file (ipg240709.zip)
- [ ] Store extracted data in intermediate dict structure
- [ ] Validate all 11 patents extracted successfully

**Test:** Print summary showing all 11 patents with title and claim count

**Status:** NOT STARTED

---

### Phase 5: Google Patents Scraper - Single Patent
**Goal:** Scrape enrichment data from Google Patents for one patent

**Tasks:**
- [ ] Create function to fetch Google Patents page
- [ ] Parse "Cited By" section for forward_cites count
- [ ] Parse "Cited By" section for top_citing_assignees with counts
- [ ] Parse "Priority And Related Applications" for simple_family_members
- [ ] Parse expiration date (adjusted)
- [ ] Parse current assignee

**Test:** Scrape US9391881B2, verify forward_cites=14 matches page

**Status:** NOT STARTED

---

### Phase 6: Google Patents Scraper - All Patents
**Goal:** Scrape enrichment data for all 11 patents

**Tasks:**
- [ ] Loop through all patent numbers with rate limiting (1 req/sec)
- [ ] Merge Google Patents data with USPTO data
- [ ] Handle any missing/error cases gracefully

**Test:** Print summary showing all 11 patents with forward_cites values

**Status:** NOT STARTED

---

### Phase 7: JSON Output Generation
**Goal:** Generate final populated JSON file

**Tasks:**
- [ ] Load template structure from IPTLpatents-template.json
- [ ] Populate portfolio metadata
- [ ] Populate each patent entry
- [ ] Write to IPTLpatents-enriched.json
- [ ] Validate JSON structure

**Test:** Compare field-by-field with IPTLpatents-complete.json for US9391881B2

**Status:** NOT STARTED

---

### Phase 8: Validation & Cleanup
**Goal:** Verify output quality and finalize

**Tasks:**
- [ ] Compare all fields against IPTLpatents-complete.json
- [ ] Document any discrepancies and reasons
- [ ] Add README section for enrichment tool
- [ ] Clean up temporary files

**Test:** Diff enriched vs complete JSON, document differences

**Status:** NOT STARTED

---

## Status Tracking

| Phase | Status | Completed | Notes |
|-------|--------|-----------|-------|
| 1 | NOT STARTED | - | |
| 2 | NOT STARTED | - | |
| 3 | NOT STARTED | - | |
| 4 | NOT STARTED | - | |
| 5 | NOT STARTED | - | |
| 6 | NOT STARTED | - | |
| 7 | NOT STARTED | - | |
| 8 | NOT STARTED | - | |

---

## Notes
- Update status table after completing each phase
- Commit after each phase completion
- If a phase fails test, document issue and fix before proceeding
