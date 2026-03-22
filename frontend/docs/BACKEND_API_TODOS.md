# Backend API Implementation - Task Breakdown

**Project**: Clima-scope Backend API  
**Framework**: Python FastAPI  
**Date**: 2026-01-18

---

## 📋 Quick Reference: All API Routes

### Authentication (`/api/v1/auth`)
- `POST /auth/register` - Register new user
- `POST /auth/login` - User login (get JWT)
- `POST /auth/refresh` - Refresh access token
- `POST /auth/logout` - Logout (invalidate token)
- `GET /auth/me` - Get current user info
- `PUT /auth/me` - Update current user
- `POST /auth/change-password` - Change password

### Counties (`/api/v1/counties`)
- `GET /counties` - List all counties (paginated)
- `GET /counties/{county_id}` - Get county details
- `GET /counties/{county_id}/wards` - Get all wards in county
- `GET /counties/{county_id}/wards/{ward_id}` - Get ward details
- `GET /counties/{county_id}/boundaries` - Get boundaries (GeoJSON)
- `POST /counties/{county_id}/boundaries` - Upload boundaries (Admin)

### Data Upload & Processing (`/api/v1/data`)
- `POST /data/upload` - Upload GFS GRIB file
- `GET /data/uploads` - List all uploads (paginated)
- `GET /data/uploads/{upload_id}` - Get upload details
- `POST /data/uploads/{upload_id}/process` - Trigger processing
- `GET /data/uploads/{upload_id}/status` - Get processing status
- `DELETE /data/uploads/{upload_id}` - Delete upload (Admin)
- `GET /data/processed` - List processed datasets
- `GET /data/processed/{dataset_id}` - Get processed dataset

### Reports (`/api/v1/reports`)
- `POST /reports/generate` - Generate report for county
- `GET /reports` - List all reports (paginated, filtered)
- `GET /reports/{report_id}` - Get report metadata
- `GET /reports/{report_id}/pdf` - Download PDF report
- `GET /reports/{report_id}/csv` - Download CSV data
- `GET /reports/{report_id}/json` - Get report JSON data
- `GET /reports/county/{county_id}` - Get reports for county
- `GET /reports/county/{county_id}/latest` - Get latest report
- `DELETE /reports/{report_id}` - Delete report (Admin)
- `POST /reports/batch-generate` - Batch generate (Admin)

### Maps (`/api/v1/maps`)
- `GET /maps/county/{county_id}/rainfall` - Get rainfall map
- `GET /maps/county/{county_id}/temperature` - Get temperature map
- `GET /maps/county/{county_id}/wind` - Get wind speed map
- `GET /maps/county/{county_id}/{variable}/{date}` - Get map by date
- `GET /maps/county/{county_id}/{variable}/{date}/metadata` - Get metadata
- `POST /maps/generate` - Generate maps for county
- `GET /maps/report/{report_id}` - Get all maps for report

### Wards (`/api/v1/wards`)
- `GET /wards/{ward_id}` - Get ward details
- `GET /wards/{ward_id}/forecast` - Get ward forecast data
- `GET /wards/{ward_id}/forecast/history` - Get historical forecasts
- `GET /counties/{county_id}/wards/aggregated` - Get aggregated data

### System (`/api/v1/system`)
- `GET /system/health` - Health check (public)
- `GET /system/status` - System status
- `GET /system/config` - Get configuration (Admin)
- `PUT /system/config` - Update configuration (Admin)
- `GET /system/stats` - System statistics (Admin)

### Logs (`/api/v1/logs`)
- `GET /logs` - Get system logs (Admin)
- `GET /logs/{log_id}` - Get specific log (Admin)
- `GET /logs/processing/{task_id}` - Get task logs
- `GET /diagnostics` - System diagnostics (Admin)
- `POST /diagnostics/test-processing` - Test pipeline (Admin)

---

## ✅ Implementation Tasks

### Phase 1: Foundation Setup

#### 1.1 Project Structure
- [ ] Create `backend/` directory
- [ ] Set up Python virtual environment
- [ ] Create directory structure (app/, tests/, alembic/, scripts/)
- [ ] Initialize Git repository for backend
- [ ] Create `.gitignore` for Python

#### 1.2 Dependencies & Configuration
- [ ] Create `requirements.txt` with all packages
- [ ] Create `app/config.py` with Pydantic settings
- [ ] Create `.env.example` with all environment variables
- [ ] Set up configuration for database, Redis, JWT, file storage

#### 1.3 Database Setup
- [ ] Set up PostgreSQL with PostGIS extension
- [ ] Create `app/database.py` with SQLAlchemy setup
- [ ] Initialize Alembic for migrations
- [ ] Create database connection and session management

#### 1.4 FastAPI Application
- [ ] Create `app/main.py` with FastAPI app
- [ ] Configure CORS middleware
- [ ] Set up error handling middleware
- [ ] Configure logging
- [ ] Create health check endpoint (`GET /system/health`)

---

### Phase 2: Authentication

#### 2.1 User Model & Database
- [ ] Create `User` model (id, email, password, role, etc.)
- [ ] Create Alembic migration for users table
- [ ] Create user repository with CRUD operations

