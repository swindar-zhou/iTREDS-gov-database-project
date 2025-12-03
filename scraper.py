#!/usr/bin/env python3
"""
County Healthcare Data Scraper
iTREDS Project

Scrapes California county websites and extracts healthcare program information
using Large Language Models.
"""

import requests
import json
import csv
import time
import os
import re
from bs4 import BeautifulSoup
from datetime import datetime
from typing import List, Dict, Optional, Tuple
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# =============================================================================
# CONFIGURATION - Edit these settings
# =============================================================================

# API Provider: "openai" or "anthropic"
API_PROVIDER = os.getenv("API_PROVIDER", "openai")

# API Keys (set via environment variables or .env file)
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY", "")
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")

# Local LLM (Ollama) settings
OLLAMA_BASE_URL = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")

# Project settings
STATE_NAME = "California"
DATA_COLLECTOR_NAME = os.getenv("DATA_COLLECTOR_NAME", "Your Name")
OUTPUT_FILE = "California_County_Healthcare_Data.csv"

# Scraping settings
MAX_CONTENT_LENGTH = 12000  # Characters to send to LLM
REQUEST_TIMEOUT = 20  # Seconds
DELAY_BETWEEN_REQUESTS = 3  # Seconds - be nice to servers

# =============================================================================
# CALIFORNIA COUNTIES - All 58 counties with official URLs
# =============================================================================

CALIFORNIA_COUNTIES = {
    "Alameda": "https://www.acgov.org/",
    "Alpine": "https://www.alpinecountyca.gov/",
    "Amador": "https://www.amadorgov.org/",
    "Butte": "https://www.buttecounty.net/",
    "Calaveras": "https://www.calaverasgov.us/",
    "Colusa": "https://www.countyofcolusa.org/",
    "Contra Costa": "https://www.contracosta.ca.gov/",
    "Del Norte": "https://www.dnco.org/",
    "El Dorado": "https://www.edcgov.us/",
    "Fresno": "https://www.co.fresno.ca.us/",
    "Glenn": "https://www.countyofglenn.net/",
    "Humboldt": "https://www.humboldtgov.org/",
    "Imperial": "https://www.co.imperial.ca.us/",
    "Inyo": "https://www.inyocounty.us/",
    "Kern": "https://www.kerncounty.com/",
    "Kings": "https://www.countyofkings.com/",
    "Lake": "https://www.lakecountyca.gov/",
    "Lassen": "https://www.lassencounty.org/",
    "Los Angeles": "https://www.lacounty.gov/",
    "Madera": "https://www.maderacounty.com/",
    "Marin": "https://www.marincounty.org/",
    "Mariposa": "https://www.mariposacounty.org/",
    "Mendocino": "https://www.mendocinocounty.org/",
    "Merced": "https://www.co.merced.ca.us/",
    "Modoc": "https://www.co.modoc.ca.us/",
    "Mono": "https://monocounty.ca.gov/",
    "Monterey": "https://www.co.monterey.ca.us/",
    "Napa": "https://www.countyofnapa.org/",
    "Nevada": "https://www.mynevadacounty.com/",
    "Orange": "https://www.ocgov.com/",
    "Placer": "https://www.placer.ca.gov/",
    "Plumas": "https://www.plumascounty.us/",
    "Riverside": "https://www.rivco.org/",
    "Sacramento": "https://www.saccounty.net/",
    "San Benito": "https://www.cosb.us/",
    "San Bernardino": "https://www.sbcounty.gov/",
    "San Diego": "https://www.sandiegocounty.gov/",
    "San Francisco": "https://sf.gov/",
    "San Joaquin": "https://www.sjgov.org/",
    "San Luis Obispo": "https://www.slocounty.ca.gov/",
    "San Mateo": "https://www.smcgov.org/",
    "Santa Barbara": "https://www.countyofsb.org/",
    "Santa Clara": "https://www.sccgov.org/",
    "Santa Cruz": "https://www.santacruzcounty.us/",
    "Shasta": "https://www.co.shasta.ca.us/",
    "Sierra": "https://www.sierracounty.ca.gov/",
    "Siskiyou": "https://www.co.siskiyou.ca.us/",
    "Solano": "https://www.solanocounty.com/",
    "Sonoma": "https://sonomacounty.ca.gov/",
    "Stanislaus": "https://www.stancounty.com/",
    "Sutter": "https://www.suttercounty.org/",
    "Tehama": "https://www.co.tehama.ca.us/",
    "Trinity": "https://www.trinitycounty.org/",
    "Tulare": "https://tularecounty.ca.gov/",
    "Tuolumne": "https://www.tuolumnecounty.ca.gov/",
    "Ventura": "https://www.ventura.org/",
    "Yolo": "https://www.yolocounty.org/",
    "Yuba": "https://www.yuba.org/"
}

