# Backend API Implementation Plan

**Project**: Clima-scope - Automated Weekly County Weather Reporting System  
**Backend Framework**: Python FastAPI  
**Date**: 2026-01-18  
**Status**: Planning Phase

---

## 📋 Table of Contents

1. [Overview](#overview)
2. [Architecture](#architecture)
3. [API Routes](#api-routes)
4. [Implementation Tasks](#implementation-tasks)
5. [Database Schema](#database-schema)
6. [Authentication & Authorization](#authentication--authorization)
7. [Data Processing Pipeline](#data-processing-pipeline)
8. [Testing Strategy](#testing-strategy)
9. [Deployment Considerations](#deployment-considerations)

---

## Overview

This document outlines the complete backend API implementation for the Clima-scope system. The backend will handle:

- **Data Ingestion**: GFS GRIB file uploads and processing
- **Spatial Processing**: Ward-level aggregation of weather data
- **Report Generation**: PDF and CSV report creation
- **Map Generation**: Geospatial visualization creation
- **Data Management**: County, ward, and report data storage
- **User Management**: Authentication and authorization
- **System Operations**: Configuration, logging, and diagnostics

---

## Architecture

### Technology Stack

- **Framework**: FastAPI 0.115+
- **Database**: PostgreSQL 15+ with PostGIS extension
- **ORM**: SQLAlchemy 2.0+ with Alembic for migrations
- **Geospatial**: GeoPandas, Shapely, PyGRIB
- **Visualization**: Matplotlib, Cartopy
- **PDF Generation**: ReportLab or WeasyPrint
- **Caching**: Redis
- **Task Queue**: Celery with Redis broker
- **File Storage**: Local filesystem (S3-compatible for production)
- **Validation**: Pydantic v2

### Project Structure

```
backend/
├── app/
│   ├── __init__.py
│   ├── main.py                 # FastAPI application entry point
│   ├── config.py               # Configuration management
│   ├── database.py             # Database connection & session
│   │
│   ├── api/
│   │   ├── __init__.py
│   │   ├── v1/
│   │   │   ├── __init__.py
│   │   │   ├── auth.py         # Authentication endpoints
│   │   │   ├── counties.py     # County management
│   │   │   ├── data_upload.py  # GFS data upload & processing
│   │   │   ├── reports.py      # Report generation & retrieval
│   │   │   ├── maps.py         # Map generation & retrieval
│   │   │   ├── wards.py        # Ward data endpoints
│   │   │   ├── system.py       # System configuration & health
│   │   │   └── logs.py         # Logs & diagnostics
│   │   └── dependencies.py     # Shared dependencies (auth, DB)
│   │
│   ├── models/
│   │   ├── __init__.py
│   │   ├── user.py             # User model
│   │   ├── county.py           # County & ward models
│   │   ├── gfs_data.py         # GFS file & processing models
│   │   ├── report.py           # Report models
│   │   ├── map.py              # Map storage models
│   │   └── system.py           # System config models
│   │
│   ├── schemas/
│   │   ├── __init__.py
│   │   ├── auth.py             # Auth request/response schemas
│   │   ├── county.py           # County schemas
│   │   ├── gfs.py              # GFS data schemas
│   │   ├── report.py           # Report schemas
│   │   ├── map.py              # Map schemas
│   │   └── common.py           # Common schemas (pagination, errors)
│   │
│   ├── services/
│   │   ├── __init__.py
│   │   ├── auth_service.py     # Authentication logic
│   │   ├── gfs_processor.py    # GFS GRIB file processing
│   │   ├── spatial_processor.py # Spatial aggregation
│   │   ├── report_generator.py # PDF/CSV report generation
│   │   ├── map_generator.py    # Map visualization generation
│   │   ├── narrative_generator.py # Narrative text generation
│   │   └── file_storage.py     # File storage management
│   │
│   ├── repositories/
│   │   ├── __init__.py
│   │   ├── user_repository.py
│   │   ├── county_repository.py
│   │   ├── gfs_repository.py
│   │   ├── report_repository.py
│   │   └── map_repository.py
│   │
│   ├── core/
│   │   ├── __init__.py
│   │   ├── security.py         # Password hashing, JWT
│   │   ├── exceptions.py       # Custom exceptions
│   │   └── middleware.py       # CORS, logging, error handling
│   │
│   └── tasks/
│       ├── __init__.py
│       ├── celery_app.py      # Celery configuration
│       ├── process_gfs.py     # GFS processing task
│       ├── generate_report.py # Report generation task
│       └── generate_maps.py   # Map generation task
│
├── alembic/                    # Database migrations
│   ├── versions/
│   └── env.py
│
├── tests/
│   ├── __init__.py
│   ├── conftest.py            # Pytest fixtures
│   ├── test_api/
│   ├── test_services/
│   └── test_repositories/
│
├── scripts/
│   ├── init_db.py             # Database initialization
│   ├── seed_counties.py      # Seed county data
│   └── process_sample_gfs.py  # Sample GFS processing
│
├── requirements.txt
├── .env.example
└── README.md
```

---

## API Routes

### Base URL
```
/api/v1
```

### Authentication Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/auth/register` | Register new user | No |
| POST | `/auth/login` | User login (get JWT) | No |
| POST | `/auth/refresh` | Refresh access token | No |
| POST | `/auth/logout` | Logout (invalidate token) | Yes |
| GET | `/auth/me` | Get current user info | Yes |
| PUT | `/auth/me` | Update current user | Yes |
| POST | `/auth/change-password` | Change password | Yes |

### County Management Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/counties` | List all counties (paginated) | Yes |
| GET | `/counties/{county_id}` | Get county details | Yes |
| GET | `/counties/{county_id}/wards` | Get all wards in county | Yes |
| GET | `/counties/{county_id}/wards/{ward_id}` | Get ward details | Yes |
| GET | `/counties/{county_id}/boundaries` | Get county/ward boundaries (GeoJSON) | Yes |
| POST | `/counties/{county_id}/boundaries` | Upload/update boundaries | Yes (Admin) |

### GFS Data Upload & Processing Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/data/upload` | Upload GFS GRIB file | Yes |
| GET | `/data/uploads` | List all uploads (paginated) | Yes |
| GET | `/data/uploads/{upload_id}` | Get upload details | Yes |
| POST | `/data/uploads/{upload_id}/process` | Trigger processing | Yes |
| GET | `/data/uploads/{upload_id}/status` | Get processing status | Yes |
| DELETE | `/data/uploads/{upload_id}` | Delete upload | Yes (Admin) |
| GET | `/data/processed` | List processed datasets | Yes |
| GET | `/data/processed/{dataset_id}` | Get processed dataset | Yes |

### Report Generation & Retrieval Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| POST | `/reports/generate` | Generate report for county | Yes |
| GET | `/reports` | List all reports (paginated, filtered) | Yes |
| GET | `/reports/{report_id}` | Get report metadata | Yes |
| GET | `/reports/{report_id}/pdf` | Download PDF report | Yes |
| GET | `/reports/{report_id}/csv` | Download CSV data | Yes |
| GET | `/reports/{report_id}/json` | Get report JSON data | Yes |
| GET | `/reports/county/{county_id}` | Get reports for county | Yes |
| GET | `/reports/county/{county_id}/latest` | Get latest report for county | Yes |
| DELETE | `/reports/{report_id}` | Delete report | Yes (Admin) |
| POST | `/reports/batch-generate` | Generate reports for multiple counties | Yes (Admin) |

### Map Generation & Retrieval Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/maps/county/{county_id}/rainfall` | Get rainfall map | Yes |
| GET | `/maps/county/{county_id}/temperature` | Get temperature map | Yes |
| GET | `/maps/county/{county_id}/wind` | Get wind speed map | Yes |
| GET | `/maps/county/{county_id}/{variable}/{date}` | Get specific map by date | Yes |
| GET | `/maps/county/{county_id}/{variable}/{date}/metadata` | Get map metadata | Yes |
| POST | `/maps/generate` | Generate maps for county | Yes |
| GET | `/maps/report/{report_id}` | Get all maps for report | Yes |

### Ward Data Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/wards/{ward_id}` | Get ward details | Yes |
| GET | `/wards/{ward_id}/forecast` | Get ward forecast data | Yes |
| GET | `/wards/{ward_id}/forecast/history` | Get historical forecasts | Yes |
| GET | `/counties/{county_id}/wards/aggregated` | Get aggregated ward data for county | Yes |

### System Configuration & Health Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/system/health` | Health check | No |
| GET | `/system/status` | System status | Yes |
| GET | `/system/config` | Get system configuration | Yes (Admin) |
| PUT | `/system/config` | Update system configuration | Yes (Admin) |
| GET | `/system/stats` | System statistics | Yes (Admin) |

### Logs & Diagnostics Endpoints

| Method | Endpoint | Description | Auth Required |
|--------|----------|-------------|---------------|
| GET | `/logs` | Get system logs (paginated, filtered) | Yes (Admin) |
| GET | `/logs/{log_id}` | Get specific log entry | Yes (Admin) |
| GET | `/logs/processing/{task_id}` | Get processing task logs | Yes |
| GET | `/diagnostics` | System diagnostics | Yes (Admin) |
| POST | `/diagnostics/test-processing` | Test processing pipeline | Yes (Admin) |

---

## Implementation Tasks

### Phase 1: Project Setup & Foundation

#### Task 1.1: Project Initialization
- [ ] Create backend directory structure
- [ ] Initialize Python virtual environment
- [ ] Create `requirements.txt` with all dependencies
- [ ] Set up `pyproject.toml` or `setup.py`
- [ ] Configure `.env.example` with all environment variables
- [ ] Create `README.md` for backend
- [ ] Set up `.gitignore` for Python

**Dependencies to include:**
- fastapi>=0.115.0
- uvicorn[standard]>=0.30.0
- sqlalchemy>=2.0.0
- alembic>=1.13.0
- pydantic>=2.9.0
- pydantic-settings>=2.5.0
- python-jose[cryptography]>=3.3.0
- passlib[bcrypt]>=1.7.4
- python-multipart>=0.0.9
- postgis (via psycopg2-binary>=2.9.9)
- geopandas>=0.14.0
- pygrib>=2.1.5
- matplotlib>=3.8.0
- cartopy>=0.22.0
- reportlab>=4.0.0
- celery>=5.4.0
- redis>=5.0.0
- pytest>=8.0.0
- pytest-asyncio>=0.23.0
- httpx>=0.27.0 (for testing)

#### Task 1.2: Database Setup
- [ ] Set up PostgreSQL database with PostGIS extension
- [ ] Configure database connection in `app/database.py`
- [ ] Create SQLAlchemy base and session management
- [ ] Initialize Alembic for migrations
- [ ] Create initial migration structure

#### Task 1.3: Configuration Management
- [ ] Create `app/config.py` with Pydantic settings
- [ ] Define environment variables:
  - Database URL
  - Redis URL
  - JWT secret keys
  - File storage paths
  - CORS origins
  - API version
- [ ] Set up configuration validation

#### Task 1.4: FastAPI Application Setup
- [ ] Create `app/main.py` with FastAPI app
- [ ] Configure CORS middleware
- [ ] Set up error handling middleware
- [ ] Configure logging
- [ ] Set up API router structure
- [ ] Create health check endpoint

---

### Phase 2: Authentication & User Management

#### Task 2.1: User Model & Repository
- [ ] Create `User` model in `app/models/user.py`
  - Fields: id, email, hashed_password, full_name, role, is_active, created_at, updated_at
- [ ] Create user repository with CRUD operations
- [ ] Add database migration for users table

#### Task 2.2: Authentication Service
- [ ] Implement password hashing (bcrypt)
- [ ] Implement JWT token generation and validation
- [ ] Create login/register logic
- [ ] Implement refresh token mechanism
- [ ] Add token blacklist (optional, for logout)

#### Task 2.3: Authentication Endpoints
- [ ] Implement `/auth/register` endpoint
- [ ] Implement `/auth/login` endpoint
- [ ] Implement `/auth/refresh` endpoint
- [ ] Implement `/auth/logout` endpoint
- [ ] Implement `/auth/me` endpoint (GET & PUT)
- [ ] Implement `/auth/change-password` endpoint
- [ ] Add request/response schemas
- [ ] Add input validation

#### Task 2.4: Authorization Middleware
- [ ] Create dependency for JWT authentication
- [ ] Create dependency for role-based access (Admin, User)
- [ ] Add authorization checks to protected endpoints

---

### Phase 3: County & Ward Management

#### Task 3.1: County & Ward Models
- [ ] Create `County` model
  - Fields: id (KNBS code), name, region, geometry (PostGIS)
- [ ] Create `Ward` model
  - Fields: id, name, county_id, geometry (PostGIS), area_km2
- [ ] Set up relationships (County → Wards)
- [ ] Create database migrations

#### Task 3.2: County Repository
- [ ] Implement county CRUD operations
- [ ] Implement spatial queries (PostGIS)
- [ ] Implement ward queries by county
- [ ] Add GeoJSON serialization

#### Task 3.3: County Endpoints
- [ ] Implement `GET /counties` (list with pagination)
- [ ] Implement `GET /counties/{county_id}` (details)
- [ ] Implement `GET /counties/{county_id}/wards` (list wards)
- [ ] Implement `GET /counties/{county_id}/wards/{ward_id}` (ward details)
- [ ] Implement `GET /counties/{county_id}/boundaries` (GeoJSON)
- [ ] Implement `POST /counties/{county_id}/boundaries` (upload boundaries, admin only)

#### Task 3.4: County Data Seeding
- [ ] Create script to seed 47 Kenyan counties
- [ ] Create script to seed ward boundaries (if available)
- [ ] Add validation for county data

---

### Phase 4: GFS Data Processing

#### Task 4.1: GFS Data Models
- [ ] Create `GFSUpload` model
  - Fields: id, filename, file_path, file_size, model_run, uploaded_by, status, created_at
- [ ] Create `GFSProcessedDataset` model
  - Fields: id, upload_id, county_id, processing_status, processed_at, metadata
- [ ] Create `WardForecast` model
  - Fields: id, dataset_id, ward_id, variable, daily_values (JSON), weekly_total, quality_flag
- [ ] Create database migrations

#### Task 4.2: File Storage Service
- [ ] Implement file upload handling
- [ ] Implement file validation (GRIB format check)
- [ ] Implement file storage (local filesystem)
- [ ] Add file cleanup on deletion

#### Task 4.3: GFS Processing Service
- [ ] Implement GRIB file reading (PyGRIB)
- [ ] Implement spatial extraction for Kenya region
- [ ] Implement grid point to ward aggregation
- [ ] Implement data validation
- [ ] Add error handling and logging

#### Task 4.4: GFS Upload Endpoints
- [ ] Implement `POST /data/upload` (file upload)
- [ ] Implement `GET /data/uploads` (list uploads)
- [ ] Implement `GET /data/uploads/{upload_id}` (upload details)
- [ ] Implement `POST /data/uploads/{upload_id}/process` (trigger processing)
- [ ] Implement `GET /data/uploads/{upload_id}/status` (processing status)
- [ ] Implement `DELETE /data/uploads/{upload_id}` (delete upload, admin)

#### Task 4.5: Celery Task for Processing
- [ ] Create Celery task for GFS processing
- [ ] Implement async processing with progress tracking
- [ ] Add task status updates
- [ ] Handle processing errors

---

### Phase 5: Spatial Processing & Aggregation

#### Task 5.1: Spatial Processing Service
- [ ] Implement point-in-polygon spatial join
- [ ] Implement area-weighted aggregation
- [ ] Implement ward-level data aggregation
- [ ] Calculate statistics (mean, max, min, total)
- [ ] Add quality flags based on grid point coverage

#### Task 5.2: County Report Data Generation
- [ ] Aggregate ward data to county level
- [ ] Calculate county-level statistics
- [ ] Identify extreme values (hottest, coolest, wettest, etc.)
- [ ] Generate flood risk assessments
- [ ] Create county report data structure

---

### Phase 6: Report Generation

#### Task 6.1: Report Models
- [ ] Create `Report` model
  - Fields: id, county_id, period_start, period_end, status, generated_at, generated_by
- [ ] Create `ReportFile` model (for PDF/CSV storage)
  - Fields: id, report_id, file_type, file_path, file_size
- [ ] Create database migrations

#### Task 6.2: Narrative Generation Service
- [ ] Implement executive summary generation
- [ ] Implement weekly narrative generation
- [ ] Implement variable-specific narratives (rainfall, temperature, wind)
- [ ] Generate advisories and impacts
- [ ] Add template-based text generation

#### Task 6.3: PDF Report Generation
- [ ] Implement PDF structure (11 sections)
- [ ] Add cover page generation
- [ ] Add executive summary section
- [ ] Add narrative sections
- [ ] Add data tables
- [ ] Integrate map images
- [ ] Add metadata and disclaimers

#### Task 6.4: CSV Export Service
- [ ] Implement CSV generation from report data
- [ ] Include ward-level data
- [ ] Include daily breakdowns
- [ ] Add metadata rows

#### Task 6.5: Report Endpoints
- [ ] Implement `POST /reports/generate` (generate report)
- [ ] Implement `GET /reports` (list reports with filters)
- [ ] Implement `GET /reports/{report_id}` (report metadata)
- [ ] Implement `GET /reports/{report_id}/pdf` (download PDF)
- [ ] Implement `GET /reports/{report_id}/csv` (download CSV)
- [ ] Implement `GET /reports/{report_id}/json` (JSON data)
- [ ] Implement `GET /reports/county/{county_id}` (county reports)
- [ ] Implement `GET /reports/county/{county_id}/latest` (latest report)
- [ ] Implement `DELETE /reports/{report_id}` (delete, admin)
- [ ] Implement `POST /reports/batch-generate` (batch generation, admin)

#### Task 6.6: Celery Task for Report Generation
- [ ] Create Celery task for report generation
- [ ] Implement async PDF generation
- [ ] Add progress tracking
- [ ] Handle generation errors

---

### Phase 7: Map Generation

#### Task 7.1: Map Models
- [ ] Create `Map` model
  - Fields: id, report_id, county_id, variable, date, file_path, resolution, format, metadata
- [ ] Create database migrations

#### Task 7.2: Map Generation Service
- [ ] Implement base map creation (Cartopy)
- [ ] Implement ward-level choropleth maps
- [ ] Add color schemes (rainfall, temperature, wind)
- [ ] Add cartographic elements (legend, scale, north arrow)
- [ ] Generate maps at different resolutions (300 DPI, 400 DPI)
- [ ] Export to PNG format
- [ ] Generate web-optimized versions (WebP)

#### Task 7.3: Map Storage Service
- [ ] Implement map file storage
- [ ] Organize maps by county/variable/date
- [ ] Generate map metadata
- [ ] Implement map retrieval

#### Task 7.4: Map Endpoints
- [ ] Implement `GET /maps/county/{county_id}/rainfall` (rainfall map)
- [ ] Implement `GET /maps/county/{county_id}/temperature` (temperature map)
- [ ] Implement `GET /maps/county/{county_id}/wind` (wind map)
- [ ] Implement `GET /maps/county/{county_id}/{variable}/{date}` (specific map)
- [ ] Implement `GET /maps/county/{county_id}/{variable}/{date}/metadata` (metadata)
- [ ] Implement `POST /maps/generate` (generate maps)
- [ ] Implement `GET /maps/report/{report_id}` (report maps)

#### Task 7.5: Celery Task for Map Generation
- [ ] Create Celery task for map generation
- [ ] Implement async map generation
- [ ] Add progress tracking

---

### Phase 8: Ward Data Endpoints

#### Task 8.1: Ward Data Service
- [ ] Implement ward forecast retrieval
- [ ] Implement historical data queries
- [ ] Add data aggregation functions

#### Task 8.2: Ward Endpoints
- [ ] Implement `GET /wards/{ward_id}` (ward details)
- [ ] Implement `GET /wards/{ward_id}/forecast` (current forecast)
- [ ] Implement `GET /wards/{ward_id}/forecast/history` (historical)
- [ ] Implement `GET /counties/{county_id}/wards/aggregated` (aggregated data)

---

### Phase 9: System Configuration & Monitoring

#### Task 9.1: System Configuration Models
- [ ] Create `SystemConfig` model
  - Fields: key, value, description, updated_at, updated_by
- [ ] Create database migration

#### Task 9.2: System Endpoints
- [ ] Implement `GET /system/health` (health check)
- [ ] Implement `GET /system/status` (system status)
- [ ] Implement `GET /system/config` (get configuration, admin)
- [ ] Implement `PUT /system/config` (update configuration, admin)
- [ ] Implement `GET /system/stats` (system statistics, admin)

#### Task 9.3: Logging & Diagnostics
- [ ] Create `LogEntry` model
- [ ] Implement structured logging
- [ ] Implement log retrieval
- [ ] Implement diagnostics endpoint
- [ ] Add processing task logs

#### Task 9.4: Logs Endpoints
- [ ] Implement `GET /logs` (system logs, admin)
- [ ] Implement `GET /logs/{log_id}` (specific log, admin)
- [ ] Implement `GET /logs/processing/{task_id}` (task logs)
- [ ] Implement `GET /diagnostics` (diagnostics, admin)
- [ ] Implement `POST /diagnostics/test-processing` (test pipeline, admin)

---

### Phase 10: Testing

#### Task 10.1: Test Setup
- [ ] Configure pytest
- [ ] Set up test database
- [ ] Create test fixtures
- [ ] Set up test data factories

#### Task 10.2: Unit Tests
- [ ] Test authentication service
- [ ] Test GFS processing service
- [ ] Test spatial processing service
- [ ] Test report generation service
- [ ] Test map generation service
- [ ] Test repositories

#### Task 10.3: Integration Tests
- [ ] Test API endpoints
- [ ] Test database operations
- [ ] Test file upload/download
- [ ] Test Celery tasks

#### Task 10.4: End-to-End Tests
- [ ] Test complete workflow (upload → process → generate report)
- [ ] Test error scenarios
- [ ] Test authentication flows

---

### Phase 11: Documentation & Deployment

#### Task 11.1: API Documentation
- [ ] Configure FastAPI automatic docs (Swagger/OpenAPI)
- [ ] Add detailed endpoint descriptions
- [ ] Add request/response examples
- [ ] Document error responses

#### Task 11.2: Deployment Configuration
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml (for local development)
- [ ] Create production deployment config
- [ ] Set up environment variable documentation

#### Task 11.3: Performance Optimization
- [ ] Add database indexes
- [ ] Implement caching (Redis)
- [ ] Optimize queries
- [ ] Add connection pooling

---

## Database Schema

### Core Tables

#### users
```sql
- id (UUID, PK)
- email (VARCHAR, UNIQUE, NOT NULL)
- hashed_password (VARCHAR, NOT NULL)
- full_name (VARCHAR)
- role (ENUM: 'admin', 'user', NOT NULL)
- is_active (BOOLEAN, DEFAULT true)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### counties
```sql
- id (VARCHAR(2), PK) -- KNBS code
- name (VARCHAR, NOT NULL)
- region (VARCHAR)
- geometry (GEOMETRY(POLYGON, 4326))
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### wards
```sql
- id (VARCHAR, PK)
- name (VARCHAR, NOT NULL)
- county_id (VARCHAR(2), FK → counties.id)
- geometry (GEOMETRY(POLYGON, 4326))
- area_km2 (DECIMAL)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### gfs_uploads
```sql
- id (UUID, PK)
- filename (VARCHAR, NOT NULL)
- file_path (VARCHAR, NOT NULL)
- file_size (BIGINT)
- model_run (TIMESTAMP)
- uploaded_by (UUID, FK → users.id)
- status (ENUM: 'uploaded', 'processing', 'processed', 'failed')
- error_message (TEXT)
- created_at (TIMESTAMP)
- updated_at (TIMESTAMP)
```

#### gfs_processed_datasets
```sql
- id (UUID, PK)
- upload_id (UUID, FK → gfs_uploads.id)
- county_id (VARCHAR(2), FK → counties.id)
- processing_status (ENUM: 'pending', 'processing', 'completed', 'failed')
- processed_at (TIMESTAMP)
- metadata (JSONB)
- created_at (TIMESTAMP)
```

#### ward_forecasts
```sql
- id (UUID, PK)
- dataset_id (UUID, FK → gfs_processed_datasets.id)
- ward_id (VARCHAR, FK → wards.id)
- variable (VARCHAR) -- 'rainfall', 'temperature', 'wind_speed', etc.
- daily_values (JSONB) -- Array of 7 values
- weekly_total (DECIMAL)
- weekly_mean (DECIMAL)
- weekly_max (DECIMAL)
- weekly_min (DECIMAL)
- aggregation_method (VARCHAR)
- grid_points_used (INTEGER)
- quality_flag (ENUM: 'good', 'degraded', 'missing')
- units (VARCHAR)
- created_at (TIMESTAMP)
```

#### reports
```sql
- id (UUID, PK)
- county_id (VARCHAR(2), FK → counties.id)
- period_start (DATE, NOT NULL)
- period_end (DATE, NOT NULL)
- status (ENUM: 'generating', 'completed', 'failed')
- generated_by (UUID, FK → users.id)
- generated_at (TIMESTAMP)
- metadata (JSONB)
- created_at (TIMESTAMP)
```

#### report_files
```sql
- id (UUID, PK)
- report_id (UUID, FK → reports.id)
- file_type (ENUM: 'pdf', 'csv', 'json')
- file_path (VARCHAR, NOT NULL)
- file_size (BIGINT)
- created_at (TIMESTAMP)
```

#### maps
```sql
- id (UUID, PK)
- report_id (UUID, FK → reports.id, NULLABLE)
- county_id (VARCHAR(2), FK → counties.id)
- variable (VARCHAR) -- 'rainfall', 'temperature', 'wind_speed'
- date (DATE)
- file_path (VARCHAR, NOT NULL)
- resolution (INTEGER) -- DPI
- format (VARCHAR) -- 'PNG', 'WebP'
- metadata (JSONB)
- created_at (TIMESTAMP)
```

#### system_config
```sql
- id (UUID, PK)
- key (VARCHAR, UNIQUE, NOT NULL)
- value (TEXT)
- description (TEXT)
- updated_by (UUID, FK → users.id)
- updated_at (TIMESTAMP)
```

#### log_entries
```sql
- id (UUID, PK)
- level (VARCHAR) -- 'INFO', 'WARNING', 'ERROR'
- message (TEXT)
- module (VARCHAR)
- user_id (UUID, FK → users.id, NULLABLE)
- task_id (VARCHAR, NULLABLE) -- Celery task ID
- metadata (JSONB)
- created_at (TIMESTAMP)
```

### Indexes

- `users.email` (UNIQUE)
- `counties.id` (PRIMARY KEY)
- `wards.county_id` (INDEX)
- `gfs_uploads.uploaded_by` (INDEX)
- `gfs_uploads.status` (INDEX)
- `gfs_processed_datasets.county_id` (INDEX)
- `ward_forecasts.dataset_id` (INDEX)
- `ward_forecasts.ward_id` (INDEX)
- `reports.county_id` (INDEX)
- `reports.period_start` (INDEX)
- `maps.county_id` (INDEX)
- `maps.variable` (INDEX)
- `log_entries.created_at` (INDEX)
- `log_entries.level` (INDEX)

### Spatial Indexes (PostGIS)

- `counties.geometry` (GIST)
- `wards.geometry` (GIST)

---

## Authentication & Authorization

### JWT Token Structure

```json
{
  "sub": "user_id",
  "email": "user@example.com",
  "role": "admin",
  "exp": 1234567890,
  "iat": 1234567890
}
```

### Roles

- **admin**: Full access to all endpoints, system configuration
- **user**: Access to reports, data viewing, limited operations

### Protected Endpoints

All endpoints except:
- `POST /auth/register`
- `POST /auth/login`
- `GET /system/health`

### Authorization Levels

- **Public**: No authentication required
- **Authenticated**: Valid JWT token required
- **Admin**: Valid JWT token with `role: "admin"` required

---

## Data Processing Pipeline

### GFS Processing Flow

1. **Upload**: User uploads GFS GRIB file
2. **Validation**: Validate file format and structure
3. **Storage**: Save file to storage system
4. **Processing Trigger**: User or system triggers processing
5. **Spatial Extraction**: Extract Kenya region from GFS data
6. **Spatial Join**: Join grid points to ward polygons
7. **Aggregation**: Aggregate grid points to ward-level data
8. **Storage**: Store processed ward forecasts
9. **Status Update**: Update processing status

### Report Generation Flow

1. **Request**: User requests report generation for county
2. **Data Retrieval**: Retrieve processed ward forecasts
3. **Aggregation**: Aggregate to county-level statistics
4. **Narrative Generation**: Generate narrative text
5. **Map Generation**: Generate geospatial maps
6. **PDF Generation**: Assemble PDF report
7. **CSV Generation**: Generate CSV export
8. **Storage**: Store generated files
9. **Status Update**: Update report status

---

## Testing Strategy

### Unit Tests (80% coverage target)
- Service layer logic
- Utility functions
- Data validation
- Business rules

### Integration Tests (15% coverage target)
- API endpoints
- Database operations
- File operations
- External service interactions

### End-to-End Tests (5% coverage target)
- Complete workflows
- Error scenarios
- Authentication flows

### Test Data
- Use factories for test data generation
- Use test database (separate from development)
- Clean up test data after tests

---

## Deployment Considerations

### Environment Variables

```env
# Database
DATABASE_URL=postgresql://user:pass@localhost/clima_scope
POSTGRES_USER=clima_scope
POSTGRES_PASSWORD=secret
POSTGRES_DB=clima_scope

# Redis
REDIS_URL=redis://localhost:6379/0

# JWT
JWT_SECRET_KEY=your-secret-key
JWT_ALGORITHM=HS256
JWT_ACCESS_TOKEN_EXPIRE_MINUTES=30
JWT_REFRESH_TOKEN_EXPIRE_DAYS=7

# File Storage
STORAGE_PATH=/app/storage
MAX_UPLOAD_SIZE=1073741824  # 1GB

# CORS
CORS_ORIGINS=http://localhost:3000,https://yourdomain.com

# API
API_V1_PREFIX=/api/v1
ENVIRONMENT=development

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0
```

### Docker Setup

- Multi-stage Dockerfile for production
- docker-compose.yml for local development
- Health checks
- Volume mounts for file storage

### Production Considerations

- Use environment-specific configurations
- Set up database backups
- Implement monitoring (Prometheus, Grafana)
- Set up error tracking (Sentry)
- Configure rate limiting
- Set up CDN for static files
- Use cloud storage (S3) for production
- Implement horizontal scaling

---

## Estimated Timeline

- **Phase 1**: 2-3 days
- **Phase 2**: 3-4 days
- **Phase 3**: 2-3 days
- **Phase 4**: 5-7 days
- **Phase 5**: 3-4 days
- **Phase 6**: 7-10 days
- **Phase 7**: 5-7 days
- **Phase 8**: 2-3 days
- **Phase 9**: 3-4 days
- **Phase 10**: 5-7 days
- **Phase 11**: 3-4 days

**Total Estimated Time**: 42-58 days

---

## Next Steps

1. Review and approve this implementation plan
2. Set up development environment
3. Begin Phase 1: Project Setup & Foundation
4. Iterate through phases sequentially
5. Regular code reviews and testing
6. Documentation updates as implementation progresses

---

**Last Updated**: 2026-01-18  
**Version**: 1.0.0  
**Status**: Planning Complete - Ready for Implementation
