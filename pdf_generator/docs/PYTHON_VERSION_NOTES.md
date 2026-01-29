# Python Version Compatibility Notes

## Recommended Python Versions

- **Python 3.8** - Fully supported
- **Python 3.9** - Fully supported
- **Python 3.10** - Fully supported
- **Python 3.11** - Fully supported
- **Python 3.12** - Fully supported
- **Python 3.13** - Should work, but may have minor issues
- **Python 3.14+** - Some optional dependencies may not build

## Known Issues

### Python 3.14+ and renderPM

The `rl_renderPM` package (optional dependency for advanced ReportLab features) may fail to build on Python 3.14+ due to compatibility issues with the build system.

**Impact:** Low - `renderPM` is only needed for advanced image rendering features. Basic PDF generation works without it.

**Solution:** 
1. Skip renderPM installation (it's optional)
2. Use Python 3.12 or 3.13 instead
3. Wait for renderPM to be updated for Python 3.14+

### Installation Options

**Option 1: Skip renderPM (Recommended for Python 3.14+)**
```bash
# Install without renderPM
pip install -r requirements.txt
```

**Option 2: Use Python 3.12 (Recommended)**
```bash
# Create venv with specific Python version
python3.12 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
```

**Option 3: Try renderPM anyway**
```bash
# May fail, but you can try
pip install -r requirements-renderpm.txt
```

## Testing Your Installation

After installation, test that everything works:

```bash
# Test basic PDF generation (doesn't require renderPM)
python -m pdf_generator.generate_sample

# Test AI-powered generation
python -m pdf_generator.generate_ai_sample
```

If these work, you're all set! renderPM is only needed for advanced features.

## What renderPM Provides

`renderPM` enables:
- Advanced image rendering in PDFs
- Better font rendering
- Enhanced graphics capabilities

**For most use cases, you don't need it.** The basic PDF generation works perfectly without it.

## Getting Help

If you encounter issues:

1. **Check Python version:** `python --version`
2. **Try without renderPM:** Just install base requirements
3. **Use Python 3.12:** Most compatible version
4. **Check error messages:** They usually indicate what's missing

## Future Updates

We're monitoring compatibility and will update requirements as packages add Python 3.14+ support.
