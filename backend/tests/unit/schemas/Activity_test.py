# Spec: DATA-009
# Schema: Activity
# File: specs/data/Activity.schema.json
# API Refs: (none — internal audit log)
# Description: An INSERT-only audit log record tracking mutations on patient-related entities.

"""
Schema validation tests for the Activity entity.
@spec DATA-009
@file specs/data/Activity.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Activity.schema.json"


@pytest.fixture
def activity_schema():
    """Load the Activity JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(activity_schema):
    """Create a Draft202012Validator for the Activity schema."""
    return Draft202012Validator(activity_schema)


@pytest.fixture
def valid_activity_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "990e8400-e29b-41d4-a716-446655440004",
        "patientId": "770e8400-e29b-41d4-a716-446655440002",
        "userId": "660e8400-e29b-41d4-a716-446655440001",
        "action": "patient.created",
        "entityType": "patient",
        "entityId": "770e8400-e29b-41d4-a716-446655440002",
        "description": "Created patient record for Aarav Mehta",
        "metadata": {"full_name": "Aarav Mehta", "age": "45"},
        "createdAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-009")
class TestActivitySchema:
    """Validation tests for Activity.schema.json (DATA-009)."""

    def test_valid_complete_instance(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-1
        A complete Activity instance should pass validation.
        """
        result = validator.validate(valid_activity_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-009-2
        An empty dict should fail because required fields are missing.
        Required: id, patientId, userId, action, description, createdAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 6

    def test_additional_properties_rejected(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_activity_instance, "ipAddress": "192.168.1.1"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-4
        Wrong types should fail validation.
        - action (string) given as integer
        - description (string) given as array
        - metadata (object) given as string
        - patientId (string) given as integer
        """
        wrong_action = {**valid_activity_instance, "action": 42}
        with pytest.raises(ValidationError):
            validator.validate(wrong_action)

        wrong_desc = {**valid_activity_instance, "description": ["Created patient"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_desc)

        wrong_meta = {**valid_activity_instance, "metadata": "key=value"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_meta)

        wrong_patient = {**valid_activity_instance, "patientId": 999}
        with pytest.raises(ValidationError):
            validator.validate(wrong_patient)

    def test_field_constraints(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-5
        Test string length, pattern, and metadata constraints.
        - action: minLength 1, maxLength 50, pattern ^[a-z][a-z0-9_.]*$
        - description: minLength 1, maxLength 2000
        - entityType: maxLength 50
        - metadata: maxProperties 20, values maxLength 512
        """
        # action too long
        long_action = {**valid_activity_instance, "action": "a" * 51}
        with pytest.raises(ValidationError):
            validator.validate(long_action)

        # action wrong pattern (starts with uppercase)
        bad_action = {**valid_activity_instance, "action": "Patient.created"}
        with pytest.raises(ValidationError):
            validator.validate(bad_action)

        # empty description
        empty_desc = {**valid_activity_instance, "description": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_desc)

        # description too long
        long_desc = {**valid_activity_instance, "description": "x" * 2001}
        with pytest.raises(ValidationError):
            validator.validate(long_desc)

        # metadata with too many properties
        too_many = {str(i): "val" for i in range(21)}
        huge_meta = {**valid_activity_instance, "metadata": too_many}
        with pytest.raises(ValidationError):
            validator.validate(huge_meta)

    def test_nullable_fields_accept_null(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-6
        Nullable fields should accept null.
        - entityType, entityId, metadata are nullable.
        """
        instance = {
            **valid_activity_instance,
            "entityType": None,
            "entityId": None,
            "metadata": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_activity_instance):
        """
        Scenario: DATA-009-7
        UUID fields should accept valid UUID format.
        Fields: id, patientId, userId, entityId.
        """
        valid = {
            **valid_activity_instance,
            "id": "990e8400-e29b-41d4-a716-446655440004",
            "patientId": "770e8400-e29b-41d4-a716-446655440002",
            "userId": "660e8400-e29b-41d4-a716-446655440001",
            "entityId": "770e8400-e29b-41d4-a716-446655440002",
        }
        result = validator.validate(valid)
        assert result is None
