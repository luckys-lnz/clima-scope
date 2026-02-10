#!/bin/bash
# Setup script for backend virtual environment (Arch-safe, Python-pinned)

set -e

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Clima-scope Backend API - Virtual Environment Setup${NC}"
echo "================================================================"
echo ""

# ------------------------------------------------------------------
# FORCE PYTHON VERSION (critical for FastAPI/Supabase stack)
# ------------------------------------------------------------------

REQUIRED_PYTHON="python3.11"

if ! command -v $REQUIRED_PYTHON &> /dev/null; then
    echo -e "${RED}Python 3.11 is required but not installed.${NC}"
    echo ""
    echo "On Arch run:"
    echo "  sudo pacman -S python311"
    echo ""
    exit 1
fi

PYTHON_CMD=$(command -v $REQUIRED_PYTHON)
echo -e "${GREEN}Using Python interpreter: $PYTHON_CMD${NC}"
$PYTHON_CMD --version
echo ""

# ------------------------------------------------------------------
# VENV SETUP
# ------------------------------------------------------------------

VENV_DIR="venv"

if [ -d "$VENV_DIR" ]; then
    echo -e "${YELLOW}Virtual environment already exists.${NC}"
    read -p "Recreate it with Python 3.11? (y/N): " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        rm -rf "$VENV_DIR"
        echo "Old venv removed."
    else
        echo -e "${RED}Existing venv may be using wrong Python version.${NC}"
        echo "Delete it manually if you hit dependency issues."
    fi
fi

if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment with Python 3.11..."
    $PYTHON_CMD -m venv "$VENV_DIR"
    echo -e "${GREEN}✓ Virtual environment created${NC}"
fi

# ------------------------------------------------------------------
# ACTIVATE
# ------------------------------------------------------------------

source "$VENV_DIR/bin/activate"

echo "Python inside venv:"
python --version
echo ""

# ------------------------------------------------------------------
# PACKAGE INSTALL
# ------------------------------------------------------------------

echo "Upgrading pip tooling..."
pip install --upgrade pip setuptools wheel

echo ""
echo "Installing requirements..."
pip install -r requirements.txt

# ------------------------------------------------------------------
# Install pdf_generator (editable)
# ------------------------------------------------------------------

echo ""
echo "Installing pdf_generator package..."
PDF_GEN_PATH="../pdf_generator"

if [ -d "$PDF_GEN_PATH" ] && [ -f "$PDF_GEN_PATH/setup.py" ]; then
    pip install -e "$PDF_GEN_PATH"
    echo -e "${GREEN}✓ pdf_generator installed${NC}"
else
    echo -e "${YELLOW}⚠ pdf_generator not found, skipping${NC}"
fi

# ------------------------------------------------------------------
# ENV FILE
# ------------------------------------------------------------------

echo ""
if [ ! -f ".env" ] && [ -f ".env.example" ]; then
    cp .env.example .env
    echo -e "${YELLOW}⚠ .env created. Configure it before running.${NC}"
fi

# ------------------------------------------------------------------
# Alembic
# ------------------------------------------------------------------

if [ ! -f "alembic.ini" ]; then
    echo "Initializing Alembic..."
    alembic init alembic
fi

echo ""
echo "================================================================"
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "Activate:"
echo "  source venv/bin/activate"
echo ""
echo "Run server:"
echo "  uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
echo ""
