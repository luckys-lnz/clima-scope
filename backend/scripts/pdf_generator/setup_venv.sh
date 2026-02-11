#!/bin/bash
# Setup script for creating a virtual environment and installing dependencies
# Usage: ./setup_venv.sh [anthropic|openai]

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Clima-scope PDF Generator - Virtual Environment Setup${NC}"
echo "================================================================"
echo ""

# Determine Python version
PYTHON_CMD="python3"
if ! command -v python3 &> /dev/null; then
    PYTHON_CMD="python"
fi

# Check Python version
PYTHON_VERSION=$($PYTHON_CMD --version 2>&1 | awk '{print $2}')
echo "Detected Python version: $PYTHON_VERSION"

# Check if Python 3.8+
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d. -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d. -f2)
if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 8 ]); then
    echo -e "${RED}Error: Python 3.8 or higher is required${NC}"
    exit 1
fi

# Create virtual environment
VENV_DIR="venv"
if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists at $VENV_DIR${NC}"
    read -p "Remove and recreate? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        echo "Removing existing virtual environment..."
        rm -rf "$VENV_DIR"
    else
        echo "Using existing virtual environment"
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"

# Upgrade pip
echo "Upgrading pip..."
pip install --upgrade pip setuptools wheel

# Install base requirements
echo ""
echo "Installing base requirements..."
pip install -r requirements.txt

# Note: renderPM may fail on Python 3.14+, skip if it fails
echo ""
echo "Attempting to install renderPM (optional, may fail on Python 3.14+)..."
pip install -r requirements-renderpm.txt 2>/dev/null || echo -e "${YELLOW}⚠ renderPM installation skipped (not critical)${NC}"

# Install provider-specific requirements
PROVIDER=${1:-openai}
if [ "$PROVIDER" = "anthropic" ]; then
    echo "Installing Anthropic dependencies..."
    pip install -r requirements-anthropic.txt
    echo -e "${GREEN}✓ Anthropic dependencies installed${NC}"
else
    echo -e "${GREEN}✓ OpenAI dependencies installed (default)${NC}"
fi

# Install package in editable mode
echo ""
echo "Installing pdf_generator package in editable mode..."
# Use --no-build-isolation to avoid issues with pyproject.toml
pip install -e . --no-build-isolation || {
    echo -e "${YELLOW}⚠ Standard install failed, trying alternative method...${NC}"
    # Alternative: install without editable mode first
    pip install . --no-build-isolation
}

# Setup .env file
echo ""
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env and add your API key${NC}"
        echo "   See API_KEY_SETUP.md for instructions"
    else
        echo -e "${YELLOW}⚠ No .env.example found. Create .env manually with your API key${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

echo ""
echo "================================================================"
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To activate the virtual environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To deactivate, run:"
echo "  deactivate"
echo ""
echo "To test the installation, run:"
echo "  python -m pdf_generator.generate_sample"
echo ""
echo "For AI-powered generation, set your API key in .env and run:"
echo "  python -m pdf_generator.generate_ai_sample"
echo ""
