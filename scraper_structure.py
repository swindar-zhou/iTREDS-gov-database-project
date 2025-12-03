#!/usr/bin/env python3
"""
Phase 3 - Structuring (Pilot)

Reads Phase 2 raw page JSON under data/raw/** and converts them into structured
program entries using an LLM (OpenAI gpt-4o-mini by default). Aggregates per
county and writes the CSV using scraper.save_to_csv.
"""

import os
import re
import json
import glob
import time
from typing import Dict, List, Optional
from datetime import datetime
from dotenv import load_dotenv

# Import CSV writer from existing scraper (does not execute main)
from scraper import save_to_csv, STATE_NAME  # reuse project constants/CSV writer

load_dotenv()

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

API_PROVIDER = os.getenv("API_PROVIDER", "openai")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")

RAW_DIR = os.path.join("data", "raw")
DISCOVERY_PATH = os.path.join("data", "discovery_results.json")
OUTPUT_FILE = "California_County_Healthcare_Data.csv"

# Budget guardrails
MAX_INPUT_CHARS = 10000   # truncate raw text sent to LLM
OPENAI_MODEL = "gpt-4o-mini"
OPENAI_MAX_TOKENS = 1500  # response cap
TEMPERATURE = 0.1
SLEEP_BETWEEN_CALLS = 0.5

# -----------------------------------------------------------------------------
# Utilities
# -----------------------------------------------------------------------------

def load_discovery(path: str) -> Dict[str, Dict]:
    """Return mapping county_name -> discovery entry (to get county_url, etc.)."""
    if not os.path.exists(path):
        return {}
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    results = data.get("results", [])
    return {r.get("county_name", ""): r for r in results}

def iter_raw_pages() -> List[str]:
    return glob.glob(os.path.join(RAW_DIR, "*", "*.json"))

def build_prompt(county_name: str, county_url: str, page: Dict) -> str:
    text = page.get("text", "")[:MAX_INPUT_CHARS]
    contacts = page.get("contacts", {})
    pdf_links = page.get("pdf_links", [])
    page_url = page.get("page_url", "")
    link_text = page.get("link_text", "")
    nav_path = page.get("nav_path", "")
    return f"""You are extracting structured healthcare program data from a {STATE_NAME} county website page.

COUNTY: {county_name} County
COUNTY WEBSITE: {county_url}
PAGE URL: {page_url}
LINK TEXT: {link_text}
NAVIGATION PATH: {nav_path}
CONTACTS FOUND: {json.dumps(contacts)}
DOC LINKS: {json.dumps(pdf_links[:8])}

PAGE CONTENT:
{text}

---
TASK: Return a JSON object with a single program entry using this schema:
{{
  "county_name": "{county_name}",
  "state": "{STATE_NAME}",
  "county_website_url": "{county_url}",
  "health_department_name": "Official name or 'Not found'",
  "health_department_contact_email": "Email or 'Not found'",
  "health_department_contact_phone": "Phone or 'Not found'",
  "programs": [
    {{
      "program_name": "Name of healthcare program",
      "program_category": "Maternal Health | Mental Health | Substance Abuse | Immunization | Chronic Disease | Emergency Services | Primary Care | Dental | Vision | Other",
      "program_description": "Brief description (1-2 sentences)",
      "target_population": "Who the program serves",
      "eligibility_requirements": "Requirements or 'Not specified'",
      "application_process": "How to apply or 'Not specified'",
      "required_documentation": "Documents needed or 'Not specified'",
      "financial_assistance_available": "Yes | No | Unknown",
      "program_website_url": "{page_url}"
    }}
  ],
  "notes": "Any data quality observations"
}}

RULES:
1) Extract only from provided content/metadata; never invent facts.
2) If a field is missing, use 'Not found' or 'Not specified' as appropriate.
3) Return ONLY the JSON object, no extra text.
"""

