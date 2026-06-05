# Spec: DATA-011
# Schema: ClinicianReview
# File: specs/data/ClinicianReview.schema.json
# API Refs: API-080..082
# Description: A clinician's review of AI-generated medical content.

"""
Schema validation tests for the ClinicianReview entity.
@spec DATA-011
@file specs/data/ClinicianReview.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "ClinicianReview.schema.json"


@pytest.fixture
def review_schema():
    """Load the ClinicianReview JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(review_schema):
    """Create a Draft202012Validator for the ClinicianReview schema."""
    return Draft202012Validator(review_schema)


@pytest.fixture
def valid_review_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "ee0e8400-e29b-41d4-a716-446655440009",
        "caseId": "880e8400-e29b-41d4-a716-446655440003",
        "clinicianId": "660e8400-e29b-41d4-a716-446655440001",
        "reviewType": "ai_summary_approval",
        "content": "Summary accurately reflects the biopsy findings. Staging is correct at T2N0M0. Approved for care coordination use.",
        "status": "approved",
        "reviewedAt": "2026-06-04T12:00:00.000Z",
        "createdAt": "2026-06-04T11:50:00.000Z",
        "updatedAt": "2026-06-04T12:00:00.000Z",
    }


@pytest.mark.spec("DATA-011")
class TestClinicianReviewSchema:
    """Validation tests for ClinicianReview.schema.json (DATA-011)."""

    def test_valid_complete_instance(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-1
        A complete ClinicianReview instance should pass validation.
        """
        result = validator.validate(valid_review_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-011-2
        An empty dict should fail because required fields are missing.
        Required: id, caseId, clinicianId, reviewType, content, status,
                  createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 8

    def test_additional_properties_rejected(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_review_instance, "attachments": ["file.pdf"]}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-4
        Wrong types should fail validation.
        - content (string) given as integer
        - reviewType (string) given as array
        - status (string) given as boolean
        - clinicianId (string) given as integer
        """
        wrong_content = {**valid_review_instance, "content": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_content)

        wrong_type = {**valid_review_instance, "reviewType": ["approval"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_type)

        wrong_status = {**valid_review_instance, "status": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_status)

        wrong_clinician = {**valid_review_instance, "clinicianId": 999}
        with pytest.raises(ValidationError):
            validator.validate(wrong_clinician)

    def test_field_constraints(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-5
        Test enum and string length constraints.
        - reviewType: enum [ai_summary_approval, recommendation, correction]
        - status: enum [pending, approved, revision_requested]
        - content: minLength 1, maxLength 10000
        """
        # invalid reviewType
        bad_type = {**valid_review_instance, "reviewType": "rejection"}
        with pytest.raises(ValidationError):
            validator.validate(bad_type)

        # invalid status
        bad_status = {**valid_review_instance, "status": "rejected"}
        with pytest.raises(ValidationError):
            validator.validate(bad_status)

        # empty content
        empty_content = {**valid_review_instance, "content": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_content)

        # content too long
        long_content = {**valid_review_instance, "content": "x" * 10001}
        with pytest.raises(ValidationError):
            validator.validate(long_content)

    def test_nullable_fields_accept_null(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-6
        Nullable fields should accept null.
        - reviewedAt is nullable.
        """
        instance = {**valid_review_instance, "reviewedAt": None}
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_review_instance):
        """
        Scenario: DATA-011-7
        UUID fields should accept valid UUID format.
        Fields: id, caseId, clinicianId.
        """
        valid = {
            **valid_review_instance,
            "id": "ee0e8400-e29b-41d4-a716-446655440009",
            "caseId": "880e8400-e29b-41d4-a716-446655440003",
            "clinicianId": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