# =============================================================================
# WEB SCRAPING FUNCTIONS
# =============================================================================

def scrape_website(url: str) -> Tuple[Optional[str], List[str]]:
    """
    Scrape a county website and extract text content.
    
    Returns:
        Tuple of (text_content, health_related_links)
    """
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
        'Accept': 'text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8',
        'Accept-Language': 'en-US,en;q=0.5',
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=REQUEST_TIMEOUT)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove script, style, nav, footer elements
        for element in soup(['script', 'style', 'nav', 'footer', 'header', 'aside', 'noscript']):
            element.decompose()
        
        # Find health-related links
        health_keywords = ['health', 'medical', 'clinic', 'hospital', 'mental', 'behavioral', 
                          'public health', 'services', 'programs', 'assistance', 'care']
        health_links = []
        
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            href = link['href'].lower()
            if any(kw in link_text or kw in href for kw in health_keywords):
                full_url = link['href']
                if not full_url.startswith('http'):
                    full_url = url.rstrip('/') + '/' + full_url.lstrip('/')
                health_links.append(full_url)
        
        # Extract text content
        text = soup.get_text(separator='\n', strip=True)
        
        # Clean up whitespace
        text = re.sub(r'\n{3,}', '\n\n', text)
        text = re.sub(r' {2,}', ' ', text)
        
        # Truncate to max length
        if len(text) > MAX_CONTENT_LENGTH:
            text = text[:MAX_CONTENT_LENGTH] + "\n\n[Content truncated...]"
        
        return text, health_links[:20]  # Return up to 20 health links
        
    except requests.exceptions.Timeout:
        print(f"    ⚠ Timeout after {REQUEST_TIMEOUT}s")
        return None, []
    except requests.exceptions.RequestException as e:
        print(f"    ⚠ Request error: {e}")
        return None, []
    except Exception as e:
        print(f"    ⚠ Error: {e}")
        return None, []


def scrape_health_subpages(health_links: List[str], max_pages: int = 3) -> str:
    """
    Scrape additional health-related subpages for more program information.
    """
    additional_content = []
    
    for i, link in enumerate(health_links[:max_pages]):
        try:
            print(f"    → Scraping subpage {i+1}: {link[:60]}...")
            content, _ = scrape_website(link)
            if content:
                additional_content.append(f"\n\n--- SUBPAGE: {link} ---\n{content[:4000]}")
            time.sleep(1)
        except Exception as e:
            print(f"    ⚠ Error scraping subpage: {e}")
    
    return "\n".join(additional_content)

# =============================================================================
# LLM EXTRACTION FUNCTIONS
# =============================================================================

