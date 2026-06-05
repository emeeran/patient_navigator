# Patient Navigator Platform
# Product Requirements Document (PRD)

Version: 1.0
Status: Draft
Owner: Meeran

---

# 1. Executive Summary

Patient Navigator is a lightweight AI-assisted platform designed to help patients:

- Understand medical conditions
- Organize medical records
- Identify suitable hospitals
- Locate funding opportunities
- Coordinate treatment journeys
- Collaborate with clinicians, volunteers, and NGOs

The system is designed to operate primarily using free and open-source technologies.

---

# 2. Vision

Provide every patient with access to understandable medical information, treatment guidance pathways, and financial assistance navigation regardless of technical or healthcare literacy.

---

# 3. Objectives

## Business Objectives

- Improve patient outcomes
- Reduce confusion after diagnosis
- Accelerate treatment initiation
- Increase access to funding programs
- Build a scalable care-navigation ecosystem

## User Objectives

- Upload medical records
- Receive plain-language explanations
- Find treatment centers
- Track treatment progress
- Manage funding applications

---

# 4. Stakeholders

## Primary

- Patients
- Family Members
- Patient Navigators

## Secondary

- Doctors
- Nurses
- Social Workers
- NGOs
- Funding Organizations

## Administrative

- System Administrators
- Program Directors

---

# 5. User Roles

## Administrator

Permissions:
- Full system access
- User management
- Configuration management

## Navigator

Permissions:
- Create patients
- Manage cases
- Upload documents
- Track funding

## Clinician

Permissions:
- Review AI summaries
- Approve content
- Add recommendations

## Volunteer

Permissions:
- View assigned cases
- Update activities

## Patient

Permissions:
- View own records
- Download summaries

---

# 6. Functional Requirements

## FR-001 Patient Management

Features:

- Create patient
- Edit patient
- Search patient
- Archive patient

Fields:

- Name
- Age
- Gender
- Phone
- Email
- Address
- Emergency Contact

---

## FR-002 Case Management

Each patient may have multiple cases.

Fields:

- Diagnosis
- Status
- Notes
- Priority

Statuses:

- New
- Under Review
- Hospital Selected
- Funding Applied
- Treatment Started
- Closed

---

## FR-003 Document Management

Supported:

- PDF
- JPG
- PNG
- DOCX

Functions:

- Upload
- Download
- Preview
- OCR Extraction

---

## FR-004 AI Medical Summary

Generate:

- Diagnosis summary
- Plain-language explanation
- Key findings
- Suggested specialist
- Questions for doctor

Restrictions:

- No diagnosis generation
- No prescriptions
- No treatment decisions

---

## FR-005 Hospital Directory

Maintain:

- Hospital Name
- Specialty
- Location
- Contact Information
- Cost Range
- Financial Assistance Availability

---

## FR-006 Funding Directory

Maintain:

- Scheme Name
- Eligibility
- Documents Required
- Contact Information
- Website

---

## FR-007 Follow-Up Tracking

Track:

- Appointments
- Deadlines
- Funding Status
- Treatment Progress

---

# 7. Version Roadmap

## Version 1

### Core Features

- Authentication
- Patient Records
- Case Management
- Document Upload
- AI Summaries
- Hospital Directory
- Funding Directory
- Follow-Ups

---

## Version 2

### Enhancements

- ChromaDB RAG
- Tamil Support
- Hospital Recommendation Engine
- Funding Recommendation Engine
- PDF Case Reports
- Knowledge Library

---

## Version 3

### Advanced Features

- Clinician Portal
- Volunteer Portal
- NGO Portal
- Treatment Timeline
- AI Case Navigator
- Document Intelligence
- Analytics Dashboard

---

# 8. Non-Functional Requirements

## Performance

- Page load < 2 seconds
- AI summary < 30 seconds

## Reliability

- Daily backups
- Data validation

## Security

- Password hashing
- Role-based access
- Audit logging

## Scalability

Initial:
- 1,000 patients

Target:
- 50,000 patients

---

# 9. AI Architecture

## LLM

Ollama

Models:

- Qwen
- Gemma
- Phi

Tasks:

- Summarization
- Translation
- Report explanation

---

## OCR

PaddleOCR

Tasks:

- Scan extraction
- Prescription extraction

---

## Vector Search

ChromaDB

Tasks:

- Document search
- Knowledge retrieval

---

# 10. Database Design

## Tables

patients
cases
documents
users
roles
hospitals
funding_programs
followups
activities
timeline_events
clinician_reviews
knowledge_articles

---

# 11. API Design

## Authentication

POST /login

POST /logout

POST /register

---

## Patients

GET /patients

POST /patients

PUT /patients/{id}

DELETE /patients/{id}

---

## Cases

GET /cases

POST /cases

PUT /cases/{id}

---

## Documents

POST /documents/upload

GET /documents/{id}

DELETE /documents/{id}

---

## AI

POST /ai/summarize

POST /ai/explain

POST /ai/translate

---

# 12. UI Pages

## Dashboard

Widgets:

- Active Patients
- Open Cases
- Follow-Ups
- Funding Requests

## Patients

- Search
- Create
- Edit

## Cases

- Overview
- Notes
- Documents

## Hospitals

- Directory
- Search

## Funding

- Programs
- Eligibility

## Reports

- Export PDF

---

# 13. Security Model

Authentication:

- Username/Password

Future:

- Magic Links
- OTP

Authorization:

- RBAC

Logging:

- Login Logs
- Activity Logs
- Audit Trails

---

# 14. Deployment

## Development

Ubuntu 24.04

FastAPI

SQLite

Ollama

---

## Production

FastAPI

PostgreSQL

Nginx

Systemd

---

# 15. MVP Development Plan

Phase 1:
- Database
- Authentication

Phase 2:
- Patient Module

Phase 3:
- Document Module

Phase 4:
- AI Integration

Phase 5:
- Hospital & Funding

Phase 6:
- Testing

Phase 7:
- Pilot Launch

---

# 16. Success Metrics

Operational

- Patients onboarded
- Cases managed

Clinical

- Treatment initiation rate

Financial

- Aid secured

User Satisfaction

- Patient satisfaction score

---

# 17. Future Versions

Version 4:
- Mobile responsive PWA
- WhatsApp notifications
- Advanced analytics

Version 5:
- Telemedicine integrations
- Insurance integrations
- Regional expansion

---

End of PRD
