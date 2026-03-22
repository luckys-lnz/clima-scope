---
name: Phase 3.2 Database Migrations
overview: Create the initial Alembic database migration to establish proper version control for the database schema. This is foundational for production deployment and future schema changes.
todos:
  - id: migration-1
    content: Generate initial Alembic migration using autogenerate
    status: completed
  - id: migration-2
    content: Review generated migration file for correctness
    status: completed
  - id: migration-3
    content: Apply migration and verify tables created
    status: completed
  - id: migration-4
    content: Test seed script with migrated database
    status: completed
  - id: migration-5
    content: Update documentation if needed
    status: completed
isProject: false
---

# Phase 3.2: Database Migrations

## Overview

Create the initial Alembic migration to establish database version control. Currently, the database is initialized using `init_db()` which creates tables directly. Migrations provide proper versioning and are essential for production.

## Current State

- Alembic is configured in `backend/alembic/`
- Models exist: County, Ward, WeatherReport, CompleteReport, PDFReport
- No migration files exist yet (only `.gitkeep` in `alembic/versions/`)
- Helper script exists: `backend/create_initial_migration.sh`

## Tasks

### 1. Generate Initial Migration

- Run `alembic revision --autogenerate` to create initial migration
- Migration should include all 5 models:
  - `counties` table (KNBS codes, names, regions)
  - `wards` table (with foreign key to counties)
  - `weather_reports` table (with JSON raw_data)
  - `complete_reports` table (with JSON report_data)
  - `pdf_reports` table (with file metadata)
- Include all indexes defined in models
- Include foreign key constraints

### 2. Review Generated Migration

- Check `alembic/versions/` for the new migration file
- Verify:
  - All tables are created correctly
  - Foreign keys match model relationships
  - Indexes are included (especially composite indexes)
  - Column types match models (String lengths, JSON types)
  - Cascade deletes are configured

### 3. Test Migration

- Apply migration: `alembic upgrade head`
- Verify tables created in database
- Test that seed script still works: `python scripts/seed_counties.py`
- Verify existing functionality still works

### 4. Update Documentation

- Update `MIGRATIONS.md` if needed
- Document migration workflow
- Add notes about seed script usage with migrations

## Files to Modify

### Created

- `alembic/versions/XXXX_initial_migration_create_tables.py` (auto-generated)

### Modified

- `backend/MIGRATIONS.md` (if updates needed)

## Commands

```bash
cd backend
source venv/bin/activate

# Generate migration
alembic revision --autogenerate -m "Initial migration: create tables"

# Review the generated file in alembic/versions/

# Apply migration
alembic upgrade head

# Verify
alembic current  # Should show the new revision
```

## Success Criteria

- [ ] Initial migration file created
- [ ] Migration reviewed and verified
- [ ] Migration applied successfully
- [ ] All tables created correctly
- [ ] Seed script works with migrated database
- [ ] Tests pass with migrated database

## Notes

- The migration will replace the need for `init_db()` in production
- Keep `init_db()` for development/testing convenience
- Future schema changes will require new migrations