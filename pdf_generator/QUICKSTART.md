# Quick Start Guide

Get up and running with the AI-powered PDF generator in 5 minutes!

## Step 1: Setup Virtual Environment

**Linux/macOS:**
```bash
cd pdf_generator
./setup_venv.sh
source venv/bin/activate
```

**Windows:**
```cmd
cd pdf_generator
setup_venv.bat
venv\Scripts\activate.bat
```

**Or use Make:**
```bash
make setup
source venv/bin/activate
```

## Step 2: Configure API Key

Edit the `.env` file and add your API key:

```bash
# For OpenAI
OPENAI_API_KEY=sk-your-key-here

# OR for Anthropic
ANTHROPIC_API_KEY=sk-ant-your-key-here
```

Get your API key:
- OpenAI: https://platform.openai.com/api-keys
- Anthropic: https://console.anthropic.com/settings/keys

## Step 3: Generate Your First Report

```bash
# Basic PDF (no AI required)
python -m pdf_generator.generate_sample

# AI-powered PDF (requires API key)
python -m pdf_generator.generate_ai_sample
```

## That's It! 🎉

Your PDF will be generated in the `output/` directory.

## Next Steps

- Read [INSTALLATION.md](INSTALLATION.md) for detailed setup
- See [API_KEY_SETUP.md](API_KEY_SETUP.md) for API key troubleshooting
- Check [README.md](README.md) for usage examples
- Review [AI_INTEGRATION_SUMMARY.md](AI_INTEGRATION_SUMMARY.md) for architecture details

## Common Commands

```bash
# Activate virtual environment
source venv/bin/activate  # Linux/macOS
venv\Scripts\activate.bat  # Windows

# Install dependencies
pip install -r requirements.txt

# Install package
pip install -e .

# Run tests
pytest tests/

# Clean up
make clean
```

## Troubleshooting

**Problem:** `./setup_venv.sh: Permission denied`
**Solution:** `chmod +x setup_venv.sh`

**Problem:** `ModuleNotFoundError`
**Solution:** Make sure virtual environment is activated and package is installed: `pip install -e .`

**Problem:** API key not found
**Solution:** Check `.env` file exists and contains your key. See [API_KEY_SETUP.md](API_KEY_SETUP.md)
