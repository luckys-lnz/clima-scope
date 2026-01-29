# Import Issues Fix Summary

## Date: 2026-01-29

## Problem

Users were encountering import errors when trying to run `pdf_builder.py` and other library modules directly:

```bash
cd pdf_generator
python3 pdf_builder.py

# Error:
ImportError: attempted relative import with no known parent package
```

## Root Cause

Python modules that use relative imports (e.g., `from .models import ...`) cannot be run as scripts directly. They must be imported as part of a package. Files like `pdf_builder.py` and `enhanced_pdf_builder.py` are library modules, not standalone scripts.

## Solutions Implemented

### 1. Created Comprehensive Import Guide

**File**: `/home/lnz/DEV/clima-scope/IMPORT_ISSUES_GUIDE.md`

A complete guide that explains:
- Why the error occurs
- Correct ways to run PDF generator scripts
- Correct ways to run backend API
- Quick reference table of correct commands
- Troubleshooting common issues

### 2. Created Helper Script

**File**: `/home/lnz/DEV/clima-scope/generate_pdf.sh`

A user-friendly bash script that makes PDF generation easy from anywhere in the project:

```bash
# Interactive mode
./generate_pdf.sh

# Direct commands
./generate_pdf.sh basic      # Generate basic PDF
./generate_pdf.sh ai         # Generate AI-powered PDF
./generate_pdf.sh test       # Test API key
```

Features:
- Automatic directory navigation
- Virtual environment activation
- Colored output for better UX
- Error checking and validation
- API key setup guidance

### 3. Added Helpful Error Messages

**Modified Files**:
- `pdf_generator/pdf_builder.py`
- `pdf_generator/enhanced_pdf_builder.py`

Added `if __name__ == "__main__":` blocks with clear instructions (though import errors will still occur first, these serve as documentation).

## Correct Usage

### PDF Generation

#### ❌ Wrong
```bash
python3 pdf_builder.py
python3 enhanced_pdf_builder.py
```

#### ✅ Correct
```bash
# Option 1: Use the helper script
./generate_pdf.sh

# Option 2: Use provided scripts
cd pdf_generator
python generate_sample.py           # Basic PDF
python generate_ai_sample.py        # AI-powered PDF

# Option 3: Run as module
python -m pdf_generator.generate_sample
```

### Backend API

#### ❌ Wrong
```bash
python3 backend/app/main.py
```

#### ✅ Correct
```bash
# Option 1: Use uvicorn
cd backend
uvicorn app.main:app --reload

# Option 2: Use run script
cd backend
python run.py
```

## File Categories

### PDF Generator

**Library Modules** (cannot be run directly):
- `pdf_builder.py` - Main PDF builder (relative imports)
- `enhanced_pdf_builder.py` - Enhanced PDF builder (relative imports)
- `models.py`, `config.py`, `utils.py`, `section_generators.py`
- `chart_generator.py`, `report_generator.py`, `ai_service.py`

**Runnable Scripts** (can be executed):
- `generate_sample.py` ✓
- `generate_ai_sample.py` ✓
- `test_api_key.py` ✓

### Backend

**Library Modules** (cannot be run directly):
- All files in `app/` directory
- `app/main.py`, `app/config.py`, `app/database.py`
- All API routes, models, schemas, services

**Runnable Scripts**:
- `run.py` ✓
- `setup_venv.sh` ✓

## Testing the Fixes

### Test Helper Script

```bash
cd /home/lnz/DEV/clima-scope
./generate_pdf.sh
# Should show interactive menu

./generate_pdf.sh basic
# Should generate basic PDF
```

### Test PDF Generation Scripts

```bash
cd /home/lnz/DEV/clima-scope/pdf_generator
python generate_sample.py
# Should generate: output/nairobi_report_sample.pdf
```

### Test Backend

```bash
cd /home/lnz/DEV/clima-scope/backend
source venv/bin/activate
uvicorn app.main:app --reload
# Should start server at http://localhost:8000
```

## Documentation Updates

### New Files Created
1. `/home/lnz/DEV/clima-scope/IMPORT_ISSUES_GUIDE.md` - Comprehensive guide
2. `/home/lnz/DEV/clima-scope/generate_pdf.sh` - Helper script
3. `/home/lnz/DEV/clima-scope/IMPORT_FIXES_SUMMARY.md` - This file

### Files Modified
1. `pdf_generator/pdf_builder.py` - Added helpful error message
2. `pdf_generator/enhanced_pdf_builder.py` - Added helpful error message

## Quick Reference

| Task | Command |
|------|---------|
| Generate basic PDF | `./generate_pdf.sh basic` or `cd pdf_generator && python generate_sample.py` |
| Generate AI PDF | `./generate_pdf.sh ai` or `cd pdf_generator && python generate_ai_sample.py` |
| Test API key | `./generate_pdf.sh test` or `cd pdf_generator && python test_api_key.py` |
| Start backend | `cd backend && uvicorn app.main:app --reload` |
| Interactive mode | `./generate_pdf.sh` |

## Benefits

1. **Clearer Guidance**: Users know exactly how to run each component
2. **Better UX**: Helper script provides interactive, user-friendly interface
3. **Less Confusion**: Comprehensive guide addresses common pitfalls
4. **Faster Onboarding**: New users can generate PDFs without reading all docs
5. **Error Prevention**: Makes it harder to run commands incorrectly

## Related Documentation

- `/home/lnz/DEV/clima-scope/README.md` - Project overview
- `/home/lnz/DEV/clima-scope/pdf_generator/README.md` - PDF generator documentation
- `/home/lnz/DEV/clima-scope/pdf_generator/docs/QUICKSTART.md` - Quick start guide
- `/home/lnz/DEV/clima-scope/backend/README.md` - Backend API documentation

## Next Steps for Users

1. **Try the helper script**:
   ```bash
   ./generate_pdf.sh
   ```

2. **Read the import guide** if you encounter issues:
   ```bash
   cat IMPORT_ISSUES_GUIDE.md
   ```

3. **Check component READMEs** for detailed usage:
   - `pdf_generator/README.md`
   - `backend/README.md`

---

**Note**: The import errors when running library modules directly cannot be completely prevented (Python will error on the import statements before reaching our error messages), but we've provided multiple ways to help users run the code correctly.
