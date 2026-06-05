---
id: FEAT-001
title: "Authentication and Role-Based Access Control"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-001
  - DATA-002
  - API-001
  - API-002
  - API-003
  - API-004
  - API-005
  - API-095
  - API-096
  - API-097
supersedes: null
tags:
  - auth
  - rbac
  - jwt
  - security
  - foundation
---

# Feature: Authentication and Role-Based Access Control

  As a user of the Patient Navigator Platform,
  I want to authenticate with email and password and access features based on my assigned role,
  So that I can securely perform my duties while patient data remains protected.

  ## Scope

  ### In scope
  - User registration (admin creates accounts with role assignment)
  - Login with email and password (JWT access + refresh tokens)
  - Token refresh with rotation
  - Logout (refresh token invalidation)
  - Current user profile retrieval
  - Role-based access control for 5 roles: admin, navigator, clinician, volunteer, patient
  - Permission enforcement at API endpoint level
  - Audit logging of all authentication events
  - Login rate limiting (brute-force protection)
  - Admin user management (list, update role, disable account)
  - Audit log viewing (admin only)

  ### Out of scope
  - OAuth / social login
  - Magic link authentication
  - OTP / multi-factor authentication
  - Password reset flow (V2)
  - Self-registration (only admin creates accounts)
  - Session management UI

  ## Glossary

  | Term | Definition |
  |------|------------|
  | JWT | JSON Web Token — stateless authentication token signed with HS256 |
  | Access Token | Short-lived JWT (30 min) sent in Authorization header |
  | Refresh Token | Long-lived JWT (7 days) used to obtain new access tokens |
  | RBAC | Role-Based Access Control — permissions assigned to roles, not individual users |
  | Permission Level | `full` (CRUD), `read` (read-only), `own` (own records only), `review` (review+comment), `none` (no access) |
  | Audit Log | INSERT-only record of security-relevant events |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | patients | cases | documents | hospitals | funding | followups | ai    | reports | users | audit |
      | admin     | full     | full  | full      | full      | full    | full      | full  | full    | full  | full  |
      | navigator | full     | full  | full      | read      | read    | full      | full  | read    | none  | none  |
      | clinician | read     | read  | read      | read      | read    | read      | review | read   | none  | none  |
      | volunteer | read     | read  | none      | read      | read    | read      | none  | none    | none  | none  |
      | patient   | own      | own   | own       | read      | read    | own       | own   | own     | none  | none  |
    And the following users exist:
      | email              | role      | state  |
      | admin@test.com     | admin     | active |
      | nav@test.com       | navigator | active |
      | clin@test.com      | clinician | active |
      | vol@test.com       | volunteer | active |
      | patient@test.com   | patient   | active |
      | disabled@test.com  | navigator | inactive |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-001-h1
  Scenario: Admin registers a new navigator user
    Given an authenticated admin user
    When they submit a registration request with:
      | field     | value                    |
      | email     | newnav@test.com          |
      | password  | SecurePass123!           |
      | full_name | New Navigator            |
      | role      | navigator                |
    Then a new user is created with status "active"
    And the response contains the user profile with role "navigator"
    And the password is stored as a bcrypt hash (not plaintext)
    And an audit event is recorded with action "user.registered"
    And the response status is 201

  @happy-path @smoke @FEAT-001-h2
  Scenario: Successful login with valid credentials
    Given a registered user with email "nav@test.com" and password "SecurePass123!"
    When they submit login credentials to POST /auth/login
    Then the response status is 200
    And the response contains an access_token (JWT with 30-minute expiry)
    And the response contains a refresh_token (JWT with 7-day expiry)
    And the response contains the user profile with role and permissions
    And an audit event is recorded with action "user.login"
    And the user's last_login_at is updated to current timestamp

  @happy-path @FEAT-001-h3
  Scenario: Token refresh with rotation
    Given an authenticated user with a valid refresh token
    When they submit the refresh token to POST /auth/refresh
    Then a new access token is issued with 30-minute expiry
    And a new refresh token is issued (old refresh token is invalidated)
    And the response status is 200
    And an audit event is recorded with action "user.token_refreshed"

  @happy-path @FEAT-001-h4
  Scenario: Logout invalidates refresh token
    Given an authenticated user with a valid refresh token
    When they submit POST /auth/logout with the refresh token
    Then the refresh token is invalidated and cannot be reused
    And the response status is 200
    And an audit event is recorded with action "user.logout"

  @happy-path @FEAT-001-h5
  Scenario: Retrieve current user profile
    Given an authenticated user with a valid access token
    When they submit GET /auth/me
    Then the response contains their user profile
    And the response includes: id, email, full_name, role, permissions, is_active
    And the response does NOT contain password_hash
    And the response status is 200

  @happy-path @FEAT-001-h6
  Scenario: RBAC allows navigator to create patients
    Given an authenticated user with role "navigator"
    When they submit POST /patients with valid patient data
    Then the request succeeds with status 201
    And the patient record is created

  @happy-path @FEAT-001-h7
  Scenario: Admin lists all users
    Given an authenticated admin user
    When they submit GET /admin/users
    Then the response contains a paginated list of all users
    And each user entry includes: id, email, full_name, role, is_active, last_login_at
    And no password_hash values are included
    And the response status is 200

  @happy-path @FEAT-001-h8
  Scenario: Admin updates user role
    Given an authenticated admin user
    And a user with id "user-123" and role "volunteer"
    When they submit PATCH /admin/users/user-123 with:
      | field | value      |
      | role  | navigator  |
    Then the user's role is updated to "navigator"
    And all active tokens for the user are invalidated (force re-login)
    And an audit event is recorded with action "user.role_changed"
    And the response status is 200

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-001-ec1
  Scenario Outline: Email format validation on registration
    Given an authenticated admin user
    When they submit a registration request with email "<email>"
    Then the outcome is "<expected_result>"

    Examples:
      | email                       | expected_result                         |
      | valid@example.com           | success                                 |
      | user.name+tag@domain.co     | success                                 |
      | ""                          | 422 validation error: email required    |
      | not-an-email                | 422 validation error: invalid email     |
      | @domain.com                 | 422 validation error: invalid email     |
      | user@                       | 422 validation error: invalid email     |
      | user@.com                   | 422 validation error: invalid email     |

  @edge-case @FEAT-001-ec2
  Scenario Outline: Password strength validation on registration
    Given an authenticated admin user
    When they submit a registration request with password "<password>"
    Then the outcome is "<expected_result>"

    Examples:
      | password         | expected_result                              |
      | SecurePass123!   | success (strong password)                    |
      | ""               | 422 validation error: password required      |
      | short            | 422 validation error: min 8 characters       |
      | alllowercase123  | 422 validation error: requires uppercase     |
      | ALLUPPERCASE123  | 422 validation error: requires lowercase     |
      | NoNumbersHere!   | 422 validation error: requires digit         |
      | NoSpecialChar123 | 422 validation error: requires special char  |

  @edge-case @FEAT-001-ec3
  Scenario: Case-insensitive email login
    Given a registered user with email "Nav@Test.com"
    When they submit login with email "nav@test.com" and correct password
    Then login succeeds and access token is returned

  @edge-case @FEAT-001-ec4
  Scenario: Concurrent login sessions remain valid
    Given a registered user "nav@test.com"
    When they login from session A and receive token_A
    And they login from session B and receive token_B
    Then both token_A and token_B are valid
    And both sessions can make authenticated requests independently

  @edge-case @FEAT-001-ec5
  Scenario: Access token expires at exact claim boundary
    Given an access token with exp claim set to "2026-06-04T12:30:00Z"
    When a request is made at "2026-06-04T12:29:59Z" with this token
    Then the request succeeds
    When a request is made at "2026-06-04T12:30:01Z" with this token
    Then the request is rejected with 401

  @edge-case @FEAT-001-ec6
  Scenario: Admin disables a user account
    Given an authenticated admin user
    And an active user "vol@test.com"
    When admin submits PATCH /admin/users/vol-user-id with is_active=false
    Then the user's account is marked inactive
    And all active tokens for the user are invalidated
    And the disabled user's next login attempt returns 403 with error "account_disabled"

  @edge-case @FEAT-001-ec7
  Scenario: Role change invalidates existing tokens
    Given an authenticated user "vol@test.com" with role "volunteer"
    And the user holds a valid access token
    When admin changes the user's role to "navigator"
    Then the user's existing access token is rejected with 401
    And the user must re-login to get a new token with updated permissions

  @edge-case @FEAT-001-ec8
  Scenario: User self-access for patient role
    Given an authenticated user with role "patient" and user_id "patient-123"
    When they request GET /patients/patient-123
    Then the request succeeds (they can view their own record)
    When they request GET /patients/other-patient-456
    Then the request is rejected with 403 (cannot view other patients)

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-001-er1
  Scenario: Login with incorrect password
    Given a registered user with email "nav@test.com"
    When they submit login with email "nav@test.com" and password "WrongPassword!"
    Then the response status is 401
    And the error is "invalid_credentials" (no hint about which field is wrong)
    And the failed attempt is recorded in the audit log
    And no information about the user's existence is revealed

  @error-case-case @FEAT-001-er2
  Scenario: Login with non-existent email
    Given no user exists with email "ghost@test.com"
    When they submit login with email "ghost@test.com" and any password
    Then the response status is 401
    And the error is "invalid_credentials" (same as wrong password — no enumeration)

  @error-case-case @FEAT-001-er3
  Scenario: Login with disabled account
    Given a user "disabled@test.com" with is_active=false
    When they submit login with correct credentials
    Then the response status is 403
    And the error type is "account_disabled"
    And the failed attempt is recorded in the audit log

  @error-case-case @FEAT-001-er4
  Scenario: Duplicate email registration
    Given a user with email "nav@test.com" already exists
    When admin submits registration with email "nav@test.com"
    Then the response status is 409 Conflict
    And the error indicates the email is already registered
    And no existing user data is modified

  @error-case-case @FEAT-001-er5
  Scenario: Expired refresh token
    Given a refresh token that has expired (past 7-day window)
    When the user submits it to POST /auth/refresh
    Then the response status is 401
    And the error is "token_expired"
    And the user must re-authenticate via POST /auth/login

  @error-case-case @FEAT-001-er6
  Scenario: Invalid JWT format
    Given a malformed JWT string "not.a.valid-jwt"
    When a request is made with Authorization: Bearer not.a.valid-jwt
    Then the response status is 401
    And the error is "invalid_token"

  @error-case-case @FEAT-001-er7
  Scenario: Missing Authorization header on protected endpoint
    Given no Authorization header is provided
    When a request is made to GET /patients
    Then the response status is 401
    And the error is "missing_authentication"

  @error-case-case @FEAT-001-er8
  Scenario: Non-admin attempts user management
    Given an authenticated user with role "navigator"
    When they submit GET /admin/users
    Then the response status is 403
    And the error is "insufficient_permissions"
    And the attempt is logged in the audit log

  @error-case-case @FEAT-001-er9
  Scenario: Volunteer attempts write operation
    Given an authenticated user with role "volunteer"
    When they submit POST /patients with valid data
    Then the response status is 403
    And the error is "insufficient_permissions"
    And no patient record is created

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-001-s1
  Scenario: Password stored as bcrypt hash, never plaintext
    Given a user registers with password "MySecretPass123!"
    When the user record is examined in the database
    Then the password_hash field contains a bcrypt hash (starts with "$2b$12$")
    And the plaintext password "MySecretPass123!" is not stored anywhere
    And the password_hash is never included in any API response

  @security @FEAT-001-s2
  Scenario: JWT tampering is detected and rejected
    Given a valid JWT access token for user "nav@test.com"
    When the payload is modified (e.g., role changed from "navigator" to "admin")
    And the modified token is used in a request
    Then the response status is 401
    And the error is "invalid_token"
    And no elevated access is granted

  @security @FEAT-001-s3
  Scenario: Brute-force rate limiting on login
    Given a registered user "nav@test.com"
    When 5 consecutive failed login attempts are made within 10 minutes
    Then each attempt returns 401 up to the 5th attempt
    When a 6th attempt is made within the 10-minute window
    Then the response status is 429
    And the response includes a Retry-After header
    And all 6 attempts are recorded in the audit log

  @security @FEAT-001-s4
  Scenario: Refresh token reuse detection (possible compromise)
    Given a valid refresh token that has already been used for rotation
    When the same refresh token is submitted again to POST /auth/refresh
    Then all refresh tokens for that user are invalidated
    And the user must re-authenticate via login
    And a security event is recorded with action "security.token_reuse_detected"

  @security @FEAT-001-s5
  Scenario: RBAC enforcement across all modules
    Given an authenticated user with role "volunteer"
    Then they CANNOT access the following:
      | endpoint                    | method | reason                          |
      | /patients (create)          | POST   | permission: patients=write      |
      | /documents (upload)         | POST   | permission: documents=full      |
      | /ai/summarize               | POST   | permission: ai=full             |
      | /admin/users                | GET    | permission: users=full          |
      | /admin/audit-log            | GET    | permission: audit=full          |
    And each denied request returns 403

  @security @FEAT-001-s6
  Scenario: Clinician cannot create or modify resources
    Given an authenticated user with role "clinician"
    Then they CAN:
      | endpoint                | method | reason                  |
      | /patients               | GET    | permission: patients=read |
      | /cases                  | GET    | permission: cases=read    |
      | /ai/summarize           | GET    | permission: ai=review     |
      | /cases/{id}/reviews     | POST   | permission: ai=review     |
    And they CANNOT:
      | endpoint                | method | reason                  |
      | /patients               | POST   | permission: patients=read (not full) |
      | /cases                  | POST   | permission: cases=read (not full)    |

  @security @FEAT-001-s7
  Scenario: Input sanitization — injection prevention on login
    Given a login request with email containing "<injection>"
    When the request is submitted to POST /auth/login
    Then the payload is rejected or sanitized
    And the malicious content is never executed or persisted as-is

    Examples:
      | injection                          |
      | <script>alert('xss')</script>      |
      | '; DROP TABLE users; --            |
      | ${7*7}                             |
      | admin" OR 1=1 --                   |

  @security @FEAT-001-s8
  Scenario: Audit log is INSERT-only (tamper-proof)
    Given an existing audit log entry with id "log-123"
    When any attempt is made to UPDATE or DELETE the entry
    Then the operation is rejected at the database level
    And the audit log entry remains unchanged

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-001-p1
  Scenario: Login response time under normal load
    Given 50 concurrent users are logging in
    When each user submits POST /auth/login
    Then 95th percentile response time is under 500ms
    And 99th percentile response time is under 1000ms
    And error rate does not exceed 0.1%

  @performance @FEAT-001-p2
  Scenario: RBAC permission check adds minimal overhead
    Given an authenticated user making API requests
    When the RBAC middleware checks permissions on each request
    Then the permission check adds less than 5ms to request latency
    And role permissions are cached for the duration of the request

  @performance @FEAT-001-p3
  Scenario: Admin user list with pagination
    Given 1000 users in the system
    When admin requests GET /admin/users?page=1&limit=20
    Then the response time is under 200ms
    And the response contains exactly 20 user records
    And pagination metadata is correct

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-001-o1
  Scenario: Authentication events are audited
    When any authentication action occurs (login, logout, register, token_refresh, login_failure)
    Then a structured audit event is emitted with:
      | field       | value                              |
      | event_type  | auth.<action>.completed/failed     |
      | user_id     | [affected user id]                 |
      | actor_id    | [initiating user id or anonymous]  |
      | ip_address  | [request source IP]                |
      | user_agent  | [request User-Agent]               |
      | timestamp   | [ISO 8601 UTC]                     |
    And the event is written to the activities table
    And the event is also written to the application log file

  @observability @FEAT-001-o2
  Scenario: RBAC denial events are audited
    When a user attempts an action they lack permission for
    Then an audit event is emitted with:
      | field         | value                            |
      | event_type    | auth.rbac.denied                 |
      | user_id       | [requesting user id]             |
      | required_perm | [required permission, e.g. "patients:write"] |
      | user_role     | [user's current role]            |
      | endpoint      | [attempted endpoint]             |
      | timestamp     | [ISO 8601 UTC]                   |

  # ─────────────────────────────────────────────
  # ACCEPTANCE CRITERIA SUMMARY
  # ─────────────────────────────────────────────

  # AC-1: Admin can register users with email, password, full_name, and role — Covered by: Scenario "Admin registers a new navigator user" @FEAT-001-h1
  # AC-2: Users can login and receive JWT access token (30min) + refresh token (7d) — Covered by: Scenario "Successful login" @FEAT-001-h2
  # AC-3: Every API endpoint enforces role-based permissions matching roles.permissions matrix — Covered by: Scenarios @FEAT-001-h6, @FEAT-001-s5, @FEAT-001-s6
  # AC-4: All auth events (login, logout, failure, role change) are recorded in audit log — Covered by: Scenarios @FEAT-001-o1, @FEAT-001-o2
  # AC-5: Failed login attempts are rate-limited (5 per 10 min, then 429 with Retry-After) — Covered by: Scenario @FEAT-001-s3
  # AC-6: Passwords stored as bcrypt hash, never returned in API responses — Covered by: Scenario @FEAT-001-s1
  # AC-7: JWT tampering detected, refresh token reuse triggers full session invalidation — Covered by: Scenarios @FEAT-001-s2, @FEAT-001-s4
  # AC-8: Admin can list users, change roles, disable accounts; role changes invalidate tokens — Covered by: Scenarios @FEAT-001-h7, @FEAT-001-h8, @FEAT-001-ec6, @FEAT-001-ec7
