# Import Issues Guide

## Date: 2026-01-29

## Overview

This guide explains how to properly run different components of the Clima-scope project and avoid common import errors.

---

## PDF Generator

### ❌ WRONG: Running library modules directly

```bash
cd pdf_generator
python3 pdf_builder.py  # ERROR: attempted relative import with no known parent package
python3 enhanced_pdf_builder.py  # ERROR: attempted relative import with no known parent package
```

### ✅ CORRECT: Using the provided scripts

**Option 1: Generate basic PDF (no AI required)**
```bash
cd pdf_generator
python generate_sample.py
```

**Option 2: Generate AI-powered PDF (requires API key)**
```bash
cd pdf_generator
python generate_ai_sample.py
```

**Option 3: Run as Python module (from project root)**
```bash
python -m pdf_generator.generate_sample
python -m pdf_generator.generate_ai_sample
```

**Option 4: In your own Python code**
```python
from pdf_generator import PDFReportBuilder, EnhancedPDFBuilder
from pdf_generator.config import ReportConfig

# For basic PDF
builder = PDFReportBuilder(report_data, config=ReportConfig())
builder.generate('output.pdf')

# For AI-powered PDF
from pdf_generator import ReportGenerator
generator = ReportGenerator()
complete_report = generator.generate_complete_report(raw_data)
pdf_builder = EnhancedPDFBuilder(complete_report)
pdf_builder.generate('output.pdf')
```

### Understanding the Error

When you see:
```
ImportError: attempted relative import with no known parent package
```

This means you're trying to run a file with relative imports (using `.` like `from .models import ...`) as a script. Python modules using relative imports must be imported as part of a package, not run directly.

**Files that are library modules** (use relative imports, can't be run directly):
- `pdf_builder.py`
- `enhanced_pdf_builder.py`
- `models.py`
- `config.py`
- `utils.py`
- `section_generators.py`
- `chart_generator.py`
- `report_generator.py`
- `ai_service.py`

**Files that are runnable scripts** (use absolute imports):
- `generate_sample.py` ✓
- `generate_ai_sample.py` ✓
- `test_api_key.py` ✓

---

## Backend API

### ❌ WRONG: Running backend modules directly

```bash
cd backend/app
python3 main.py  # ERROR: attempted relative import with no known parent package
```

### ✅ CORRECT: Using uvicorn

**Option 1: From backend directory**
```bash
cd backend
source venv/bin/activate  # Activate virtual environment
uvicorn app.main:app --reload
```

**Option 2: Using the run script**
```bash
cd backend
source venv/bin/activate
python run.py
```

**Option 3: From project root**
```bash
cd /home/lnz/DEV/clima-scope
source backend/venv/bin/activate
uvicorn backend.app.main:app --reload
```

### Backend File Structure

**Library modules** (use relative imports, can't be run directly):
- `app/main.py`
- `app/config.py`
- `app/database.py`
- All files in `app/api/`, `app/models/`, `app/schemas/`, `app/services/`

**Runnable scripts**:
- `run.py` ✓
- `setup_venv.sh` ✓

---

## General Best Practices

### 1. Always use virtual environments

```bash
# PDF Generator
cd pdf_generator
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Backend
cd backend
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

### 2. Run scripts from their intended directory

Most scripts are designed to be run from their parent directory:
```bash
# Good
cd pdf_generator
python generate_sample.py

# Also good
python -m pdf_generator.generate_sample
```

### 3. Check README files

Each major component has a README with proper usage instructions:
- `/home/lnz/DEV/clima-scope/README.md` - Project overview
- `/home/lnz/DEV/clima-scope/pdf_generator/README.md` - PDF generator usage
- `/home/lnz/DEV/clima-scope/backend/README.md` - Backend API usage

### 4. Use the provided setup scripts

```bash
# PDF Generator
cd pdf_generator
./setup_venv.sh  # Linux/macOS
setup_venv.bat   # Windows

# Backend
cd backend
./setup_venv.sh  # Linux/macOS
```

---

## Quick Start Commands

### Generate a PDF Report

```bash
# From project root
cd pdf_generator
python generate_sample.py
```

Output: `output/nairobi_report_sample.pdf`

### Generate AI-Powered PDF

```bash
# 1. Set up API key (one time)
cd pdf_generator
echo "OPENAI_API_KEY=sk-your-key-here" > .env

# 2. Generate report
python generate_ai_sample.py
```

Output: `output/ai_generated_report.pdf`

### Start Backend API

```bash
cd backend
source venv/bin/activate
python run.py
```

API available at: http://localhost:8000
Docs available at: http://localhost:8000/api/docs

---

## Troubleshooting

### "No module named 'pdf_generator'"

**Solution**: Install the package in editable mode:
```bash
cd /home/lnz/DEV/clima-scope
pip install -e pdf_generator/
```

### "No module named 'app'"

**Solution**: Run the backend with uvicorn, not python directly:
```bash
cd backend
uvicorn app.main:app --reload
```

### "ModuleNotFoundError: No module named 'reportlab'"

**Solution**: Install dependencies:
```bash
cd pdf_generator
pip install -r requirements.txt
```

### "attempted relative import with no known parent package"

**Solution**: Don't run library modules directly. Use the provided scripts:
- For PDF generation: `generate_sample.py` or `generate_ai_sample.py`
- For backend: `uvicorn app.main:app --reload`

---

## Summary Table

| Component | Wrong Command | Correct Command |
|-----------|---------------|-----------------|
| PDF Builder | `python3 pdf_builder.py` | `python generate_sample.py` |
| Enhanced PDF | `python3 enhanced_pdf_builder.py` | `python generate_ai_sample.py` |
| Backend API | `python3 app/main.py` | `uvicorn app.main:app --reload` |
| Test API Key | ✓ Works | `python test_api_key.py` |

---

## Files Modified

To help users avoid these errors, the following files were updated:

1. **`pdf_generator/pdf_builder.py`** - Added helpful error message when run directly
2. **`pdf_generator/enhanced_pdf_builder.py`** - Added helpful error message when run directly

These modules now display clear instructions if someone tries to run them directly.
