# Installation Troubleshooting

## Problem: "package directory 'pdf_generator' does not exist"

This error occurs when installing from within the `pdf_generator` directory.

### Solution 1: Install from Parent Directory (Recommended)

```bash
# Go to parent directory
cd /home/lnz/DEV/clima-scope

# Install the package
pip install -e pdf_generator/
```

### Solution 2: Use Simple Installation Script

```bash
cd pdf_generator
./install_simple.sh
```

This adds the package to Python path without using pip.

### Solution 3: Add to PYTHONPATH Manually

```bash
# Add to your shell profile (~/.bashrc or ~/.zshrc)
export PYTHONPATH="/home/lnz/DEV/clima-scope:$PYTHONPATH"

# Or activate in current session
export PYTHONPATH="/home/lnz/DEV/clima-scope:$PYTHONPATH"
```

Then you can use:
```bash
python -m pdf_generator.generate_sample
```

### Solution 4: Use Python Directly (No Installation Needed)

You can run the scripts directly without installing:

```bash
cd pdf_generator
python generate_sample.py
python generate_ai_sample.py
```

## Problem: Network Errors During Installation

If you see connection errors when installing:

1. **Check internet connection**
2. **Use offline mode** if you have cached packages
3. **Install dependencies manually** one by one

## Problem: renderPM Build Failures (Python 3.14+)

This is expected and not critical. See [PYTHON_VERSION_NOTES.md](PYTHON_VERSION_NOTES.md).

## Quick Test Without Installation

You can test the package without installing it:

```bash
cd pdf_generator

# Add parent directory to Python path
export PYTHONPATH="$(dirname $(pwd)):$PYTHONPATH"

# Run scripts
python -m pdf_generator.generate_sample
```

## Verify Installation

After installation, verify it works:

```python
python -c "import pdf_generator; print('✓ Package imported successfully')"
```

Or test the scripts:

```bash
python -m pdf_generator.generate_sample
```

## Still Having Issues?

1. Check Python version: `python --version` (should be 3.8+)
2. Ensure virtual environment is activated: `which python` should show venv path
3. Try installing from parent directory instead
4. Use the simple installation script as a workaround
