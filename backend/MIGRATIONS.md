# Database Migrations Guide

This guide explains how to work with Alembic database migrations in the Clima-scope backend.

## Initial Setup

### 1. Create Initial Migration

After creating new models, generate the initial migration:

```bash
cd backend
source venv/bin/activate  # Activate virtual environment
alembic revision --autogenerate -m "Initial migration: create tables"
```

This will create a migration file in `alembic/versions/` that includes all table creation statements.

### 2. Review Migration

**Always review the generated migration file** before applying it. Alembic's autogenerate is good but not perfect.

Check the file in `alembic/versions/` and verify:
- All tables are created correctly
- Foreign keys are set up properly
- Indexes are included
- Column types match your models

### 3. Apply Migration

```bash
alembic upgrade head
```

This will create all tables in your database.

## Common Commands

### Create a New Migration

```bash
# Auto-generate from model changes
alembic revision --autogenerate -m "Description of changes"

# Create empty migration (manual)
alembic revision -m "Description of changes"
```

### Apply Migrations

```bash
# Apply all pending migrations
alembic upgrade head

# Apply next migration
alembic upgrade +1

# Apply specific revision
alembic upgrade <revision_id>
```

### Rollback Migrations

```bash
# Rollback one migration
alembic downgrade -1

# Rollback to specific revision
alembic downgrade <revision_id>

# Rollback all migrations
alembic downgrade base
```

### Check Migration Status

```bash
# Show current revision
alembic current

# Show migration history
alembic history

# Show pending migrations
alembic heads
```

## Migration Workflow

1. **Modify Models**: Update your SQLAlchemy models in `app/models/`
2. **Generate Migration**: Run `alembic revision --autogenerate -m "description"`
3. **Review Migration**: Check the generated migration file
4. **Test Locally**: Apply migration to local database and test
5. **Commit**: Commit both model changes and migration file
6. **Deploy**: Apply migration in production with `alembic upgrade head`

## Troubleshooting

### Migration Conflicts

If you have conflicts (multiple heads), merge them:

```bash
alembic merge heads -m "Merge migration branches"
```

### Reset Database (Development Only)

⚠️ **Warning**: Only use in development!

```bash
# Drop all tables
alembic downgrade base

# Recreate all tables
alembic upgrade head
```

### Fix Autogenerate Issues

If Alembic doesn't detect changes:
1. Make sure all models are imported in `alembic/env.py`
2. Check that models inherit from `Base`
3. Verify `target_metadata = Base.metadata` in `env.py`

## Database Models

Current models:
- `County` - County information with KNBS codes
- `Ward` - Ward information (linked to counties)
- `WeatherReport` - Raw weather data from GFS
- `CompleteReport` - AI-generated complete reports
- `PDFReport` - Generated PDF metadata

See `app/models/` for model definitions.
