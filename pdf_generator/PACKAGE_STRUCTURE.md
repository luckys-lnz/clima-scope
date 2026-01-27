# Package Structure

This document describes the complete structure of the clima-scope-pdf-generator package.

## Directory Structure

```
pdf_generator/
├── __init__.py                 # Package initialization and exports
├── ai_service.py               # AI service for generating narratives
├── config.py                   # Configuration (fonts, colors, spacing)
├── enhanced_pdf_builder.py    # Enhanced PDF builder with better formatting
├── models.py                   # Pydantic models matching TypeScript interfaces
├── pdf_builder.py             # Basic PDF builder (original)
├── report_generator.py        # AI-powered report generator
├── section_generators.py      # Individual section generators
├── utils.py                   # Utility functions
│
├── sample_data/               # Sample data for testing
│   └── nairobi_sample.json
│
├── tests/                     # Unit tests (to be created)
│   └── (test files)
│
├── output/                    # Generated PDFs (gitignored)
│   └── *.pdf
│
├── venv/                      # Virtual environment (gitignored, created by setup)
│
├── .env                       # API keys (gitignored, create from .env.example)
├── .env.example               # Template for .env file
├── .gitignore                 # Git ignore rules
│
├── requirements.txt           # Base dependencies
├── requirements-dev.txt       # Development dependencies
├── requirements-anthropic.txt # Anthropic-specific dependencies
│
├── setup.py                   # Setup script (setuptools)
├── pyproject.toml             # Modern Python project configuration
├── MANIFEST.in                # Files to include in package distribution
│
├── setup_venv.sh             # Linux/macOS setup script
├── setup_venv.bat            # Windows setup script
├── Makefile                   # Make commands for convenience
│
├── README.md                  # Main documentation
├── INSTALLATION.md            # Detailed installation guide
├── QUICKSTART.md              # Quick start guide
├── API_KEY_SETUP.md           # API key setup instructions
├── AI_INTEGRATION_SUMMARY.md  # AI integration overview
├── PACKAGE_STRUCTURE.md       # This file
└── IMPLEMENTATION_STATUS.md   # Implementation status tracking
```

## File Descriptions

### Core Package Files

- **`__init__.py`**: Package initialization, exports main classes
- **`ai_service.py`**: AI service supporting OpenAI and Anthropic
- **`config.py`**: Configuration for fonts, colors, page sizes
- **`enhanced_pdf_builder.py`**: Professional PDF builder with tables and formatting
- **`models.py`**: Pydantic models matching TypeScript interfaces
- **`pdf_builder.py`**: Original basic PDF builder
- **`report_generator.py`**: Transforms raw data to complete reports using AI
- **`section_generators.py`**: Generators for individual report sections
- **`utils.py`**: Utility functions for formatting, text wrapping, etc.

### Setup and Configuration

- **`setup.py`**: Setuptools setup script (backward compatibility)
- **`pyproject.toml`**: Modern Python project configuration (PEP 518)
- **`MANIFEST.in`**: Specifies files to include in package distribution
- **`requirements.txt`**: Base dependencies (reportlab, pydantic, openai, etc.)
- **`requirements-dev.txt`**: Development dependencies (pytest, black, etc.)
- **`requirements-anthropic.txt`**: Anthropic SDK dependency

### Setup Scripts

- **`setup_venv.sh`**: Automated setup script for Linux/macOS
- **`setup_venv.bat`**: Automated setup script for Windows
- **`Makefile`**: Make commands for common tasks

### Documentation

- **`README.md`**: Main package documentation
- **`INSTALLATION.md`**: Detailed installation instructions
- **`QUICKSTART.md`**: Quick start guide (5-minute setup)
- **`API_KEY_SETUP.md`**: API key configuration guide
- **`AI_INTEGRATION_SUMMARY.md`**: Overview of AI integration
- **`PACKAGE_STRUCTURE.md`**: This file

### Configuration Files

- **`.env.example`**: Template for environment variables
- **`.env`**: Actual environment variables (gitignored, user-created)
- **`.gitignore`**: Git ignore rules for Python projects

### Sample Data

- **`sample_data/nairobi_sample.json`**: Sample weather report data

## Installation Methods

### Method 1: Automated Setup (Recommended)

```bash
./setup_venv.sh        # Linux/macOS
setup_venv.bat         # Windows
```

### Method 2: Manual Setup

```bash
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install -e .
```

### Method 3: Using Make

```bash
make setup
source venv/bin/activate
```

## Package Installation

The package can be installed in several ways:

### Editable Installation (Development)

```bash
pip install -e .
```

### Regular Installation

```bash
pip install .
```

### With Optional Dependencies

```bash
pip install -e ".[anthropic]"    # Add Anthropic support
pip install -e ".[dev]"          # Add development tools
pip install -e ".[all]"           # Add everything
```

## Entry Points

After installation, these command-line tools are available:

- **`clima-pdf-generate`**: Basic PDF generation
- **`clima-pdf-generate-ai`**: AI-powered PDF generation

## Virtual Environment

The `venv/` directory contains the virtual environment and is:
- Created by setup scripts
- Gitignored (not committed)
- Contains all installed packages
- Activated with `source venv/bin/activate` (Linux/macOS) or `venv\Scripts\activate.bat` (Windows)

## Environment Variables

The `.env` file (created from `.env.example`) contains:
- `OPENAI_API_KEY`: OpenAI API key (for GPT-4)
- `ANTHROPIC_API_KEY`: Anthropic API key (for Claude)

Only one is needed, depending on which provider you use.

## Output Files

Generated PDFs are saved to:
- `output/` directory (gitignored)
- Can be configured in code

## Testing

Tests should be placed in `tests/` directory:
```
tests/
├── test_ai_service.py
├── test_pdf_builder.py
├── test_report_generator.py
└── ...
```

Run tests with:
```bash
pytest tests/
```

## Distribution

To build a distribution package:

```bash
python -m build
```

This creates:
- `dist/clima-scope-pdf-generator-0.2.0.tar.gz` (source distribution)
- `dist/clima_scope_pdf_generator-0.2.0-py3-none-any.whl` (wheel)

## Dependencies

### Required
- `reportlab>=4.0.0`: PDF generation
- `Pillow>=10.0.0`: Image handling
- `pydantic>=2.9.0`: Data validation
- `python-dateutil>=2.9.0`: Date handling
- `openai>=1.0.0`: OpenAI API (default)

### Optional
- `anthropic>=0.18.0`: Anthropic API (alternative to OpenAI)
- `matplotlib>=3.8.0`: Charts/graphs
- `pytest>=8.0.0`: Testing
- `black>=23.0.0`: Code formatting
- `flake8>=6.0.0`: Linting
- `mypy>=1.0.0`: Type checking

## Version

Current version: **0.2.0**

Version is defined in:
- `pyproject.toml`
- `setup.py`
- `__init__.py`

## License

MIT License (to be added)

## Support

For issues or questions:
1. Check `QUICKSTART.md` for quick setup
2. See `INSTALLATION.md` for detailed setup
3. Review `API_KEY_SETUP.md` for API issues
4. Check `README.md` for usage examples
