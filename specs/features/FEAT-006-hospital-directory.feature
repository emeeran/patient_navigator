---
id: FEAT-006
title: "Hospital Directory"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-006
  - API-040
  - API-041
  - API-042
  - API-043
  - FEAT-001
supersedes: null
tags:
  - hospitals
  - directory
  - search
  - filter
---

# Feature: Hospital Directory

  As a navigator or clinician,
  I want to search and browse a directory of hospitals with specialties, costs, and financial assistance details,
  So that I can recommend the best care option for each patient's case.

  ## Scope

  ### In scope
  - List hospitals with pagination and sorting
  - Search hospitals by name (text search)
  - Filter by city, specialty, financial assistance availability
  - View hospital detail with all fields
  - Admin-only create and update hospital records
  - Cost range (min/max) for treatment estimates
  - Financial assistance flag and details
  - Rating field (0.0–5.0)
  - Soft-delete via is_active flag

  ### Out of scope
  - Hospital availability / bed tracking (V2)
  - Appointment booking integration (V2)
  - Hospital-to-case auto-matching (V2)
  - Geolocation / distance-based search (V2)
  - Hospital reviews by users

  ## Glossary

  | Term | Definition |
  |------|------------|
  | Specialty | Comma-separated list of medical specialties offered by a hospital |
  | Cost Range | Estimated minimum and maximum treatment cost in INR |
  | Financial Assistance | Whether the hospital offers internal financial aid programs |
  | Rating | Aggregate quality rating on a 0.0–5.0 scale |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | hospitals |
      | admin     | full      |
      | navigator | read      |
      | clinician | read      |
      | volunteer | read      |
      | patient   | read      |
    And the following users exist:
      | email          | role      | state  |
      | admin@test.com | admin     | active |
      | nav@test.com   | navigator | active |
      | clin@test.com  | clinician | active |
      | vol@test.com   | volunteer | active |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-006-h1
  Scenario: List hospitals with default pagination
    Given 25 hospitals exist in the system
    And an authenticated user with role "navigator"
    When they submit GET /hospitals
    Then the response status is 200
    And the response contains 20 hospitals (default page size)
    And pagination metadata shows total=25, page=1, per_page=20

  @happy-path @smoke @FEAT-006-h2
  Scenario: Get hospital detail by ID
    Given a hospital exists with id "h-001" named "Apollo Cancer Centre"
    And an authenticated user with role "navigator"
    When they submit GET /hospitals/h-001
    Then the response status is 200
    And the response contains all fields: id, name, specialty, city, state, address, phone, email, website, cost_range_min, cost_range_max, has_financial_assistance, financial_assistance_details, rating, is_active, created_at, updated_at

  @happy-path @FEAT-006-h3
  Scenario: Admin creates a new hospital
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with:
      | field                       | value                                       |
      | name                        | Apollo Cancer Centre                        |
      | specialty                   | Oncology, Head and Neck Surgery             |
      | city                        | Chennai                                     |
      | state                       | Tamil Nadu                                  |
      | address                     | 320, Anna Salai, Chennai 600006             |
      | phone                       | +914428291890                               |
      | email                       | info@apollocancer.in                        |
      | website                     | https://www.apollocancercentre.com          |
      | cost_range_min              | 200000                                      |
      | cost_range_max              | 1500000                                     |
      | has_financial_assistance    | true                                        |
      | financial_assistance_details | SAP scheme available for low-income families |
      | rating                      | 4.5                                         |
    Then the response status is 201
    And the hospital is created with is_active=true

  @happy-path @FEAT-006-h4
  Scenario: Admin updates hospital information
    Given a hospital exists with id "h-001" and rating 4.5
    And an authenticated user with role "admin"
    When they submit PATCH /hospitals/h-001 with:
      | field  | value |
      | rating | 4.8   |
    Then the response status is 200
    And the rating is updated to 4.8
    And updated_at is refreshed

  @happy-path @FEAT-006-h5
  Scenario: Filter hospitals by city
    Given 15 hospitals in Chennai and 10 hospitals in Bangalore
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?city=Chennai
    Then the response status is 200
    And all returned hospitals have city "Chennai"

  @happy-path @FEAT-006-h6
  Scenario: Filter hospitals by financial assistance availability
    Given 8 hospitals with has_financial_assistance=true and 17 with false
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?has_financial_assistance=true
    Then the response status is 200
    And all returned hospitals have has_financial_assistance=true

  @happy-path @FEAT-006-h7
  Scenario: Search hospitals by name
    Given hospitals named "Apollo Cancer Centre", "Apollo General Hospital", "AIIMS Delhi"
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?search=Apollo
    Then the response status is 200
    And results include hospitals matching "Apollo" in name

  @happy-path @FEAT-006-h8
  Scenario: Filter hospitals by specialty
    Given hospitals with specialties including "Oncology" and others
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?specialty=Oncology
    Then the response status is 200
    And all results have "Oncology" in their specialty field

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-006-ec1
  Scenario: Hospital with minimal required fields
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with:
      | field | value          |
      | name  | Basic Hospital |
      | city  | Mumbai         |
    Then the response status is 201
    And optional fields (specialty, state, address, phone, email, website, cost ranges, financial assistance, rating) are null or defaults

  @edge-case @FEAT-006-ec2
  Scenario: Rating at boundary 0.0
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with rating 0.0
    Then the response status is 201

  @edge-case @FEAT-006-ec3
  Scenario: Rating at boundary 5.0
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with rating 5.0
    Then the response status is 201

  @edge-case @FEAT-006-ec4
  Scenario: Sort hospitals by rating descending
    Given hospitals with ratings 3.0, 4.5, 4.8, 2.0
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?sort=-rating
    Then results are ordered 4.8, 4.5, 3.0, 2.0

  @edge-case @FEAT-006-ec5
  Scenario: Hospital with cost range only min
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with cost_range_min=500000 and no cost_range_max
    Then the response status is 201
    And cost_range_max is null

  @edge-case @FEAT-006-ec6
  Scenario: Inactive hospitals excluded from default listing
    Given 20 active hospitals and 3 inactive hospitals
    And an authenticated user with role "navigator"
    When they submit GET /hospitals
    Then only active hospitals are returned (is_active=true)

  @edge-case @FEAT-006-ec7
  Scenario: Admin can view inactive hospitals
    Given 3 inactive hospitals exist
    And an authenticated user with role "admin"
    When they submit GET /hospitals?is_active=false
    Then the response contains the 3 inactive hospitals

  @edge-case @FEAT-006-ec8
  Scenario: Combined filters (city + specialty + financial assistance)
    Given hospitals with various combinations
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?city=Chennai&specialty=Oncology&has_financial_assistance=true
    Then all results match all three filter criteria

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-006-e1
  Scenario: Non-admin cannot create hospital
    Given an authenticated user with role "navigator"
    When they submit POST /hospitals with valid data
    Then the response status is 403

  @error-case-case @FEAT-006-e2
  Scenario: Non-admin cannot update hospital
    Given an authenticated user with role "clinician"
    When they submit PATCH /hospitals/h-001 with valid data
    Then the response status is 403

  @error-case-case @FEAT-006-e3
  Scenario: Create hospital missing required name
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with:
      | field | value   |
      | city  | Chennai |
    Then the response status is 422
    And the error indicates "name" is required

  @error-case-case @FEAT-006-e4
  Scenario: Rating above 5.0
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with rating 5.5
    Then the response status is 422
    And the error indicates rating must be between 0.0 and 5.0

  @error-case-case @FEAT-006-e5
  Scenario: Negative rating
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with rating -1.0
    Then the response status is 422

  @error-case-case @FEAT-006-e6
  Scenario: Get non-existent hospital
    Given an authenticated user with role "navigator"
    When they submit GET /hospitals/00000000-0000-0000-0000-000000000000
    Then the response status is 404

  @error-case-case @FEAT-006-e7
  Scenario: cost_range_min exceeds cost_range_max
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with cost_range_min=1000000 and cost_range_max=500000
    Then the response status is 422
    And the error indicates cost_range_min must not exceed cost_range_max

  @error-case-case @FEAT-006-e8
  Scenario: Invalid website URL format
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with website "not-a-valid-url"
    Then the response status is 422

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-006-s1
  Scenario: Unauthenticated user cannot access hospitals
    Given no authentication token is provided
    When they submit GET /hospitals
    Then the response status is 401

  @security @FEAT-006-s2
  Scenario: SQL injection in search parameter
    Given an authenticated user with role "navigator"
    When they submit GET /hospitals?search='; DROP TABLE hospitals; --
    Then the response status is 200
    And no SQL error occurs
    And the hospitals table remains intact

  @security @FEAT-006-s3
  Scenario: XSS prevention in hospital fields
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with name containing "<script>alert('xss')</script>"
    Then the input is sanitized or rejected
    And no script execution is possible in the response

  @security @FEAT-006-s4
  Scenario: Admin deactivation preserves hospital data
    Given a hospital exists with id "h-001" referenced by active cases
    And an authenticated user with role "admin"
    When they set is_active to false
    Then existing case references to h-001 remain intact
    And the hospital still appears in case detail views

  @security @FEAT-006-s5
  Scenario: Volunteer read-only access enforced
    Given an authenticated user with role "volunteer"
    When they submit GET /hospitals
    Then the response status is 200
    When they submit POST /hospitals
    Then the response status is 403
    When they submit PATCH /hospitals/h-001
    Then the response status is 403

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-006-p1
  Scenario: Hospital list under 200ms with 1,000 records
    Given 1,000 hospital records exist
    And an authenticated user with role "navigator"
    When they submit GET /hospitals
    Then the response time is under 200ms at the 95th percentile

  @performance @FEAT-006-p2
  Scenario: Filtered search under 300ms with 1,000 records
    Given 1,000 hospital records exist
    And an authenticated user with role "navigator"
    When they submit GET /hospitals?city=Chennai&specialty=Oncology
    Then the response time is under 300ms at the 95th percentile

  @performance @FEAT-006-p3
  Scenario: Hospital creation under 100ms
    Given an authenticated user with role "admin"
    When they submit POST /hospitals with valid data
    Then the response time is under 100ms at the 95th percentile

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-006-o1
  Scenario: Hospital CRUD operations are logged
    Given an authenticated admin
    When they create and update a hospital
    Then audit events are recorded for:
      | action              |
      | hospital.created    |
      | hospital.updated    |

  @observability @FEAT-006-o2
  Scenario: Search queries with no results are logged
    Given an authenticated user with role "navigator"
    When they submit GET /hospitals?search=nonexistentterm
    Then the response status is 200 with empty results
    And a search event is logged with query="nonexistentterm" and result_count=0
