# iTREDS Maternal Health Scraper - Quick Reference

## Overview

This document provides a quick reference for developing the deep scraper in Cursor. The goal is to move from **14.7% actionability** (pilot) to **60%+ actionability** (target).

---

## Why Deep Scraping?

The initial pilot failed because it only scraped **main county pages**:

| Problem | Pilot Result | Fix |
|---------|-------------|-----|
| No eligibility info | 0% | Scrape individual program pages |
| No contact info | 2.3% phone, 0% email | Extract from headers/footers/contact pages |
| Generic categories | 69.8% "Other" | Use maternal health-specific keywords |
| Missing counties | 10 major counties | Navigate deeper into site structure |

---

## 4-Phase Architecture

```
Phase 1: DISCOVERY          Phase 2: EXTRACTION
┌─────────────────┐         ┌─────────────────┐
│ County Main URL │ ──────▶ │ Program Pages   │
│ → Health Dept   │         │ → Full HTML     │
│ → MCH Section   │         │ → Contact Info  │
│ → Program Links │         │ → PDF Links     │
└─────────────────┘         └─────────────────┘
        │                           │
        ▼                           ▼
Phase 4: VALIDATION         Phase 3: STRUCTURING
┌─────────────────┐         ┌─────────────────┐
│ Quality Scores  │ ◀────── │ LLM Processing  │
│ Human Review    │         │ → Schema Fields │
│ Final Dataset   │         │ → Classification│
└─────────────────┘         └─────────────────┘
```

---

## Runbook (Aligned to Current Repo)

1. Configure `.env`:
   - `API_PROVIDER=openai` (or `anthropic` or `ollama`)
   - `OPENAI_API_KEY=...` if using OpenAI
   - Optional (local): `OLLAMA_MODEL=llama3.1:8b-instruct`
2. Install deps: `pip install -r requirements.txt`
3. Verify: `python test_setup.py`
4. Pilot run on 5 counties:
   - In `scraper.py`, temporarily set `counties_to_process = counties_to_process[:5]`
   - Run: `python scraper.py`
5. Full run for 58 counties:
   - Remove the 5-county cap; re-run the scraper
6. Output: `California_County_Healthcare_Data.csv`

Settings in `scraper.py` to control cost/performance:
- `MAX_CONTENT_LENGTH = 12000` (characters sent to LLM; lower to save)
- `DELAY_BETWEEN_REQUESTS = 3` (be polite to servers)
- LLM `max_tokens` currently 4000; safe to reduce to ~1500 for cost control
- Subpage scraping is OFF by default; only enable if needed

---

## Navigation Keywords

### Level 1: Find Health Department
```python
DEPT_KEYWORDS = [
    "health department", "health services", "public health",
    "health and human services", "hhs", "hhsa", "dph"
]
```

### Level 2: Find Maternal/Child Section
```python
SECTION_KEYWORDS = [
    "maternal health", "maternal child health", "mch", "mcah",
    "women's health", "family health", "perinatal",
    "reproductive health", "prenatal"
]
```

### Level 3: Find Specific Programs
```python
PROGRAM_KEYWORDS = [
    "healthy start", "wic", "home visiting", "miechv",
    "black infant health", "first 5", "nurse-family partnership",
    "title v", "perinatal equity", "postpartum", "breastfeeding",
    "lactation", "family planning"
]
```

---

## Extraction Schema

The current Python scraper expects a county object with a `programs` array. Fields map into the CSV columns used by `save_to_csv`.

```python
EXTRACTION_SCHEMA = {
    "county_name": str,
    "state": str,
    "county_website_url": str,
    "health_department_name": str,        # e.g., "Department of Public Health"
    "health_department_contact_email": str,
    "health_department_contact_phone": str,
    "programs": [
        {
            "program_name": str,
            "program_category": str,      # Maternal Health | Mental Health | ... | Other
            "program_description": str,   # 1–2 sentences
            "target_population": str,
            "eligibility_requirements": str,
            "application_process": str,
            "required_documentation": str,
            "financial_assistance_available": str, # Yes | No | Unknown
            "program_website_url": str
        }
    ],
    "notes": str
}
```

---

## Contact Extraction Patterns