#### 2.2 Authentication Service
- [ ] Implement password hashing (bcrypt)
- [ ] Implement JWT token generation/validation
- [ ] Create login/register logic
- [ ] Implement refresh token mechanism

#### 2.3 Authentication Endpoints
- [ ] `POST /auth/register` - Register endpoint
- [ ] `POST /auth/login` - Login endpoint
- [ ] `POST /auth/refresh` - Refresh token endpoint
- [ ] `POST /auth/logout` - Logout endpoint
- [ ] `GET /auth/me` - Get current user
- [ ] `PUT /auth/me` - Update current user
- [ ] `POST /auth/change-password` - Change password

#### 2.4 Authorization Middleware
- [ ] Create JWT authentication dependency
- [ ] Create role-based authorization dependency
- [ ] Add auth checks to protected endpoints

---

### Phase 3: County & Ward Management

#### 3.1 County & Ward Models
- [ ] Create `County` model (id, name, geometry)
- [ ] Create `Ward` model (id, name, county_id, geometry)
- [ ] Create Alembic migrations
- [ ] Set up PostGIS spatial columns

#### 3.2 County Repository
- [ ] Implement county CRUD operations
- [ ] Implement spatial queries (PostGIS)
- [ ] Implement ward queries by county
- [ ] Add GeoJSON serialization

#### 3.3 County Endpoints
- [ ] `GET /counties` - List counties with pagination
- [ ] `GET /counties/{county_id}` - Get county details
- [ ] `GET /counties/{county_id}/wards` - List wards
- [ ] `GET /counties/{county_id}/wards/{ward_id}` - Ward details
- [ ] `GET /counties/{county_id}/boundaries` - Get GeoJSON boundaries
- [ ] `POST /counties/{county_id}/boundaries` - Upload boundaries (Admin)

#### 3.4 Data Seeding
- [ ] Create script to seed 47 Kenyan counties
- [ ] Create script to seed ward boundaries (if available)

---

### Phase 4: GFS Data Processing

#### 4.1 GFS Data Models
- [ ] Create `GFSUpload` model
- [ ] Create `GFSProcessedDataset` model
- [ ] Create `WardForecast` model
- [ ] Create Alembic migrations

#### 4.2 File Storage Service
- [ ] Implement file upload handling
- [ ] Implement GRIB file validation
- [ ] Implement file storage (local filesystem)
- [ ] Add file cleanup on deletion

#### 4.3 GFS Processing Service
- [ ] Implement GRIB file reading (PyGRIB)
- [ ] Implement spatial extraction for Kenya region
- [ ] Implement grid point to ward aggregation
- [ ] Implement data validation
- [ ] Add error handling

#### 4.4 GFS Upload Endpoints
- [ ] `POST /data/upload` - Upload GFS file
- [ ] `GET /data/uploads` - List uploads
- [ ] `GET /data/uploads/{upload_id}` - Upload details
- [ ] `POST /data/uploads/{upload_id}/process` - Trigger processing
- [ ] `GET /data/uploads/{upload_id}/status` - Processing status
- [ ] `DELETE /data/uploads/{upload_id}` - Delete upload (Admin)

#### 4.5 Celery Task for Processing
- [ ] Create Celery task for GFS processing
- [ ] Implement async processing with progress tracking
- [ ] Add task status updates

---

### Phase 5: Spatial Processing

#### 5.1 Spatial Processing Service
- [ ] Implement point-in-polygon spatial join
- [ ] Implement area-weighted aggregation
- [ ] Implement ward-level data aggregation
- [ ] Calculate statistics (mean, max, min, total)
- [ ] Add quality flags

#### 5.2 County Report Data
- [ ] Aggregate ward data to county level
- [ ] Calculate county-level statistics
- [ ] Identify extreme values
- [ ] Generate flood risk assessments

---

### Phase 6: Report Generation

#### 6.1 Report Models
- [ ] Create `Report` model
- [ ] Create `ReportFile` model
- [ ] Create Alembic migrations

#### 6.2 Narrative Generation
- [ ] Implement executive summary generation
- [ ] Implement weekly narrative generation
- [ ] Implement variable-specific narratives
- [ ] Generate advisories and impacts

#### 6.3 PDF Generation
- [ ] Implement PDF structure (11 sections)
- [ ] Add cover page generation
- [ ] Add executive summary section
- [ ] Add narrative sections
- [ ] Add data tables
- [ ] Integrate map images
- [ ] Add metadata and disclaimers

#### 6.4 CSV Export
- [ ] Implement CSV generation
- [ ] Include ward-level data
- [ ] Include daily breakdowns

#### 6.5 Report Endpoints
- [ ] `POST /reports/generate` - Generate report
- [ ] `GET /reports` - List reports with filters
- [ ] `GET /reports/{report_id}` - Report metadata
- [ ] `GET /reports/{report_id}/pdf` - Download PDF
- [ ] `GET /reports/{report_id}/csv` - Download CSV
- [ ] `GET /reports/{report_id}/json` - Get JSON data
- [ ] `GET /reports/county/{county_id}` - County reports
- [ ] `GET /reports/county/{county_id}/latest` - Latest report
- [ ] `DELETE /reports/{report_id}` - Delete report (Admin)
- [ ] `POST /reports/batch-generate` - Batch generation (Admin)

