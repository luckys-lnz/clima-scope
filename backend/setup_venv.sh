#!/bin/bash
# Setup script for backend virtual environment
# Usage: ./setup_venv.sh

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Clima-scope Backend API - Virtual Environment Setup${NC}"
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

# Install pdf_generator package (from parent directory)
echo ""
echo "Installing pdf_generator package..."
PDF_GEN_PATH="../pdf_generator"
if [ -d "$PDF_GEN_PATH" ] && [ -f "$PDF_GEN_PATH/setup.py" ]; then
    echo "  Found pdf_generator at: $PDF_GEN_PATH"
    cd "$PDF_GEN_PATH"
    pip install -e . 2>/dev/null || {
        echo -e "${YELLOW}⚠ Could not install pdf_generator as package${NC}"
        echo "  Will use path-based import instead"
    }
    cd - > /dev/null
    echo -e "${GREEN}✓ pdf_generator package installed${NC}"
else
    echo -e "${YELLOW}⚠ pdf_generator not found at $PDF_GEN_PATH${NC}"
    echo "  Make sure pdf_generator directory exists at project root"
fi

# Setup .env file
echo ""
if [ ! -f ".env" ]; then
    if [ -f ".env.example" ]; then
        echo "Creating .env file from template..."
        cp .env.example .env
        echo -e "${YELLOW}⚠ Please edit .env and configure your settings${NC}"
        echo "   - Set DATABASE_URL"
        echo "   - Set OPENAI_API_KEY (or ANTHROPIC_API_KEY)"
        echo "   - Set SECRET_KEY (generate a random key)"
    else
        echo -e "${YELLOW}⚠ No .env.example found. Create .env manually${NC}"
    fi
else
    echo -e "${GREEN}✓ .env file already exists${NC}"
fi

# Initialize Alembic (if not already done)
if [ ! -f "alembic.ini" ]; then
    echo ""
    echo "Initializing Alembic for database migrations..."
    alembic init alembic
    echo -e "${GREEN}✓ Alembic initialized${NC}"
fi

echo ""
echo "================================================================"
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To activate the virtual environment, run:"
echo "  source $VENV_DIR/bin/activate"
echo ""
echo "To start the development server, run:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
echo "To run database migrations:"
echo "  alembic upgrade head"
echo ""
