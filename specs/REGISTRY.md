# Spec Registry

> **This file is the authoritative traceability matrix for the Patient Navigator Platform.**
> CI validates that every `APPROVED` spec has at least one mapped test, and that every test
> references a valid `spec_id` from this registry.
>
> Update this file whenever a spec is created, promoted, or deprecated.

---

## Feature Specs

| ID | Title | Status | Version | Owner | Tests |
|----|-------|--------|---------|-------|-------|
| FEAT-001 | Authentication and RBAC | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_auth_rbac.py` |
| FEAT-002 | Patient Management | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_patient_management.py` |
| FEAT-003 | Case Management | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_case_management.py` |
| FEAT-004 | Document Management | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_document_management.py` |
| FEAT-005 | AI Medical Summary | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_ai_medical_summary.py` |
| FEAT-006 | Hospital Directory | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_hospital_directory.py` |
| FEAT-007 | Funding Directory | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_funding_directory.py` |
| FEAT-008 | Follow-Up Tracking | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_follow_up_tracking.py` |
| FEAT-009 | Settings & Data Import | DRAFT | 1.0.0 | @platform | `backend/tests/integration/test_admin_settings.py`, `backend/tests/unit/test_scraper_service.py` |

---

## API Specs

| ID | Endpoint / Operation | Status | Version | Feature Ref | Tests |
|----|---------------------|--------|---------|-------------|-------|
| API-001 | `POST /auth/register` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-002 | `POST /auth/login` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-003 | `POST /auth/refresh` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-004 | `POST /auth/logout` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-005 | `GET /auth/me` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-010 | `GET /patients` | DRAFT | 1.0.0 | FEAT-002 | `backend/tests/integration/test_patient_management.py` |
| API-011 | `POST /patients` | DRAFT | 1.0.0 | FEAT-002 | `backend/tests/integration/test_patient_management.py` |
| API-012 | `GET /patients/{id}` | DRAFT | 1.0.0 | FEAT-002 | `backend/tests/integration/test_patient_management.py` |
| API-013 | `PATCH /patients/{id}` | DRAFT | 1.0.0 | FEAT-002 | `backend/tests/integration/test_patient_management.py` |
| API-014 | `DELETE /patients/{id}` | DRAFT | 1.0.0 | FEAT-002 | `backend/tests/integration/test_patient_management.py` |
| API-020 | `GET /patients/{patientId}/cases` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-021 | `POST /patients/{patientId}/cases` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-022 | `GET /cases/{id}` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-023 | `PATCH /cases/{id}` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-024 | `PATCH /cases/{id}/status` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-025 | `GET /cases` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-026 | `GET /cases/{id}/timeline` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_case_management.py` |
| API-030 | `GET /cases/{caseId}/documents` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-031 | `POST /cases/{caseId}/documents/upload` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-032 | `GET /documents/{id}` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-033 | `GET /documents/{id}/download` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-034 | `GET /documents/{id}/preview` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-035 | `DELETE /documents/{id}` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-036 | `POST /documents/{id}/ocr` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-037 | `GET /documents/{id}/ocr` | DRAFT | 1.0.0 | FEAT-004 | `backend/tests/integration/test_document_management.py` |
| API-040 | `GET /hospitals` | DRAFT | 1.0.0 | FEAT-006 | `backend/tests/integration/test_hospital_directory.py` |
| API-041 | `POST /hospitals` | DRAFT | 1.0.0 | FEAT-006 | `backend/tests/integration/test_hospital_directory.py` |
| API-042 | `GET /hospitals/{id}` | DRAFT | 1.0.0 | FEAT-006 | `backend/tests/integration/test_hospital_directory.py` |
| API-043 | `PATCH /hospitals/{id}` | DRAFT | 1.0.0 | FEAT-006 | `backend/tests/integration/test_hospital_directory.py` |
| API-050 | `GET /funding` | DRAFT | 1.0.0 | FEAT-007 | `backend/tests/integration/test_funding_directory.py` |
| API-051 | `POST /funding` | DRAFT | 1.0.0 | FEAT-007 | `backend/tests/integration/test_funding_directory.py` |
| API-052 | `GET /funding/{id}` | DRAFT | 1.0.0 | FEAT-007 | `backend/tests/integration/test_funding_directory.py` |
| API-053 | `PATCH /funding/{id}` | DRAFT | 1.0.0 | FEAT-007 | `backend/tests/integration/test_funding_directory.py` |
| API-060 | `GET /cases/{caseId}/followups` | DRAFT | 1.0.0 | FEAT-008 | `backend/tests/integration/test_follow_up_tracking.py` |
| API-061 | `POST /cases/{caseId}/followups` | DRAFT | 1.0.0 | FEAT-008 | `backend/tests/integration/test_follow_up_tracking.py` |
| API-062 | `GET /followups/{id}` | DRAFT | 1.0.0 | FEAT-008 | `backend/tests/integration/test_follow_up_tracking.py` |
| API-063 | `PATCH /followups/{id}` | DRAFT | 1.0.0 | FEAT-008 | `backend/tests/integration/test_follow_up_tracking.py` |
| API-064 | `GET /followups/upcoming` | DRAFT | 1.0.0 | FEAT-008 | `backend/tests/integration/test_follow_up_tracking.py` |
| API-070 | `POST /ai/summarize` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-071 | `POST /ai/explain` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-072 | `POST /ai/suggest-specialist` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-073 | `POST /ai/questions-for-doctor` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-080 | `GET /cases/{caseId}/reviews` | DRAFT | 1.0.0 | FEAT-003 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-081 | `POST /cases/{caseId}/reviews` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-082 | `PATCH /reviews/{id}` | DRAFT | 1.0.0 | FEAT-005 | `backend/tests/integration/test_ai_medical_summary.py` |
| API-090 | `GET /reports/dashboard` | DRAFT | 1.0.0 | FEAT-002/003 | — |
| API-091 | `GET /reports/case-summary/{caseId}` | DRAFT | 1.0.0 | FEAT-003 | — |
| API-095 | `GET /admin/users` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-096 | `PATCH /admin/users/{id}` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py` |
| API-097 | `GET /admin/audit-log` | DRAFT | 1.0.0 | FEAT-001 | `backend/tests/integration/test_auth_rbac.py`, `backend/tests/integration/test_admin_settings.py` |
| API-098 | `GET /health` | DRAFT | 1.0.0 | — | — |
| API-100 | `GET /admin/settings` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-101 | `PUT /admin/settings` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-102 | `GET /admin/settings/health` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-103 | `POST /admin/scrape/hospitals` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-104 | `POST /admin/import/hospitals` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-105 | `POST /admin/import/hospitals/csv` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |
| API-106 | `POST /admin/import/ngos/csv` | DRAFT | 1.0.0 | FEAT-009 | `backend/tests/integration/test_admin_settings.py` |

