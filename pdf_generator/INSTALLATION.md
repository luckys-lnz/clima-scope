# Installation Guide

This guide explains how to set up the Clima-scope PDF Generator in a virtual environment.

## Prerequisites

- Python 3.8 or higher (Python 3.12 recommended for best compatibility)
- pip (Python package manager)
- Git (for cloning the repository)

**Note:** Python 3.14+ may have issues with optional `renderPM` package. See [PYTHON_VERSION_NOTES.md](PYTHON_VERSION_NOTES.md) for details.

## Quick Start

### Option 1: Automated Setup (Recommended)

**Linux/macOS:**
```bash
cd pdf_generator
chmod +x setup_venv.sh
./setup_venv.sh
```

**Windows:**
```cmd
cd pdf_generator
setup_venv.bat
```

This script will:
1. Create a virtual environment
2. Install all dependencies
3. Install the package in editable mode
4. Create a `.env` file template

### Option 2: Manual Setup

#### Step 1: Create Virtual Environment

**Linux/macOS:**
```bash
cd pdf_generator
python3 -m venv venv
source venv/bin/activate
```

**Windows:**
```cmd
cd pdf_generator
python -m venv venv
venv\Scripts\activate.bat
```

#### Step 2: Upgrade pip

```bash
pip install --upgrade pip setuptools wheel
```

#### Step 3: Install Dependencies

**For OpenAI (default):**
```bash
pip install -r requirements.txt
```

**For Anthropic:**
```bash
pip install -r requirements.txt
pip install -r requirements-anthropic.txt
```

**For Development:**
```bash
pip install -r requirements-dev.txt
```

#### Step 4: Install Package

```bash
# Install in editable mode (recommended for development)
pip install -e .

# OR install normally
pip install .
```

#### Step 5: Configure API Key

```bash
# Copy the example file
cp .env.example .env

# Edit .env and add your API key
# See API_KEY_SETUP.md for detailed instructions
```

## Verification

Test the installation:

```bash
# Basic PDF generation (no AI required)
python -m pdf_generator.generate_sample

# AI-powered generation (requires API key)
python -m pdf_generator.generate_ai_sample
```

## Project Structure

After installation, your structure should look like:

```
pdf_generator/
├── venv/                    # Virtual environment (created)
├── .env                     # API keys (create from .env.example)
├── __init__.py
├── ai_service.py
├── config.py
├── enhanced_pdf_builder.py
├── models.py
├── pdf_builder.py
├── report_generator.py
├── requirements.txt
├── requirements-dev.txt
├── requirements-anthropic.txt
├── setup.py
├── pyproject.toml
└── sample_data/
    └── nairobi_sample.json
```

## Using the Package

### As a Library

```python
from pdf_generator.report_generator import ReportGenerator
from pdf_generator.ai_service import AIProvider
from pdf_generator.enhanced_pdf_builder import EnhancedPDFBuilder

# Generate report
generator = ReportGenerator(ai_provider=AIProvider.OPENAI)
complete_report = generator.generate_complete_report(raw_data)

# Create PDF
pdf_builder = EnhancedPDFBuilder(complete_report)
pdf_path = pdf_builder.generate("output/report.pdf")
```

### As a Command-Line Tool

After installation, you can use the command-line tools:

```bash
# Basic generation
clima-pdf-generate

# AI-powered generation
clima-pdf-generate-ai
```

## Development Setup

For development work, install with dev dependencies:

```bash
pip install -e ".[dev]"
```

This includes:
- pytest (testing)
- black (code formatting)
- flake8 (linting)
- mypy (type checking)

## Troubleshooting

### Virtual Environment Issues

**Problem:** `python3 -m venv` not found
**Solution:** Install python3-venv package:
```bash
# Ubuntu/Debian
sudo apt-get install python3-venv

# macOS (with Homebrew)
brew install python3
```

**Problem:** Permission denied when activating venv
**Solution:** Make scripts executable:
```bash
chmod +x venv/bin/activate
```

### Import Errors

**Problem:** `ModuleNotFoundError: No module named 'pdf_generator'`
**Solution:** 
1. Ensure virtual environment is activated
2. Install package: `pip install -e .`
3. Check Python path: `python -c "import sys; print(sys.path)"`

### API Key Issues

**Problem:** API key not found
**Solution:**
1. Check `.env` file exists
2. Verify environment variable is set: `echo $OPENAI_API_KEY`
3. See `API_KEY_SETUP.md` for detailed instructions

### Dependency Conflicts

**Problem:** Package conflicts during installation
**Solution:**
1. Use a fresh virtual environment
2. Upgrade pip: `pip install --upgrade pip`
3. Install dependencies one by one to identify conflicts

### renderPM Build Errors (Python 3.14+)

**Problem:** `ERROR: Failed to build 'rl_renderPM'`
**Solution:** This is expected on Python 3.14+. renderPM is optional and not needed for basic PDF generation. The setup script will skip it automatically. See [PYTHON_VERSION_NOTES.md](PYTHON_VERSION_NOTES.md) for details.

## Uninstallation

To remove the package:

```bash
# Deactivate virtual environment
deactivate

# Remove virtual environment
rm -rf venv  # Linux/macOS
rmdir /s venv  # Windows

# Uninstall package (if installed globally)
pip uninstall clima-scope-pdf-generator
```

## Next Steps

1. **Set up API key**: See `API_KEY_SETUP.md`
2. **Read documentation**: See `README.md` and `AI_INTEGRATION_SUMMARY.md`
3. **Try examples**: Run `generate_ai_sample.py`
4. **Integrate**: Use the package in your own code

## Support

For issues:
1. Check this installation guide
2. Review `API_KEY_SETUP.md` for API issues
3. Check `README.md` for usage examples
4. Review error messages carefully
