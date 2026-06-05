---
id: FEAT-008
title: "Follow-Up Tracking"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-008
  - API-060
  - API-061
  - API-062
  - API-063
  - API-064
  - FEAT-001
  - FEAT-002
  - FEAT-003
supersedes: null
tags:
  - followups
  - tracking
  - appointments
  - overdue
  - scheduling
---

# Feature: Follow-Up Tracking

  As a navigator,
  I want to create and track follow-up tasks for patient cases,
  So that no appointment, deadline, or treatment milestone falls through the cracks.

  ## Scope

  ### In scope
  - Create follow-ups for a case with type, title, description, due date
  - Follow-up types: appointment, deadline, funding_status, treatment_progress
  - List follow-ups for a specific case
  - Get follow-up detail
  - Update follow-up (title, description, due_date, status)
  - Mark follow-up as completed
  - Cancel follow-up
  - Upcoming view: list follow-ups across all active cases, sorted by due date
  - Automatic overdue detection (status becomes "overdue" when due_date < today)
  - Filter by status and type
  - RBAC enforced (navigator+ for CUD, all authenticated for read)

  ### Out of scope
  - Recurring follow-ups (V2)
  - Email/SMS notifications for upcoming follow-ups (V2)
  - Calendar integration (V2)
  - Follow-up assignment to specific team members (V2)
  - Automated follow-up creation from case events

  ## Glossary

  | Term | Definition |
  |------|------------|
  | Follow-Up | A tracked task related to a case with a due date and status |
  | Overdue | A pending follow-up whose due_date has passed (automatically flagged) |
  | Upcoming View | Cross-case listing of all pending follow-ups sorted by due date ascending |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | followups |
      | admin     | full      |
      | navigator | full      |
      | clinician | read      |
      | volunteer | read      |
      | patient   | own       |
    And the following users exist:
      | email          | role      | state  |
      | admin@test.com | admin     | active |
      | nav@test.com   | navigator | active |
      | clin@test.com  | clinician | active |
      | vol@test.com   | volunteer | active |
    And the following cases exist:
      | id    | patient_id | status            |
      | c-001 | p-001      | hospital_selected |
      | c-002 | p-002      | under_review      |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-008-h1
  Scenario: Navigator creates a follow-up for a case
    Given an authenticated user with role "navigator"
    And case "c-001" exists
    When they submit POST /cases/c-001/followups with:
      | field       | value                                        |
      | type        | appointment                                  |
      | title       | Consultation with oncologist                 |
      | description | First appointment at Apollo Cancer Centre    |
      | due_date    | 2026-06-15                                   |
    Then the response status is 201
    And a follow-up is created with:
      | field       | value                        |
      | case_id     | c-001                        |
      | patient_id  | p-001 (denormalized)         |
      | type        | appointment                  |
      | title       | Consultation with oncologist |
      | status      | pending                      |
      | due_date    | 2026-06-15                   |
      | created_by  | the navigator's user ID      |

  @happy-path @smoke @FEAT-008-h2
  Scenario: List follow-ups for a case
    Given case "c-001" has 4 follow-ups
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/followups
    Then the response status is 200
    And the response contains 4 follow-ups ordered by due_date ascending
    And each entry includes: id, type, title, status, due_date, created_at

  @happy-path @FEAT-008-h3
  Scenario: Get follow-up detail
    Given a follow-up exists with id "fu-001"
    And an authenticated user with role "navigator"
    When they submit GET /followups/fu-001
    Then the response status is 200
    And the response contains all fields: id, case_id, patient_id, type, title, description, due_date, status, completed_at, created_by, created_at, updated_at

  @happy-path @FEAT-008-h4
  Scenario: Mark follow-up as completed
    Given a follow-up exists with id "fu-001" and status "pending"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-001 with:
      | field   | value     |
      | status  | completed |
    Then the response status is 200
    And status is updated to "completed"
    And completed_at is set to current timestamp

  @happy-path @FEAT-008-h5
  Scenario: Update follow-up title and due date
    Given a follow-up exists with id "fu-001"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-001 with:
      | field     | value                            |
      | title     | Follow-up consultation (rescheduled) |
      | due_date  | 2026-06-20                       |
    Then the response status is 200
    And title and due_date are updated

  @happy-path @FEAT-008-h6
  Scenario: Cancel a follow-up
    Given a follow-up exists with id "fu-001" and status "pending"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-001 with:
      | field   | value     |
      | status  | cancelled |
    Then the response status is 200
    And status is updated to "cancelled"

  @happy-path @FEAT-008-h7
  Scenario: View upcoming follow-ups across all cases
    Given 8 pending follow-ups exist across 3 cases with various due dates
    And an authenticated user with role "navigator"
    When they submit GET /followups/upcoming
    Then the response status is 200
    And follow-ups are sorted by due_date ascending (soonest first)
    And only pending follow-ups are included (completed/cancelled excluded)

  @happy-path @FEAT-008-h8
  Scenario: Automatic overdue detection
    Given a pending follow-up with due_date "2026-06-01"
    And the current date is "2026-06-04"
    When the follow-up is queried
    Then the status is automatically "overdue" (computed from due_date < today)
    And the database status remains "pending" (overdue is a computed status)

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-008-ec1
  Scenario: Create follow-up with due_date today
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with due_date equal to today
    Then the response status is 201
    And the follow-up is created with status "pending" (not overdue yet)

  @edge-case @FEAT-008-ec2
  Scenario: Create follow-up with due_date in the past
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with due_date "2026-05-01"
    Then the response status is 201
    And the follow-up is immediately flagged as overdue when queried

  @edge-case @FEAT-008-ec3
  Scenario: Multiple follow-up types
    Given an authenticated user with role "navigator"
    When they create follow-ups with types:
      | type                |
      | appointment         |
      | deadline            |
      | funding_status      |
      | treatment_progress  |
    Then all are created successfully with their respective types

  @edge-case @FEAT-008-ec4
  Scenario: Filter upcoming by follow-up type
    Given pending follow-ups of various types exist
    And an authenticated user with role "navigator"
    When they submit GET /followups/upcoming?type=appointment
    Then only appointment-type follow-ups are returned

  @edge-case @FEAT-008-ec5
  Scenario: Patient views own follow-ups only
    Given patient user "patient1@test.com" owns patient record "p-001"
    And follow-ups exist for cases of both p-001 and p-002
    When the patient submits GET /followups/upcoming
    Then only follow-ups for their own cases (p-001) are returned

  @edge-case @FEAT-008-ec6
  Scenario: Completed follow-up with completed_at timestamp
    Given a follow-up completed on "2026-06-10"
    When the follow-up is queried
    Then completed_at is "2026-06-10T..."
    And status is "completed"

  @edge-case @FEAT-008-ec7
  Scenario: Follow-up list pagination
    Given 50 follow-ups exist for case "c-001"
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/followups?page=2&per_page=20
    Then the response contains 20 follow-ups
    And pagination shows total=50, page=2

  @edge-case @FEAT-008-ec8
  Scenario: Upcoming view limited to next 30 days by default
    Given follow-ups with due dates ranging from today to 60 days out
    And an authenticated user with role "navigator"
    When they submit GET /followups/upcoming
    Then only follow-ups with due_date within the next 30 days are returned
    And a total_count of all pending follow-ups is included in metadata

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-008-e1
  Scenario: Create follow-up with missing required fields
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with:
      | field  | value       |
      | title  | Test        |
    Then the response status is 422
    And the error indicates "type" and "due_date" are required

  @error-case-case @FEAT-008-e2
  Scenario: Invalid follow-up type
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with type "surgery"
    Then the response status is 422
    And the error indicates type must be: appointment, deadline, funding_status, treatment_progress

  @error-case-case @FEAT-008-e3
  Scenario: Create follow-up for non-existent case
    Given an authenticated user with role "navigator"
    When they submit POST /cases/00000000-0000-0000-0000-000000000000/followups
    Then the response status is 404

  @error-case-case @FEAT-008-e4
  Scenario: Invalid date format for due_date
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with due_date "not-a-date"
    Then the response status is 422

  @error-case-case @FEAT-008-e5
  Scenario: Update completed follow-up
    Given a follow-up with id "fu-done" and status "completed"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-done with:
      | field   | value     |
      | title   | Updated   |
    Then the response status is 400
    And the error indicates completed follow-ups cannot be modified

  @error-case-case @FEAT-008-e6
  Scenario: Cancel an already cancelled follow-up
    Given a follow-up with status "cancelled"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-cancel with status "cancelled"
    Then the response status is 200 (idempotent)

  @error-case-case @FEAT-008-e7
  Scenario: Get non-existent follow-up
    Given an authenticated user with role "navigator"
    When they submit GET /followups/00000000-0000-0000-0000-000000000000
    Then the response status is 404

  @error-case-case @FEAT-008-e8
  Scenario: Invalid status transition (completed → pending)
    Given a follow-up with status "completed"
    And an authenticated user with role "navigator"
    When they submit PATCH /followups/fu-done with status "pending"
    Then the response status is 422
    And the error indicates invalid status transition

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-008-s1
  Scenario: Volunteer cannot create follow-ups
    Given an authenticated user with role "volunteer"
    When they submit POST /cases/c-001/followups with valid data
    Then the response status is 403

  @security @FEAT-008-s2
  Scenario: Unauthenticated access rejected
    Given no authentication token is provided
    When they submit GET /followups/upcoming
    Then the response status is 401

  @security @FEAT-008-s3
  Scenario: Clinician can read but not modify follow-ups
    Given an authenticated user with role "clinician"
    When they submit GET /cases/c-001/followups
    Then the response status is 200
    When they submit PATCH /followups/fu-001 with status "completed"
    Then the response status is 403

  @security @FEAT-008-s4
  Scenario: Patient can only see own follow-ups
    Given a patient user
    And follow-ups for a different patient's case
    When the patient submits GET /followups/fu-other
    Then the response status is 403

  @security @FEAT-008-s5
  Scenario: SQL injection in title field
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with title "'; DROP TABLE followups; --"
    Then the response status is 201
    And the title is stored as literal text

  @security @FEAT-008-s6
  Scenario: Follow-up mutations are audited
    Given an authenticated user with role "navigator"
    When they create and complete a follow-up
    Then activity events are logged for:
      | action               |
      | followup.created     |
      | followup.completed   |

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-008-p1
  Scenario: Upcoming view under 200ms with 1,000 follow-ups
    Given 1,000 pending follow-ups across 200 cases
    And an authenticated user with role "navigator"
    When they submit GET /followups/upcoming
    Then the response time is under 200ms at the 95th percentile

  @performance @FEAT-008-p2
  Scenario: Follow-up creation under 100ms
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/followups with valid data
    Then the response time is under 100ms at the 95th percentile

  @performance @FEAT-008-p3
  Scenario: Overdue detection query under 100ms
    Given 500 pending follow-ups with 100 overdue
    When the overdue detection query runs
    Then the computation takes under 100ms
    And all overdue follow-ups are correctly identified

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-008-o1
  Scenario: Follow-up lifecycle events are logged
    Given an authenticated user with role "navigator"
    When they create, update, complete, and cancel follow-ups
    Then activity events are emitted for:
      | action               |
      | followup.created     |
      | followup.updated     |
      | followup.completed   |
      | followup.cancelled   |

  @observability @FEAT-008-o2
  Scenario: Overdue follow-up count in dashboard metrics
    Given 15 overdue follow-ups exist
    When the dashboard metrics endpoint (GET /reports/dashboard) is called
    Then the response includes overdue_followups_count: 15
    And the metric is computed from real-time due_date evaluation
