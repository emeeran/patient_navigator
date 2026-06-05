---
id: FEAT-002
title: "Patient Management"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-003
  - DATA-009
  - API-010
  - API-011
  - API-012
  - API-013
  - API-014
  - API-090
  - FEAT-001
supersedes: null
tags:
  - patients
  - crud
  - pii
  - search
  - pagination
---

# Feature: Patient Management

  As a navigator or admin,
  I want to create, view, update, and archive patient records,
  So that I can coordinate care for patients throughout their healthcare journey.

  ## Scope

  ### In scope
  - Create patient with required fields (full_name, age, gender)
  - List patients with pagination, sorting, and text search
  - View individual patient details
  - Update patient information
  - Soft-delete (archive) patient records
  - PII field masking based on viewer role
  - Activity logging for all patient mutations
  - Fuzzy search via GIN trigram index on full_name

  ### Out of scope
  - Patient self-registration (admin/navigator creates records)
  - Bulk import/export of patient records
  - Patient portal access (V2)
  - Patient merging/deduplication
  - Audit log UI for patient changes

  ## Glossary

  | Term | Definition |
  |------|------------|
  | PII | Personally Identifiable Information — fields marked x-pii in DATA-003 |
  | Soft Delete | Setting deleted_at timestamp; record retained for audit but hidden from queries |
  | PII Masking | Partially obscuring sensitive fields (e.g., phone shown as +91****3210) based on role |
  | GIN Trigram | PostgreSQL trigram similarity index for fuzzy full_name search |
  | Pagination | Cursor-based pagination with configurable page size (default 20, max 100) |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | patients |
      | admin     | full     |
      | navigator | full     |
      | clinician | read     |
      | volunteer | read     |
      | patient   | own      |
    And the following users exist:
      | email              | role      | state  |
      | admin@test.com     | admin     | active |
      | nav@test.com       | navigator | active |
      | clin@test.com      | clinician | active |
      | vol@test.com       | volunteer | active |
      | patient1@test.com  | patient   | active |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-002-h1
  Scenario: Navigator creates a new patient
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field                  | value                  |
      | full_name              | Aarav Mehta            |
      | age                    | 45                     |
      | gender                 | male                   |
      | phone                  | +919876543210          |
      | emergency_contact_name | Priya Mehta            |
      | emergency_contact_phone | +919876543211         |
    Then a new patient record is created with status "active"
    And the response status is 201
    And the response contains the patient with id, full_name "Aarav Mehta", age 45
    And created_by is set to the navigator's user ID
    And created_at is set to the current timestamp
    And an activity record is logged with action "patient.created"

  @happy-path @smoke @FEAT-002-h2
  Scenario: List patients with default pagination
    Given 25 patients exist in the system
    And an authenticated user with role "navigator"
    When they submit GET /patients
    Then the response status is 200
    And the response contains exactly 20 patients (default page size)
    And the response includes pagination metadata with total=25, page=1, per_page=20
    And each patient entry contains: id, full_name, age, gender, status, navigator_id

  @happy-path @FEAT-002-h3
  Scenario: Search patients by name with fuzzy matching
    Given patients exist with names "Aarav Mehta", "Arun Kumar", "Priya Sharma"
    And an authenticated user with role "navigator"
    When they submit GET /patients?search=Aarav
    Then the response status is 200
    And the response contains at least 1 patient matching "Aarav Mehta"
    And fuzzy matching uses the GIN trigram index on full_name

  @happy-path @FEAT-002-h4
  Scenario: Get patient details by ID
    Given a patient exists with id "p-001" and full_name "Aarav Mehta"
    And an authenticated user with role "navigator"
    When they submit GET /patients/p-001
    Then the response status is 200
    And the response contains all patient fields: id, full_name, age, gender, phone, email, address, emergency contacts, navigator_id, status, notes, created_at, updated_at

  @happy-path @FEAT-002-h5
  Scenario: Update patient information
    Given a patient exists with id "p-001" and phone "+919876543210"
    And an authenticated user with role "navigator"
    When they submit PATCH /patients/p-001 with:
      | field | value           |
      | phone | +919876599999   |
      | notes | Moved to Chennai |
    Then the response status is 200
    And the patient's phone is updated to "+919876599999"
    And the patient's notes are updated to "Moved to Chennai"
    And updated_at is refreshed to current timestamp
    And an activity record is logged with action "patient.updated"

  @happy-path @FEAT-002-h6
  Scenario: Archive (soft delete) a patient
    Given a patient exists with id "p-001"
    And an authenticated user with role "navigator"
    When they submit DELETE /patients/p-001
    Then the response status is 204
    And the patient's deleted_at is set to the current timestamp
    And the patient's status is set to "archived"
    And the patient no longer appears in GET /patients results
    And an activity record is logged with action "patient.archived"

  @happy-path @FEAT-002-h7
  Scenario: List patients sorted by creation date descending
    Given patients created on 2026-06-01, 2026-06-02, 2026-06-03
    And an authenticated user with role "admin"
    When they submit GET /patients?sort=-created_at
    Then the response status is 200
    And patients are returned in descending created_at order (newest first)

  @happy-path @FEAT-002-h8
  Scenario: Filter patients by status
    Given 15 active patients and 5 archived patients exist
    And an authenticated user with role "navigator"
    When they submit GET /patients?status=active
    Then the response status is 200
    And the response contains exactly 15 patients
    And all returned patients have status "active"

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-002-ec1
  Scenario: Create patient with minimal required fields only
    Given an authenticated user with role "navigator"
    When they submit POST /patients with only required fields:
      | field     | value        |
      | full_name | Min Patient  |
      | age       | 30           |
      | gender    | other        |
    Then the response status is 201
    And optional fields (phone, email, address, emergency contacts, navigator_id) are null

  @edge-case @FEAT-002-ec2
  Scenario: Patient list pagination second page
    Given 25 patients exist in the system
    And an authenticated user with role "navigator"
    When they submit GET /patients?page=2&per_page=20
    Then the response status is 200
    And the response contains exactly 5 patients
    And pagination metadata shows total=25, page=2, per_page=20

  @edge-case @FEAT-002-ec3
  Scenario: Age boundary value 0
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value       |
      | full_name | Newborn     |
      | age       | 0           |
      | gender    | female      |
    Then the response status is 201
    And the patient is created with age 0

  @edge-case @FEAT-002-ec4
  Scenario: Age boundary value 150
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value       |
      | full_name | Elder       |
      | age       | 150         |
      | gender    | male        |
    Then the response status is 201
    And the patient is created with age 150

  @edge-case @FEAT-002-ec5
  Scenario: Gender value "prefer_not_to_say"
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value             |
      | full_name | Private Person    |
      | age       | 25                |
      | gender    | prefer_not_to_say |
    Then the response status is 201
    And the patient is created with gender "prefer_not_to_say"

  @edge-case @FEAT-002-ec6
  Scenario: Empty search returns all active patients
    Given 30 active patients exist
    And an authenticated user with role "navigator"
    When they submit GET /patients?search=
    Then the response status is 200
    And the response contains the first 20 patients (default pagination)

  @edge-case @FEAT-002-ec7
  Scenario: Patient name with special characters
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value              |
      | full_name | José García-López  |
      | age       | 40                 |
      | gender    | male               |
    Then the response status is 201
    And the patient is created with full_name "José García-López"

  @edge-case @FEAT-002-ec8
  Scenario: Clinician views patient with PII masking
    Given a patient exists with phone "+919876543210" and email "patient@example.org"
    And an authenticated user with role "clinician"
    When they submit GET /patients/p-001
    Then the response status is 200
    And the phone field is partially masked (e.g., "+91****3210")
    And the email field is partially masked (e.g., "p***@example.org")

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-002-e1
  Scenario: Create patient missing required field
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field | value |
      | age   | 30    |
    Then the response status is 422
    And the error message indicates "full_name" is required
    And the error message indicates "gender" is required

  @error-case-case @FEAT-002-e2
  Scenario: Age outside valid range (negative)
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value       |
      | full_name | Bad Age     |
      | age       | -1          |
      | gender    | male        |
    Then the response status is 422
    And the error message indicates age must be between 0 and 150

  @error-case-case @FEAT-002-e3
  Scenario: Age outside valid range (151)
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value       |
      | full_name | Too Old     |
      | age       | 151         |
      | gender    | female      |
    Then the response status is 422
    And the error message indicates age must be between 0 and 150

  @error-case-case @FEAT-002-e4
  Scenario: Invalid gender value
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value        |
      | full_name | Bad Gender   |
      | age       | 30           |
      | gender    | helicopter   |
    Then the response status is 422
    And the error message indicates gender must be one of: male, female, other, prefer_not_to_say

  @error-case-case @FEAT-002-e5
  Scenario: Get non-existent patient
    Given an authenticated user with role "navigator"
    When they submit GET /patients/00000000-0000-0000-0000-000000000000
    Then the response status is 404
    And the error message indicates patient not found

  @error-case-case @FEAT-002-e6
  Scenario: Update archived patient
    Given an archived patient with id "p-archived"
    And an authenticated user with role "navigator"
    When they submit PATCH /patients/p-archived with:
      | field | value       |
      | notes | Should fail |
    Then the response status is 400
    And the error message indicates archived patients cannot be modified

  @error-case-case @FEAT-002-e7
  Scenario: Pagination with invalid page number
    Given an authenticated user with role "navigator"
    When they submit GET /patients?page=-1
    Then the response status is 422
    And the error message indicates page must be a positive integer

  @error-case-case @FEAT-002-e8
  Scenario: Full_name exceeds max length
    Given an authenticated user with role "navigator"
    When they submit POST /patients with:
      | field     | value                                                         |
      | full_name | A very long name that exceeds two hundred and fifty five characters (...) |
      | age       | 30                                                            |
      | gender    | male                                                          |
    Then the response status is 422
    And the error message indicates full_name must not exceed 255 characters

  @error-case-case @FEAT-002-e9
  Scenario: Update patient with empty full_name
    Given a patient exists with id "p-001"
    And an authenticated user with role "navigator"
    When they submit PATCH /patients/p-001 with:
      | field     | value |
      | full_name |       |
    Then the response status is 422
    And the error message indicates full_name must not be empty

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-002-s1
  Scenario: Volunteer cannot create patients
    Given an authenticated user with role "volunteer"
    When they submit POST /patients with valid data
    Then the response status is 403
    And an audit event is recorded with action "patient.create_denied"

  @security @FEAT-002-s2
  Scenario: Unauthenticated user cannot list patients
    Given no authentication token is provided
    When they submit GET /patients
    Then the response status is 401

  @security @FEAT-002-s3
  Scenario: PII fields encrypted at rest in database
    Given the database is directly inspected
    Then the following fields are stored with at-rest encryption:
      | field                    |
      | full_name                |
      | phone                    |
      | email                    |
      | address                  |
      | emergency_contact_name   |
      | emergency_contact_phone  |

  @security @FEAT-002-s4
  Scenario: Patient role can only view own record
    Given a patient user owns record "p-self"
    And a different patient record "p-other" exists
    When the patient submits GET /patients/p-other
    Then the response status is 403
    And an audit event is recorded with action "patient.access_denied"

  @security @FEAT-002-s5
  Scenario: SQL injection in search parameter
    Given an authenticated user with role "navigator"
    When they submit GET /patients?search='; DROP TABLE patients; --
    Then the response status is 200
    And no SQL error occurs
    And the search string is treated as literal text (no patients match)
    And the patients table remains intact

  @security @FEAT-002-s6
  Scenario: PII masking for volunteer role
    Given a patient exists with full_name "Aarav Mehta" and phone "+919876543210"
    And an authenticated user with role "volunteer"
    When they submit GET /patients/p-001
    Then the response status is 200
    And full_name is partially masked (e.g., "A**** M****")
    And phone is fully masked (e.g., "**********")

  @security @FEAT-002-s7
  Scenario: Navigator cannot delete patient they did not create
    Given a patient exists created by a different navigator
    And an authenticated user with role "navigator" who did not create the patient
    When they submit DELETE /patients/p-001
    Then the response status is 200
    And the archive succeeds (navigators can archive any patient they have access to)

  @security @FEAT-002-s8
  Scenario: Patient mutation audit trail is tamper-proof
    Given activities exist for patient "p-001"
    When any user attempts to UPDATE or DELETE from the activities table directly
    Then the database rejects the operation (INSERT-only table policy)
    And activity records remain intact

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-002-p1
  Scenario: Patient list query under 200ms with 10,000 records
    Given 10,000 patient records exist in the database
    And the GIN trigram index is active on full_name
    And an authenticated user with role "navigator"
    When they submit GET /patients
    Then the response time is under 200ms at the 95th percentile
    And the query uses the idx_patients_status index for filtering

  @performance @FEAT-002-p2
  Scenario: Fuzzy search under 300ms with 10,000 records
    Given 10,000 patient records exist in the database
    And an authenticated user with role "navigator"
    When they submit GET /patients?search=Mehta
    Then the response time is under 300ms at the 95th percentile
    And the query uses the GIN trigram index on full_name

  @performance @FEAT-002-p3
  Scenario: Patient creation under 100ms
    Given an authenticated user with role "navigator"
    When they submit POST /patients with valid data
    Then the response time is under 100ms at the 95th percentile
    Including: validation, database insert, activity log write

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-002-o1
  Scenario: Patient CRUD operations emit activity records
    Given an authenticated user with role "navigator"
    When they create, update, and archive a patient in sequence
    Then activity records are emitted for each action:
      | action             | entity_type |
      | patient.created    | patient     |
      | patient.updated    | patient     |
      | patient.archived   | patient     |
    And each activity includes: patient_id, user_id, timestamp, description, metadata

  @observability @FEAT-002-o2
  Scenario: RBAC denial on patient operations is audited
    Given an authenticated user with role "volunteer"
    When they attempt to create a patient and receive 403
    Then an audit event is recorded with:
      | field   | value                              |
      | action  | patient.create_denied              |
      | user_id | the volunteer's user ID            |
      | details | role=volunteer, required=navigator+ |
