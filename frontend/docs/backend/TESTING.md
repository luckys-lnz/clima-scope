# Testing API Endpoints

This guide explains how to test the API endpoints.

## Quick Start for Testing

### Option 1: Use SQLite (Easiest for Testing)

1. **Create a test .env file:**
```bash
cd backend
cp .env.example .env
```

2. **Edit .env to use SQLite:**
```env
DATABASE_URL=sqlite:///./test.db
```

3. **Set up and start:**
```bash
# Activate venv (if not already)
source venv/bin/activate

# Create database tables (SQLite will create the file automatically)
python -c "from app.database import init_db; from app.models import *; init_db()"

# Start server
python run.py
```

### Option 2: Use PostgreSQL

1. **Set up PostgreSQL database:**
```bash
createdb climascope
```

2. **Create .env file:**
```bash
cp .env.example .env
# Edit .env with your PostgreSQL connection string
```

3. **Run migrations:**
```bash
source venv/bin/activate
alembic upgrade head
```

4. **Start server:**
```bash
python run.py
```

## Running the Test Script

Once the server is running, you can use the test script:

```bash
# Make sure requests is installed
pip install requests

# Run the test script (from backend/ directory)
python tests/test_endpoints.py

# Or from project root
python backend/tests/test_endpoints.py
```

Or test manually with curl:

## Manual Testing with curl

### 1. Health Check
```bash
curl http://localhost:8000/api/v1/health
```

### 2. List Counties
```bash
curl http://localhost:8000/api/v1/counties
```

### 3. Create County
```bash
curl -X POST http://localhost:8000/api/v1/counties \
  -H "Content-Type: application/json" \
  -d '{
    "id": "31",
    "name": "Nairobi",
    "region": "Nairobi"
  }'
```

### 4. Get County
```bash
curl http://localhost:8000/api/v1/counties/31
```

### 5. List Weather Reports
```bash
curl http://localhost:8000/api/v1/reports/weather
```

### 6. Create Weather Report
```bash
curl -X POST http://localhost:8000/api/v1/reports/weather \
  -H "Content-Type: application/json" \
  -d @weather_report.json
```

### 7. List Complete Reports
```bash
curl http://localhost:8000/api/v1/reports/complete
```

### 8. List PDF Reports
```bash
curl http://localhost:8000/api/v1/pdf
```

## Using the API Documentation

Once the server is running, visit:

- **Swagger UI**: http://localhost:8000/api/docs
- **ReDoc**: http://localhost:8000/api/redoc

You can test endpoints directly from the Swagger UI by clicking "Try it out" on any endpoint.

## Testing AI-Powered Endpoints

To test endpoints that generate complete reports or PDFs, you need:

1. **AI API Key** in `.env`:
   ```env
   OPENAI_API_KEY=sk-your-key-here
   # OR
   ANTHROPIC_API_KEY=sk-ant-your-key-here
   AI_PROVIDER=openai  # or anthropic
   ```

2. **PDF Generator installed:**
   ```bash
   cd ../pdf_generator
   pip install -e .
   ```

3. **Generate Complete Report:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/reports/complete/generate \
     -H "Content-Type: application/json" \
     -d '{
       "weather_report_id": 1
     }'
   ```

4. **Generate PDF:**
   ```bash
   curl -X POST http://localhost:8000/api/v1/pdf/generate \
     -H "Content-Type: application/json" \
     -d '{
       "complete_report_id": 1
     }'
   ```

## Troubleshooting

### Server won't start

1. **Check dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

2. **Check database connection:**
   - For SQLite: Make sure you have write permissions
   - For PostgreSQL: Verify connection string in `.env`

3. **Check for port conflicts:**
   ```bash
   lsof -i :8000  # Check if port 8000 is in use
   ```

### Database errors

1. **For SQLite:** Tables are created automatically on first run
2. **For PostgreSQL:** Run migrations:
   ```bash
   alembic upgrade head
   ```

### PDF Generator errors

1. **Check if pdf_generator is installed:**
   ```bash
   python -c "from pdf_generator import ReportGenerator; print('OK')"
   ```

2. **Check API keys:**
   ```bash
   # Test OpenAI key
   python -c "import os; from dotenv import load_dotenv; load_dotenv(); print('OPENAI_API_KEY:', 'SET' if os.getenv('OPENAI_API_KEY') else 'NOT SET')"
   ```

## Expected Test Results

Test scripts are located in `backend/tests/`.

When running `tests/test_endpoints.py`, you should see:

✅ Health check returns 200
✅ Can create, read, update, delete counties
✅ Can create and list weather reports
✅ Can list complete reports (empty initially)
✅ Can list PDF reports (empty initially)

Note: AI-powered endpoints (generate complete report, generate PDF) require:
- Valid API keys
- pdf_generator package installed
- May take 30-60 seconds to complete
