# Clima-scope Backend API

FastAPI backend for the Clima-scope meteorological weather report system.

## Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py              # FastAPI app entry point
│   ├── config.py            # Configuration management
│   ├── database.py          # Database connection
│   ├── models/              # SQLAlchemy models
│   ├── schemas/             # Pydantic request/response schemas
│   ├── api/                 # API routes
│   │   ├── __init__.py
│   │   └── v1/
│   │       ├── __init__.py
│   │       ├── reports.py
│   │       ├── counties.py
│   │       ├── wards.py
│   │       ├── pdf.py
│   │       └── health.py
│   ├── services/            # Business logic
│   │   ├── report_service.py
│   │   ├── pdf_service.py
│   │   └── ai_service.py
│   ├── utils/               # Utility functions
│   └── middleware/          # Custom middleware
├── requirements.txt
├── .env.example
└── README.md
```

## Setup

### 1. Create Virtual Environment

```bash
cd backend
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

### 2. Install Dependencies

```bash
pip install --upgrade pip
pip install -r requirements.txt
```

### 3. Configure Environment

```bash
cp .env.example .env
# Edit .env with your configuration
```

### 4. Run Development Server

```bash
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

The API will be available at:
- API: http://localhost:8000
- Docs: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Development

### Running Tests

```bash
pytest
```

### Database Migrations

```bash
# Create migration
alembic revision --autogenerate -m "description"

# Apply migration
alembic upgrade head
```

## API Documentation

Once the server is running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc

## Documentation

Detailed documentation is available in the [docs/backend/](../docs/backend/) directory:

- [STRUCTURE.md](../docs/backend/STRUCTURE.md) - Backend architecture and structure
- [MIGRATIONS.md](../docs/backend/MIGRATIONS.md) - Database migrations guide
- [TESTING.md](../docs/backend/TESTING.md) - Testing guide and examples
- [phases/](../docs/backend/phases/) - Implementation phase completion summaries

See also: [Backend API Implementation Plan](../docs/BACKEND_API_IMPLEMENTATION_PLAN.md)
