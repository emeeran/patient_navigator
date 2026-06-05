# Spec: DATA-010
# Schema: TimelineEvent
# File: specs/data/TimelineEvent.schema.json
# API Refs: API-026
# Description: An INSERT-only audit record of every change made to a case.

"""
Schema validation tests for the TimelineEvent entity.
@spec DATA-010
@file specs/data/TimelineEvent.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "TimelineEvent.schema.json"


@pytest.fixture
def timeline_schema():
    """Load the TimelineEvent JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(timeline_schema):
    """Create a Draft202012Validator for the TimelineEvent schema."""
    return Draft202012Validator(timeline_schema)


@pytest.fixture
def valid_timeline_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "bb0e8400-e29b-41d4-a716-446655440006",
        "caseId": "880e8400-e29b-41d4-a716-446655440003",
        "userId": "660e8400-e29b-41d4-a716-446655440001",
        "eventType": "case.status_changed",
        "title": "Status changed: new -> under_review",
        "description": "Navigator began reviewing the case",
        "oldValue": "new",
        "newValue": "under_review",
        "createdAt": "2026-06-04T10:30:00.000Z",
    }


@pytest.mark.spec("DATA-010")
class TestTimelineEventSchema:
    """Validation tests for TimelineEvent.schema.json (DATA-010)."""

    def test_valid_complete_instance(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-1
        A complete TimelineEvent instance should pass validation.
        """
        result = validator.validate(valid_timeline_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-010-2
        An empty dict should fail because required fields are missing.
        Required: id, caseId, userId, eventType, title, createdAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 6

    def test_additional_properties_rejected(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_timeline_instance, "sourceIp": "10.0.0.1"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-4
        Wrong types should fail validation.
        - eventType (string) given as integer
        - title (string) given as array
        - caseId (string) given as boolean
        - oldValue (string) given as integer
        """
        wrong_event = {**valid_timeline_instance, "eventType": 42}
        with pytest.raises(ValidationError):
            validator.validate(wrong_event)

        wrong_title = {**valid_timeline_instance, "title": ["Status changed"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_title)

        wrong_case = {**valid_timeline_instance, "caseId": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_case)

        wrong_old = {**valid_timeline_instance, "oldValue": 123}
        with pytest.raises(ValidationError):
            validator.validate(wrong_old)

    def test_field_constraints(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-5
        Test string length and pattern constraints.
        - eventType: minLength 1, maxLength 50, pattern ^[a-z][a-z0-9_.]*$
        - title: minLength 1, maxLength 255
        - description: maxLength 2000
        - oldValue: maxLength 500
        - newValue: maxLength 500
        """
        # eventType too long
        long_event = {**valid_timeline_instance, "eventType": "a" * 51}
        with pytest.raises(ValidationError):
            validator.validate(long_event)

        # eventType wrong pattern
        bad_pattern = {**valid_timeline_instance, "eventType": "Case.Created"}
        with pytest.raises(ValidationError):
            validator.validate(bad_pattern)

        # empty title
        empty_title = {**valid_timeline_instance, "title": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_title)

        # title too long
        long_title = {**valid_timeline_instance, "title": "x" * 256}
        with pytest.raises(ValidationError):
            validator.validate(long_title)

        # description too long
        long_desc = {**valid_timeline_instance, "description": "x" * 2001}
        with pytest.raises(ValidationError):
            validator.validate(long_desc)

        # oldValue too long
        long_old = {**valid_timeline_instance, "oldValue": "x" * 501}
        with pytest.raises(ValidationError):
            validator.validate(long_old)

    def test_nullable_fields_accept_null(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-6
        Nullable fields should accept null.
        - description, oldValue, newValue are nullable.
        """
        instance = {
            **valid_timeline_instance,
            "description": None,
            "oldValue": None,
            "newValue": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_timeline_instance):
        """
        Scenario: DATA-010-7
        UUID fields should accept valid UUID format.
        Fields: id, caseId, userId.
        """
        valid = {
            **valid_timeline_instance,
            "id": "bb0e8400-e29b-41d4-a716-446655440006",
            "caseId": "880e8400-e29b-41d4-a716-446655440003",
            "userId": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
