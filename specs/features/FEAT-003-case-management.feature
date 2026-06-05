---
id: FEAT-003
title: "Case Management"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-004
  - DATA-010
  - API-020
  - API-021
  - API-022
  - API-023
  - API-024
  - API-025
  - API-026
  - API-080
  - API-091
  - FEAT-001
  - FEAT-002
supersedes: null
tags:
  - cases
  - state-machine
  - timeline
  - workflow
---

# Feature: Case Management

  As a navigator or admin,
  I want to create and manage patient cases with status transitions and a full timeline,
  So that each patient's care journey is tracked from diagnosis through treatment to closure.

  ## Scope

  ### In scope
  - Create case with diagnosis, priority, initial status "new"
  - List cases per patient and across all patients (filtered)
  - View case detail with all fields and current status
  - Update case fields (diagnosis, priority, notes, hospital, funding, clinician)
  - Status transitions following defined state machine
  - Timeline events recorded for every case mutation
  - Multiple cases per patient supported
  - RBAC enforced on all case operations
  - Case status transition validation (reject invalid transitions)

  ### Out of scope
  - Case templates or cloning
  - Bulk case operations
  - Case merging
  - Automated status transitions based on external events
  - Case assignment workflows (manual in V1)

  ## Glossary

  | Term | Definition |
  |------|------------|
  | Case | A care coordination record linking a patient to a diagnosis, hospital, and funding |
  | State Machine | Validated status transitions: new → under_review → hospital_selected → funding_applied → treatment_started → closed |
  | Timeline Event | An INSERT-only audit record of every change made to a case |
  | Priority | Case urgency level: low, medium, high, critical |
  | Reopen | Transition from "closed" back to "under_review" |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | cases |
      | admin     | full  |
      | navigator | full  |
      | clinician | read  |
      | volunteer | read  |
      | patient   | own   |
    And the following users exist:
      | email              | role      | state  |
      | admin@test.com     | admin     | active |
      | nav@test.com       | navigator | active |
      | clin@test.com      | clinician | active |
      | vol@test.com       | volunteer | active |
      | patient1@test.com  | patient   | active |
    And the following patients exist:
      | id    | full_name    |
      | p-001 | Aarav Mehta  |
      | p-002 | Priya Sharma |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-003-h1
  Scenario: Navigator creates a new case for a patient
    Given an authenticated user with role "navigator"
    And patient "p-001" exists
    When they submit POST /patients/p-001/cases with:
      | field     | value                  |
      | diagnosis | Stage 2B Oral Cancer   |
      | priority  | high                   |
      | notes     | Biopsy confirmed       |
    Then a new case is created with status "new"
    And the response status is 201
    And the response contains: id, patient_id "p-001", diagnosis, priority "high", status "new"
    And created_by is set to the navigator's user ID
    And a timeline event is recorded with event_type "case.created"

  @happy-path @smoke @FEAT-003-h2
  Scenario: List cases for a specific patient
    Given patient "p-001" has 3 cases
    And an authenticated user with role "navigator"
    When they submit GET /patients/p-001/cases
    Then the response status is 200
    And the response contains exactly 3 cases for patient "p-001"
    And each case includes: id, diagnosis, status, priority, created_at

  @happy-path @FEAT-003-h3
  Scenario: Get case detail by ID
    Given a case exists with id "c-001" for patient "p-001"
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001
    Then the response status is 200
    And the response contains all case fields: id, patient_id, diagnosis, status, priority, notes, recommended_hospital_id, applied_funding_id, assigned_clinician_id, created_by, closed_at, created_at, updated_at

  @happy-path @FEAT-003-h4
  Scenario: Transition case status from "new" to "under_review"
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with:
      | field  | value        |
      | status | under_review |
    Then the response status is 200
    And the case status is updated to "under_review"
    And a timeline event is recorded with event_type "case.status_changed", old_value "new", new_value "under_review"

  @happy-path @FEAT-003-h5
  Scenario: Full status lifecycle from "new" to "closed"
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When the navigator transitions: new → under_review → hospital_selected → funding_applied → treatment_started → closed
    Then each transition succeeds with status 200
    And 5 timeline events are recorded (one per transition)
    And closed_at is set when status becomes "closed"

  @happy-path @FEAT-003-h6
  Scenario: Reopen a closed case
    Given a case exists with id "c-001" and status "closed"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with:
      | field  | value        |
      | status | under_review |
    Then the response status is 200
    And the case status is updated to "under_review"
    And closed_at is cleared (set to null)
    And a timeline event is recorded with event_type "case.reopened"

  @happy-path @FEAT-003-h7
  Scenario: Update case fields (diagnosis, priority, notes)
    Given a case exists with id "c-001"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001 with:
      | field     | value                    |
      | priority  | critical                 |
      | notes     | Updated: MRI shows spread |
    Then the response status is 200
    And priority is updated to "critical"
    And notes are updated to "Updated: MRI shows spread"
    And a timeline event is recorded with event_type "case.updated"

  @happy-path @FEAT-003-h8
  Scenario: List all cases across patients with filters
    Given 10 cases exist across 5 patients with various statuses and priorities
    And an authenticated user with role "admin"
    When they submit GET /cases?status=under_review&priority=high
    Then the response status is 200
    And all returned cases have status "under_review" and priority "high"
    And the response includes pagination metadata

  @happy-path @FEAT-003-h9
  Scenario: Get case timeline events
    Given a case exists with id "c-001" and 5 timeline events
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/timeline
    Then the response status is 200
    And the response contains 5 timeline events in chronological order (oldest first)
    And each event includes: id, event_type, title, description, old_value, new_value, user_id, created_at

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-003-ec1
  Scenario: Create multiple cases for same patient
    Given patient "p-001" already has 1 active case
    And an authenticated user with role "navigator"
    When they submit POST /patients/p-001/cases with a different diagnosis
    Then the response status is 201
    And patient "p-001" now has 2 active cases

  @edge-case @FEAT-003-ec2
  Scenario: Assign recommended hospital to case
    Given a case exists with id "c-001" and status "under_review"
    And a hospital exists with id "h-001"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001 with:
      | field                    | value |
      | recommended_hospital_id  | h-001 |
    Then the response status is 200
    And recommended_hospital_id is set to "h-001"

  @edge-case @FEAT-003-ec3
  Scenario: Case with null optional fields
    Given an authenticated user with role "navigator"
    When they submit POST /patients/p-001/cases with only required fields:
      | field     | value        |
      | diagnosis | Basic Case   |
      | priority  | medium       |
    Then the response status is 201
    And optional fields (notes, recommended_hospital_id, applied_funding_id, assigned_clinician_id) are null

  @edge-case @FEAT-003-ec4
  Scenario: Timeline event records old and new values on status change
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with status "under_review"
    Then the timeline event has:
      | field      | value        |
      | event_type | case.status_changed |
      | old_value  | new          |
      | new_value  | under_review |

  @edge-case @FEAT-003-ec5
  Scenario: Priority can be changed at any status
    Given a case exists with id "c-001" and status "treatment_started" and priority "medium"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001 with:
      | field    | value   |
      | priority | critical |
    Then the response status is 200
    And priority is updated to "critical"
    And status remains "treatment_started" (priority change does not affect status)

  @edge-case @FEAT-003-ec6
  Scenario: Patient views their own cases only
    Given patient user "patient1@test.com" owns patient record "p-001"
    And patient "p-001" has 2 cases
    And patient "p-002" has 1 case
    When the patient submits GET /patients/p-001/cases
    Then the response status is 200
    And the response contains exactly 2 cases (own patient's cases)
    When the patient submits GET /patients/p-002/cases
    Then the response status is 403

  @edge-case @FEAT-003-ec7
  Scenario: Case list pagination with large dataset
    Given 50 cases exist for patient "p-001"
    And an authenticated user with role "navigator"
    When they submit GET /patients/p-001/cases?page=2&per_page=20
    Then the response status is 200
    And the response contains exactly 20 cases
    And pagination metadata shows total=50, page=2, per_page=20

  @edge-case @FEAT-003-ec8
  Scenario: Sort cases by priority then by created_at
    Given cases exist with various priorities and dates
    And an authenticated user with role "navigator"
    When they submit GET /cases?sort=-priority,-created_at
    Then the response status is 200
    And cases are sorted by priority descending (critical first), then by created_at descending

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-003-e1
  Scenario: Invalid status transition (new → closed)
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with:
      | field  | value  |
      | status | closed |
    Then the response status is 422
    And the error message indicates "Invalid transition: new → closed. Valid transitions from 'new': [under_review]"

  @error-case-case @FEAT-003-e2
  Scenario: Invalid status transition (under_review → treatment_started)
    Given a case exists with id "c-001" and status "under_review"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with:
      | field  | value             |
      | status | treatment_started |
    Then the response status is 422
    And the error message indicates "Invalid transition: under_review → treatment_started"

  @error-case-case @FEAT-003-e3
  Scenario: Create case for non-existent patient
    Given an authenticated user with role "navigator"
    When they submit POST /patients/00000000-0000-0000-0000-000000000000/cases with:
      | field     | value        |
      | diagnosis | Test         |
      | priority  | low          |
    Then the response status is 404
    And the error message indicates patient not found

  @error-case-case @FEAT-003-e4
  Scenario: Create case with missing required diagnosis
    Given an authenticated user with role "navigator"
    When they submit POST /patients/p-001/cases with:
      | field    | value   |
      | priority | medium  |
    Then the response status is 422
    And the error message indicates "diagnosis" is required

  @error-case-case @FEAT-003-e5
  Scenario: Invalid priority value
    Given an authenticated user with role "navigator"
    When they submit POST /patients/p-001/cases with:
      | field     | value      |
      | diagnosis | Test       |
      | priority  | super-high |
    Then the response status is 422
    And the error message indicates priority must be one of: low, medium, high, critical

  @error-case-case @FEAT-003-e6
  Scenario: Get non-existent case
    Given an authenticated user with role "navigator"
    When they submit GET /cases/00000000-0000-0000-0000-000000000000
    Then the response status is 404

  @error-case-case @FEAT-003-e7
  Scenario: Update case with invalid hospital reference
    Given a case exists with id "c-001"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001 with:
      | field                   | value                                  |
      | recommended_hospital_id | 00000000-0000-0000-0000-000000000000   |
    Then the response status is 422
    And the error message indicates hospital not found (FK constraint violation)

  @error-case-case @FEAT-003-e8
  Scenario: Transition with invalid status value
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with:
      | field  | value        |
      | status | non_existent |
    Then the response status is 422
    And the error message indicates status must be one of: new, under_review, hospital_selected, funding_applied, treatment_started, closed

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-003-s1
  Scenario: Volunteer cannot create cases
    Given an authenticated user with role "volunteer"
    When they submit POST /patients/p-001/cases with valid data
    Then the response status is 403
    And an audit event is recorded with action "case.create_denied"

  @security @FEAT-003-s2
  Scenario: Volunteer cannot transition case status
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "volunteer"
    When they submit PATCH /cases/c-001/status with status "under_review"
    Then the response status is 403

  @security @FEAT-003-s3
  Scenario: Unauthenticated user cannot access cases
    Given no authentication token is provided
    When they submit GET /cases
    Then the response status is 401

  @security @FEAT-003-s4
  Scenario: Timeline events are tamper-proof (INSERT-only)
    Given timeline events exist for case "c-001"
    When any user attempts to UPDATE a timeline_event record
    Then the database rejects the operation
    And existing timeline events remain intact

  @security @FEAT-003-s5
  Scenario: Clinician cannot modify case (read-only)
    Given a case exists with id "c-001"
    And an authenticated user with role "clinician"
    When they submit PATCH /cases/c-001 with:
      | field    | value              |
      | priority | high               |
    Then the response status is 403
    And an audit event is recorded with action "case.update_denied"

  @security @FEAT-003-s6
  Scenario: Case status transition with audit trail
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator" with user_id "u-nav"
    When they transition status to "under_review"
    Then a timeline event is recorded with:
      | field      | value              |
      | event_type | case.status_changed |
      | user_id    | u-nav              |
      | old_value  | new                |
      | new_value  | under_review       |

  @security @FEAT-003-s7
  Scenario: SQL injection in diagnosis field
    Given an authenticated user with role "navigator"
    When they submit POST /patients/p-001/cases with:
      | field     | value                      |
      | diagnosis | '; DROP TABLE cases; --     |
      | priority  | low                         |
    Then the response status is 201
    And the diagnosis is stored as literal text
    And the cases table remains intact

  @security @FEAT-003-s8
  Scenario: Patient cannot view other patient's cases
    Given patient user "patient1@test.com" owns patient record "p-001"
    And patient "p-002" has a case "c-002"
    When the patient submits GET /cases/c-002
    Then the response status is 403

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-003-p1
  Scenario: Case list query under 200ms with 5,000 cases
    Given 5,000 case records exist across 2,000 patients
    And an authenticated user with role "navigator"
    When they submit GET /cases?status=under_review
    Then the response time is under 200ms at the 95th percentile
    And the query uses the idx_cases_status index

  @performance @FEAT-003-p2
  Scenario: Status transition under 150ms
    Given a case exists with id "c-001" and status "new"
    And an authenticated user with role "navigator"
    When they submit PATCH /cases/c-001/status with status "under_review"
    Then the response time is under 150ms at the 95th percentile
    Including: state machine validation, status update, timeline event insert

  @performance @FEAT-003-p3
  Scenario: Timeline retrieval under 100ms with 500 events
    Given a case with 500 timeline events
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/timeline
    Then the response time is under 100ms at the 95th percentile

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-003-o1
  Scenario: Case lifecycle emits complete timeline
    Given an authenticated user with role "navigator"
    When they create, update, transition, and close a case
    Then timeline events are emitted for each action:
      | event_type          | title                              |
      | case.created        | Case created                       |
      | case.updated        | Case updated: priority → critical  |
      | case.status_changed | Status: new → under_review         |
      | case.status_changed | Status: under_review → closed      |
      | case.closed         | Case closed                        |

  @observability @FEAT-003-o2
  Scenario: RBAC denial on case operations is audited
    Given an authenticated user with role "clinician"
    When they attempt to create a case and receive 403
    Then an audit event is recorded with:
      | field   | value                             |
      | action  | case.create_denied                |
      | user_id | the clinician's user ID           |
      | details | role=clinician, required=navigator+ |
