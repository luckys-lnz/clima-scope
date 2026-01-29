```markdown
# Backend API TODO List - Clima-scope Weather Reporting System

## 🎯 MVP PRIORITY (Week 1-2)

### Phase 0: Project Skeleton (1 hour)
```
backend/
├── requirements.txt
├── .env.example
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI app
│   ├── config.py               # Settings
│   ├── database.py             # Session
│   ├── models/
│   │   ├── __init__.py
│   │   ├── county.py
│   │   └── weather_report.py
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── county.py
│   │   └── weather_report.py
│   └── api/
│       └── v1/
│           ├── __init__.py
│           ├── counties.py
│           └── reports.py
└── alembic.ini
```

**Cmd+K**: "Generate this EXACT structure using .cursorrules"

### Phase 1: Core Data Models & Schemas (Day 1)

**Database Models** (EXACT):
```python
# app/models/county.py
class County(Base):
    __tablename__ = "counties"
    id: Mapped[str] = mapped_column(String(2), primary_key=True)  # "31"
    name: Mapped[str] = mapped_column(String(50), unique=True, index=True)
    region: Mapped[str] = mapped_column(String(50))
    
class WeatherReport(Base):
    __tablename__ = "weather_reports"
    id: Mapped[UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    county_id: Mapped[str] = mapped_column(ForeignKey("counties.id"))
    period_start: Mapped[date]
    period_end: Mapped[date]
    raw_data: Mapped[JSON] = mapped_column(JSON)  # CountyWeatherReport schema
    status: Mapped[str] = mapped_column(String(20), default="raw")  # raw|processed|complete
    pdf_county_path: Mapped[Optional[str]]
    pdf_wards_path: Mapped[Optional[str]]  # JSON array paths
```

**Pydantic Schemas** (Match JSON Schema):
- `CountyOut`, `CountyListResponse`
- `RawWeatherReportCreate`, `CompleteWeatherReportOut`

### Phase 2: Essential Endpoints (Day 2)

```
GET    /api/v1/counties              # List 47 counties
GET    /api/v1/counties/{id}         # Nairobi details + ward count
POST   /api/v1/reports/weather       # Ingest raw JSON → DB
GET    /api/v1/reports/{id}/raw      # Return validated JSON
GET    /api/v1/reports/{id}/pdf      # Serve generated PDF
POST   /api/v1/reports/{id}/process  # Trigger full pipeline
```

### Phase 3: PDF Integration (Day 3)
```
POST   /api/v1/reports/{id}/generate-pdf
- Calls pdf_generator/enhanced_pdf_builder.py
- Returns job status + download URL
- Async via `background_tasks`
```

## 🏗️ Phase 4: Production Features (Week 2)

```
Auth: JWT API keys only (no users)
GET    /api/v1/auth/api-keys
POST   /api/v1/auth/api-keys

Search:
GET    /api/v1/reports               # ?county_id=31&period_start=2026-01-01
GET    /api/v1/reports/search        # Full-text + filters

Batch:
POST   /api/v1/reports/batch/generate  # Nairobi + Kisumu
GET    /api/v1/reports/{id}/wards     # Ward-specific PDFs
```

## 📊 Data Flow Pipeline (SINGLE RESPONSIBILITY)

```
1. POST /reports/weather → Store raw JSON (schemas/county_weather_report.json)
2. POST /reports/{id}/process → 
   a) ai_service.generate_narratives(raw) → complete JSON
   b) enhanced_pdf_builder.complete → PDFs
   c) Update DB paths
3. GET /reports/{id}/pdf → Serve file
```

## ⚙️ requirements.txt (EXACT)
```
fastapi==0.112.0
uvicorn[standard]==0.30.1
sqlalchemy==2.0.32
alembic==1.13.2
pydantic==2.8.2
psycopg2-binary==2.9.9
python-multipart==0.0.9
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-dotenv==1.0.1
structlog==24.2.0
```

## 🧪 Testing Strategy
```
tests/
├── test_api/
│   ├── test_counties.py
│   └── test_reports.py
├── test_integration/
│   └── test_full_pipeline.py
└── fixtures/
    └── sample_nairobi.json  # Valid schema data
```

**pytest -v --cov=90**

## 🚀 MVP Success Criteria (End of Week 1)
```
✅ 47 counties seeded
✅ POST raw JSON → DB → PDF download
✅ Nairobi full pipeline <3min
✅ OpenAPI docs complete
✅ Dockerized (docker-compose up)
✅ Schema validation 100%
```

## 📋 Implementation Order (Cursor Cmd+K Each)
```
1. "Generate backend structure from .cursorrules"
2. "Create County + WeatherReport models + Alembic"
3. "Generate counties_router.py with pagination"
4. "Create reports_router.py MVP endpoints"
5. "Integrate pdf_generator calling enhanced_pdf_builder"
6. "Add API key auth middleware"
7. "Full test suite + fixtures"
8. "Docker + docker-compose"
```

## 🎨 Frontend Teaser (Week 2)
```
app/
├── counties/page.tsx           # County list + stats
├── reports/[id]/page.tsx       # Report viewer + PDF download
└── dashboard/page.tsx          # Processing queue
```

## 🚫 NEVER DO
```
❌ User county creation (reference data only)
❌ Schema changes without migration
❌ Print debugging (structlog ONLY)
❌ Matplotlib maps (PNG embed ONLY)
❌ >1 endpoint per file
```

## ✅ Cursor Directives
```
PRIORITY: Backend MVP → Tests → Docker → Frontend dashboard
VALIDATE: Every JSON against schemas/county_weather_report.json
AUTH: API keys only (no user registration)
PDF: enhanced_pdf_builder.py integration MANDATORY
```

**Week 1 Goal**: `curl -X POST /reports/weather nairobi.json → PDF download URL`
```
