# Backend Scripts

Utility scripts for database management and setup.

## Database Setup Scripts

### `setup_postgres.sh`

Sets up PostgreSQL database, user, and permissions for the Clima-scope project.

**Usage:**

```bash
cd backend

# Interactive setup (will prompt for password)
./scripts/setup_postgres.sh

# Custom database name, user, and password
./scripts/setup_postgres.sh climascope climascope_user mypassword
```

**What it does:**
- Creates PostgreSQL database (default: `climascope`)
- Creates database user (default: `climascope_user`)
- Sets appropriate permissions
- Outputs connection string for `.env` file

**Prerequisites:**
- PostgreSQL must be installed and running
- Requires PostgreSQL superuser access (sudo or postgres user)

### `init_db.py`

Initializes the database by running migrations and optionally seeding data.

**Usage:**

```bash
cd backend
source venv/bin/activate

# Run migrations only
python scripts/init_db.py

# Run migrations and seed counties
python scripts/init_db.py --seed

# Skip migrations, use create_tables instead
python scripts/init_db.py --skip-migrations
```

**What it does:**
- Checks database connection
- Runs Alembic migrations (or creates tables)
- Optionally seeds counties data

## Seed Scripts

### `seed_counties.py`

Seeds the database with all 47 official Kenya counties with their KNBS codes.

**Usage:**

```bash
cd backend
source venv/bin/activate

# Seed counties (skips existing ones)
python scripts/seed_counties.py

# Force update existing counties
python scripts/seed_counties.py --force
```

**What it does:**
- Populates the `counties` table with all 47 Kenya counties
- Uses official KNBS 2-digit codes (01-47)
- Includes county names and regions
- Skips existing counties by default (use `--force` to update)

**Note:** Counties are reference data and should only be seeded once during initial setup. The API does not allow creating or deleting counties.

## County Data

The seed script includes all 47 counties:
- Mombasa (01) through Nyamira (47)
- Official KNBS codes
- Region assignments
- Proper formatting

## Quick Start

1. **Start PostgreSQL** (if not running):
   ```bash
   sudo systemctl start postgresql
   ```

2. **Run setup script**:
   ```bash
   cd backend
   ./scripts/setup_postgres.sh
   ```

3. **Update `.env`** with the connection string from step 2

4. **Initialize database**:
   ```bash
   source venv/bin/activate
   python scripts/init_db.py --seed
   ```

For detailed setup instructions, see [DATABASE_SETUP.md](./DATABASE_SETUP.md).

For more information about counties, see the API documentation at `/api/docs` when the server is running.
