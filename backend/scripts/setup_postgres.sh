#!/bin/bash
# PostgreSQL Database Setup Script for Clima-scope
#
# This script sets up the PostgreSQL database for the Clima-scope project.
# It creates the database, user, and sets appropriate permissions.
#
# Usage:
#   ./scripts/setup_postgres.sh [database_name] [username] [password]
#
# Defaults:
#   database_name: climascope
#   username: climascope_user
#   password: (will prompt if not provided)

set -e

# Default values
DB_NAME="${1:-climascope}"
DB_USER="${2:-climascope_user}"
DB_PASSWORD="${3:-}"

# Colors for output
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

echo -e "${GREEN}=== Clima-scope PostgreSQL Setup ===${NC}\n"

# Check if PostgreSQL is running
if ! pg_isready -q; then
    echo -e "${RED}Error: PostgreSQL is not running. Please start PostgreSQL first.${NC}"
    exit 1
fi

echo -e "${YELLOW}Configuration:${NC}"
echo "  Database: $DB_NAME"
echo "  User: $DB_USER"
echo ""

# Prompt for password if not provided
if [ -z "$DB_PASSWORD" ]; then
    read -sp "Enter password for database user: " DB_PASSWORD
    echo ""
    if [ -z "$DB_PASSWORD" ]; then
        echo -e "${RED}Error: Password cannot be empty${NC}"
        exit 1
    fi
fi

# Check if running as postgres user or with sudo
if [ "$(whoami)" != "postgres" ] && [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Note: This script may require PostgreSQL superuser privileges.${NC}"
    echo -e "${YELLOW}You may be prompted for your sudo password.${NC}\n"
fi

# Create user (if not exists)
echo -e "${GREEN}Creating database user...${NC}"
sudo -u postgres psql -c "DO \$\$ BEGIN CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'; EXCEPTION WHEN duplicate_object THEN RAISE NOTICE 'User $DB_USER already exists.'; END \$\$;" || {
    echo -e "${YELLOW}Attempting alternative method...${NC}"
    psql -U postgres -c "DO \$\$ BEGIN CREATE USER $DB_USER WITH PASSWORD '$DB_PASSWORD'; EXCEPTION WHEN duplicate_object THEN RAISE NOTICE 'User $DB_USER already exists.'; END \$\$;" 2>/dev/null || {
        echo -e "${RED}Error: Could not create user. You may need to run this script as the postgres user or with sudo.${NC}"
        exit 1
    }
}

# Create database (if not exists)
echo -e "${GREEN}Creating database...${NC}"
sudo -u postgres psql -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
    sudo -u postgres psql -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" || {
    echo -e "${YELLOW}Attempting alternative method...${NC}"
    psql -U postgres -c "SELECT 1 FROM pg_database WHERE datname = '$DB_NAME'" | grep -q 1 || \
        psql -U postgres -c "CREATE DATABASE $DB_NAME OWNER $DB_USER;" 2>/dev/null || {
            echo -e "${RED}Error: Could not create database. You may need to run this script as the postgres user or with sudo.${NC}"
            exit 1
        }
}

# Grant privileges
echo -e "${GREEN}Granting privileges...${NC}"
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" || \
    psql -U postgres -d "$DB_NAME" -c "GRANT ALL PRIVILEGES ON DATABASE $DB_NAME TO $DB_USER;" 2>/dev/null || true

# Grant schema privileges
sudo -u postgres psql -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;" || \
    psql -U postgres -d "$DB_NAME" -c "GRANT ALL ON SCHEMA public TO $DB_USER;" 2>/dev/null || true

echo -e "\n${GREEN}✓ PostgreSQL database setup complete!${NC}\n"

# Generate connection string
DB_URL="postgresql://$DB_USER:$DB_PASSWORD@localhost:5432/$DB_NAME"

echo -e "${YELLOW}Database connection string:${NC}"
echo "  $DB_URL"
echo ""
echo -e "${YELLOW}Add this to your .env file:${NC}"
echo "  DATABASE_URL=$DB_URL"
echo ""
echo -e "${GREEN}Next steps:${NC}"
echo "  1. Update backend/.env with the DATABASE_URL above"
echo "  2. Run migrations: cd backend && alembic upgrade head"
echo "  3. Seed counties: python scripts/seed_counties.py"
echo ""
