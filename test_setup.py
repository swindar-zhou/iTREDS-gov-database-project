#!/usr/bin/env python3
"""
Quick test script - scrape one county to verify setup works.
Run this before the full scraper!
"""

import requests
from bs4 import BeautifulSoup
import os
from dotenv import load_dotenv

load_dotenv()

def test_scraping():
    """Test basic web scraping on Alameda County."""
    
    print("Testing web scraping...")
    
    url = "https://www.acgov.org/"
    headers = {
        'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36'
    }
    
    try:
        response = requests.get(url, headers=headers, timeout=15)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.content, 'lxml')
        
        # Remove unwanted elements
        for element in soup(['script', 'style', 'nav', 'footer']):
            element.decompose()
        
        text = soup.get_text(separator='\n', strip=True)
        
        print(f"✓ Successfully scraped {url}")
        print(f"  Content length: {len(text)} characters")
        
        # Find health-related links
        health_links = []
        for link in soup.find_all('a', href=True):
            link_text = link.get_text(strip=True).lower()
            if 'health' in link_text:
                health_links.append(link.get_text(strip=True))
        
        print(f"  Health-related links found: {len(health_links)}")
        if health_links[:5]:
            for hl in health_links[:5]:
                print(f"    - {hl}")
        
        return True
        
    except Exception as e:
        print(f"✗ Scraping failed: {e}")
        return False


def test_openai():
    """Test OpenAI API connection."""
    
    api_key = os.getenv("OPENAI_API_KEY", "")
    
    if not api_key or api_key.startswith("sk-your"):
        print("\n⚠ OpenAI API key not configured")
        print("  Set OPENAI_API_KEY in .env file")
        return False
    
    print("\nTesting OpenAI API...")
    
    try:
        import openai
        client = openai.OpenAI(api_key=api_key)
        
        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role": "user", "content": "Say 'API working' in exactly 2 words"}],
            max_tokens=10
        )
        
        result = response.choices[0].message.content
        print(f"✓ OpenAI API working: {result}")
        return True
        
    except Exception as e:
        print(f"✗ OpenAI API error: {e}")
        return False


def test_anthropic():
    """Test Anthropic API connection."""
    
    api_key = os.getenv("ANTHROPIC_API_KEY", "")
    
    if not api_key or api_key.startswith("sk-ant-your"):
        print("\n⚠ Anthropic API key not configured")
        print("  Set ANTHROPIC_API_KEY in .env file")
        return False
    
    print("\nTesting Anthropic API...")
    
    try:
        import anthropic
        client = anthropic.Anthropic(api_key=api_key)
        
        response = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=10,
            messages=[{"role": "user", "content": "Say 'API working' in exactly 2 words"}]
        )
        
        result = response.content[0].text
        print(f"✓ Anthropic API working: {result}")
        return True
        
    except Exception as e:
        print(f"✗ Anthropic API error: {e}")
        return False


def test_ollama():
    """Test local Ollama connectivity."""
    base_url = os.getenv("OLLAMA_BASE_URL", "http://localhost:11434")
    model = os.getenv("OLLAMA_MODEL", "llama3.1:8b-instruct")
    
    print("\nTesting Ollama (local model)...")
    
    try:
        # Quick server check (optional)
        # tags_resp = requests.get(f"{base_url}/api/tags", timeout=5)
        # tags_resp.raise_for_status()
        
        # Minimal chat
        payload = {
            "model": model,
            "messages": [{"role": "user", "content": "Say 'API working' in exactly 2 words"}],
            "stream": False,
            "options": {"temperature": 0.1}
        }
        resp = requests.post(f"{base_url}/api/chat", json=payload, timeout=30)
        resp.raise_for_status()
        data = resp.json()
        text = (data.get("message") or {}).get("content", "").strip()
        print(f"✓ Ollama working: {text}")
        return True
    except Exception as e:
        print(f"⚠ Ollama not available: {e}")
        print("  Install from https://ollama.com and run: ollama serve")
        return False


if __name__ == "__main__":
    print("="*50)
    print("County Scraper - Setup Test")
    print("="*50 + "\n")
    
    scrape_ok = test_scraping()
    openai_ok = test_openai()
    anthropic_ok = test_anthropic()
    ollama_ok = test_ollama()
    
    print("\n" + "="*50)
    print("SUMMARY")
    print("="*50)
    print(f"Web scraping: {'✓ OK' if scrape_ok else '✗ FAILED'}")
    print(f"OpenAI API:   {'✓ OK' if openai_ok else '⚠ Not configured'}")
    print(f"Anthropic API: {'✓ OK' if anthropic_ok else '⚠ Not configured'}")
    print(f"Ollama:       {'✓ OK' if ollama_ok else '⚠ Not available'}")
    
    if scrape_ok and (openai_ok or anthropic_ok):
        print("\n✓ Ready to run scraper!")
        print("  Run: python scraper.py")
    else:
        if scrape_ok and ollama_ok:
            print("\n✓ Ready to run scraper with local model (Ollama)!")
            print("  In .env set: API_PROVIDER=ollama")
            print("  Then run: python scraper.py")
        else:
            print("\n⚠ Please configure at least one provider (OpenAI, Anthropic, or Ollama)")