def get_extraction_prompt(content: str, county_name: str, county_url: str, health_links: List[str]) -> str:
    """Generate the prompt for LLM extraction."""
    
    return f"""You are extracting healthcare program information from a {STATE_NAME} county government website.

COUNTY: {county_name} County
WEBSITE: {county_url}

HEALTH-RELATED LINKS FOUND:
{json.dumps(health_links[:10], indent=2) if health_links else "None found"}

WEBSITE CONTENT:
{content}

---

TASK: Extract ALL healthcare programs and services mentioned. Return ONLY valid JSON in this exact format:

{{
    "county_name": "{county_name}",
    "state": "{STATE_NAME}",
    "county_website_url": "{county_url}",
    "health_department_name": "Official name of health department or 'Not found'",
    "health_department_contact_email": "Email if found or 'Not found'",
    "health_department_contact_phone": "Phone if found or 'Not found'",
    "programs": [
        {{
            "program_name": "Name of healthcare program",
            "program_category": "Category: Maternal Health | Mental Health | Substance Abuse | Immunization | Chronic Disease | Emergency Services | Primary Care | Dental | Vision | Other",
            "program_description": "Brief description (1-2 sentences)",
            "target_population": "Who the program serves",
            "eligibility_requirements": "Requirements or 'Not specified'",
            "application_process": "How to apply or 'Not specified'",
            "required_documentation": "Documents needed or 'Not specified'",
            "financial_assistance_available": "Yes | No | Unknown",
            "program_website_url": "Specific URL if available or 'Not found'"
        }}
    ],
    "notes": "Any data quality observations"
}}

IMPORTANT RULES:
1. Extract ALL healthcare programs mentioned - aim for completeness
2. Use "Not found" or "Not specified" for missing information - never invent data
3. If no programs are found, return empty programs array
4. Return ONLY the JSON object, no other text
5. Ensure valid JSON syntax"""


def extract_with_openai(content: str, county_name: str, county_url: str, health_links: List[str]) -> Optional[Dict]:
    """Extract healthcare data using OpenAI API."""
    
    if not OPENAI_API_KEY:
        print("    ✗ OpenAI API key not set")
        return None
    
    try:
        import openai
        client = openai.OpenAI(api_key=OPENAI_API_KEY)
        
        prompt = get_extraction_prompt(content, county_name, county_url, health_links)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",  # Cost-effective, good for extraction
            messages=[
                {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.1,
            max_tokens=4000
        )
        
        result_text = response.choices[0].message.content.strip()
        
        # Clean up response - remove markdown code blocks if present
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)
        
        return json.loads(result_text)
        
    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    ✗ OpenAI error: {e}")
        return None


def extract_with_anthropic(content: str, county_name: str, county_url: str, health_links: List[str]) -> Optional[Dict]:
    """Extract healthcare data using Anthropic API."""
    
    if not ANTHROPIC_API_KEY:
        print("    ✗ Anthropic API key not set")
        return None
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=ANTHROPIC_API_KEY)
        
        prompt = get_extraction_prompt(content, county_name, county_url, health_links)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=4000,
            messages=[
                {"role": "user", "content": prompt}
            ]
        )
        
        result_text = response.content[0].text.strip()
        
        # Clean up response
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)
        
        return json.loads(result_text)
        
    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error: {e}")
        return None
    except Exception as e:
        print(f"    ✗ Anthropic error: {e}")
        return None


