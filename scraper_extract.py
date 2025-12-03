#!/usr/bin/env python3
"""
Phase 2 - Deep Content Extraction (Pilot)

Reads data/discovery_results.json from Phase 1 and fetches the content of each
program page. Extracts main text, basic contact info, and PDF/form links.
Persists one JSON per page under data/raw/{county}/.
"""

import os
import re
import json
import time
import hashlib
import requests
from typing import Dict, List, Optional, Tuple
from bs4 import BeautifulSoup
from datetime import datetime
from urllib.parse import urlparse, urljoin

# -----------------------------------------------------------------------------
# Config
# -----------------------------------------------------------------------------

REQUEST_TIMEOUT = 20
DELAY_BETWEEN_REQUESTS = 2  # polite delay between page fetches
MAX_TEXT_CHARS = 20000
INPUT_PATH = os.path.join("data", "discovery_results.json")
RAW_DIR = os.path.join("data", "raw")

# Contact patterns
PHONE_PATTERN = r'\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}'
EMAIL_PATTERN = r'[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'

# -----------------------------------------------------------------------------
# Helpers
# -----------------------------------------------------------------------------

def slugify(text: str) -> str:
    s = re.sub(r'[^a-zA-Z0-9]+', '-', text.strip().lower())
    s = re.sub(r'-{2,}', '-', s).strip('-')
    return s or "item"

def ensure_dir(path: str) -> None:
    os.makedirs(path, exist_ok=True)

def fetch_soup(url: str) -> Optional[BeautifulSoup]:
    headers = {
        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.5",
    }
    try:
        resp = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        resp.raise_for_status()
        soup = BeautifulSoup(resp.content, "lxml")
        for el in soup(["script", "style", "nav", "footer", "header", "aside", "noscript"]):
            el.decompose()
        return soup
    except Exception:
        return None

def extract_text(soup: BeautifulSoup) -> str:
    text = soup.get_text(separator="\n", strip=True)
    text = re.sub(r'\n{3,}', '\n\n', text)
    text = re.sub(r' {2,}', ' ', text)
    if len(text) > MAX_TEXT_CHARS:
        text = text[:MAX_TEXT_CHARS] + "\n\n[Content truncated...]"
    return text

def collect_pdf_links(soup: BeautifulSoup, base_url: str) -> List[str]:
    pdfs: List[str] = []
    for a in soup.find_all("a", href=True):
        href = a["href"]
        if not href:
            continue
        full = urljoin(base_url, href)
        href_l = href.lower()
        txt_l = a.get_text(strip=True).lower()
        if href_l.endswith(".pdf") or "pdf" in href_l or "pdf" in txt_l:
            # prioritize likely docs
            if any(k in href_l or k in txt_l for k in ["eligibility", "apply", "application", "brochure", "program"]):
                pdfs.append(full)
            else:
                pdfs.append(full)
    # Deduplicate preserving order
    seen = set()
    out: List[str] = []
    for u in pdfs:
        if u not in seen:
            seen.add(u)
            out.append(u)
    return out[:20]

def extract_contacts(text: str) -> Dict[str, List[str]]:
    try:
        phones = re.findall(PHONE_PATTERN, text)
    except re.error:
        phones = []
    try:
        emails = re.findall(EMAIL_PATTERN, text)
    except re.error:
        emails = []
    return {
        "phones": sorted(set(phones)),
        "emails": sorted(set(emails)),
    }

def page_hash(url: str) -> str:
    return hashlib.sha1(url.encode("utf-8")).hexdigest()[:10]

# -----------------------------------------------------------------------------
# Core
# -----------------------------------------------------------------------------

def load_discovery(path: str) -> List[Dict]:
    if not os.path.exists(path):
        raise FileNotFoundError(f"Discovery results not found: {path}")
    with open(path, "r", encoding="utf-8") as f:
        data = json.load(f)
    return data.get("results", [])

def save_raw(county: str, record: Dict) -> str:
    county_dir = os.path.join(RAW_DIR, slugify(county))
    ensure_dir(county_dir)
    # Prefer link text slug + short hash to avoid collisions
    base = slugify(record.get("program_name_guess") or record.get("link_text") or "program")
    fname = f"{base}-{page_hash(record.get('page_url',''))}.json"
    out_path = os.path.join(county_dir, fname)
    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(record, f, ensure_ascii=False, indent=2)
    return out_path

def process_program_page(county: str, program: Dict) -> Optional[str]:
    url = program.get("url", "")
    if not url:
        return None
    soup = fetch_soup(url)
    if not soup:
        return None
    text = extract_text(soup)
    contacts = extract_contacts(text)
    pdf_links = collect_pdf_links(soup, url)
    record = {
        "county": county,
        "page_url": url,
        "link_text": program.get("link_text", ""),
        "program_name_guess": program.get("name", ""),
        "nav_path": program.get("nav_path", ""),
        "scraped_at": datetime.now().isoformat(),
        "text": text,
        "contacts": contacts,
        "pdf_links": pdf_links
    }
    return save_raw(county, record)

def main():
    print("\n" + "="*60)
    print("🕸️ Phase 2 - Deep Content Extraction (Pilot)")
    print("="*60 + "\n")
    try:
        discovery = load_discovery(INPUT_PATH)
    except Exception as e:
        print(f"❌ Cannot load discovery results: {e}")
        print("   Run: python scraper_discovery.py")
        return
    ensure_dir(RAW_DIR)
    total_pages = 0
    saved_files: List[str] = []
    for county_entry in discovery:
        county = county_entry.get("county_name", "")
        programs = county_entry.get("programs", [])
        print(f"County: {county} — {len(programs)} candidate pages")
        for p in programs:
            try:
                out_path = process_program_page(county, p)
                if out_path:
                    total_pages += 1
                    saved_files.append(out_path)
                    print(f"   ✓ Saved: {os.path.basename(out_path)}")
                else:
                    print("   ⚠ Skipped (fetch failed)")
            except Exception as e:
                print(f"   ✗ Error: {e}")
            time.sleep(DELAY_BETWEEN_REQUESTS)
    print(f"\n✓ Completed Phase 2. Raw pages saved: {total_pages}")
    print(f"Output dir: {RAW_DIR}")

if __name__ == "__main__":
    main()


