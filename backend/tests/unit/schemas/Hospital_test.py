# Spec: DATA-006
# Schema: Hospital
# File: specs/data/Hospital.schema.json
# API Refs: API-040..043
# Description: A hospital or healthcare facility in the directory.

"""
Schema validation tests for the Hospital entity.
@spec DATA-006
@file specs/data/Hospital.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Hospital.schema.json"


@pytest.fixture
def hospital_schema():
    """Load the Hospital JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(hospital_schema):
    """Create a Draft202012Validator for the Hospital schema."""
    return Draft202012Validator(hospital_schema)


@pytest.fixture
def valid_hospital_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "110e8400-e29b-41d4-a716-446655440011",
        "name": "Apollo Cancer Centre",
        "specialty": "Oncology, Head and Neck Surgery, Reconstructive Surgery",
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": "320, Anna Salai, Chennai 600006",
        "phone": "+914428291890",
        "email": "info@apollocancer.in",
        "website": "https://www.apollocancercentre.com",
        "costRangeMin": 200000,
        "costRangeMax": 1500000,
        "hasFinancialAssistance": True,
        "financialAssistanceDetails": "SAP scheme available for low-income families.",
        "rating": 4.5,
        "isActive": True,
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-006")
class TestHospitalSchema:
    """Validation tests for Hospital.schema.json (DATA-006)."""

    def test_valid_complete_instance(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-1
        A complete Hospital instance should pass validation.
        """
        result = validator.validate(valid_hospital_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-006-2
        An empty dict should fail because required fields are missing.
        Required: id, name, city, isActive, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 6

    def test_additional_properties_rejected(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_hospital_instance, "bedCount": 500}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-4
        Wrong types should fail validation.
        - name (string) given as integer
        - city (string) given as array
        - isActive (boolean) given as string
        - rating (number) given as string
        """
        wrong_name = {**valid_hospital_instance, "name": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_name)

        wrong_city = {**valid_hospital_instance, "city": ["Chennai"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_city)

        wrong_active = {**valid_hospital_instance, "isActive": "yes"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_active)

        wrong_rating = {**valid_hospital_instance, "rating": "excellent"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_rating)

    def test_field_constraints(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-5
        Test numeric bounds and string length constraints.
        - rating: minimum 0, maximum 5, multipleOf 0.1
        - costRangeMin: minimum 0, exclusiveMaximum 100000000, multipleOf 0.01
        - costRangeMax: minimum 0, exclusiveMaximum 100000000, multipleOf 0.01
        - name: minLength 1, maxLength 255
        - city: minLength 1, maxLength 100
        """
        # rating above maximum
        high_rating = {**valid_hospital_instance, "rating": 5.1}
        with pytest.raises(ValidationError):
            validator.validate(high_rating)

        # rating below minimum
        low_rating = {**valid_hospital_instance, "rating": -0.1}
        with pytest.raises(ValidationError):
            validator.validate(low_rating)

        # rating wrong precision (multipleOf 0.1)
        bad_precision = {**valid_hospital_instance, "rating": 4.53}
        with pytest.raises(ValidationError):
            validator.validate(bad_precision)

        # costRangeMin negative
        neg_cost = {**valid_hospital_instance, "costRangeMin": -100}
        with pytest.raises(ValidationError):
            validator.validate(neg_cost)

        # name too long
        long_name = {**valid_hospital_instance, "name": "x" * 256}
        with pytest.raises(ValidationError):
            validator.validate(long_name)

        # city too long
        long_city = {**valid_hospital_instance, "city": "x" * 101}
        with pytest.raises(ValidationError):
            validator.validate(long_city)

    def test_nullable_fields_accept_null(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-6
        Nullable fields should accept null.
        - specialty, state, address, phone, email, website, costRangeMin,
          costRangeMax, financialAssistanceDetails, rating are nullable.
        """
        instance = {
            **valid_hospital_instance,
            "specialty": None,
            "state": None,
            "address": None,
            "phone": None,
            "email": None,
            "website": None,
            "costRangeMin": None,
            "costRangeMax": None,
            "financialAssistanceDetails": None,
            "rating": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_hospital_instance):
        """
        Scenario: DATA-006-7
        UUID fields should accept valid UUID format.
        Field: id.
        """
        valid = {**valid_hospital_instance, "id": "110e8400-e29b-41d4-a716-446655440011"}
        result = validator.validate(valid)
        assert result is None