def extract_with_ollama(content: str, county_name: str, county_url: str, health_links: List[str]) -> Optional[Dict]:
    """Extract healthcare data using a local Ollama model (no API cost)."""
    try:
        prompt = get_extraction_prompt(content, county_name, county_url, health_links)
        
        # Use Ollama chat API to get a single non-streaming response
        payload = {
            "model": OLLAMA_MODEL,
            "messages": [
                {"role": "system", "content": "You are a data extraction assistant. Return only valid JSON."},
                {"role": "user", "content": prompt}
            ],
            "stream": False,
            # Keep deterministic for schema extraction
            "options": {"temperature": 0.1}
        }
        
        resp = requests.post(f"{OLLAMA_BASE_URL}/api/chat", json=payload, timeout=60)
        resp.raise_for_status()
        data = resp.json()
        
        # Ollama returns {"message":{"role":"assistant","content":"..."}, ...}
        result_text = (data.get("message") or {}).get("content", "").strip()
        if not result_text:
            print("    ✗ Ollama returned empty response")
            return None
        
        # Clean possible markdown fences
        if result_text.startswith("```"):
            result_text = re.sub(r'^```(?:json)?\n?', '', result_text)
            result_text = re.sub(r'\n?```$', '', result_text)
        
        return json.loads(result_text)
    except json.JSONDecodeError as e:
        print(f"    ✗ JSON parse error (ollama): {e}")
        return None
    except requests.RequestException as e:
        print(f"    ✗ Ollama HTTP error: {e}")
        return None
    except Exception as e:
        print(f"    ✗ Ollama error: {e}")
        return None


def extract_data(content: str, county_name: str, county_url: str, health_links: List[str]) -> Optional[Dict]:
    """Extract data using configured API provider."""
    
    if API_PROVIDER == "openai":
        return extract_with_openai(content, county_name, county_url, health_links)
    elif API_PROVIDER == "anthropic":
        return extract_with_anthropic(content, county_name, county_url, health_links)
    elif API_PROVIDER == "ollama":
        return extract_with_ollama(content, county_name, county_url, health_links)
    else:
        print(f"    ✗ Unknown API provider: {API_PROVIDER}")
        return None

# =============================================================================
# CSV OUTPUT
# =============================================================================

def save_to_csv(results: List[Dict], filename: str):
    """Save extracted data to CSV file."""
    
    fieldnames = [
        'State', 'County_Name', 'County_Website_URL',
        'Health_Department_Name', 'Health_Department_Contact_Email', 'Health_Department_Contact_Phone',
        'Program_Name', 'Program_Category', 'Program_Description',
        'Target_Population', 'Eligibility_Requirements', 'Application_Process',
        'Required_Documentation', 'Financial_Assistance_Available', 'Program_Website_URL',
        'Last_Updated', 'Data_Collector_Name', 'Notes'
    ]
    
    rows = []
    
    for county_data in results:
        programs = county_data.get('programs', [])
        
        if not programs:
            # Still create a row even if no programs found
            rows.append({
                'State': county_data.get('state', STATE_NAME),
                'County_Name': county_data.get('county_name', ''),
                'County_Website_URL': county_data.get('county_website_url', ''),
                'Health_Department_Name': county_data.get('health_department_name', ''),
                'Health_Department_Contact_Email': county_data.get('health_department_contact_email', ''),
                'Health_Department_Contact_Phone': county_data.get('health_department_contact_phone', ''),
                'Program_Name': 'No programs found on main page',
                'Program_Category': '',
                'Program_Description': '',
                'Target_Population': '',
                'Eligibility_Requirements': '',
                'Application_Process': '',
                'Required_Documentation': '',
                'Financial_Assistance_Available': '',
                'Program_Website_URL': '',
                'Last_Updated': datetime.now().strftime('%Y-%m-%d'),
                'Data_Collector_Name': DATA_COLLECTOR_NAME,
                'Notes': county_data.get('notes', '')
            })
        else:
            # One row per program
            for program in programs:
                rows.append({
                    'State': county_data.get('state', STATE_NAME),
                    'County_Name': county_data.get('county_name', ''),
                    'County_Website_URL': county_data.get('county_website_url', ''),
                    'Health_Department_Name': county_data.get('health_department_name', ''),
                    'Health_Department_Contact_Email': county_data.get('health_department_contact_email', ''),
                    'Health_Department_Contact_Phone': county_data.get('health_department_contact_phone', ''),
                    'Program_Name': program.get('program_name', ''),
                    'Program_Category': program.get('program_category', ''),
                    'Program_Description': program.get('program_description', ''),
                    'Target_Population': program.get('target_population', ''),
                    'Eligibility_Requirements': program.get('eligibility_requirements', ''),
                    'Application_Process': program.get('application_process', ''),
                    'Required_Documentation': program.get('required_documentation', ''),
                    'Financial_Assistance_Available': program.get('financial_assistance_available', ''),
                    'Program_Website_URL': program.get('program_website_url', ''),
                    'Last_Updated': datetime.now().strftime('%Y-%m-%d'),
                    'Data_Collector_Name': DATA_COLLECTOR_NAME,
                    'Notes': county_data.get('notes', '')
                })
    
    with open(filename, 'w', newline='', encoding='utf-8') as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)
    
    print(f"\n✓ Saved {len(rows)} rows to {filename}")

