# County Healthcare Data Scraper

**iTREDS Project** - Extract healthcare program data from California county websites using LLMs.

## Quick Start (3-phase pipeline)

```bash
# 1) Install dependencies
pip install -r requirements.txt

# 2) Configure your provider
cp .env.example .env
# Edit .env and set API provider and keys as needed
#   API_PROVIDER=openai        # or "anthropic" or "ollama"
# If OpenAI/Anthropic: add your API key
# If Ollama (local): install from https://ollama.com and pull a model:
#   ollama pull llama3.1:8b-instruct

# 3) Test the setup
python test_setup.py

# 4) Run the pilot pipeline (5 counties)
# Phase 1 - Discovery (collect candidate program links)
python scraper_discovery.py

# Phase 2 - Deep Extraction (fetch program pages, contacts, PDFs)
python scraper_extract.py

# Phase 3 - LLM Structuring (OpenAI gpt-4o-mini by default)
# Produces California_County_Healthcare_Data.csv
python scraper_structure.py
```

## How it works (explained with visuals)

This project runs in three simple phases. You don’t need prior context—think of it like a web “treasure hunt”:

```
PHASE 1: DISCOVERY            PHASE 2: DEEP EXTRACTION         PHASE 3: STRUCTURING
┌─────────────────────┐       ┌────────────────────────┐       ┌─────────────────────────┐
│ Start at County URL │  ──▶  │ Open each Program Page │  ──▶  │ Turn Text → Spreadsheet │
│  → Find Health Dept │       │  → Read the full text  │       │  → 1 row per program    │
│  → Find Maternal/MCH│       │  → Grab phones/emails  │       │  → CSV output           │
│  → Collect program  │       │  → Save page as JSON   │       │                         │
│    links (WIC, BIH) │       │    (raw content)       │       │                         │
└─────────────────────┘       └────────────────────────┘       └─────────────────────────┘
```

### Phase 1 — Discovery (what pages should we read?)
- Goal: Find the right pages on each county’s website that likely describe maternal health programs.
- Navigation recipe:
  - County homepage → Health Department → Maternal/Child Health section → Program pages (e.g., WIC, Healthy Start, BIH, Home Visiting).
  - We score links using keywords (department, section, and program levels).
- Output:
  - `data/discovery_results.json` with, per county:
    - `health_dept_url`, `maternal_section_url`
    - `programs[]` = list of candidate program links and how we got there.
- Why it matters: County sites are organized differently; a small, smart crawl gets you to the right pages quickly without breaking sites or budgets.

Mini visual
```
County Home
   │
   ├─▶ Health Department (Public Health / HHSA)
   │      │
   │      └─▶ Maternal/Child Health (MCH/MCAH/Women’s/Family)
   │              │
   │              └─▶ Program Pages (WIC, BIH, Home Visiting, NFP, etc.)
   │
   └─▶ (Ignore social/external links)
```

### Phase 2 — Deep Content Extraction (what’s on those pages?)
- Goal: For every program page found in Phase 1, fetch the content and capture helpful signals.
- What we do on each page:
  - Read HTML and strip layout (nav/header/footer).
  - Extract clean text (truncated to keep things fast).
  - Pull contact info via regex (phone numbers, emails).
  - Collect document links, especially “Eligibility”, “Apply”, “Application”, and “Brochure” PDFs.
- Output per page:
  - `data/raw/{county}/{program-slug}-{hash}.json` containing:
    - `page_url`, `link_text`, `nav_path`
    - `text` (main content), `contacts { phones[], emails[] }`
    - `pdf_links[]`

Mini visual
```
Program Page HTML
   │
   ├─▶ Strip layout → get main text
   ├─▶ Regex phones/emails
   └─▶ Collect likely PDFs (eligibility/apply/brochure)
        ↳ Save as raw JSON per page
```

### Phase 3 — LLM Structuring (turn the text into a consistent table)
- Goal: Convert unstructured text from Phase 2 into a clean, consistent dataset.
- How it works:
  - For each raw page JSON, we send up to ~10k characters to OpenAI `gpt-4o-mini`.
  - The model returns a small JSON object (program name, category, eligibility, application process, contact, link).
  - We aggregate all programs per county and write one CSV.
- Budget guardrails:
  - Input text truncated to 10k characters.
  - `max_tokens=1500`, `temperature=0.1`.
  - Short delay between calls.
- Output:
  - `California_County_Healthcare_Data.csv` (one row per program).

Mini visual
```
Raw Page JSON (text + contacts + PDFs)
   │
   └─▶ LLM (JSON-only prompt)
         │
         └─▶ Structured Program Object(s)
               │
               └─▶ Aggregated by County → CSV
```

Tip for visual learners
- There’s an interactive visualization of this workflow in `workflow-visuals.jsx` that you can drop into any React app to demo the process with panels and timelines.

## Configuration

Edit `.env` file:

