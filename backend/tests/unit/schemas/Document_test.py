# Spec: DATA-005
# Schema: Document
# File: specs/data/Document.schema.json
# API Refs: API-030..037
# Description: A medical document uploaded to a case with OCR processing tracking.

"""
Schema validation tests for the Document entity.
@spec DATA-005
@file specs/data/Document.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Document.schema.json"


@pytest.fixture
def document_schema():
    """Load the Document JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(document_schema):
    """Create a Draft202012Validator for the Document schema."""
    return Draft202012Validator(document_schema)


@pytest.fixture
def valid_document_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "dd0e8400-e29b-41d4-a716-446655440008",
        "caseId": "880e8400-e29b-41d4-a716-446655440003",
        "originalFilename": "biopsy_report.pdf",
        "storedFilename": "a1b2c3d4-e5f6-7890-abcd-ef1234567890.pdf",
        "fileType": "pdf",
        "fileSizeBytes": 2516582,
        "mimeType": "application/pdf",
        "ocrText": "Biopsy report shows moderately differentiated squamous cell carcinoma...",
        "ocrStatus": "completed",
        "ocrProcessedAt": "2026-06-04T10:05:00.000Z",
        "uploadedBy": "660e8400-e29b-41d4-a716-446655440001",
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:05:00.000Z",
        "deletedAt": None,
    }


@pytest.mark.spec("DATA-005")
class TestDocumentSchema:
    """Validation tests for Document.schema.json (DATA-005)."""

    def test_valid_complete_instance(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-1
        A complete Document instance should pass validation.
        """
        result = validator.validate(valid_document_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-005-2
        An empty dict should fail because required fields are missing.
        Required: id, caseId, originalFilename, storedFilename, fileType,
                  fileSizeBytes, mimeType, ocrStatus, uploadedBy, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 11

    def test_additional_properties_rejected(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_document_instance, "thumbnailUrl": "https://example.com/thumb.png"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-4
        Wrong types should fail validation.
        - fileSizeBytes (integer) given as string
        - mimeType (string) given as integer
        - fileType (string) given as array
        - ocrStatus (string) given as boolean
        """
        wrong_size = {**valid_document_instance, "fileSizeBytes": "two_megabytes"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_size)

        wrong_mime = {**valid_document_instance, "mimeType": 200}
        with pytest.raises(ValidationError):
            validator.validate(wrong_mime)

        wrong_type = {**valid_document_instance, "fileType": ["pdf"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_type)

        wrong_status = {**valid_document_instance, "ocrStatus": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_status)

    def test_field_constraints(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-5
        Test enum, numeric bounds, and string length constraints.
        - fileType: enum [pdf, jpg, jpeg, png, docx]
        - ocrStatus: enum [pending, processing, completed, failed]
        - fileSizeBytes: minimum 1, maximum 26214400
        - originalFilename: minLength 1, maxLength 500
        """
        # invalid fileType
        bad_type = {**valid_document_instance, "fileType": "exe"}
        with pytest.raises(ValidationError):
            validator.validate(bad_type)

        # invalid ocrStatus
        bad_ocr = {**valid_document_instance, "ocrStatus": "done"}
        with pytest.raises(ValidationError):
            validator.validate(bad_ocr)

        # fileSizeBytes below minimum
        zero_size = {**valid_document_instance, "fileSizeBytes": 0}
        with pytest.raises(ValidationError):
            validator.validate(zero_size)

        # fileSizeBytes above maximum (25MB + 1)
        huge_size = {**valid_document_instance, "fileSizeBytes": 26214401}
        with pytest.raises(ValidationError):
            validator.validate(huge_size)

        # originalFilename too long
        long_name = {**valid_document_instance, "originalFilename": "x" * 501}
        with pytest.raises(ValidationError):
            validator.validate(long_name)

        # originalFilename empty
        empty_name = {**valid_document_instance, "originalFilename": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_name)

    def test_nullable_fields_accept_null(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-6
        Nullable fields should accept null.
        - ocrText, ocrProcessedAt, deletedAt are nullable.
        """
        instance = {
            **valid_document_instance,
            "ocrText": None,
            "ocrProcessedAt": None,
            "deletedAt": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_document_instance):
        """
        Scenario: DATA-005-7
        UUID fields should accept valid UUID format.
        Fields: id, caseId, uploadedBy.
        """
        valid = {
            **valid_document_instance,
            "id": "dd0e8400-e29b-41d4-a716-446655440008",
            "caseId": "880e8400-e29b-41d4-a716-446655440003",
            "uploadedBy": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