#### 6.6 Celery Task for Reports
- [ ] Create Celery task for report generation
- [ ] Implement async PDF generation
- [ ] Add progress tracking

---

### Phase 7: Map Generation

#### 7.1 Map Models
- [ ] Create `Map` model
- [ ] Create Alembic migration

#### 7.2 Map Generation Service
- [ ] Implement base map creation (Cartopy)
- [ ] Implement ward-level choropleth maps
- [ ] Add color schemes (rainfall, temperature, wind)
- [ ] Add cartographic elements
- [ ] Generate maps at different resolutions
- [ ] Export to PNG format
- [ ] Generate web-optimized versions (WebP)

#### 7.3 Map Storage
- [ ] Implement map file storage
- [ ] Organize maps by county/variable/date
- [ ] Generate map metadata

#### 7.4 Map Endpoints
- [ ] `GET /maps/county/{county_id}/rainfall` - Rainfall map
- [ ] `GET /maps/county/{county_id}/temperature` - Temperature map
- [ ] `GET /maps/county/{county_id}/wind` - Wind map
- [ ] `GET /maps/county/{county_id}/{variable}/{date}` - Specific map
- [ ] `GET /maps/county/{county_id}/{variable}/{date}/metadata` - Metadata
- [ ] `POST /maps/generate` - Generate maps
- [ ] `GET /maps/report/{report_id}` - Report maps

#### 7.5 Celery Task for Maps
- [ ] Create Celery task for map generation
- [ ] Implement async map generation

---

### Phase 8: Ward Data

#### 8.1 Ward Data Service
- [ ] Implement ward forecast retrieval
- [ ] Implement historical data queries
- [ ] Add data aggregation functions

#### 8.2 Ward Endpoints
- [ ] `GET /wards/{ward_id}` - Ward details
- [ ] `GET /wards/{ward_id}/forecast` - Current forecast
- [ ] `GET /wards/{ward_id}/forecast/history` - Historical data
- [ ] `GET /counties/{county_id}/wards/aggregated` - Aggregated data

---

### Phase 9: System & Monitoring

#### 9.1 System Configuration
- [ ] Create `SystemConfig` model
- [ ] Create Alembic migration

#### 9.2 System Endpoints
- [ ] `GET /system/health` - Health check (already done)
- [ ] `GET /system/status` - System status
- [ ] `GET /system/config` - Get configuration (Admin)
- [ ] `PUT /system/config` - Update configuration (Admin)
- [ ] `GET /system/stats` - System statistics (Admin)

#### 9.3 Logging & Diagnostics
- [ ] Create `LogEntry` model
- [ ] Implement structured logging
- [ ] Implement log retrieval
- [ ] Implement diagnostics

#### 9.4 Logs Endpoints
- [ ] `GET /logs` - System logs (Admin)
- [ ] `GET /logs/{log_id}` - Specific log (Admin)
- [ ] `GET /logs/processing/{task_id}` - Task logs
- [ ] `GET /diagnostics` - Diagnostics (Admin)
- [ ] `POST /diagnostics/test-processing` - Test pipeline (Admin)

---

### Phase 10: Testing

#### 10.1 Test Setup
- [ ] Configure pytest
- [ ] Set up test database
- [ ] Create test fixtures
- [ ] Create test data factories

#### 10.2 Unit Tests
- [ ] Test authentication service
- [ ] Test GFS processing service
- [ ] Test spatial processing service
- [ ] Test report generation service
- [ ] Test map generation service
- [ ] Test repositories

#### 10.3 Integration Tests
- [ ] Test API endpoints
- [ ] Test database operations
- [ ] Test file operations
- [ ] Test Celery tasks

#### 10.4 E2E Tests
- [ ] Test complete workflow
- [ ] Test error scenarios
- [ ] Test authentication flows

---

### Phase 11: Documentation & Deployment

#### 11.1 API Documentation
- [ ] Configure FastAPI automatic docs (Swagger)
- [ ] Add endpoint descriptions
- [ ] Add request/response examples
- [ ] Document error responses

#### 11.2 Deployment
- [ ] Create Dockerfile
- [ ] Create docker-compose.yml
- [ ] Create production deployment config
- [ ] Document environment variables

#### 11.3 Performance
- [ ] Add database indexes
- [ ] Implement Redis caching
- [ ] Optimize queries
- [ ] Add connection pooling

---

## 📊 Summary

**Total API Endpoints**: 50+  
**Total Tasks**: 100+  
**Estimated Time**: 6-8 weeks

**Key Features**:
- ✅ Complete authentication system
- ✅ County and ward management
- ✅ GFS data upload and processing
- ✅ Spatial aggregation to ward level
- ✅ PDF and CSV report generation
- ✅ Geospatial map generation
- ✅ System monitoring and logging
- ✅ Admin configuration management

---

**Status**: Ready for implementation  
**Next Step**: Begin Phase 1 - Foundation Setup
