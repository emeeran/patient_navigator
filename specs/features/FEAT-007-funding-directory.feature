---
id: FEAT-007
title: "Funding Directory"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-007
  - API-050
  - API-051
  - API-052
  - API-053
  - FEAT-001
supersedes: null
tags:
  - funding
  - directory
  - eligibility
  - financial-assistance
---

# Feature: Funding Directory

  As a navigator,
  I want to search a directory of funding programs with eligibility criteria and application details,
  So that I can match patients to the best financial assistance for their treatment.

  ## Scope

  ### In scope
  - List funding programs with pagination
  - Search funding programs by name
  - View program detail with eligibility, documents required, application process
  - Contact person, phone, email, website per program
  - Maximum funding amount per program
  - Admin-only create and update
  - Soft-delete via is_active flag

  ### Out of scope
  - Online application submission (V2)
  - Eligibility auto-matching against patient profiles (V2)
  - Funding status tracking within a case (handled in FEAT-003)
  - Payment disbursement tracking (V2)

  ## Glossary

  | Term | Definition |
  |------|------------|
  | Funding Program | A government, NGO, or hospital-based financial assistance scheme for medical treatment |
  | Eligibility Criteria | Text description of who qualifies for the program |
  | Max Amount | Maximum financial assistance available in INR |
  | Documents Required | List of documents needed to apply for the program |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | funding |
      | admin     | full    |
      | navigator | read    |
      | clinician | read    |
      | volunteer | read    |
      | patient   | read    |
    And the following users exist:
      | email          | role      | state  |
      | admin@test.com | admin     | active |
      | nav@test.com   | navigator | active |
      | clin@test.com  | clinician | active |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-007-h1
  Scenario: List funding programs with default pagination
    Given 30 funding programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding
    Then the response status is 200
    And the response contains 20 programs (default page size)
    And pagination metadata shows total=30, page=1, per_page=20

  @happy-path @smoke @FEAT-007-h2
  Scenario: Get funding program detail
    Given a funding program exists with id "f-001" named "Chief Minister's Health Insurance Scheme"
    And an authenticated user with role "navigator"
    When they submit GET /funding/f-001
    Then the response status is 200
    And the response contains: id, scheme_name, description, eligibility_criteria, documents_required, application_process, contact_person, contact_phone, contact_email, website, max_amount, is_active, created_at, updated_at

  @happy-path @FEAT-007-h3
  Scenario: Admin creates a funding program
    Given an authenticated user with role "admin"
    When they submit POST /funding with:
      | field                 | value                                                     |
      | scheme_name           | Chief Minister's Health Insurance Scheme                   |
      | description           | Tamil Nadu government scheme providing free treatment for low-income families |
      | eligibility_criteria  | Annual family income below ₹72,000. Tamil Nadu resident.  |
      | documents_required    | Income certificate, Aadhaar card, hospital estimate, ration card |
      | application_process   | Apply through the hospital's billing department with required documents |
      | contact_person        | Ramesh Kumar                                              |
      | contact_phone         | +914425340540                                             |
      | contact_email         | cmhis@tn.gov.in                                           |
      | website               | https://cmhisco.tn.gov.in                                 |
      | max_amount            | 500000                                                    |
    Then the response status is 201
    And the program is created with is_active=true

  @happy-path @FEAT-007-h4
  Scenario: Admin updates funding program
    Given a funding program exists with id "f-001" and max_amount 500000
    And an authenticated user with role "admin"
    When they submit PATCH /funding/f-001 with:
      | field       | value  |
      | max_amount  | 750000 |
    Then the response status is 200
    And max_amount is updated to 750000

  @happy-path @FEAT-007-h5
  Scenario: Search funding programs by name
    Given programs named "CM Health Insurance", "PM Jan Arogya Yojana", "Tamil Nadu Cancer Fund"
    And an authenticated user with role "navigator"
    When they submit GET /funding?search=Cancer
    Then the response status is 200
    And results include "Tamil Nadu Cancer Fund"

  @happy-path @FEAT-007-h6
  Scenario: Filter by active programs only
    Given 25 active and 5 inactive programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding
    Then only active programs are returned (is_active=true)

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-007-ec1
  Scenario: Funding program with minimal fields
    Given an authenticated user with role "admin"
    When they submit POST /funding with only:
      | field        | value                     |
      | scheme_name  | Basic Assistance Program  |
    Then the response status is 201
    And optional fields are null

  @edge-case @FEAT-007-ec2
  Scenario: Program with max_amount of 0 (free treatment)
    Given an authenticated user with role "admin"
    When they submit POST /funding with max_amount 0
    Then the response status is 201
    And max_amount is 0 (indicates fully covered treatment)

  @edge-case @FEAT-007-ec3
  Scenario: Program with very large max_amount
    Given an authenticated user with role "admin"
    When they submit POST /funding with max_amount 10000000 (₹1 crore)
    Then the response status is 201

  @edge-case @FEAT-007-ec4
  Scenario: Pagination second page
    Given 30 funding programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding?page=2&per_page=20
    Then the response contains exactly 10 programs
    And pagination shows page=2, total=30

  @edge-case @FEAT-007-ec5
  Scenario: Sort by max_amount descending
    Given programs with max_amounts 100000, 500000, 2000000
    And an authenticated user with role "navigator"
    When they submit GET /funding?sort=-max_amount
    Then programs are ordered 2000000, 500000, 100000

  @edge-case @FEAT-007-ec6
  Scenario: Program with long eligibility criteria text
    Given an authenticated user with role "admin"
    When they submit POST /funding with eligibility_criteria of 5,000 characters
    Then the response status is 201

  @edge-case @FEAT-007-ec7
  Scenario: Admin can view inactive programs
    Given 5 inactive programs exist
    And an authenticated user with role "admin"
    When they submit GET /funding?is_active=false
    Then the response contains the 5 inactive programs

  @edge-case @FEAT-007-ec8
  Scenario: Empty search returns all active programs
    Given 25 active programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding?search=
    Then the response status is 200
    And the first 20 active programs are returned

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-007-e1
  Scenario: Non-admin cannot create program
    Given an authenticated user with role "navigator"
    When they submit POST /funding with valid data
    Then the response status is 403

  @error-case-case @FEAT-007-e2
  Scenario: Non-admin cannot update program
    Given an authenticated user with role "clinician"
    When they submit PATCH /funding/f-001 with valid data
    Then the response status is 403

  @error-case-case @FEAT-007-e3
  Scenario: Create program missing scheme_name
    Given an authenticated user with role "admin"
    When they submit POST /funding with:
      | field       | value      |
      | description | Some text  |
    Then the response status is 422
    And the error indicates "scheme_name" is required

  @error-case-case @FEAT-007-e4
  Scenario: Negative max_amount
    Given an authenticated user with role "admin"
    When they submit POST /funding with max_amount -500
    Then the response status is 422

  @error-case-case @FEAT-007-e5
  Scenario: Get non-existent program
    Given an authenticated user with role "navigator"
    When they submit GET /funding/00000000-0000-0000-0000-000000000000
    Then the response status is 404

  @error-case-case @FEAT-007-e6
  Scenario: Invalid email format in contact_email
    Given an authenticated user with role "admin"
    When they submit POST /funding with contact_email "not-an-email"
    Then the response status is 422

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-007-s1
  Scenario: Unauthenticated access rejected
    Given no authentication token is provided
    When they submit GET /funding
    Then the response status is 401

  @security @FEAT-007-s2
  Scenario: SQL injection in search
    Given an authenticated user with role "navigator"
    When they submit GET /funding?search='; DROP TABLE funding_programs; --
    Then the response status is 200
    And the funding_programs table remains intact

  @security @FEAT-007-s3
  Scenario: XSS in scheme_name sanitized
    Given an authenticated user with role "admin"
    When they submit POST /funding with scheme_name containing "<script>alert(1)</script>"
    Then the input is sanitized or rejected

  @security @FEAT-007-s4
  Scenario: Admin deactivation preserves program data
    Given a funding program referenced by an active case
    And an authenticated user with role "admin"
    When they set is_active to false
    Then existing case references remain intact

  @security @FEAT-007-s5
  Scenario: Patient can read funding programs
    Given an authenticated user with role "patient"
    When they submit GET /funding
    Then the response status is 200

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-007-p1
  Scenario: Program list under 200ms with 500 records
    Given 500 funding programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding
    Then the response time is under 200ms at the 95th percentile

  @performance @FEAT-007-p2
  Scenario: Search under 300ms with 500 records
    Given 500 funding programs exist
    And an authenticated user with role "navigator"
    When they submit GET /funding?search=Cancer
    Then the response time is under 300ms at the 95th percentile

  @performance @FEAT-007-p3
  Scenario: Program creation under 100ms
    Given an authenticated user with role "admin"
    When they submit POST /funding with valid data
    Then the response time is under 100ms at the 95th percentile

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-007-o1
  Scenario: Funding program mutations are logged
    Given an authenticated admin
    When they create and update a funding program
    Then audit events are recorded for:
      | action              |
      | funding.created     |
      | funding.updated     |

  @observability @FEAT-007-o2
  Scenario: Search with no results is logged
    Given an authenticated user with role "navigator"
    When they submit GET /funding?search=zzznonexistent
    And the response has zero results
    Then a search event is logged with query and result_count=0