---

## Data Schema Specs

| ID | Schema | Status | Version | API Refs | Tests |
|----|--------|--------|---------|----------|-------|
| DATA-001 | `Role` | DRAFT | 1.0.0 | API-001..005 | `backend/tests/unit/schemas/Role_test.py` |
| DATA-002 | `User` | DRAFT | 1.0.0 | API-001..005, API-095..096 | `backend/tests/unit/schemas/User_test.py` |
| DATA-003 | `Patient` | DRAFT | 1.0.0 | API-010..014 | `backend/tests/unit/schemas/Patient_test.py` |
| DATA-004 | `Case` | DRAFT | 1.0.0 | API-020..026 | `backend/tests/unit/schemas/Case_test.py` |
| DATA-005 | `Document` | DRAFT | 1.0.0 | API-030..037 | `backend/tests/unit/schemas/Document_test.py` |
| DATA-006 | `Hospital` | DRAFT | 1.0.0 | API-040..043 | `backend/tests/unit/schemas/Hospital_test.py` |
| DATA-007 | `FundingProgram` | DRAFT | 1.0.0 | API-050..053 | `backend/tests/unit/schemas/FundingProgram_test.py` |
| DATA-008 | `FollowUp` | DRAFT | 1.0.0 | API-060..064 | `backend/tests/unit/schemas/FollowUp_test.py` |
| DATA-009 | `Activity` | DRAFT | 1.0.0 | — | `backend/tests/unit/schemas/Activity_test.py` |
| DATA-010 | `TimelineEvent` | DRAFT | 1.0.0 | API-026 | `backend/tests/unit/schemas/TimelineEvent_test.py` |
| DATA-011 | `ClinicianReview` | DRAFT | 1.0.0 | API-080..082 | `backend/tests/unit/schemas/ClinicianReview_test.py` |
| DATA-012 | `KnowledgeArticle` | DRAFT | 1.0.0 | — | `backend/tests/unit/schemas/KnowledgeArticle_test.py` |