```bash
API_PROVIDER=openai              # or "anthropic" or "ollama"
OPENAI_API_KEY=openai-key        # Your OpenAI key
ANTHROPIC_API_KEY=sk-ant-key     # Your Anthropic key (if used)
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=llama3.1:8b-instruct
DATA_COLLECTOR_NAME=Swindar    # For attribution
```

### Using Ollama (free, local model)
- Install Ollama on macOS: see `https://ollama.com`
- Pull a small instruction-tuned model (recommended for structure extraction):
  - `ollama pull llama3.1:8b-instruct` (default in `.env`)
  - Alternatives: `qwen2.5:7b-instruct`, `mistral:7b-instruct`
- In `.env`, set `API_PROVIDER=ollama`
- Run `python test_setup.py` to confirm Ollama connectivity
- Run `python scraper.py`

## Output

Phase outputs:
- Phase 1: `data/discovery_results.json`
- Phase 2: `data/raw/{county}/*.json` (one per program page)
- Phase 3: Per‑county CSVs in `data/structured/`:
  - `data/structured/California_<County>_Healthcare_Data.csv`
  - Plus a combined file `California_County_Healthcare_Data.csv` for convenience

## Pilot on Fewer Counties or Full Run

The `run_pipeline.py` script targets 10 counties by default:
- Alameda, Fresno, Sacramento, Kern, Los Angeles, San Francisco, Orange, Riverside, Santa Clara, Contra Costa

To run individual phases or customize counties:
- **Phase 1 only**: `python scraper_discovery.py` (modify the county list in the script)
- **Phase 2 only**: `python scraper_extract.py` (processes `data/discovery_results.json`)
- **Phase 3 only**: `python scraper_structure.py` (processes `data/raw/` files)

For the legacy all-in-one script:
```python
# python scraper.py
# Inside it, you may uncomment the slice to limit counties:
# counties_to_process = counties_to_process[:5]
```

## Files

### Core Scripts
- `scraper_discovery.py` - Phase 1: Discovery (collect program links for counties)
- `scraper_extract.py` - Phase 2: Deep extraction (raw page JSON with contacts/PDFs)
- `scraper_structure.py` - Phase 3: LLM structuring → CSV (budget‑guarded)
- `run_pipeline.py` - Orchestrates all 3 phases for 10 preselected counties
- `scraper.py` - Legacy all-in-one scraper (OpenAI/Anthropic/Ollama)

### Configuration & Setup
- `test_setup.py` - Connectivity checks for API providers (OpenAI/Anthropic/Ollama)
- `.env.example` - Template for environment configuration
- `.env` - Your local configuration (gitignored, create from `.env.example`)
- `requirements.txt` - Python dependencies

### Documentation & Assets
- `workflow-demo/workflow-ref.md` - Detailed workflow documentation
- `workflow-demo/workflow-visuals.jsx` - React component for workflow visualization

## Folder Structure

```
iTREDS-gov-database-project-1/
├── data/
│   ├── discovery_results.json        # Phase 1 output: discovered program links per county
│   ├── raw/                          # Phase 2 output: raw page content per county
│   │   ├── {county-slug}/
│   │   │   └── program-{hash}.json   # One JSON file per program page
│   │   ├── los-angeles/              # Example: Los Angeles county raw data
│   │   └── san-diego/                # Example: San Diego county raw data
│   ├── structured/                   # Phase 3 output: structured CSV files
│   │   ├── California_{County}_Healthcare_Data.csv  # Per-county CSVs
│   │   ├── California_Los_Angeles_Healthcare_Data.csv
│   │   └── California_County_Healthcare_Data_San_Diego.csv
│   ├── reports/                      # Quality reports (future)
│   └── Raw_Data.csv                  # Legacy combined raw data (if generated)
├── workflow-demo/                    # Workflow visualization assets
│   ├── workflow-ref.md              # Workflow documentation
│   └── workflow-visuals.jsx         # React component for workflow visualization
├── scraper_discovery.py              # Phase 1: Discovery script
├── scraper_extract.py                # Phase 2: Deep extraction script
├── scraper_structure.py              # Phase 3: LLM structuring script
├── scraper.py                        # Legacy all-in-one scraper
├── run_pipeline.py                   # Batch runner for 10 counties (orchestrates all 3 phases)
├── test_setup.py                     # Connectivity checks for API providers
├── requirements.txt                  # Python dependencies
├── .env.example                      # Environment configuration template
├── .env                              # Your local config (gitignored, not in repo)
├── .gitignore                        # Git ignore rules
└── California_County_Healthcare_Data.csv  # Phase 3 combined CSV output (optional)
```

## Budget Guardrails (OpenAI)
- `scraper_structure.py` truncates input text to 10k chars and caps `max_tokens` to 1500.
- Keep subpage recursion off for the pilot.
- Optional: set a monthly cap (e.g., $5) in OpenAI billing.
