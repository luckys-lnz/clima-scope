#!/usr/bin/env python3
"""
Database Initialization Script

This script initializes the PostgreSQL database by:
1. Creating all tables from models
2. Running Alembic migrations
3. Optionally seeding initial data

Usage:
    python scripts/init_db.py [--seed]
"""

import sys
from pathlib import Path

# Add backend directory to path
backend_dir = Path(__file__).parent.parent
sys.path.insert(0, str(backend_dir))

from sqlalchemy import text
from app.database import engine, Base
from app.config import settings
from app.utils.logging import get_logger

logger = get_logger(__name__)


def check_database_connection():
    """Check if database connection is working."""
    try:
        with engine.connect() as conn:
            result = conn.execute(text("SELECT version();"))
            version = result.fetchone()[0]
            logger.info("database_connected", version=version.split(",")[0])
            return True
    except Exception as e:
        logger.error("database_connection_failed", error=str(e))
        return False


def create_tables():
    """Create all tables from models."""
    try:
        logger.info("creating_tables")
        Base.metadata.create_all(bind=engine)
        logger.info("tables_created_successfully")
        return True
    except Exception as e:
        logger.error("table_creation_failed", error=str(e))
        return False


def run_migrations():
    """Run Alembic migrations."""
    import subprocess
    import os
    
    try:
        logger.info("running_migrations")
        os.chdir(backend_dir)
        result = subprocess.run(
            ["alembic", "upgrade", "head"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            logger.info("migrations_completed_successfully")
            return True
        else:
            logger.error("migrations_failed", error=result.stderr)
            return False
    except Exception as e:
        logger.error("migration_execution_failed", error=str(e))
        return False


def seed_counties():
    """Seed counties data."""
    try:
        logger.info("seeding_counties")
        from scripts.seed_counties import seed_counties as seed_func
        seed_func(force=False)
        logger.info("counties_seeded_successfully")
        return True
    except Exception as e:
        logger.error("county_seeding_failed", error=str(e))
        return False


def main():
    """Main initialization function."""
    import argparse
    
    parser = argparse.ArgumentParser(description="Initialize Clima-scope database")
    parser.add_argument(
        "--seed",
        action="store_true",
        help="Seed initial data (counties)"
    )
    parser.add_argument(
        "--skip-migrations",
        action="store_true",
        help="Skip Alembic migrations (use create_tables instead)"
    )
    args = parser.parse_args()
    
    logger.info("database_initialization_started", database_url=settings.DATABASE_URL.split("@")[-1] if "@" in settings.DATABASE_URL else "not_set")
    
    # Check connection
    if not check_database_connection():
        logger.error("cannot_proceed_without_database_connection")
        sys.exit(1)
    
    # Run migrations or create tables
    if args.skip_migrations:
        if not create_tables():
            logger.error("table_creation_failed")
            sys.exit(1)
    else:
        if not run_migrations():
            logger.error("migrations_failed")
            sys.exit(1)
    
    # Seed data if requested
    if args.seed:
        if not seed_counties():
            logger.warning("county_seeding_failed_but_continuing")
    
    logger.info("database_initialization_complete")
    print("\n✓ Database initialization complete!")
    print(f"  Database: {settings.DATABASE_URL.split('@')[-1] if '@' in settings.DATABASE_URL else 'unknown'}")
    if args.seed:
        print("  Counties: Seeded")
    print("\nYou can now start the API server.")


if __name__ == "__main__":
    main()
