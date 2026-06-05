# Spec: FEAT-004 — Document Management
# File: specs/features/FEAT-004-document-management.feature
# Relates: API-030..037, DATA-005

import pytest
from httpx import AsyncClient

pytestmark = pytest.mark.asyncio


# ===================================================================
# HAPPY PATH
# ===================================================================

class TestHappyPath:
    """FEAT-004 happy-path scenarios (h1–h8)."""

    @pytest.mark.spec("FEAT-004-h1")
    async def test_FEAT_004_h1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Navigator uploads a PDF document to a case.

        Given an authenticated navigator and case "c-001" exists
        When they submit POST /cases/c-001/documents/upload with a PDF file
        Then the response status is 201
        And a document record is created with correct metadata
        And the file is stored with a UUID-based sanitized filename
        """
        case_id = "c-001"  # TODO: use seeded case id

        # TODO: create actual test file for upload
        files = {"file": ("biopsy_report.pdf", b"fake-pdf-content", "application/pdf")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-004-h2")
    async def test_FEAT_004_h2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        List documents for a case.

        Given case "c-001" has 3 uploaded documents
        When they submit GET /cases/c-001/documents
        Then the response contains 3 document entries
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.get(
            f"/cases/{case_id}/documents",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-h3")
    async def test_FEAT_004_h3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get document metadata.

        Given a document exists with id "d-001"
        When they submit GET /documents/d-001
        Then the response contains all metadata
        And the response does NOT contain ocr_text
        """
        doc_id = "d-001"  # TODO: use seeded document id

        response = await async_client.get(
            f"/documents/{doc_id}",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-h4")
    async def test_FEAT_004_h4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Download original document file.

        Given a PDF document exists with id "d-001"
        When they submit GET /documents/d-001/download
        Then the response contains raw file bytes
        And Content-Type matches the document's mime_type
        And Content-Disposition is "attachment"
        """
        doc_id = "d-001"  # TODO: use seeded document id

        response = await async_client.get(
            f"/documents/{doc_id}/download",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-h5")
    async def test_FEAT_004_h5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Preview document inline (PDF).

        Given a PDF document exists with id "d-001"
        When they submit GET /documents/d-001/preview
        Then Content-Disposition is "inline"
        And Content-Type is "application/pdf"
        """
        doc_id = "d-001"  # TODO: use seeded document id

        response = await async_client.get(
            f"/documents/{doc_id}/preview",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-h6")
    async def test_FEAT_004_h6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Trigger OCR extraction on a document.

        Given a document exists with id "d-001" and ocr_status "pending"
        When they submit POST /documents/d-001/ocr
        Then the response status is 202
        And ocr_status is updated to "processing"
        And upon completion ocr_status becomes "completed" and ocr_text is populated
        """
        doc_id = "d-001"  # TODO: use seeded document id

        response = await async_client.post(
            f"/documents/{doc_id}/ocr",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions including async completion
        assert response.status_code == 202

    @pytest.mark.spec("FEAT-004-h7")
    async def test_FEAT_004_h7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get OCR results for a document.

        Given a document with ocr_status "completed" and ocr_text populated
        When they submit GET /documents/d-001/ocr
        Then the response contains ocr_text with extracted content
        """
        doc_id = "d-001"  # TODO: use seeded document with completed OCR

        response = await async_client.get(
            f"/documents/{doc_id}/ocr",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-h8")
    async def test_FEAT_004_h8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Soft-delete a document.

        Given a document exists with id "d-001"
        When they submit DELETE /documents/d-001
        Then the response status is 204
        And the document no longer appears in listings
        And the physical file remains on disk
        """
        doc_id = "d-001"  # TODO: use seeded document id

        response = await async_client.delete(
            f"/documents/{doc_id}",
            headers=auth_headers_navigator,
        )

        # TODO: Implement assertions
        assert response.status_code == 204


# ===================================================================
# EDGE CASES
# ===================================================================

class TestEdgeCases:
    """FEAT-004 edge-case scenarios (ec1–ec8)."""

    @pytest.mark.spec("FEAT-004-ec1")
    async def test_FEAT_004_ec1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload JPG image document.

        Given an authenticated navigator
        When they upload a JPG file
        Then the response status is 201
        And file_type is "jpg", mime_type is "image/jpeg"
        """
        case_id = "c-001"  # TODO: use seeded case id
        files = {"file": ("scan_result.jpg", b"fake-jpg-content", "image/jpeg")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-004-ec2")
    async def test_FEAT_004_ec2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload DOCX document.

        Given an authenticated navigator
        When they upload a DOCX file
        Then the response status is 201
        And file_type is "docx"
        """
        case_id = "c-001"  # TODO: use seeded case id
        files = {"file": (
            "referral_letter.docx",
            b"fake-docx-content",
            "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 201

    @pytest.mark.spec("FEAT-004-ec3")
    async def test_FEAT_004_ec3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload file at exactly 25MB limit.

        Given an authenticated navigator
        When they upload a 25MB file
        Then the response status is 201
        """
        case_id = "c-001"  # TODO: use seeded case id
        # TODO: generate exactly 25MB test file
        # content = b"\x00" * 26214400
        # files = {"file": ("large.pdf", content, "application/pdf")}
        # response = await async_client.post(...)
        assert True

    @pytest.mark.spec("FEAT-004-ec4")
    async def test_FEAT_004_ec4(
        self,
        async_client: AsyncClient,
        auth_headers_clinician: dict,
    ):
        """
        Preview an image document inline.

        Given a JPG document exists
        And an authenticated clinician
        When they submit GET /documents/d-img/preview
        Then Content-Type is "image/jpeg" and Content-Disposition is "inline"
        """
        doc_id = "d-img"  # TODO: use seeded image document id

        response = await async_client.get(
            f"/documents/{doc_id}/preview",
            headers=auth_headers_clinician,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-ec5")
    async def test_FEAT_004_ec5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        OCR status transitions from pending to processing to completed.

        Given a document with ocr_status "pending"
        When OCR is triggered -> "processing"
        When OCR completes -> "completed"
        Then ocr_text contains extracted text and ocr_processed_at is set
        """
        # TODO: Implement OCR status transition test
        assert True

    @pytest.mark.spec("FEAT-004-ec6")
    async def test_FEAT_004_ec6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        OCR fails on corrupted file.

        Given a corrupted document exists
        When OCR is triggered and fails
        Then ocr_status becomes "failed"
        And ocr_text remains null
        And the error is logged
        """
        # TODO: Implement OCR failure test
        assert True

    @pytest.mark.spec("FEAT-004-ec7")
    async def test_FEAT_004_ec7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Query OCR status while processing.

        Given a document with ocr_status "processing"
        When they submit GET /documents/d-001/ocr
        Then ocr_status is "processing" and ocr_text is null
        """
        doc_id = "d-001"  # TODO: use seeded document with processing status

        response = await async_client.get(
            f"/documents/{doc_id}/ocr",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-ec8")
    async def test_FEAT_004_ec8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Filename with special characters is sanitized.

        Given an authenticated navigator
        When they upload a file named "../../../etc/passwd.pdf"
        Then original_filename stores the name as-is
        And stored_filename uses a UUID-based name (no path traversal)
        """
        case_id = "c-001"  # TODO: use seeded case id
        files = {"file": ("../../../etc/passwd.pdf", b"fake-content", "application/pdf")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions verifying sanitized storage
        assert response.status_code == 201


# ===================================================================
# ERROR CASES
# ===================================================================

class TestErrorCases:
    """FEAT-004 error-case scenarios (e1–e8)."""

    @pytest.mark.spec("FEAT-004-e1")
    async def test_FEAT_004_e1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload file exceeding 25MB limit.

        Given an authenticated navigator
        When they upload a 26MB file
        Then the response status is 413
        """
        case_id = "c-001"  # TODO: use seeded case id
        # TODO: generate 26MB file and upload
        # content = b"\x00" * (26 * 1024 * 1024)
        # files = {"file": ("huge.pdf", content, "application/pdf")}
        # response = await async_client.post(...)
        assert True

    @pytest.mark.spec("FEAT-004-e2")
    async def test_FEAT_004_e2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload unsupported file type (.txt).

        Given an authenticated navigator
        When they upload a .txt file
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id
        files = {"file": ("notes.txt", b"plain text", "text/plain")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-004-e3")
    async def test_FEAT_004_e3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload to non-existent case.

        Given an authenticated navigator
        When they upload to a non-existent case
        Then the response status is 404
        """
        files = {"file": ("test.pdf", b"content", "application/pdf")}

        response = await async_client.post(
            "/cases/00000000-0000-0000-0000-000000000000/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 404

    @pytest.mark.spec("FEAT-004-e4")
    async def test_FEAT_004_e4(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Upload without file attachment.

        Given an authenticated navigator
        When they submit POST with no file field
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-004-e5")
    async def test_FEAT_004_e5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        MIME type mismatch (renamed executable).

        Given an authenticated navigator
        When they upload a file named "malware.pdf" but actual content is executable
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id
        # Actual executable content declared as PDF
        files = {"file": ("malware.pdf", b"\x7fELF", "application/pdf")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-004-e6")
    async def test_FEAT_004_e6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Get non-existent document.

        Given an authenticated navigator
        When they submit GET /documents/{non-existent}
        Then the response status is 404
        """
        response = await async_client.get(
            "/documents/00000000-0000-0000-0000-000000000000",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 404

    @pytest.mark.spec("FEAT-004-e7")
    async def test_FEAT_004_e7(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Trigger OCR on already completed document.

        Given a document with ocr_status "completed"
        When they submit POST /documents/d-001/ocr
        Then the response status is 200 (idempotent)
        And ocr_status remains "completed"
        """
        doc_id = "d-001"  # TODO: use seeded document with completed OCR

        response = await async_client.post(
            f"/documents/{doc_id}/ocr",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 200

    @pytest.mark.spec("FEAT-004-e8")
    async def test_FEAT_004_e8(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Download soft-deleted document.

        Given a soft-deleted document
        When they submit GET /documents/d-del/download
        Then the response status is 404
        """
        doc_id = "d-del"  # TODO: use seeded soft-deleted document id

        response = await async_client.get(
            f"/documents/{doc_id}/download",
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 404


# ===================================================================
# SECURITY
# ===================================================================

class TestSecurity:
    """FEAT-004 security scenarios (s1–s8)."""

    @pytest.mark.spec("FEAT-004-s1")
    async def test_FEAT_004_s1(
        self,
        async_client: AsyncClient,
        auth_headers_volunteer: dict,
    ):
        """
        Volunteer cannot upload documents.

        Given an authenticated volunteer
        When they submit POST /cases/c-001/documents/upload
        Then the response status is 403
        """
        files = {"file": ("test.pdf", b"content", "application/pdf")}

        response = await async_client.post(
            "/cases/c-001/documents/upload",
            files=files,
            headers=auth_headers_volunteer,
        )
        # TODO: Implement assertions
        assert response.status_code == 403

    @pytest.mark.spec("FEAT-004-s2")
    async def test_FEAT_004_s2(
        self,
        async_client: AsyncClient,
        auth_headers_volunteer: dict,
    ):
        """
        Volunteer cannot list documents.

        Given an authenticated volunteer
        When they submit GET /cases/c-001/documents
        Then the response status is 403
        """
        response = await async_client.get(
            "/cases/c-001/documents",
            headers=auth_headers_volunteer,
        )
        # TODO: Implement assertions
        assert response.status_code == 403

    @pytest.mark.spec("FEAT-004-s3")
    async def test_FEAT_004_s3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Path traversal prevention in filename.

        Given an authenticated navigator
        When they upload a file named "../../etc/shadow"
        Then stored_filename is a UUID (no directory components)
        And no file is written outside the designated upload directory
        """
        # TODO: Implement test verifying path traversal is blocked
        assert True

    @pytest.mark.spec("FEAT-004-s4")
    async def test_FEAT_004_s4(
        self,
        async_client: AsyncClient,
    ):
        """
        Unauthenticated upload rejected.

        Given no authentication token
        When they submit POST /cases/c-001/documents/upload
        Then the response status is 401
        """
        files = {"file": ("test.pdf", b"content", "application/pdf")}

        response = await async_client.post(
            "/cases/c-001/documents/upload",
            files=files,
        )
        # TODO: Implement assertions
        assert response.status_code == 401

    @pytest.mark.spec("FEAT-004-s5")
    async def test_FEAT_004_s5(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        MIME type spoofing prevention.

        Given an authenticated navigator
        When they upload a file claiming to be image/jpeg but containing HTML/JS
        Then the response status is 422
        """
        case_id = "c-001"  # TODO: use seeded case id
        html_content = b"<html><script>alert('xss')</script></html>"
        files = {"file": ("fake.jpg", html_content, "image/jpeg")}

        response = await async_client.post(
            f"/cases/{case_id}/documents/upload",
            files=files,
            headers=auth_headers_navigator,
        )
        # TODO: Implement assertions
        assert response.status_code == 422

    @pytest.mark.spec("FEAT-004-s6")
    async def test_FEAT_004_s6(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Stored filename is never user-controlled.

        Given an authenticated navigator
        When they upload a document
        Then stored_filename is a system-generated UUID with extension
        And the physical file path cannot be influenced by user input
        """
        # TODO: Implement test verifying UUID-based storage
        assert True

    @pytest.mark.spec("FEAT-004-s7")
    async def test_FEAT_004_s7(
        self,
        async_client: AsyncClient,
        auth_headers_clinician: dict,
    ):
        """
        Clinician read-only access to documents.

        Given a document exists and an authenticated clinician
        When they submit GET /documents/d-001 -> 200
        When they submit DELETE /documents/d-001 -> 403
        """
        doc_id = "d-001"  # TODO: use seeded document id

        get_response = await async_client.get(
            f"/documents/{doc_id}",
            headers=auth_headers_clinician,
        )
        delete_response = await async_client.delete(
            f"/documents/{doc_id}",
            headers=auth_headers_clinician,
        )
        # TODO: Implement assertions
        assert get_response.status_code == 200
        assert delete_response.status_code == 403

    @pytest.mark.spec("FEAT-004-s8")
    async def test_FEAT_004_s8(self):
        """
        Upload directory not web-accessible.

        Given the filesystem upload directory
        Then it is not served by Nginx as a static path
        And downloads are served only through authenticated API endpoint
        """
        # This is a deployment/infrastructure test, not an API test.
        # Verify via configuration review or integration environment check.
        # TODO: Implement configuration-based assertion
        assert True


# ===================================================================
# PERFORMANCE
# ===================================================================

class TestPerformance:
    """FEAT-004 performance scenarios (p1–p3)."""

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-004-p1")
    async def test_FEAT_004_p1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Document upload under 500ms (excluding OCR).

        Given an authenticated navigator
        When they upload a 5MB PDF
        Then the response time is under 500ms at the 95th percentile
        """
        # TODO: Implement performance test
        assert True

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-004-p2")
    async def test_FEAT_004_p2(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Document list under 200ms with 100 documents.

        Given a case with 100 uploaded documents
        When they submit GET /cases/c-001/documents
        Then the response time is under 200ms at the 95th percentile
        """
        # TODO: Implement performance test
        assert True

    @pytest.mark.performance
    @pytest.mark.spec("FEAT-004-p3")
    async def test_FEAT_004_p3(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        OCR processing completes within 30 seconds for 10-page PDF.

        Given a 10-page PDF document (5MB)
        When OCR is triggered
        Then ocr_status transitions to "completed" within 30 seconds
        """
        # TODO: Implement performance test with real OCR
        assert True


# ===================================================================
# OBSERVABILITY
# ===================================================================

class TestObservability:
    """FEAT-004 observability scenarios (o1–o2)."""

    @pytest.mark.observability
    @pytest.mark.spec("FEAT-004-o1")
    async def test_FEAT_004_o1(
        self,
        async_client: AsyncClient,
        auth_headers_navigator: dict,
    ):
        """
        Document lifecycle events are logged.

        Given an authenticated navigator
        When they upload, trigger OCR, and delete a document
        Then activity events are logged for:
          - document.uploaded, document.ocr_run, document.deleted
        """
        # TODO: Implement lifecycle audit verification
        assert True

    @pytest.mark.observability
    @pytest.mark.spec("FEAT-004-o2")
    async def test_FEAT_004_o2(
        self,
        async_client: AsyncClient,
    ):
        """
        OCR failure is logged with error details.

        Given OCR processing fails for a document
        Then an error log entry is created with document_id, ocr_status, error_message, timestamp
        """
        # TODO: Implement OCR failure logging verification
        assert True
