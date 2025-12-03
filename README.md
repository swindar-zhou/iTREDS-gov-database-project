# County Healthcare Data Scraper

**iTREDS Project** - Extract healthcare program data from California county websites using LLMs.

## Quick Start

```bash
# 1. Install dependencies
pip install -r requirements.txt

# 2. Configure your provider
cp .env.example .env
# Edit .env and set:
#   API_PROVIDER=openai        # or "anthropic" or "ollama"
# If using OpenAI/Anthropic, add your API key
# If using Ollama (local), install from https://ollama.com and pull a model:
#   ollama pull llama3.1:8b-instruct

# 3. Test the setup
python test_setup.py

# 4. Run the scraper (starts with all 58 CA counties)
python scraper.py
```

## Configuration

Edit `.env` file:

```bash
API_PROVIDER=openai              # or "anthropic" or "ollama"
OPENAI_API_KEY=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  # Your OpenAI key
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

Results are saved to `California_County_Healthcare_Data.csv` with one row per healthcare program.

## Testing on Fewer Counties

To test on just a few counties first, edit `scraper.py` line ~290 and uncomment:

```python
# counties_to_process = counties_to_process[:5]  # Process first 5 only
```

## Files

- `scraper.py` - Main scraper script (all 58 CA counties included)
- `test_setup.py` - Test your setup before running
- `.env.example` - Template for configuration
- `requirements.txt` - Python dependencies
