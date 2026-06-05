# Spec: DATA-004
# Schema: Case
# File: specs/data/Case.schema.json
# API Refs: API-020..026, API-091
# Description: A care coordination case linking a patient to diagnosis, hospital, funding, clinician.

"""
Schema validation tests for the Case entity.
@spec DATA-004
@file specs/data/Case.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Case.schema.json"


@pytest.fixture
def case_schema():
    """Load the Case JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(case_schema):
    """Create a Draft202012Validator for the Case schema."""
    return Draft202012Validator(case_schema)


@pytest.fixture
def valid_case_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "880e8400-e29b-41d4-a716-446655440003",
        "patientId": "770e8400-e29b-41d4-a716-446655440002",
        "diagnosis": "Stage 2B Oral Cancer",
        "status": "under_review",
        "priority": "high",
        "notes": "Biopsy confirmed. Awaiting hospital assignment.",
        "recommendedHospitalId": None,
        "appliedFundingId": None,
        "assignedClinicianId": None,
        "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        "closedAt": None,
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:30:00.000Z",
        "deletedAt": None,
    }


@pytest.mark.spec("DATA-004")
class TestCaseSchema:
    """Validation tests for Case.schema.json (DATA-004)."""

    def test_valid_complete_instance(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-1
        A complete Case instance should pass validation.
        """
        result = validator.validate(valid_case_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-004-2
        An empty dict should fail because required fields are missing.
        Required: id, patientId, diagnosis, status, priority, createdBy, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 8

    def test_additional_properties_rejected(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_case_instance, "treatmentPlan": "chemotherapy"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-4
        Wrong types should fail validation.
        - diagnosis (string) given as integer
        - status (string) given as integer
        - priority (string) given as boolean
        - patientId (string) given as array
        """
        wrong_diagnosis = {**valid_case_instance, "diagnosis": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_diagnosis)

        wrong_status = {**valid_case_instance, "status": 1}
        with pytest.raises(ValidationError):
            validator.validate(wrong_status)

        wrong_priority = {**valid_case_instance, "priority": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_priority)

        wrong_patient = {**valid_case_instance, "patientId": ["uuid"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_patient)

    def test_field_constraints(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-5
        Test enum and string length constraints.
        - status: enum [new, under_review, hospital_selected, funding_applied,
                        treatment_started, closed]
        - priority: enum [low, medium, high, critical]
        - diagnosis: minLength 1, maxLength 5000
        """
        # invalid status
        bad_status = {**valid_case_instance, "status": "approved"}
        with pytest.raises(ValidationError):
            validator.validate(bad_status)

        # invalid priority
        bad_priority = {**valid_case_instance, "priority": "urgent"}
        with pytest.raises(ValidationError):
            validator.validate(bad_priority)

        # empty diagnosis
        empty_diag = {**valid_case_instance, "diagnosis": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_diag)

        # diagnosis too long
        long_diag = {**valid_case_instance, "diagnosis": "x" * 5001}
        with pytest.raises(ValidationError):
            validator.validate(long_diag)

        # notes too long
        long_notes = {**valid_case_instance, "notes": "y" * 10001}
        with pytest.raises(ValidationError):
            validator.validate(long_notes)

    def test_nullable_fields_accept_null(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-6
        Nullable fields should accept null.
        - notes, recommendedHospitalId, appliedFundingId, assignedClinicianId,
          closedAt, deletedAt are all nullable.
        """
        instance = {
            **valid_case_instance,
            "notes": None,
            "recommendedHospitalId": None,
            "appliedFundingId": None,
            "assignedClinicianId": None,
            "closedAt": None,
            "deletedAt": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_case_instance):
        """
        Scenario: DATA-004-7
        UUID fields should accept valid UUID format.
        Fields: id, patientId, recommendedHospitalId, appliedFundingId,
                assignedClinicianId, createdBy.
        """
        valid = {
            **valid_case_instance,
            "id": "880e8400-e29b-41d4-a716-446655440003",
            "patientId": "770e8400-e29b-41d4-a716-446655440002",
            "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
