# Cursor Setup for Clima-scope

This document describes the Cursor rules, skills, and development plan configured for the Clima-scope project.

## 📁 Cursor Rules

Rules are located in `.cursor/rules/` and provide persistent context for AI assistance:

### 1. `project-overview.mdc` (Always Applied)
- Core project context and architecture
- Key principles and entities
- Data flow overview

### 2. `typescript-standards.mdc` (TypeScript/TSX files)
- Type safety requirements
- Error handling patterns
- React component patterns
- Schema validation

### 3. `python-standards.mdc` (Python files)
- Code style (Black, flake8)
- FastAPI patterns
- Database patterns
- Logging conventions
- Reference data rules

### 4. `api-design.mdc` (Python API files)
- Endpoint patterns
- Response models
- Error handling
- Pagination standards

### 5. `data-models.mdc` (Models/Schemas)
- Database model patterns
- Pydantic schema conventions
- JSON Schema standards
- County/Ward model specifics

## 🎯 Cursor Skill

**Location**: `.cursor/skills/clima-scope-development/`

**Purpose**: Guides development for Clima-scope weather reporting system

**When to Use**: 
- Working on backend API endpoints
- Database models
- County/ward reference data
- Weather reports
- PDF generation
- Implementing features for Kenya county weather reporting

**Key Guidance**:
- Reference data vs user data distinction
- API endpoint patterns
- Database model structure
- Schema validation
- Common development tasks

## 📋 Development Plan

**Location**: `DEVELOPMENT_PLAN.md` (root)

**Contents**:
- Completed phases
- Current priorities
- Future phases
- Quick start guides
- Development guidelines
- Known issues

## 🚀 Usage

### For AI Assistance
The rules and skill are automatically applied when:
- Working with TypeScript/TSX files (TypeScript standards)
- Working with Python files (Python standards)
- Working with API files (API design patterns)
- Working with models/schemas (Data model patterns)
- General project work (Project overview - always applied)

### For Development
Refer to `DEVELOPMENT_PLAN.md` for:
- Current priorities and tasks
- Phase completion status
- Quick start instructions
- Development guidelines

## 📝 Maintenance

### Updating Rules
1. Edit the `.mdc` file in `.cursor/rules/`
2. Keep rules concise (< 50 lines recommended)
3. Include concrete examples
4. Update when patterns change

### Updating Skill
1. Edit `SKILL.md` in `.cursor/skills/clima-scope-development/`
2. Keep under 500 lines
3. Use progressive disclosure for detailed content
4. Update when workflows change

### Updating Plan
1. Edit `DEVELOPMENT_PLAN.md`
2. Update status as phases complete
3. Add new phases as needed
4. Keep priorities current

---

**Last Updated**: 2026-01-27
