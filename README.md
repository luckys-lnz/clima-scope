# Climate Scoop

**Automated Weekly County Weather Reporting System for Kenya**

Climate Scoop is an automated weather reporting system that generates comprehensive weekly county-level weather forecasts and reports for all 47 Kenyan counties. The system processes GFS (Global Forecast System) 7-day forecast data, performs spatial aggregation to ward-level, and generates professional PDF reports with integrated geospatial visualizations.

---

## 🌟 Features

### Core Functionality
- **Automated Report Generation**: Weekly 7-day weather forecasts for all 47 Kenyan counties
- **Ward-Level Spatial Aggregation**: Detailed ward-level breakdowns of weather variables
- **PDF Report Generation**: Professional, multi-section PDF reports with embedded maps
- **CSV Data Export**: Tabular data export for analysis and integration
- **Geospatial Visualizations**: High-resolution ward-level distribution maps (rainfall, temperature, wind)

### Weather Variables
- **Rainfall**: Total weekly rainfall, daily breakdowns, intensity analysis, flood risk assessment
- **Temperature**: Mean, maximum, minimum temperatures with diurnal patterns
- **Wind**: Speed, direction, gust analysis with wind rose diagrams

### Report Sections
1. Cover Page with metadata and branding
2. Executive Summary with key statistics
3. Weekly Narrative Summary
4. Rainfall Outlook with distribution maps
5. Temperature Outlook with distribution maps
6. Wind Outlook with distribution maps
7. Ward-Level Visualizations (full-page maps)
8. Extreme Values and Highlights
9. Impacts and Advisories
10. Data Sources and Methodology
11. Metadata and Disclaimers

---

## 🛠️ Tech Stack

### Frontend
- **Framework**: Next.js 16 (App Router)
- **UI Library**: React 19
- **Styling**: Tailwind CSS 4
- **Components**: shadcn/ui (Radix UI primitives)
- **Icons**: Lucide React
- **Forms**: React Hook Form + Zod validation
- **Charts**: Recharts
- **Language**: TypeScript 5 (strict mode)

### Development Tools
- **Testing**: Vitest
- **Linting**: ESLint
- **Package Manager**: npm
- **Analytics**: Vercel Analytics

### Data Processing (Planned)
- **Backend**: Python FastAPI (planned)
- **Geospatial**: GeoPandas, PyGRIB
- **Visualization**: Matplotlib, Cartopy
- **PDF Generation**: ReportLab, WeasyPrint (planned)

---

## 📁 Project Structure

```
clima-scope/
├── app/                    # Next.js app directory
│   ├── dashboard/          # Dashboard pages
│   ├── sign-in/            # Authentication pages
│   ├── sign-up/
│   ├── layout.tsx          # Root layout
│   └── page.tsx           # Landing page
│
├── components/             # React components
│   ├── screens/           # Screen components
│   ├── ui/                # shadcn/ui components
│   └── *.tsx              # Shared components
│
├── lib/                    # Core libraries
│   ├── __tests__/         # Unit tests
│   ├── data-interfaces.ts # Data interface definitions
│   ├── json-schema.ts     # JSON schema implementation
│   ├── map-embedding.ts   # Map embedding strategy
│   ├── report-structure.ts # Report structure definitions
│   └── weather-schemas.ts # Weather data schemas
│
├── docs/                   # Documentation
│   ├── REPORT_STRUCTURE_SPECIFICATION.md
│   ├── DATA_INTERFACES_SPECIFICATION.md
│   ├── JSON_SCHEMA_SPECIFICATION.md
│   ├── MAP_EMBEDDING_STRATEGY.md
│   └── *.md               # Additional documentation
│
├── schemas/                # JSON schemas
│   └── county-weather-report.schema.json
│
├── scripts/                # Utility scripts
│   └── validate-schemas.ts
│
└── public/                # Static assets
```

---

## 🚀 Getting Started

### Prerequisites
- Node.js 18+ 
- npm or pnpm

### Installation

1. **Clone the repository**
   ```bash
   git clone <repository-url>
   cd clima-scope
   ```

2. **Install dependencies**
   ```bash
   npm install
   ```

3. **Run development server**
   ```bash
   npm run dev
   ```