```python
import re

PHONE_PATTERN = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
ADDRESS_PATTERN = r'\d+\s+[\w\s]+,\s*[\w\s]+,\s*[A-Z]{2}\s+\d{5}'

def extract_contacts(html_text):
    phones = re.findall(PHONE_PATTERN, html_text)
    emails = re.findall(EMAIL_PATTERN, html_text)
    return {"phones": phones, "emails": emails}
```

---

## LLM Prompt Template

```python
EXTRACTION_PROMPT = """
You are extracting structured data about a maternal health program from a county government website.

CONTENT:
{page_content}

Extract the following fields. Use "NOT_FOUND" if information is not present:

Return a JSON object with:
1. county_name, state, county_website_url
2. health_department_name, health_department_contact_email, health_department_contact_phone
3. programs[] with: program_name, program_category, program_description, target_population,
   eligibility_requirements, application_process, required_documentation, financial_assistance_available,
   program_website_url
4. notes
Rules:
- Use "Not found" or "Not specified" for missing info (never invent).
- If none found, return programs: [].

Respond in JSON format.
"""
```

---

## Pilot Counties

Start with these 5 counties (selected for website diversity and known programs):

| County | Health Dept URL | Known Programs |
|--------|-----------------|----------------|
| San Diego | sandiegocounty.gov/hhsa | First 5, Black Infant Health, MCAH |
| Alameda | acphd.org | Healthy Start, WIC, Home Visiting |
| Fresno | co.fresno.ca.us/departments/public-health | Perinatal Equity, Title V |
| Sacramento | dhs.saccounty.gov | MCAH, Nurse-Family Partnership |
| Kern | kerncounty.com/departments/public-health | WIC, Home Visiting |

---

## Quality Metrics

Calculate these after each run:

```python
def calculate_quality(programs):
    metrics = {
        "field_completeness": sum(1 for f in fields if program[f]) / len(fields),
        "contact_availability": 1 if (program["contact_phone"] or program["contact_email"]) else 0,
        "actionability": (
            (1 if program["eligibility"] != "NOT_FOUND" else 0) +
            (1 if program["application_process"] != "NOT_FOUND" else 0) +
            (1 if program["contact_phone"] or program["contact_email"] else 0)
        ) / 3,
        "funding_captured": 1 if program["funding_source"] != "NOT_FOUND" else 0
    }
    return metrics

# Targets:
# - Field completeness: 70%+ (was 47%)
# - Contact availability: 80%+ (was 2.3%)
# - Actionability: 60%+ (was 14.7%)
# - Funding captured: 50%+ (was ~0%)
```

---

## File Structure

```
itreds-maternal-health/
├── config/
│   ├── counties.json          # County URLs and metadata
│   └── keywords.json          # Search term configurations
├── scrapers/
│   ├── discovery.py           # Phase 1: Find program links
│   ├── extraction.py          # Phase 2: Scrape page content
│   └── contacts.py            # Contact info extraction
├── processing/
│   ├── llm_structuring.py     # Phase 3: LLM field extraction
│   └── validation.py          # Phase 4: Quality scoring
├── data/
│   ├── raw/                   # Raw HTML content
│   ├── structured/            # JSON/CSV outputs
│   └── reports/               # Quality reports
└── tests/
    └── test_single_county.py  # Test with one county first
```

---

## Rate Limiting

Be respectful to government servers:

```python
import time
from random import uniform

def polite_request(url, session):
    time.sleep(uniform(1.0, 2.0))  # Random 1-2 second delay
    response = session.get(url, timeout=30)
    return response
```

---

## $5 Budget Plan (OpenAI gpt-4o-mini)

- Keep subpage scraping OFF for the first full run.
- Keep `MAX_CONTENT_LENGTH` at 10k–12k chars; consider lowering to 10k.
- Reduce LLM `max_tokens` to ~1500 for responses (still enough for full JSON).
- Start with 5-county pilot; verify output volume; then run all 58.
- Set a hard usage cap in OpenAI billing (monthly $5; optional daily $1).

Rule-of-Thumb:
- ~4–6k input tokens + ~1k output tokens per county → should remain well under $5 across 58 counties with `gpt-4o-mini`, assuming no deep subpage crawling.

---

## Next Steps for Cursor

1. **Start with San Diego** - Most programs, best-structured site
2. **Build discovery.py first** - Get navigation working
3. **Test contact extraction** - Regex patterns on real pages
4. **Add LLM structuring** - Once you have raw content
5. **Calculate quality** - Verify improvement over pilot

Good luck! The goal is a **replicable workflow**, not just a dataset.