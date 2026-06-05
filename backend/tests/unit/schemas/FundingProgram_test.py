# Spec: DATA-007
# Schema: FundingProgram
# File: specs/data/FundingProgram.schema.json
# API Refs: API-050..053
# Description: A financial assistance scheme for medical treatment.

"""
Schema validation tests for the FundingProgram entity.
@spec DATA-007
@file specs/data/FundingProgram.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "FundingProgram.schema.json"


@pytest.fixture
def funding_schema():
    """Load the FundingProgram JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(funding_schema):
    """Create a Draft202012Validator for the FundingProgram schema."""
    return Draft202012Validator(funding_schema)


@pytest.fixture
def valid_funding_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "220e8400-e29b-41d4-a716-446655440012",
        "schemeName": "Chief Minister's Health Insurance Scheme",
        "description": "Tamil Nadu government scheme providing free treatment for low-income families.",
        "eligibilityCriteria": "Annual family income below 72,000 INR. Tamil Nadu resident.",
        "documentsRequired": "Income certificate, Aadhaar card, hospital estimate, ration card",
        "applicationProcess": "Apply through the hospital's billing department with required documents.",
        "contactPerson": "Ramesh Kumar",
        "contactPhone": "+914425340540",
        "contactEmail": "cmhis@tn.gov.in",
        "website": "https://cmhisco.tn.gov.in",
        "maxAmount": 500000,
        "isActive": True,
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-007")
class TestFundingProgramSchema:
    """Validation tests for FundingProgram.schema.json (DATA-007)."""

    def test_valid_complete_instance(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-1
        A complete FundingProgram instance should pass validation.
        """
        result = validator.validate(valid_funding_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-007-2
        An empty dict should fail because required fields are missing.
        Required: id, schemeName, isActive, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 5

    def test_additional_properties_rejected(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-3
        Extra fields should be rejected (additionalProperties: false).
        """
        instance = {**valid_funding_instance, "approvalRate": 0.85}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-4
        Wrong types should fail validation.
        - schemeName (string) given as integer
        - isActive (boolean) given as string
        - maxAmount (number) given as array
        - description (string) given as boolean
        """
        wrong_name = {**valid_funding_instance, "schemeName": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_name)

        wrong_active = {**valid_funding_instance, "isActive": "yes"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_active)

        wrong_amount = {**valid_funding_instance, "maxAmount": [500000]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_amount)

        wrong_desc = {**valid_funding_instance, "description": True}
        with pytest.raises(ValidationError):
            validator.validate(wrong_desc)

    def test_field_constraints(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-5
        Test numeric bounds and string length constraints.
        - maxAmount: minimum 0, exclusiveMaximum 100000000, multipleOf 0.01
        - schemeName: minLength 1, maxLength 255
        - description: maxLength 10000
        - eligibilityCriteria: maxLength 10000
        """
        # schemeName too long
        long_name = {**valid_funding_instance, "schemeName": "x" * 256}
        with pytest.raises(ValidationError):
            validator.validate(long_name)

        # schemeName empty
        empty_name = {**valid_funding_instance, "schemeName": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_name)

        # maxAmount negative
        neg_amount = {**valid_funding_instance, "maxAmount": -1}
        with pytest.raises(ValidationError):
            validator.validate(neg_amount)

        # maxAmount at exclusiveMaximum boundary
        huge_amount = {**valid_funding_instance, "maxAmount": 100000000}
        with pytest.raises(ValidationError):
            validator.validate(huge_amount)

        # description too long
        long_desc = {**valid_funding_instance, "description": "x" * 10001}
        with pytest.raises(ValidationError):
            validator.validate(long_desc)

    def test_nullable_fields_accept_null(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-6
        Nullable fields should accept null.
        - description, eligibilityCriteria, documentsRequired, applicationProcess,
          contactPerson, contactPhone, contactEmail, website, maxAmount are nullable.
        """
        instance = {
            **valid_funding_instance,
            "description": None,
            "eligibilityCriteria": None,
            "documentsRequired": None,
            "applicationProcess": None,
            "contactPerson": None,
            "contactPhone": None,
            "contactEmail": None,
            "website": None,
            "maxAmount": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_funding_instance):
        """
        Scenario: DATA-007-7
        UUID fields should accept valid UUID format.
        Field: id.
        """
        valid = {**valid_funding_instance, "id": "220e8400-e29b-41d4-a716-446655440012"}
        result = validator.validate(valid)
        assert result is None
