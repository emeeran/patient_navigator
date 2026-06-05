# Spec: DATA-008
# Schema: FollowUp
# File: specs/data/FollowUp.schema.json
# API Refs: API-060..064
# Description: A tracked task or milestone related to a patient case.

"""
Schema validation tests for the FollowUp entity.
@spec DATA-008
@file specs/data/FollowUp.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "FollowUp.schema.json"


@pytest.fixture
def followup_schema():
    """Load the FollowUp JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(followup_schema):
    """Create a Draft202012Validator for the FollowUp schema."""
    return Draft202012Validator(followup_schema)


@pytest.fixture
def valid_followup_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "330e8400-e29b-41d4-a716-446655440013",
        "caseId": "880e8400-e29b-41d4-a716-446655440003",
        "patientId": "770e8400-e29b-41d4-a716-446655440002",
        "type": "appointment",
        "title": "Consultation with oncologist",
        "description": "First appointment at Apollo Cancer Centre. Bring biopsy report and insurance documents.",
        "dueDate": "2026-06-15",
        "status": "pending",
        "completedAt": None,
        "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-008")
class TestFollowUpSchema:
    """Validation tests for FollowUp.schema.json (DATA-008)."""

    def test_valid_complete_instance(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-1
        A complete FollowUp instance should pass validation.
        """
        result = validator.validate(valid_followup_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-008-2
        An empty dict should fail because required fields are missing.
        Required: id, caseId, patientId, type, title, dueDate, status,
                  createdBy, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 10

    def test_additional_properties_rejected(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_followup_instance, "reminderSent": True}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-4
        Wrong types should fail validation.
        - title (string) given as integer
        - type (string) given as array
        - dueDate (string) given as integer
        - status (string) given as boolean
        """
        wrong_title = {**valid_followup_instance, "title": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_title)

        wrong_type = {**valid_followup_instance, "type": ["appointment"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_type)

        wrong_date = {**valid_followup_instance, "dueDate": 20260615}
        with pytest.raises(ValidationError):
            validator.validate(wrong_date)

        wrong_status = {**valid_followup_instance, "status": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_status)

    def test_field_constraints(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-5
        Test enum and string length constraints.
        - type: enum [appointment, deadline, funding_status, treatment_progress]
        - status: enum [pending, completed, overdue, cancelled]
        - title: minLength 1, maxLength 255
        - description: maxLength 5000
        """
        # invalid type
        bad_type = {**valid_followup_instance, "type": "call"}
        with pytest.raises(ValidationError):
            validator.validate(bad_type)

        # invalid status
        bad_status = {**valid_followup_instance, "status": "in_progress"}
        with pytest.raises(ValidationError):
            validator.validate(bad_status)

        # empty title
        empty_title = {**valid_followup_instance, "title": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_title)

        # title too long
        long_title = {**valid_followup_instance, "title": "x" * 256}
        with pytest.raises(ValidationError):
            validator.validate(long_title)

        # description too long
        long_desc = {**valid_followup_instance, "description": "x" * 5001}
        with pytest.raises(ValidationError):
            validator.validate(long_desc)

    def test_nullable_fields_accept_null(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-6
        Nullable fields should accept null.
        - description, completedAt are nullable.
        """
        instance = {
            **valid_followup_instance,
            "description": None,
            "completedAt": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_followup_instance):
        """
        Scenario: DATA-008-7
        UUID fields should accept valid UUID format.
        Fields: id, caseId, patientId, createdBy.
        """
        valid = {
            **valid_followup_instance,
            "id": "330e8400-e29b-41d4-a716-446655440013",
            "caseId": "880e8400-e29b-41d4-a716-446655440003",
            "patientId": "770e8400-e29b-41d4-a716-446655440002",
            "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