# =============================================================================
# MAIN EXECUTION
# =============================================================================

def main():
    """Main scraping workflow."""
    
    print("\n" + "="*60)
    print("🏥 County Healthcare Data Scraper")
    print("="*60)
    print(f"State: {STATE_NAME}")
    print(f"API Provider: {API_PROVIDER}")
    print(f"Data Collector: {DATA_COLLECTOR_NAME}")
    print(f"Total Counties: {len(CALIFORNIA_COUNTIES)}")
    print("="*60 + "\n")
    
    # Check API key
    if API_PROVIDER == "openai" and not OPENAI_API_KEY:
        print("❌ ERROR: OPENAI_API_KEY not set!")
        print("   Set it in .env file or export OPENAI_API_KEY=your-key")
        return
    elif API_PROVIDER == "anthropic" and not ANTHROPIC_API_KEY:
        print("❌ ERROR: ANTHROPIC_API_KEY not set!")
        print("   Set it in .env file or export ANTHROPIC_API_KEY=your-key")
        return
    
    # Select counties to process
    # For testing, start with a small batch
    counties_to_process = list(CALIFORNIA_COUNTIES.items())
    
    # Uncomment to limit for testing:
    # counties_to_process = counties_to_process[:5]
    
    print(f"Processing {len(counties_to_process)} counties...\n")
    
    results = []
    successful = 0
    failed = 0
    
    for i, (county_name, url) in enumerate(counties_to_process, 1):
        print(f"[{i}/{len(counties_to_process)}] {county_name} County")
        print(f"    URL: {url}")
        
        # Step 1: Scrape main page
        content, health_links = scrape_website(url)
        
        if not content:
            print(f"    ✗ Could not fetch content\n")
            failed += 1
            continue
        
        print(f"    ✓ Extracted {len(content)} chars, found {len(health_links)} health links")
        
        # Step 2: Optionally scrape health subpages for more data
        # Uncomment if you want deeper scraping (slower, more API calls)
        # if health_links:
        #     additional = scrape_health_subpages(health_links, max_pages=2)
        #     content += additional
        
        # Step 3: Extract with LLM
        print(f"    → Analyzing with {API_PROVIDER.upper()}...")
        
        data = extract_data(content, county_name, url, health_links)
        
        if data:
            programs_count = len(data.get('programs', []))
            print(f"    ✓ Extracted {programs_count} programs\n")
            results.append(data)
            successful += 1
        else:
            print(f"    ✗ Failed to extract data\n")
            failed += 1
        
        # Rate limiting
        time.sleep(DELAY_BETWEEN_REQUESTS)
    
    # Save results
    if results:
        save_to_csv(results, OUTPUT_FILE)
        
        total_programs = sum(len(r.get('programs', [])) for r in results)
        
        print("\n" + "="*60)
        print("📊 SUMMARY")
        print("="*60)
        print(f"Counties processed: {successful + failed}")
        print(f"Successful: {successful}")
        print(f"Failed: {failed}")
        print(f"Total programs found: {total_programs}")
        print(f"Output file: {OUTPUT_FILE}")
        print("="*60 + "\n")
    else:
        print("\n⚠ No data extracted")


if __name__ == "__main__":
    main()
