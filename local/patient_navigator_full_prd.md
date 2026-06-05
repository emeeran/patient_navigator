# Patient Navigator Full PRD

## Master Consolidated Specification

This document consolidates the planning conversation for the Patient Navigator Platform.

### Vision
Help patients:
- Understand medical conditions
- Find treatment facilities
- Access financial assistance
- Coordinate care

## Operating Model
Roles:
- Program Director
- Medical Advisory Board
- Patient Navigators
- Medical Review Team
- Financial Assistance Team
- Volunteers
- NGO Partners

Workflow:
1. Registration
2. Document Collection
3. AI Analysis
4. Clinician Review
5. Hospital Matching
6. Funding Matching
7. Treatment Coordination
8. Follow-up

## Version 1
- FastAPI
- SQLite
- HTMX/Jinja2
- Ollama
- OCR
- Patient Management
- Case Management
- Document Upload
- AI Summaries

## Version 2
- ChromaDB
- RAG Search
- Tamil Support
- Hospital Recommendation Engine
- Funding Recommendation Engine
- PDF Reports

## Version 3
- Clinician Portal
- Volunteer Portal
- NGO Portal
- AI Case Navigator
- Timeline Tracking
- Analytics

## Final Chosen Architecture
Frontend:
- React
- TypeScript
- Tailwind

Backend:
- FastAPI
- SQLAlchemy
- Alembic

Database:
- PostgreSQL

AI:
- Ollama
- Qwen3
- Gemma

Vector Search:
- ChromaDB

OCR:
- PaddleOCR

## Core Modules
- Authentication
- RBAC
- Patients
- Cases
- Documents
- Hospitals
- Funding
- Followups
- AI Assistant

## Database Tables
users
roles
patients
cases
documents
hospitals
funding_programs
followups
activities
timeline_events
clinician_reviews
knowledge_articles

## API Groups
/auth
/patients
/cases
/documents
/hospitals
/funding
/followups
/ai
/reports

## Development Roadmap
Sprint 1: Auth + RBAC
Sprint 2: Patients + Cases
Sprint 3: Documents + OCR
Sprint 4: AI Summaries
Sprint 5: Hospital + Funding
Sprint 6: RAG
Sprint 7: Portals
Sprint 8: Testing + Deployment

## Success Metrics
- Patients Served
- Cases Closed
- Funding Secured
- Referral Success
- Satisfaction Score
