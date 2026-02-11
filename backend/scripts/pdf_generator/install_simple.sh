#!/bin/bash
# Simple installation script that adds pdf_generator to PYTHONPATH
# Use this if pip install -e . doesn't work

set -e

echo "Simple Installation Method"
echo "========================="
echo ""
echo "This script adds pdf_generator to your Python path"
echo "so you can import it without installing as a package."
echo ""

# Get the absolute path to pdf_generator directory
PDF_GEN_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PARENT_DIR="$(dirname "$PDF_GEN_DIR")"

echo "PDF generator directory: $PDF_GEN_DIR"
echo "Parent directory: $PARENT_DIR"
echo ""

# Create a .pth file in site-packages
VENV_SITE_PACKAGES="$PDF_GEN_DIR/venv/lib/python*/site-packages"
if [ -d "$PDF_GEN_DIR/venv" ]; then
    SITE_PACKAGES=$(python -c "import site; print(site.getsitepackages()[0])" 2>/dev/null || echo "")
    if [ -z "$SITE_PACKAGES" ]; then
        # Fallback: find site-packages in venv
        SITE_PACKAGES=$(find "$PDF_GEN_DIR/venv" -type d -name "site-packages" | head -1)
    fi
    
    if [ -n "$SITE_PACKAGES" ] && [ -d "$SITE_PACKAGES" ]; then
        PTH_FILE="$SITE_PACKAGES/pdf_generator.pth"
        echo "$PARENT_DIR" > "$PTH_FILE"
        echo "✓ Created .pth file: $PTH_FILE"
        echo "  This allows Python to find pdf_generator"
    else
        echo "⚠ Could not find site-packages directory"
        echo "  You can manually add to PYTHONPATH:"
        echo "  export PYTHONPATH=\"$PARENT_DIR:\$PYTHONPATH\""
    fi
else
    echo "⚠ Virtual environment not found"
    echo "  Run ./setup_venv.sh first"
    exit 1
fi

echo ""
echo "Installation complete!"
echo ""
echo "You can now use:"
echo "  python -m pdf_generator.generate_sample"
echo "  python -m pdf_generator.generate_ai_sample"
echo ""
