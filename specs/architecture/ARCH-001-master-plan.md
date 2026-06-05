# Patient Navigator Platform — Comprehensive Spec-Driven Development Plan

**Version:** 1.0
**Status:** DRAFT
**Date:** 2026-06-04
**Owner:** @platform-team

---

## Table of Contents

1. [Architecture Design](#1-architecture-design)
2. [Data Schema Specs](#2-data-schema-specs)
3. [API Specs](#3-api-specs)
4. [Feature Specs](#4-feature-specs)
5. [Test Strategy](#5-test-strategy)
6. [Implementation Roadmap](#6-implementation-roadmap)
7. [Security Considerations](#7-security-considerations)
8. [Infrastructure and Deployment](#8-infrastructure-and-deployment)

---

## 1. Architecture Design

### 1.1 System Architecture Overview

The platform uses a monolithic FastAPI backend serving a React SPA frontend, with a PostgreSQL database, Ollama for LLM inference, PaddleOCR for document extraction, and ChromaDB for vector search.

```
+--------------------------------------------------------------------+
|                        CLIENT LAYER                                 |
|  React SPA (TypeScript + Tailwind CSS)                             |
|  - Role-based route guards                                         |
|  - JWT token management in localStorage                            |
|  - Axios HTTP client with interceptors                             |
+-------------------------------+------------------------------------+
                                |
                          HTTPS / JSON
                                |
+-------------------------------v------------------------------------+
|                      API GATEWAY LAYER                              |
|  Nginx (Reverse Proxy, TLS termination, static file serving)       |
+-------------------------------+------------------------------------+
                                |
+-------------------------------v------------------------------------+
|                    APPLICATION LAYER (FastAPI)                      |
|                                                                     |
|  +-----------+  +----------+  +---------+  +---------+             |
|  | Auth      |  | Patient  |  | Case    |  | Document|             |
|  | Router    |  | Router   |  | Router  |  | Router  |             |
|  +-----+-----+  +----+-----+  +----+----+  +----+----+             |
|        |              |             |            |                  |
|  +-----v-----+  +----v-----+  +----v----+  +----v----+             |
|  | Auth      |  | Patient  |  | Case    |  | Document|             |
|  | Service   |  | Service  |  | Service |  | Service |             |
|  +-----------+  +----------+  +---------+  +---------+             |
|                                                                     |
|  +-----------+  +----------+  +---------+  +---------+             |
|  | Hospital  |  | Funding  |  | FollowUp|  | AI      |             |
|  | Router    |  | Router   |  | Router  |  | Router  |             |
|  +-----+-----+  +----+-----+  +----+----+  +----+----+             |
|        |              |             |            |                  |
|  +-----v-----+  +----v-----+  +----v----+  +----v----+             |
|  | Hospital  |  | Funding  |  | FollowUp|  | AI      |             |
|  | Service   |  | Service  |  | Service |  | Service |             |
|  +-----------+  +----------+  +---------+  +---------+             |
|                                                                     |
|  +-----------------------------------------------------+           |
|  | Middleware: JWT Auth, RBAC Enforcement, Audit Logger |           |
|  +-----------------------------------------------------+           |
+-------------------------------+------------------------------------+
                                |
          +---------------------+---------------------+
          |                     |                     |
+---------v--------+  +--------v-------+  +----------v--------+
|   PostgreSQL     |  |   Ollama       |  |   ChromaDB        |
|   (SQLAlchemy    |  |   (Qwen3,      |  |   (Vector search, |
|    + Alembic)    |  |    Gemma)      |  |    V2 RAG)        |
+------------------+  +-------+--------+  +-------------------+
                              |
                     +--------v--------+
                     |  PaddleOCR      |
                     |  (Document      |
                     |   extraction)   |
                     +-----------------+
```

### 1.2 Component Diagram

```
Frontend Components (React):
+-----------------------------------------------------------------+
| App                                                              |
|  +-- AuthProvider (JWT context, role context)                   |
|  +-- Router (React Router v6)                                   |
|      +-- Layout                                                  |
|          +-- Sidebar (role-adaptive navigation)                 |
|          +-- TopBar (user info, notifications)                  |
|      +-- Pages:                                                  |
|          +-- LoginPage                                          |
|          +-- DashboardPage (role-specific widgets)              |
|          +-- PatientsPage (list, search, create)                |
|          +-- PatientDetailPage (edit, cases, documents)         |
|          +-- CasesPage (list, filter by status)                 |
|          +-- CaseDetailPage (notes, timeline, AI summary)       |
|          +-- DocumentsPage (upload, preview, OCR results)       |
|          +-- HospitalsPage (directory, search, filter)          |
|          +-- FundingPage (programs, eligibility)                |
|          +-- FollowUpsPage (appointments, deadlines)            |
|          +-- AdminPage (users, roles, audit logs)               |
+-----------------------------------------------------------------+

Backend Components (FastAPI):
+-----------------------------------------------------------------+
| main.py (app factory, middleware registration)                  |
|  +-- api/                                                        |
|      +-- deps.py (dependency injection: DB session, current user)|
|      +-- v1/ (auth, patients, cases, documents, hospitals,      |
|      |       funding, followups, ai, reports)                   |
|  +-- services/ (auth, patient, case, document, hospital,        |
|  |              funding, followup, ai, ocr, audit)               |
|  +-- models/ (SQLAlchemy ORM models)                            |
|  +-- schemas/ (Pydantic request/response schemas)               |
|  +-- core/ (config, security, permissions, database)            |
|  +-- middleware/ (audit_log, rbac)                               |
|  +-- alembic/ (migrations)                                      |
+-----------------------------------------------------------------+
```

### 1.3 Data Flow

**Authentication Flow:**
1. User submits credentials to `POST /auth/login`
2. Auth service verifies password (bcrypt hash), loads role and permissions
3. JWT signed with user_id, role, exp (access: 30min, refresh: 7d)
4. Frontend stores access token, attaches to subsequent requests via Authorization header
5. Middleware validates JWT on every request, injects current_user dependency

**Patient Case Workflow:**
1. Navigator creates patient → Navigator creates case → Navigator uploads documents
2. PaddleOCR processes documents asynchronously, stores extracted text
3. Navigator requests AI summary → Ollama generates structured summary
4. Clinician reviews summary → approves or requests changes
5. Navigator uses hospital/funding directories to plan next steps
6. Follow-up tracking records appointments, deadlines, funding status

### 1.4 Directory Structure

```
patient-navigator/
├── specs/                          # SDD specification files
│   ├── REGISTRY.md
│   ├── features/                   # Gherkin feature specs (FEAT-001..008)
│   ├── api/                        # OpenAPI specification
│   ├── data/                       # JSON Schema data specs (DATA-001..012)
│   ├── architecture/               # Architecture decisions
│   └── adr/                        # ADR documents
├── backend/                        # FastAPI application
│   ├── app/
│   │   ├── main.py
│   │   ├── api/v1/                 # Route handlers
│   │   ├── core/                   # Config, security, permissions, database
│   │   ├── models/                 # SQLAlchemy ORM models
│   │   ├── schemas/                # Pydantic schemas
│   │   ├── services/               # Business logic
│   │   └── middleware/             # Audit log, RBAC
│   ├── alembic/                    # Database migrations
│   ├── tests/                      # unit/, integration/, contract/
│   └── pyproject.toml
├── frontend/                       # React application
│   ├── src/
│   │   ├── api/                    # API client modules
│   │   ├── components/             # layout/, common/, auth/, patients/, cases/, documents/, ai/, hospitals/, funding/
│   │   ├── hooks/                  # useAuth, usePatients, useCases, etc.
│   │   ├── pages/                  # Page components
│   │   ├── context/                # AuthContext, NotificationContext
│   │   ├── types/                  # TypeScript type definitions
│   │   └── utils/                  # permissions, formatters, constants
│   ├── tests/                      # components/, pages/, hooks/, e2e/
│   └── package.json
├── docker-compose.yml
├── Makefile
├── .env.example
└── CLAUDE.md
```

### 1.5 Architecture Decision Records

| ADR ID | Title | Decision |
|--------|-------|----------|
| ADR-001 | Monolith over microservices | Single FastAPI app for V1 MVP simplicity. Decompose later if needed. |
| ADR-002 | React SPA over HTMX | React provides richer interactivity for document preview and AI streaming. |
| ADR-003 | PostgreSQL for all environments | Eliminates dev/prod parity issues. Use Docker PostgreSQL in dev. |
| ADR-004 | JWT with refresh tokens | Stateless auth suitable for SPA. Refresh tokens in httpOnly cookies. |
| ADR-005 | Ollama local inference | No external API costs. Data stays on-premises. |
| ADR-006 | Filesystem storage for documents | V1 uses local filesystem. V2 can migrate to S3-compatible storage. |
| ADR-007 | PaddleOCR over Tesseract | Better multilingual support (Tamil in V2). Higher accuracy on medical docs. |

---

## 2. Data Schema Specs

### 2.1 Entity Relationship Summary

```
users ───< activities
users ───< timeline_events
users ───< clinician_reviews
roles  >─── users
patients ───< cases
patients ───< followups
patients ───< activities
cases   ───< documents
cases   ───< clinician_reviews
cases   ───< followups
cases   ───< timeline_events
hospitals ───< cases (recommended_hospital_id FK)
funding_programs ───< cases (applied_funding_id FK)
```

### 2.2 Table Definitions

#### roles (DATA-001)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, default uuid4 | |
| name | VARCHAR(50) | UNIQUE, NOT NULL | admin, navigator, clinician, volunteer, patient |
| description | TEXT | NULL | |
| permissions | JSONB | NOT NULL, default '{}' | Permission keys → access levels |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |

**Seed permissions:**
```
admin:      { patients: full, cases: full, documents: full, hospitals: full,
              funding: full, followups: full, ai: full, reports: full, users: full, audit: full }
navigator:  { patients: full, cases: full, documents: full, hospitals: read,
              funding: read, followups: full, ai: full, reports: read, users: none, audit: none }
clinician:  { patients: read, cases: read, documents: read, hospitals: read,
              funding: read, followups: read, ai: review, reports: read, users: none, audit: none }
volunteer:  { patients: read, cases: read, documents: none, hospitals: read,
              funding: read, followups: read, ai: none, reports: none, users: none, audit: none }
patient:    { patients: own, cases: own, documents: own, hospitals: read,
              funding: read, followups: own, ai: own, reports: own, users: none, audit: none }
```

#### users (DATA-002)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK, default uuid4 | |
| email | VARCHAR(254) | UNIQUE, NOT NULL | **x-pii: true** |
| password_hash | VARCHAR(255) | NOT NULL | bcrypt, never in API responses |
| full_name | VARCHAR(255) | NOT NULL | **x-pii: true** |
| phone | VARCHAR(20) | NULL | **x-pii: true** |
| role_id | UUID | FK → roles.id, NOT NULL | |
| is_active | BOOLEAN | NOT NULL, default true | |
| last_login_at | TIMESTAMPTZ | NULL | |
| created_at | TIMESTAMPTZ | NOT NULL, default now() | |
| updated_at | TIMESTAMPTZ | NOT NULL, default now() | |
| deleted_at | TIMESTAMPTZ | NULL | Soft delete |

#### patients (DATA-003)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| full_name | VARCHAR(255) | NOT NULL | **x-pii: true** |
| age | INTEGER | NOT NULL, CHECK (0–150) | |
| gender | VARCHAR(20) | NOT NULL | male, female, other, prefer_not_to_say |
| phone | VARCHAR(20) | NULL | **x-pii: true** |
| email | VARCHAR(254) | NULL | **x-pii: true** |
| address | TEXT | NULL | **x-pii: true** |
| emergency_contact_name | VARCHAR(255) | NULL | **x-pii: true** |
| emergency_contact_phone | VARCHAR(20) | NULL | **x-pii: true** |
| navigator_id | UUID | FK → users.id, NULL | Assigned navigator |
| status | VARCHAR(20) | NOT NULL, default 'active' | active, inactive, archived |
| notes | TEXT | NULL | |
| created_by | UUID | FK → users.id, NOT NULL | |
| created_at / updated_at / deleted_at | TIMESTAMPTZ | | |

**Indexes:** GIN trigram on `full_name` for fuzzy search; `idx_patients_status`; `idx_patients_navigator`

#### cases (DATA-004)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| patient_id | UUID | FK → patients.id, NOT NULL, CASCADE | |
| diagnosis | TEXT | NOT NULL | |
| status | VARCHAR(30) | NOT NULL, default 'new' | State machine (see below) |
| priority | VARCHAR(10) | NOT NULL, default 'medium' | low, medium, high, critical |
| notes | TEXT | NULL | |
| recommended_hospital_id | UUID | FK → hospitals.id, NULL | |
| applied_funding_id | UUID | FK → funding_programs.id, NULL | |
| assigned_clinician_id | UUID | FK → users.id, NULL | |
| created_by | UUID | FK → users.id, NOT NULL | |
| closed_at | TIMESTAMPTZ | NULL | |
| created_at / updated_at / deleted_at | TIMESTAMPTZ | | |

**Status state machine:**
```
new → under_review → hospital_selected → funding_applied → treatment_started → closed
 ↑         |                                                |
 +---------+------------------------------------------------+
 (can reopen: closed → under_review)
```

#### documents (DATA-005)

| Column | Type | Constraints | Notes |
|--------|------|-------------|-------|
| id | UUID | PK | |
| case_id | UUID | FK → cases.id, NOT NULL, CASCADE | |
| original_filename | VARCHAR(500) | NOT NULL | |
| stored_filename | VARCHAR(500) | NOT NULL | UUID-based, sanitized |
| file_type | VARCHAR(10) | NOT NULL | pdf, jpg, jpeg, png, docx |
| file_size_bytes | BIGINT | NOT NULL | Max 25MB |
| mime_type | VARCHAR(100) | NOT NULL | |
| ocr_text | TEXT | NULL | Extracted text |
| ocr_status | VARCHAR(20) | NOT NULL, default 'pending' | pending, processing, completed, failed |
| ocr_processed_at | TIMESTAMPTZ | NULL | |
| uploaded_by | UUID | FK → users.id, NOT NULL | |
| created_at / updated_at / deleted_at | TIMESTAMPTZ | | |

#### hospitals (DATA-006)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| name | VARCHAR(255) | NOT NULL |
| specialty | VARCHAR(255) | NULL (comma-separated) |
| city | VARCHAR(100) | NOT NULL |
| state | VARCHAR(100) | NULL |
| address | TEXT | NULL |
| phone / email / website | VARCHAR | NULL |
| cost_range_min / cost_range_max | DECIMAL(12,2) | NULL |
| has_financial_assistance | BOOLEAN | NOT NULL, default false |
| financial_assistance_details | TEXT | NULL |
| rating | DECIMAL(2,1) | NULL, CHECK 0–5 |
| is_active | BOOLEAN | NOT NULL, default true |
| created_at / updated_at | TIMESTAMPTZ | |

#### funding_programs (DATA-007)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| scheme_name | VARCHAR(255) | NOT NULL |
| description / eligibility_criteria / documents_required / application_process | TEXT | NULL |
| contact_person / contact_phone / contact_email / website | VARCHAR | NULL |
| max_amount | DECIMAL(12,2) | NULL |
| is_active | BOOLEAN | NOT NULL, default true |
| created_at / updated_at | TIMESTAMPTZ | |

#### followups (DATA-008)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| case_id | UUID | FK → cases.id, NOT NULL, CASCADE |
| patient_id | UUID | FK → patients.id, NOT NULL (denormalized) |
| type | VARCHAR(30) | NOT NULL: appointment, deadline, funding_status, treatment_progress |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NULL |
| due_date | DATE | NOT NULL |
| status | VARCHAR(20) | NOT NULL, default 'pending': pending, completed, overdue, cancelled |
| completed_at | TIMESTAMPTZ | NULL |
| created_by | UUID | FK → users.id, NOT NULL |
| created_at / updated_at | TIMESTAMPTZ | |

#### activities (DATA-009)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| patient_id | UUID | FK → patients.id, NOT NULL |
| user_id | UUID | FK → users.id, NOT NULL |
| action | VARCHAR(50) | NOT NULL |
| entity_type / entity_id | VARCHAR / UUID | NULL |
| description | TEXT | NOT NULL |
| metadata | JSONB | NULL |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |

#### timeline_events (DATA-010)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| case_id | UUID | FK → cases.id, NOT NULL, CASCADE |
| user_id | UUID | FK → users.id, NOT NULL |
| event_type | VARCHAR(50) | NOT NULL |
| title | VARCHAR(255) | NOT NULL |
| description | TEXT | NULL |
| old_value / new_value | TEXT | NULL (for status changes) |
| created_at | TIMESTAMPTZ | NOT NULL, default now() |

#### clinician_reviews (DATA-011)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| case_id | UUID | FK → cases.id, NOT NULL |
| clinician_id | UUID | FK → users.id, NOT NULL |
| review_type | VARCHAR(30) | NOT NULL: ai_summary_approval, recommendation, correction |
| content | TEXT | NOT NULL |
| status | VARCHAR(20) | NOT NULL, default 'pending' |
| reviewed_at | TIMESTAMPTZ | NULL |
| created_at / updated_at | TIMESTAMPTZ | |

#### knowledge_articles (DATA-012)

| Column | Type | Constraints |
|--------|------|-------------|
| id | UUID | PK |
| title | VARCHAR(500) | NOT NULL |
| content | TEXT | NOT NULL |
| category | VARCHAR(100) | NULL |
| tags | JSONB | NULL (string array) |
| language | VARCHAR(10) | NOT NULL, default 'en' (en, ta) |
| source | VARCHAR(255) | NULL |
| is_published | BOOLEAN | NOT NULL, default false |
| created_by | UUID | FK → users.id, NULL |
| created_at / updated_at | TIMESTAMPTZ | |

---

## 3. API Specs

### 3.1 API Endpoint Catalog

All endpoints under `/api/v1/`. Auth uses Bearer JWT. Errors use RFC 9457 Problem Details.

#### Auth (API-001 → API-005)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-001 | POST | /auth/register | Register new user | None |
| API-002 | POST | /auth/login | Authenticate | None |
| API-003 | POST | /auth/refresh | Refresh access token | Refresh token |
| API-004 | POST | /auth/logout | Invalidate refresh token | Bearer |
| API-005 | GET | /auth/me | Get current user profile | Bearer |

#### Patients (API-010 → API-014)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-010 | GET | /patients | List patients (paginated) | Bearer |
| API-011 | POST | /patients | Create patient | Bearer (navigator+) |
| API-012 | GET | /patients/{id} | Get patient by ID | Bearer |
| API-013 | PATCH | /patients/{id} | Update patient | Bearer (navigator+) |
| API-014 | DELETE | /patients/{id} | Archive (soft delete) | Bearer (navigator+) |

#### Cases (API-020 → API-026)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-020 | GET | /patients/{patientId}/cases | List cases for patient | Bearer |
| API-021 | POST | /patients/{patientId}/cases | Create case | Bearer (navigator+) |
| API-022 | GET | /cases/{id} | Get case detail | Bearer |
| API-023 | PATCH | /cases/{id} | Update case | Bearer (navigator+) |
| API-024 | PATCH | /cases/{id}/status | Transition status | Bearer (navigator+) |
| API-025 | GET | /cases | List all cases (filtered) | Bearer |
| API-026 | GET | /cases/{id}/timeline | Get timeline events | Bearer |

#### Documents (API-030 → API-037)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-030 | GET | /cases/{caseId}/documents | List documents | Bearer |
| API-031 | POST | /cases/{caseId}/documents/upload | Upload (multipart) | Bearer (navigator+) |
| API-032 | GET | /documents/{id} | Get metadata | Bearer |
| API-033 | GET | /documents/{id}/download | Download file | Bearer |
| API-034 | GET | /documents/{id}/preview | Preview (inline) | Bearer |
| API-035 | DELETE | /documents/{id} | Delete document | Bearer (navigator+) |
| API-036 | POST | /documents/{id}/ocr | Trigger OCR | Bearer (navigator+) |
| API-037 | GET | /documents/{id}/ocr | Get OCR result | Bearer |

#### Hospitals (API-040 → API-043)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-040 | GET | /hospitals | List hospitals | Bearer |
| API-041 | POST | /hospitals | Create hospital | Bearer (admin) |
| API-042 | GET | /hospitals/{id} | Get detail | Bearer |
| API-043 | PATCH | /hospitals/{id} | Update hospital | Bearer (admin) |

#### Funding (API-050 → API-053)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-050 | GET | /funding | List programs | Bearer |
| API-051 | POST | /funding | Create program | Bearer (admin) |
| API-052 | GET | /funding/{id} | Get detail | Bearer |
| API-053 | PATCH | /funding/{id} | Update program | Bearer (admin) |

#### Follow-Ups (API-060 → API-064)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-060 | GET | /cases/{caseId}/followups | List follow-ups | Bearer |
| API-061 | POST | /cases/{caseId}/followups | Create follow-up | Bearer (navigator+) |
| API-062 | GET | /followups/{id} | Get detail | Bearer |
| API-063 | PATCH | /followups/{id} | Update follow-up | Bearer (navigator+) |
| API-064 | GET | /followups/upcoming | List upcoming (all cases) | Bearer |

#### AI (API-070 → API-073)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-070 | POST | /ai/summarize | Generate medical summary | Bearer (navigator+) |
| API-071 | POST | /ai/explain | Plain-language explanation | Bearer |
| API-072 | POST | /ai/suggest-specialist | Suggest specialist type | Bearer (navigator+) |
| API-073 | POST | /ai/questions-for-doctor | Generate doctor questions | Bearer (navigator+) |

#### Clinician Reviews (API-080 → API-082)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-080 | GET | /cases/{caseId}/reviews | List reviews | Bearer |
| API-081 | POST | /cases/{caseId}/reviews | Create review | Bearer (clinician) |
| API-082 | PATCH | /reviews/{id} | Update review | Bearer (clinician) |

#### Reports (API-090 → API-091)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-090 | GET | /reports/dashboard | Dashboard stats | Bearer |
| API-091 | GET | /reports/case-summary/{caseId} | Case report | Bearer |

#### Admin (API-095 → API-098)

| API ID | Method | Path | Summary | Auth |
|--------|--------|------|---------|------|
| API-095 | GET | /admin/users | List users | Bearer (admin) |
| API-096 | PATCH | /admin/users/{id} | Update user | Bearer (admin) |
| API-097 | GET | /admin/audit-log | View audit log | Bearer (admin) |
| API-098 | GET | /health | Health check | None |

### 3.2 Key Request/Response Schemas

**POST /auth/login (API-002)**
```
Request:  { email, password }
Response: { access_token, refresh_token, token_type: "bearer", expires_in: 1800, user }
```

**POST /patients (API-011)**
```
Request:  { full_name, age, gender, phone?, email?, address?,
            emergency_contact_name?, emergency_contact_phone?, notes? }
Response: { id, full_name, age, gender, ..., status: "active", created_at }
```

**POST /ai/summarize (API-070)**
```
Request:  { case_id, document_ids[], prompt_override? }
Response: { summary_id, diagnosis_summary, plain_explanation, key_findings[],
            suggested_specialist, questions_for_doctor[], model_used,
            disclaimer: "This summary is for informational purposes only..." }
```

---

## 4. Feature Specs

### 4.1 FEAT-001: Authentication and RBAC

**Acceptance Criteria:**
- AC-1: User can register with email, password, full_name, and role (admin-only for role assignment)
- AC-2: User can login and receive JWT access (30min) + refresh (7d) tokens
- AC-3: Every API endpoint enforces role-based permissions from roles.permissions JSONB
- AC-4: All auth events recorded in audit log
- AC-5: Failed login attempts rate-limited (5 per 10 min)

**Key Scenarios:** happy-path login/register/refresh, invalid credentials, disabled account, expired token, duplicate email, RBAC enforcement, rate limiting, password hashing, JWT tampering

### 4.2 FEAT-002: Patient Management

**Acceptance Criteria:**
- AC-1: Navigator/Admin can create patients with required fields (full_name, age, gender)
- AC-2: Patient list supports pagination, sorting, and text search
- AC-3: Records can be updated and soft-deleted (archived)
- AC-4: RBAC restricts patient access by role
- AC-5: PII fields masked based on viewer role

### 4.3 FEAT-003: Case Management

**Acceptance Criteria:**
- AC-1: Navigator can create cases with diagnosis, priority, initial status "new"
- AC-2: Status transitions follow defined state machine with validation
- AC-3: All changes recorded in timeline_events
- AC-4: Multiple cases per patient supported
- AC-5: RBAC enforced

### 4.4 FEAT-004: Document Management

**Acceptance Criteria:**
- AC-1: Upload with type validation (PDF, JPG, PNG, DOCX) and size limit (25MB)
- AC-2: OCR extraction runs asynchronously, stores extracted text
- AC-3: Documents can be downloaded and previewed
- AC-4: File storage secure with sanitized filenames and validated content types

### 4.5 FEAT-005: AI Medical Summary

**Acceptance Criteria:**
- AC-1: AI summary generated from OCR text using Ollama
- AC-2: Summary includes diagnosis_summary, plain_explanation, key_findings, suggested_specialist, questions_for_doctor
- AC-3: Medical disclaimer always included; no diagnosis/prescription content generated
- AC-4: Clinician can review, approve, or request revision
- AC-5: Graceful degradation when Ollama unavailable

### 4.6 FEAT-006: Hospital Directory

**Acceptance Criteria:**
- AC-1: Hospitals listable, searchable, filterable by city/specialty/financial assistance
- AC-2: Only admins can create/update records
- AC-3: Hospital data includes cost range and financial assistance details

### 4.7 FEAT-007: Funding Directory

**Acceptance Criteria:**
- AC-1: Funding programs listable and searchable
- AC-2: Each shows eligibility, documents required, contact, website
- AC-3: Only admins can create/update programs

### 4.8 FEAT-008: Follow-Up Tracking

**Acceptance Criteria:**
- AC-1: Follow-ups creatable for cases with type, title, description, due date
- AC-2: Follow-ups can be marked completed
- AC-3: Upcoming view shows items across all active cases
- AC-4: Overdue follow-ups automatically detected

---

## 5. Test Strategy

### 5.1 Test Pyramid

```
                    /\
                   /  \
                  / E2E \          ~5% (10-15 Playwright tests)
                 /________\
                /          \
               /Integration\      ~25% (40-50 pytest+httpx tests)
              /______________\
             /                \
            /   Contract       \   ~15% (25-30 schemathesis tests)
           /____________________\
          /                      \
         /     Unit Tests         \ ~55% (80-100 pytest tests)
        /__________________________\
```

### 5.2 Test Coverage Targets

| Layer | Target | Tool |
|-------|--------|------|
| Unit test line coverage | 80% | pytest-cov |
| Integration: API endpoints | 100% | httpx AsyncClient |
| Contract: OpenAPI schemas | 100% | schemathesis |
| Spec scenario coverage | 100% Gherkin | sdd-coverage |
| E2E: critical paths | 100% | Playwright |

### 5.3 SDD Test Traceability

Every test carries `@spec` annotations linking to originating spec ID and scenario:

```python
# @spec FEAT-003
class TestCaseService:
    def test_status_transition(self):
        """@scenario FEAT-003-happy-path @tag @smoke"""
```

---

## 6. Implementation Roadmap

### Phase Overview

```
Phase 0: Project Setup          (Week 1)
Phase 1: Auth + RBAC            (Weeks 2-3)
Phase 2: Patients + Cases       (Weeks 4-5)
Phase 3: Documents + OCR        (Weeks 6-7)
Phase 4: AI Summaries           (Week 8)
Phase 5: Hospital + Funding     (Week 9)     ← parallel with 2-4
Phase 6: Follow-Up Tracking     (Week 10)
Phase 7: Dashboard + Polish     (Week 11)
Phase 8: Testing + Deployment   (Week 12)
```

### Dependency Graph

```
Phase 0 (Setup)
    │
    ▼
Phase 1 (Auth) ──────────► Phase 5 (Directories)
    │
    ▼
Phase 2 (Patients/Cases) ──► Phase 6 (Follow-Ups)
    │
    ▼
Phase 3 (Documents/OCR)
    │
    ▼
Phase 4 (AI Summaries)
    │
    ▼
Phase 7 (Dashboard) ◄── depends on all above
    │
    ▼
Phase 8 (Testing/Deploy)
```

### SDD Spec Creation Order

| Batch | Specs | Commands |
|-------|-------|----------|
| **Batch 1: Foundation** | DATA-001, DATA-002, FEAT-001 | `/sdd-schema`, `/sdd-spec` |
| **Batch 2: Core** | DATA-003, DATA-004, FEAT-002, FEAT-003 | |
| **Batch 3: Docs+AI** | DATA-005, DATA-011, FEAT-004, FEAT-005 | |
| **Batch 4: Directories** | DATA-006, DATA-007, DATA-008, FEAT-006, FEAT-007, FEAT-008 | |
| **Batch 5: Supporting** | DATA-009, DATA-010, DATA-012, openapi.yaml | |

---

## 7. Security Considerations

### Authentication Security
- **Passwords:** bcrypt, cost factor 12, never logged or exposed
- **JWT:** HS256, 256-bit secret from env var. Access: 30min, Refresh: 7d with rotation
- **Rate limiting:** 5 failed attempts per 10min → 429 with Retry-After
- **Token revocation:** Detected refresh reuse → invalidate all user tokens

### RBAC Enforcement
- Middleware loads role permissions per request
- Route-level: `@require_permission("patients", "write")`
- Resource scoping: patient role → own records only

### PII Handling
- Fields marked `x-pii: true` in schemas
- Application-level encryption (Fernet) at rest
- API response filtering by role
- Audit logs record access, not PII values

### Input Validation
- SQLAlchemy ORM (parameterized queries, no raw SQL)
- File uploads: magic byte validation, 25MB limit, UUID filenames
- AI prompt injection: delimited sections, output filtering

### Audit Logging
- INSERT-only activities table
- Structured JSON: timestamp, user_id, action, entity, IP, user_agent, changes

---

## 8. Infrastructure and Deployment

### Development (Docker Compose)
- PostgreSQL 16 Alpine
- Ollama (with qwen3, gemma models)
- ChromaDB (for V2)

### Production (Ubuntu 24.04)
- **Nginx:** Reverse proxy, TLS (Let's Encrypt), static files, rate limiting, security headers
- **Systemd:** uvicorn with 4 workers
- **PostgreSQL 16:** Dedicated user, SSL connections
- **Ollama:** systemd service, models pre-pulled
- **Backups:** Daily pg_dump (30-day retention), weekly restore verification

### CI/CD Pipeline
1. Spec gate (lint + validate)
2. Backend build + lint (ruff, mypy)
3. Unit tests (80% coverage gate)
4. Integration tests (PostgreSQL Docker)
5. Contract tests (schemathesis)
6. Frontend build + lint + tests
7. Security scan (pip audit, npm audit)
8. Spec status promotion

---

## Next Steps

1. **Create specs:** Run `/sdd-spec` for each FEAT-001 through FEAT-008
2. **Create schemas:** Run `/sdd-schema` for each DATA-001 through DATA-012
3. **Validate:** Run `/sdd-validate` on all specs
4. **Scaffold tests:** Run `/sdd-scaffold` for each feature
5. **Implement Phase 0:** Project scaffold, Docker Compose, CI pipeline
6. **Begin Phase 1:** Auth + RBAC (foundational dependency)
