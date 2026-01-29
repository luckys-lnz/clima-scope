#!/bin/bash
# Quick setup script for testing with SQLite

set -e

GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}Quick Test Setup for API Endpoints${NC}"
echo "=========================================="
echo ""

# Check if venv exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Virtual environment not found. Creating...${NC}"
    python3 -m venv venv
fi

# Activate venv
echo "Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Install requests for testing
pip install requests 2>/dev/null || echo "requests already installed"

# Create .env for testing if it doesn't exist
if [ ! -f ".env" ]; then
    echo "Creating .env file for testing (SQLite)..."
    cat > .env << EOF
# Test Configuration
DEBUG=true
DATABASE_URL=sqlite:///./test.db
DATABASE_ECHO=false
CORS_ORIGINS=http://localhost:3000
OPENAI_API_KEY=
ANTHROPIC_API_KEY=
AI_PROVIDER=openai
STORAGE_PATH=../storage
PDF_STORAGE_PATH=../storage/pdfs
SECRET_KEY=test-secret-key-change-in-production
LOG_LEVEL=INFO
EOF
    echo -e "${GREEN}✓ .env file created${NC}"
else
    echo -e "${YELLOW}.env file already exists${NC}"
fi

# Initialize database (SQLite)
echo ""
echo "Initializing database..."
python3 << 'PYTHON_SCRIPT'
import sys
from pathlib import Path

# Add app to path
sys.path.insert(0, str(Path(__file__).parent))

from app.database import init_db, Base, engine
from app.models import County, Ward, WeatherReport, CompleteReport, PDFReport

# Create all tables
Base.metadata.create_all(bind=engine)
print("✓ Database tables created")
PYTHON_SCRIPT

echo ""
echo -e "${GREEN}Setup complete!${NC}"
echo ""
echo "To start the server:"
echo "  source venv/bin/activate"
echo "  python run.py"
echo ""
echo "Then in another terminal, run tests:"
echo "  python tests/test_endpoints.py"
echo ""
echo "Or visit the API docs at:"
echo "  http://localhost:8000/api/docs"
echo ""