def extract_program_openai(prompt: str) -> Optional[Dict]:
    if not OPENAI_API_KEY:
        print("   ✗ OPENAI_API_KEY not set")
        return None
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        resp = client.chat.completions.create(
            model=OPENAI_MODEL,
            messages=[
                {"role": "system", "content": "You are a precise data extraction assistant. Return valid JSON only."},
                {"role": "user", "content": prompt}
            ],
            temperature=TEMPERATURE,
            max_tokens=OPENAI_MAX_TOKENS
        )
        content = resp.choices[0].message.content.strip()
        if content.startswith("```"):
            content = re.sub(r'^```(?:json)?\n?', '', content)
            content = re.sub(r'\n?```$', '', content)
        return json.loads(content)
    except Exception as e:
        print(f"   ✗ OpenAI extraction error: {e}")
        return None

# -----------------------------------------------------------------------------
# Main
# -----------------------------------------------------------------------------

def main():
    print("\n" + "="*60)
    print("🧠 Phase 3 - LLM Structuring (Pilot)")
    print("="*60 + "\n")
    if API_PROVIDER != "openai":
        print("⚠ This script currently supports OpenAI only. Set API_PROVIDER=openai in .env")
        return
    county_meta = load_discovery(DISCOVERY_PATH)
    files = iter_raw_pages()
    if not files:
        print("⚠ No raw pages found. Run Phase 2 first: python scraper_extract.py")
        return
    print(f"Found {len(files)} raw pages\n")
    # Aggregate per county
    county_to_data: Dict[str, Dict] = {}
    for path in files:
        try:
            with open(path, "r", encoding="utf-8") as f:
                page = json.load(f)
        except Exception as e:
            print(f"   ✗ Failed to read {path}: {e}")
            continue
        county_name = page.get("county", "")
        meta = county_meta.get(county_name, {})
        county_url = meta.get("county_url", "")
        prompt = build_prompt(county_name, county_url, page)
        result = extract_program_openai(prompt)
        time.sleep(SLEEP_BETWEEN_CALLS)
        if not result:
            print(f"   ⚠ Skipping (no result) for {os.path.basename(path)}")
            continue
        # Initialize county object if needed
        if county_name not in county_to_data:
            county_to_data[county_name] = {
                "county_name": county_name,
                "state": STATE_NAME,
                "county_website_url": county_url,
                "health_department_name": result.get("health_department_name", "Not found"),
                "health_department_contact_email": result.get("health_department_contact_email", "Not found"),
                "health_department_contact_phone": result.get("health_department_contact_phone", "Not found"),
                "programs": [],
                "notes": ""
            }
        # Append programs (expecting 1, but support multiple)
        programs = result.get("programs", [])
        county_to_data[county_name]["programs"].extend(programs)
        # Merge any notes
        if result.get("notes"):
            joined = county_to_data[county_name].get("notes", "")
            county_to_data[county_name]["notes"] = (joined + " " + str(result["notes"])).strip()
        print(f"   ✓ Structured {os.path.basename(path)} → {len(programs)} program(s)")
    # Convert to list and write CSV
    results_list = list(county_to_data.values())
    if not results_list:
        print("\n⚠ No structured data produced")
        return
    # Save per-county CSVs under data/structured
    os.makedirs(os.path.join("data", "structured"), exist_ok=True)
    def safe_name(name: str) -> str:
        return name.replace(" ", "_")
    for county in results_list:
        county_name = county.get("county_name", "Unknown")
        filename = os.path.join("data", "structured", f"{STATE_NAME}_{safe_name(county_name)}_Healthcare_Data.csv")
        save_to_csv([county], filename)
        print(f"✓ Wrote county CSV: {filename}")
    # Also write combined CSV (backward compatible)
    save_to_csv(results_list, OUTPUT_FILE)
    total_programs = sum(len(c.get("programs", [])) for c in results_list)
    print("\n" + "="*60)
    print("📊 Phase 3 Summary")
    print("="*60)
    print(f"Counties with data: {len(results_list)}")
    print(f"Total programs structured: {total_programs}")
    print(f"Output file (combined): {OUTPUT_FILE}")
    print(f"Per-county files: data/structured/{STATE_NAME}_<County>_Healthcare_Data.csv")
    print("="*60 + "\n")

if __name__ == "__main__":
    main()


