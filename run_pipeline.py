#!/usr/bin/env python3
"""
Run the 3-phase pipeline (Discovery → Extraction → Structuring) for a
selected set of California counties.

Default counties (10, excluding San Diego which you already ran):
  Alameda, Fresno, Sacramento, Kern, Los Angeles, San Francisco,
  Orange, Riverside, Santa Clara, Contra Costa
"""

import os
import json
import time
from typing import List, Dict
from datetime import datetime

# Phase 1 helpers
from scraper_discovery import (
    CALIFORNIA_COUNTIES,
    run_discovery_for_county,
)

# Phase 2 helpers
from scraper_extract import (
    process_program_page,
)

# Phase 3 helpers
from scraper_structure import (
    extract_program_openai,
    build_prompt,
    RAW_DIR as STRUCT_RAW_DIR,
    DISCOVERY_PATH as STRUCT_DISCOVERY_PATH,
)

from scraper import save_to_csv, STATE_NAME  # reuse CSV writer

DATA_DIR = "data"
DISCOVERY_PATH = os.path.join(DATA_DIR, "discovery_results.json")
RAW_DIR = os.path.join(DATA_DIR, "raw")

TARGET_COUNTIES = [
    "Alameda",
    "Fresno",
    "Sacramento",
    "Kern",
    "Los Angeles",
    "San Francisco",
    "Orange",
    "Riverside",
    "Santa Clara",
    "Contra Costa",
]

def run_phase_1(county_names: List[str]) -> List[Dict]:
    print("\n=== Phase 1: Discovery ===")
    os.makedirs(DATA_DIR, exist_ok=True)
    results: List[Dict] = []
    for name in county_names:
        base = CALIFORNIA_COUNTIES.get(name)
        if not base:
            print(f"   ⚠ County not found in mapping: {name}")
            continue
        res = run_discovery_for_county(name, base)
        results.append(res)
        time.sleep(1)
    with open(DISCOVERY_PATH, "w", encoding="utf-8") as f:
        json.dump({"generated_at": datetime.now().isoformat(), "results": results}, f, ensure_ascii=False, indent=2)
    print(f"✓ Discovery saved: {DISCOVERY_PATH} ({len(results)} counties)")
    return results

def run_phase_2(discovery_results: List[Dict]) -> None:
    print("\n=== Phase 2: Deep Extraction ===")
    os.makedirs(RAW_DIR, exist_ok=True)
    total = 0
    for entry in discovery_results:
        county = entry.get("county_name", "")
        programs = entry.get("programs", [])
        print(f"County: {county} — {len(programs)} pages")
        for p in programs:
            try:
                out_path = process_program_page(county, p)
                if out_path:
                    print(f"   ✓ Saved raw: {out_path}")
                    total += 1
                else:
                    print("   ⚠ Skipped (fetch failed)")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            time.sleep(0.5)
    print(f"✓ Phase 2 complete. Raw pages saved: {total}")

def run_phase_3(discovery_results: List[Dict]) -> None:
    print("\n=== Phase 3: LLM Structuring ===")
    # Map county -> county_url
    county_meta = {r.get("county_name",""): r for r in discovery_results}
    # Collect raw files for selected counties
    structured_by_county: Dict[str, Dict] = {}
    # Walk raw directory
    for county in county_meta.keys():
        county_slug = county.strip().lower().replace(" ", "-")
        county_dir = os.path.join(RAW_DIR, county_slug)
        if not os.path.isdir(county_dir):
            continue
        for fname in os.listdir(county_dir):
            if not fname.endswith(".json"):
                continue
            path = os.path.join(county_dir, fname)
            try:
                with open(path, "r", encoding="utf-8") as f:
                    page = json.load(f)
            except Exception as e:
                print(f"   ✗ Failed to read {path}: {e}")
                continue
            county_name = page.get("county", county)
            county_url = county_meta.get(county_name, {}).get("county_url", "")
            prompt = build_prompt(county_name, county_url, page)
            result = extract_program_openai(prompt)
            time.sleep(0.5)
            if not result:
                print(f"   ⚠ No result for {fname}")
                continue
            if county_name not in structured_by_county:
                structured_by_county[county_name] = {
                    "county_name": county_name,
                    "state": STATE_NAME,
                    "county_website_url": county_url,
                    "health_department_name": result.get("health_department_name", "Not found"),
                    "health_department_contact_email": result.get("health_department_contact_email", "Not found"),
                    "health_department_contact_phone": result.get("health_department_contact_phone", "Not found"),
                    "programs": [],
                    "notes": ""
                }
            structured_by_county[county_name]["programs"].extend(result.get("programs", []))
            if result.get("notes"):
                prev = structured_by_county[county_name].get("notes", "")
                structured_by_county[county_name]["notes"] = (prev + " " + str(result["notes"])).strip()
            print(f"   ✓ Structured: {fname} → {len(result.get('programs', []))} program(s)")
    results_list = list(structured_by_county.values())
    if not results_list:
        print("⚠ No structured results produced")
        return
    # Save per-county CSVs under data/structured
    os.makedirs(os.path.join("data", "structured"), exist_ok=True)
    def safe_name(name: str) -> str:
        return name.replace(" ", "_")
    for county in results_list:
        fname = os.path.join("data", "structured", f"{STATE_NAME}_{safe_name(county.get('county_name','Unknown'))}_Healthcare_Data.csv")
        save_to_csv([county], fname)
        print(f"✓ Wrote county CSV: {fname}")
    # Combined CSV (optional)
    # save_to_csv(results_list, "California_County_Healthcare_Data.csv")
    # print("✓ Combined CSV: California_County_Healthcare_Data.csv")

def main():
    print("\n" + "="*60)
    print("🚀 Run Pipeline for 10 Counties")
    print("="*60)
    print("Counties:", ", ".join(TARGET_COUNTIES))
    results = run_phase_1(TARGET_COUNTIES)
    run_phase_2(results)
    run_phase_3(results)
    print("\nDone.")

if __name__ == "__main__":
    main()