---

## Architecture Decision Records

| ID | Title | Status | Date |
|----|-------|--------|------|
| ADR-001 | Monolith over microservices | PROPOSED | 2026-06-04 |
| ADR-002 | React SPA over HTMX | PROPOSED | 2026-06-04 |
| ADR-003 | PostgreSQL for all environments | PROPOSED | 2026-06-04 |
| ADR-004 | JWT with refresh tokens | PROPOSED | 2026-06-04 |
| ADR-005 | Ollama local inference | PROPOSED | 2026-06-04 |
| ADR-006 | Filesystem storage for documents | PROPOSED | 2026-06-04 |
| ADR-007 | PaddleOCR over Tesseract | PROPOSED | 2026-06-04 |

---

## Coverage Report

> Auto-generated by spec coverage tool. Do not edit manually.

```
Last updated: 2026-06-05

Feature Specs:  9/9 (FEAT-001..009)
API Specs:      57/59 mapped to tests (API-090, API-091 pending)
Data Schemas:   12/12 test scaffolds generated (84 tests, scaffolded)
ADRs:           N/A (human-reviewed)

Total tests: 338 (29 unit scraper + 22 admin integration + 287 existing integration)
Overall spec coverage: FEAT-009 passing, others scaffolded
```

---

## Implementation Phase Mapping

| Phase | Specs | Duration | Dependencies |
|-------|-------|----------|-------------|
| Phase 0: Setup | All DATA, ADR-001..007 | Week 1 | None |
| Phase 1: Auth+RBAC | FEAT-001, API-001..005, DATA-001/002 | Weeks 2-3 | Phase 0 |
| Phase 2: Patients+Cases | FEAT-002/003, API-010..026, DATA-003/004/009/010 | Weeks 4-5 | Phase 1 |
| Phase 3: Documents+OCR | FEAT-004, API-030..037, DATA-005 | Weeks 6-7 | Phase 2 |
| Phase 4: AI Summaries | FEAT-005, API-070..082, DATA-011 | Week 8 | Phase 3 |
| Phase 5: Directories | FEAT-006/007, API-040..053, DATA-006/007 | Week 9 | Phase 1 |
| Phase 6: Follow-Ups | FEAT-008, API-060..064, DATA-008 | Week 10 | Phase 2 |
| Phase 7: Dashboard | API-090..091 | Week 11 | All above |
| Phase 8: Deploy | — | Week 12 | All above |

---

## How to Add a New Spec

1. Copy the appropriate template from `specs/*/`
2. Assign the next available ID in the relevant category above
3. Add a row to this registry with `status: DRAFT`
4. Open a PR — CI will block merge until status is `APPROVED`
5. After implementation, CI automatically sets `status: IMPLEMENTED` and links tests
