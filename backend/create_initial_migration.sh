#!/bin/bash
# Script to create the initial database migration
# Usage: ./create_initial_migration.sh

set -e

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Creating Initial Database Migration${NC}"
echo "=========================================="
echo ""

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}⚠ Virtual environment not found${NC}"
    echo "Please run ./setup_venv.sh first"
    exit 1
fi

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Check if .env exists
if [ ! -f ".env" ]; then
    echo -e "${YELLOW}⚠ .env file not found${NC}"
    echo "Please create .env file from .env.example and configure DATABASE_URL"
    exit 1
fi

# Create migration
echo ""
echo "Generating initial migration..."
alembic revision --autogenerate -m "Initial migration: create tables"

echo ""
echo -e "${GREEN}✓ Migration created successfully!${NC}"
echo ""
echo "Next steps:"
echo "1. Review the migration file in alembic/versions/"
echo "2. Apply the migration: alembic upgrade head"
echo ""
