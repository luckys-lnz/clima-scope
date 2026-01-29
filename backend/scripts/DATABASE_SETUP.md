# PostgreSQL Database Setup Guide

This guide will help you set up PostgreSQL for the Clima-scope project.

## Prerequisites

- PostgreSQL installed and running
- PostgreSQL superuser access (or sudo privileges)

## Quick Setup

### 1. Run the Setup Script

The setup script will create the database and user for you:

```bash
cd backend
./scripts/setup_postgres.sh
```

You can also specify custom values:

```bash
./scripts/setup_postgres.sh [database_name] [username] [password]
```

**Default values:**
- Database: `climascope`
- User: `climascope_user`
- Password: (will be prompted)

### 2. Update .env File

After running the setup script, update your `.env` file with the connection string provided:

```bash
DATABASE_URL=postgresql://climascope_user:your_password@localhost:5432/climascope
```

### 3. Initialize Database

Run the initialization script to create tables and run migrations:

```bash
# Activate virtual environment first
source venv/bin/activate

# Initialize database with migrations
python scripts/init_db.py

# Or initialize and seed counties data
python scripts/init_db.py --seed
```

### 4. Verify Setup

Test the database connection:

```bash
# Start the API server
python run.py

# Check health endpoint
curl http://localhost:8000/api/v1/health
```

## Manual Setup

If you prefer to set up manually:

### 1. Create Database and User

```bash
# Connect as postgres user
sudo -u postgres psql

# In psql prompt:
CREATE USER climascope_user WITH PASSWORD 'your_secure_password';
CREATE DATABASE climascope OWNER climascope_user;
GRANT ALL PRIVILEGES ON DATABASE climascope TO climascope_user;
\q
```

### 2. Update .env

```bash
DATABASE_URL=postgresql://climascope_user:your_secure_password@localhost:5432/climascope
```

### 3. Run Migrations

```bash
cd backend
source venv/bin/activate
alembic upgrade head
```

### 4. Seed Counties (Optional)

```bash
python scripts/seed_counties.py
```

## Troubleshooting

### PostgreSQL Not Running

```bash
# Check if PostgreSQL is running
pg_isready

# Start PostgreSQL (systemd)
sudo systemctl start postgresql

# Or on macOS with Homebrew
brew services start postgresql
```

### Permission Denied

If you get permission errors, try:

```bash
# Run setup script with sudo
sudo ./scripts/setup_postgres.sh

# Or connect as postgres user
sudo -u postgres psql
```

### Connection Refused

1. Check PostgreSQL is listening on the correct port (default: 5432)
2. Verify `pg_hba.conf` allows local connections
3. Check firewall settings

### Database Already Exists

The setup script will skip creation if the database/user already exists. To recreate:

```bash
# Drop and recreate (WARNING: This deletes all data!)
sudo -u postgres psql -c "DROP DATABASE IF EXISTS climascope;"
sudo -u postgres psql -c "DROP USER IF EXISTS climascope_user;"
./scripts/setup_postgres.sh
```

## Database Management

### View Database

```bash
psql -U climascope_user -d climascope
```

### List Tables

```bash
psql -U climascope_user -d climascope -c "\dt"
```

### Backup Database

```bash
pg_dump -U climascope_user climascope > backup.sql
```

### Restore Database

```bash
psql -U climascope_user climascope < backup.sql
```

## Migration Commands

```bash
# Create a new migration
alembic revision --autogenerate -m "description"

# Apply migrations
alembic upgrade head

# Rollback one migration
alembic downgrade -1

# View migration history
alembic history
```

## Next Steps

After setting up the database:

1. ✅ Database created and configured
2. ✅ Tables created via migrations
3. ✅ Counties seeded (if using `--seed` flag)
4. ✅ Ready to start the API server

For more information, see:
- [Migrations Guide](../../docs/backend/MIGRATIONS.md)
- [API Documentation](../README.md)