4. **Open in browser**
   Navigate to [http://localhost:3000](http://localhost:3000)

### Available Scripts

```bash
# Development
npm run dev          # Start development server
npm run build        # Build for production
npm run start        # Start production server

# Code Quality
npm run lint         # Run ESLint
npm run test         # Run tests in watch mode
npm run test:run     # Run tests once
```

---

## 📚 Documentation

### Specification Documents

- **[Report Structure Specification](./docs/REPORT_STRUCTURE_SPECIFICATION.md)**
  - Complete 11-section report structure
  - Content requirements and formatting standards
  - Narrative generation guidelines

- **[Data Interfaces Specification](./docs/DATA_INTERFACES_SPECIFICATION.md)**
  - Input schemas (GFS GRIB, shapefiles, observations)
  - Processing schemas (spatial aggregation)
  - Output schemas (report components)

- **[JSON Schema Specification](./docs/JSON_SCHEMA_SPECIFICATION.md)**
  - County weather report JSON schema (Draft 7)
  - TypeScript implementations
  - CSV export utilities

- **[Map Embedding Strategy](./docs/MAP_EMBEDDING_STRATEGY.md)**
  - PDF map embedding specifications
  - Web dashboard map display
  - Map generation requirements

### TypeScript Interfaces

All core data structures are defined in TypeScript:

- `lib/weather-schemas.ts` - Core weather data types
- `lib/report-structure.ts` - Report structure interfaces
- `lib/data-interfaces.ts` - Data flow interfaces
- `lib/json-schema.ts` - JSON schema types
- `lib/map-embedding.ts` - Map embedding types

---

## 🗺️ Data Flow

```
┌─────────────────┐
│  GFS GRIB Files │  (NOAA/NCEP)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Spatial Join   │  (Ward Boundaries)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Aggregation    │  (Ward-Level Data)
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Report Gen     │  (PDF + CSV)
└─────────────────┘
```

### Data Sources
- **Forecast Data**: GFS (Global Forecast System) 7-day forecasts
- **Administrative Boundaries**: Kenya county and ward shapefiles
- **Coordinate System**: UTM Zone 37N (EPSG:32637) or WGS84 (EPSG:4326)

---

## 🧪 Testing

The project includes comprehensive test coverage for schemas and data validation:

```bash
# Run all tests
npm run test:run

# Watch mode
npm run test
```

Test files:
- `lib/__tests__/schemas.test.ts` - Schema validation tests
- `scripts/validate-schemas.ts` - Schema validation script

---


### ✅ Completed (Person B Tasks)

- [x] **Report Structure & Sections** - Complete 11-section specification
- [x] **Data Interfaces & Schemas** - Comprehensive input/output schemas
- [x] **JSON Schema Definition** - Draft 7 compliant schema
- [x] **Map Embedding Strategy** - PDF and web embedding specifications
- [x] **TypeScript Type Safety** - Strict typing throughout
- [x] **Testing Infrastructure** - Vitest setup with test coverage

### 🚧 In Progress

- [ ] **PDF Generation** - Backend implementation
- [ ] **CSV Export** - Backend implementation
- [ ] **Map Generation** - Geospatial visualization pipeline
- [ ] **API Integration** - Backend service integration
- [ ] **UI Updates** - Connect frontend to backend APIs

### 📋 Planned

- [ ] **Backend Service** - Python FastAPI service
- [ ] **Automated Scheduling** - Weekly report generation
- [ ] **Email Distribution** - Automated report delivery
- [ ] **Historical Data** - Report archive and comparison
- [ ] **Multi-language** - Swahili translation support

---

## 🏗️ Architecture

### Frontend (Current)
- **Next.js 16** with App Router
- **TypeScript** for type safety
- **React 19** for UI components
- **Tailwind CSS 4** for styling
- **shadcn/ui** for component library

### Backend (Planned)
- **Python FastAPI** for API service
- **GeoPandas** for geospatial processing
- **PyGRIB** for GFS data parsing
- **Matplotlib/Cartopy** for map generation
- **ReportLab/WeasyPrint** for PDF generation

### Data Flow
1. **Input**: GFS GRIB files → Spatial processing
2. **Processing**: Ward-level aggregation → County summaries
3. **Output**: PDF reports + CSV exports

---

## 📝 Key Specifications

### Report Format
- **Type**: PDF (A4 or Letter)
- **Frequency**: Weekly (7-day forecast)
- **Coverage**: County-level with ward-level breakdowns
- **Language**: English (Swahili planned)

### Map Specifications
- **Resolution**: 300 DPI (section maps), 400 DPI (full-page)
- **Format**: PNG (preferred)
- **Projection**: UTM Zone 37N (EPSG:32637)
- **Color Schemes**: Defined per variable (rainfall, temperature, wind)

### Data Schema
- **JSON Schema**: Draft 7 compliant
- **TypeScript**: Strict typing throughout
- **Validation**: Runtime type guards and validators

---

## 🤝 Contributing

This project follows a structured development approach:

1. **Specifications First**: All features are specified before implementation
2. **Type Safety**: Strict TypeScript with no `any` types
3. **Documentation**: Comprehensive documentation for all components
4. **Testing**: Unit tests for critical functionality

### Development Workflow

1. Review specification documents in `docs/`
2. Implement according to TypeScript interfaces
3. Write tests for new functionality
4. Update documentation as needed

---

## 📄 License

[Add license information]

---

## 📧 Contact

[Add contact information]

---

## 🙏 Acknowledgments

- **Data Sources**: NOAA/NCEP for GFS forecast data
- **Administrative Boundaries**: KNBS, HDX for Kenya boundaries
- **UI Components**: shadcn/ui community
- **Icons**: Lucide React

---

**Last Updated**: 2026-01-18  
**Version**: 0.1.0  
**Status**: Development
