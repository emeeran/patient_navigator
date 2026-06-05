---
id: FEAT-004
title: "Document Management"
status: DRAFT
version: 1.0.0
owner: "@platform-team"
authors:
  - "@platform-team"
reviewers: []
created: "2026-06-04"
updated: "2026-06-04"
relates_to:
  - DATA-005
  - API-030
  - API-031
  - API-032
  - API-033
  - API-034
  - API-035
  - API-036
  - API-037
  - FEAT-001
  - FEAT-003
supersedes: null
tags:
  - documents
  - upload
  - ocr
  - paddleocr
  - file-storage
---

# Feature: Document Management

  As a navigator,
  I want to upload medical documents to a case and extract text via OCR,
  So that patient records are digitized and available for AI-powered summarization.

  ## Scope

  ### In scope
  - Upload documents (PDF, JPG, JPEG, PNG, DOCX) to a case via multipart form
  - File type validation and size limit (max 25MB)
  - Sanitized filenames (UUID-based storage names)
  - List documents for a case
  - Get document metadata
  - Download original file
  - Inline preview (for images and PDFs)
  - Soft-delete documents
  - Trigger OCR extraction on uploaded documents
  - Query OCR status and extracted text
  - Asynchronous OCR processing (status: pending → processing → completed/failed)
  - MIME type validation (content-type header matches actual file content)

  ### Out of scope
  - Versioned documents / revision history
  - Document annotation or markup
  - Batch upload (one file per request in V1)
  - Direct patient document upload (navigator uploads on behalf)
  - Document sharing via email or external link
  - OCR for handwritten notes (V2)

  ## Glossary

  | Term | Definition |
  |------|------------|
  | OCR | Optical Character Recognition — extracting text from scanned documents/images via PaddleOCR |
  | Stored Filename | UUID-based sanitized filename used for filesystem storage (never the user's original filename) |
  | MIME Type | Multipurpose Internet Mail Extensions type — validated against actual file content, not just extension |
  | Inline Preview | Browser-renderable preview via Content-Disposition: inline for PDFs and images |

  ---

  Background:
    Given the system is in a healthy operational state
    And the following roles exist with their permission sets:
      | role      | documents |
      | admin     | full      |
      | navigator | full      |
      | clinician | read      |
      | volunteer | none      |
      | patient   | own       |
    And the following users exist:
      | email            | role      | state  |
      | admin@test.com   | admin     | active |
      | nav@test.com     | navigator | active |
      | clin@test.com    | clinician | active |
      | vol@test.com     | volunteer | active |
    And the following cases exist:
      | id    | patient_id | diagnosis            |
      | c-001 | p-001      | Stage 2B Oral Cancer |

  # ─────────────────────────────────────────────
  # HAPPY PATH
  # ─────────────────────────────────────────────

  @happy-path @smoke @FEAT-004-h1
  Scenario: Navigator uploads a PDF document to a case
    Given an authenticated user with role "navigator"
    And case "c-001" exists
    When they submit POST /cases/c-001/documents/upload with multipart form:
      | field | value                              |
      | file  | biopsy_report.pdf (application/pdf, 2.4MB) |
    Then the response status is 201
    And a document record is created with:
      | field              | value                          |
      | original_filename  | biopsy_report.pdf              |
      | file_type          | pdf                            |
      | file_size_bytes    | 2516582                        |
      | mime_type          | application/pdf                |
      | ocr_status         | pending                        |
      | uploaded_by        | the navigator's user ID        |
    And the file is stored with a UUID-based sanitized filename
    And the stored file is saved to the configured filesystem directory

  @happy-path @smoke @FEAT-004-h2
  Scenario: List documents for a case
    Given case "c-001" has 3 uploaded documents
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/documents
    Then the response status is 200
    And the response contains 3 document entries
    And each entry includes: id, original_filename, file_type, file_size_bytes, ocr_status, uploaded_by, created_at

  @happy-path @FEAT-004-h3
  Scenario: Get document metadata
    Given a document exists with id "d-001" for case "c-001"
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-001
    Then the response status is 200
    And the response contains all metadata: id, case_id, original_filename, file_type, file_size_bytes, mime_type, ocr_status, ocr_processed_at, uploaded_by, created_at, updated_at
    And the response does NOT contain ocr_text (use /documents/d-001/ocr for that)

  @happy-path @FEAT-004-h4
  Scenario: Download original document file
    Given a PDF document exists with id "d-001"
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-001/download
    Then the response status is 200
    And the Content-Type header matches the document's mime_type
    And the Content-Disposition header is "attachment; filename=\"biopsy_report.pdf\""
    And the response body is the raw file bytes

  @happy-path @FEAT-004-h5
  Scenario: Preview document inline (PDF)
    Given a PDF document exists with id "d-001"
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-001/preview
    Then the response status is 200
    And the Content-Type header is "application/pdf"
    And the Content-Disposition header is "inline; filename=\"biopsy_report.pdf\""

  @happy-path @FEAT-004-h6
  Scenario: Trigger OCR extraction on a document
    Given a document exists with id "d-001" and ocr_status "pending"
    And an authenticated user with role "navigator"
    When they submit POST /documents/d-001/ocr
    Then the response status is 202
    And ocr_status is updated to "processing"
    And OCR processing runs asynchronously via PaddleOCR
    And upon completion, ocr_status becomes "completed" and ocr_text is populated
    And ocr_processed_at is set to the completion timestamp

  @happy-path @FEAT-004-h7
  Scenario: Get OCR results for a document
    Given a document exists with id "d-001" and ocr_status "completed" and ocr_text "Biopsy shows squamous cell carcinoma..."
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-001/ocr
    Then the response status is 200
    And the response contains ocr_text with the extracted content
    And the response contains ocr_status "completed" and ocr_processed_at

  @happy-path @FEAT-004-h8
  Scenario: Soft-delete a document
    Given a document exists with id "d-001"
    And an authenticated user with role "navigator"
    When they submit DELETE /documents/d-001
    Then the response status is 204
    And the document's deleted_at is set to current timestamp
    And the document no longer appears in GET /cases/c-001/documents
    And the physical file remains on disk (retained for compliance)

  # ─────────────────────────────────────────────
  # EDGE CASES
  # ─────────────────────────────────────────────

  @edge-case @FEAT-004-ec1
  Scenario: Upload JPG image document
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with:
      | field | value                          |
      | file  | scan_result.jpg (image/jpeg, 800KB) |
    Then the response status is 201
    And file_type is "jpg"
    And mime_type is "image/jpeg"

  @edge-case @FEAT-004-ec2
  Scenario: Upload DOCX document
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with:
      | field | value                                       |
      | file  | referral_letter.docx (application/vnd.openxmlformats-officedocument.wordprocessingml.document, 150KB) |
    Then the response status is 201
    And file_type is "docx"

  @edge-case @FEAT-004-ec3
  Scenario: Upload file at exactly 25MB limit
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with a 25MB PDF file
    Then the response status is 201
    And file_size_bytes is 26214400

  @edge-case @FEAT-004-ec4
  Scenario: Preview an image document inline
    Given a JPG document exists with id "d-img"
    And an authenticated user with role "clinician"
    When they submit GET /documents/d-img/preview
    Then the response status is 200
    And the Content-Type header is "image/jpeg"
    And the Content-Disposition header is "inline"

  @edge-case @FEAT-004-ec5
  Scenario: OCR status transitions from pending to processing to completed
    Given a document exists with id "d-001" and ocr_status "pending"
    When OCR is triggered
    Then ocr_status becomes "processing"
    When OCR completes successfully
    Then ocr_status becomes "completed"
    And ocr_text contains extracted text
    And ocr_processed_at is set

  @edge-case @FEAT-004-ec6
  Scenario: OCR fails on corrupted file
    Given a corrupted document exists with id "d-bad" and ocr_status "pending"
    When OCR is triggered and fails
    Then ocr_status becomes "failed"
    And ocr_text remains null
    And the error is logged for observability

  @edge-case @FEAT-004-ec7
  Scenario: Query OCR status while processing
    Given a document exists with id "d-001" and ocr_status "processing"
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-001/ocr
    Then the response status is 200
    And ocr_status is "processing"
    And ocr_text is null

  @edge-case @FEAT-004-ec8
  Scenario: Filename with special characters is sanitized
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with file named "../../../etc/passwd.pdf"
    Then the response status is 201
    And original_filename stores "../../../etc/passwd.pdf" as-is
    And stored_filename uses a UUID-based name (no path traversal)
    And the file is stored safely in the designated upload directory

  # ─────────────────────────────────────────────
  # ERROR CASES
  # ─────────────────────────────────────────────

  @error-case-case @FEAT-004-e1
  Scenario: Upload file exceeding 25MB limit
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with a 26MB file
    Then the response status is 413
    And the error message indicates file size exceeds 25MB limit

  @error-case-case @FEAT-004-e2
  Scenario: Upload unsupported file type (.txt)
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with a .txt file
    Then the response status is 422
    And the error message indicates supported types: pdf, jpg, jpeg, png, docx

  @error-case-case @FEAT-004-e3
  Scenario: Upload to non-existent case
    Given an authenticated user with role "navigator"
    When they submit POST /cases/00000000-0000-0000-0000-000000000000/documents/upload with valid file
    Then the response status is 404

  @error-case-case @FEAT-004-e4
  Scenario: Upload without file attachment
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with no file field
    Then the response status is 422
    And the error message indicates "file" field is required

  @error-case-case @FEAT-004-e5
  Scenario: MIME type mismatch (renamed executable)
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with file named "malware.pdf" but actual content is application/x-executable
    Then the response status is 422
    And the error message indicates MIME type validation failed

  @error-case-case @FEAT-004-e6
  Scenario: Get non-existent document
    Given an authenticated user with role "navigator"
    When they submit GET /documents/00000000-0000-0000-0000-000000000000
    Then the response status is 404

  @error-case-case @FEAT-004-e7
  Scenario: Trigger OCR on already completed document
    Given a document exists with id "d-001" and ocr_status "completed"
    And an authenticated user with role "navigator"
    When they submit POST /documents/d-001/ocr
    Then the response status is 200
    And ocr_status remains "completed"
    And ocr_text is unchanged (idempotent re-trigger returns existing result)

  @error-case-case @FEAT-004-e8
  Scenario: Download soft-deleted document
    Given a soft-deleted document with id "d-del"
    And an authenticated user with role "navigator"
    When they submit GET /documents/d-del/download
    Then the response status is 404

  # ─────────────────────────────────────────────
  # SECURITY
  # ─────────────────────────────────────────────

  @security @FEAT-004-s1
  Scenario: Volunteer cannot upload documents
    Given an authenticated user with role "volunteer"
    When they submit POST /cases/c-001/documents/upload with valid file
    Then the response status is 403

  @security @FEAT-004-s2
  Scenario: Volunteer cannot list documents
    Given an authenticated user with role "volunteer"
    When they submit GET /cases/c-001/documents
    Then the response status is 403

  @security @FEAT-004-s3
  Scenario: Path traversal prevention in filename
    Given an authenticated user with role "navigator"
    When they upload a file named "../../etc/shadow"
    Then the stored_filename is a UUID (no directory components)
    And no file is written outside the designated upload directory

  @security @FEAT-004-s4
  Scenario: Unauthenticated upload rejected
    Given no authentication token is provided
    When they submit POST /cases/c-001/documents/upload
    Then the response status is 401

  @security @FEAT-004-s5
  Scenario: MIME type spoofing prevention
    Given an authenticated user with role "navigator"
    When they submit POST /cases/c-001/documents/upload with file claiming to be image/jpeg but containing HTML/JS content
    Then the response status is 422
    And the file is rejected (actual content does not match declared MIME type)

  @security @FEAT-004-s6
  Scenario: Stored filename is never user-controlled
    Given an authenticated user with role "navigator"
    When they upload a document
    Then stored_filename is a system-generated UUID with extension
    And original_filename is stored separately for display only
    And the physical file path cannot be influenced by user input

  @security @FEAT-004-s7
  Scenario: Clinician read-only access to documents
    Given a document exists with id "d-001"
    And an authenticated user with role "clinician"
    When they submit GET /documents/d-001
    Then the response status is 200
    When they submit DELETE /documents/d-001
    Then the response status is 403

  @security @FEAT-004-s8
  Scenario: Upload directory not web-accessible
    Given the filesystem upload directory
    Then the directory is not served by Nginx as a static path
    And document downloads are served only through the authenticated API endpoint

  # ─────────────────────────────────────────────
  # PERFORMANCE
  # ─────────────────────────────────────────────

  @performance @FEAT-004-p1
  Scenario: Document upload under 500ms (excluding OCR)
    Given an authenticated user with role "navigator"
    When they upload a 5MB PDF document
    Then the response time is under 500ms at the 95th percentile
    Including: validation, file write, database record creation
    Excluding: OCR processing (runs asynchronously)

  @performance @FEAT-004-p2
  Scenario: Document list under 200ms with 100 documents
    Given a case with 100 uploaded documents
    And an authenticated user with role "navigator"
    When they submit GET /cases/c-001/documents
    Then the response time is under 200ms at the 95th percentile

  @performance @FEAT-004-p3
  Scenario: OCR processing completes within 30 seconds for 10-page PDF
    Given a 10-page PDF document (5MB)
    When OCR is triggered
    Then ocr_status transitions to "completed" within 30 seconds
    And ocr_text contains extracted text from all pages

  # ─────────────────────────────────────────────
  # OBSERVABILITY
  # ─────────────────────────────────────────────

  @observability @FEAT-004-o1
  Scenario: Document lifecycle events are logged
    Given an authenticated user with role "navigator"
    When they upload, trigger OCR, and delete a document
    Then the following activity events are logged:
      | action              | entity_type |
      | document.uploaded   | document    |
      | document.ocr_run    | document    |
      | document.deleted    | document    |

  @observability @FEAT-004-o2
  Scenario: OCR failure is logged with error details
    Given OCR processing fails for document "d-bad"
    Then an error log entry is created with:
      | field         | value                |
      | document_id   | d-bad                |
      | ocr_status    | failed               |
      | error_message | PaddleOCR error details |
      | timestamp     | current UTC time     |
