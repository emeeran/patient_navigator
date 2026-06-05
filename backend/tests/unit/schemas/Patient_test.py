# Spec: DATA-003
# Schema: Patient
# File: specs/data/Patient.schema.json
# API Refs: API-010..014, API-090
# Description: A patient record in the care coordination system.

"""
Schema validation tests for the Patient entity.
@spec DATA-003
@file specs/data/Patient.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Patient.schema.json"


@pytest.fixture
def patient_schema():
    """Load the Patient JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(patient_schema):
    """Create a Draft202012Validator for the Patient schema."""
    return Draft202012Validator(patient_schema)


@pytest.fixture
def valid_patient_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "770e8400-e29b-41d4-a716-446655440002",
        "fullName": "Aarav Mehta",
        "age": 45,
        "gender": "male",
        "phone": "+919876543210",
        "email": "aarav.mehta@example.org",
        "address": "42, Anna Nagar, Chennai 600040",
        "emergencyContactName": "Priya Mehta",
        "emergencyContactPhone": "+919876543211",
        "navigatorId": "660e8400-e29b-41d4-a716-446655440001",
        "status": "active",
        "notes": "Referred from Government General Hospital",
        "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
        "deletedAt": None,
    }


@pytest.mark.spec("DATA-003")
class TestPatientSchema:
    """Validation tests for Patient.schema.json (DATA-003)."""

    def test_valid_complete_instance(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-1
        A complete Patient instance with all required and optional fields
        should pass validation.
        """
        result = validator.validate(valid_patient_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-003-2
        An empty dict should fail because required fields are missing.
        Required: id, fullName, age, gender, status, createdBy, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 8

    def test_additional_properties_rejected(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_patient_instance, "insuranceNumber": "INS-12345"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-4
        Wrong types should fail validation.
        - fullName (string) given as array
        - age (integer) given as string
        - gender (string) given as integer
        - status (string) given as boolean
        """
        wrong_name = {**valid_patient_instance, "fullName": ["Aarav"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_name)

        wrong_age = {**valid_patient_instance, "age": "forty-five"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_age)

        wrong_gender = {**valid_patient_instance, "gender": 1}
        with pytest.raises(ValidationError):
            validator.validate(wrong_gender)

        wrong_status = {**valid_patient_instance, "status": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_status)

    def test_field_constraints(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-5
        Test numeric bounds, enum, string length, and pattern constraints.
        - age: minimum 0, maximum 150
        - gender: enum [male, female, other, prefer_not_to_say]
        - status: enum [active, inactive, archived]
        - fullName: minLength 1, maxLength 255, pattern ^\\S.*\\S$|^\\S$
        - phone: pattern ^\\+?[0-9]{7,20}$
        """
        # age below minimum
        young = {**valid_patient_instance, "age": -1}
        with pytest.raises(ValidationError):
            validator.validate(young)

        # age above maximum
        old = {**valid_patient_instance, "age": 151}
        with pytest.raises(ValidationError):
            validator.validate(old)

        # invalid gender enum
        bad_gender = {**valid_patient_instance, "gender": "unknown"}
        with pytest.raises(ValidationError):
            validator.validate(bad_gender)

        # invalid status enum
        bad_status = {**valid_patient_instance, "status": "deleted"}
        with pytest.raises(ValidationError):
            validator.validate(bad_status)

        # fullName with leading/trailing whitespace only
        space_name = {**valid_patient_instance, "fullName": " "}
        with pytest.raises(ValidationError):
            validator.validate(space_name)

    def test_nullable_fields_accept_null(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-6
        Nullable fields should accept null.
        - phone, email, address, emergencyContactName, emergencyContactPhone,
          navigatorId, notes, deletedAt are all nullable.
        """
        instance = {
            **valid_patient_instance,
            "phone": None,
            "email": None,
            "address": None,
            "emergencyContactName": None,
            "emergencyContactPhone": None,
            "navigatorId": None,
            "notes": None,
            "deletedAt": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_patient_instance):
        """
        Scenario: DATA-003-7
        UUID fields should accept valid UUID format.
        Fields: id, navigatorId, createdBy.
        """
        valid = {
            **valid_patient_instance,
            "id": "770e8400-e29b-41d4-a716-446655440002",
            "navigatorId": "660e8400-e29b-41d4-a716-446655440001",
            "createdBy": "660e8400-e29b-41d4-a716-446655440001",
        }
        result = validator.validate(valid)
        assert result is None
