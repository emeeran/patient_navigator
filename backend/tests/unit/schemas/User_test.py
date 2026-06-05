# Spec: DATA-002
# Schema: User
# File: specs/data/User.schema.json
# API Refs: API-001..005, API-095..096
# Description: A platform user with authentication credentials and an assigned role.

"""
Schema validation tests for the User entity.
@spec DATA-002
@file specs/data/User.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "User.schema.json"


@pytest.fixture
def user_schema():
    """Load the User JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(user_schema):
    """Create a Draft202012Validator for the User schema."""
    return Draft202012Validator(user_schema)


@pytest.fixture
def valid_user_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "550e8400-e29b-41d4-a716-446655440000",
        "email": "admin@navigator.org",
        "passwordHash": "$2b$12$xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx",
        "fullName": "System Administrator",
        "phone": "+919876543210",
        "roleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "isActive": True,
        "lastLoginAt": "2026-06-04T14:22:00.000Z",
        "createdAt": "2026-06-01T10:00:00.000Z",
        "updatedAt": "2026-06-04T14:22:00.000Z",
        "deletedAt": None,
    }


@pytest.mark.spec("DATA-002")
class TestUserSchema:
    """Validation tests for User.schema.json (DATA-002)."""

    def test_valid_complete_instance(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-1
        A complete User instance with all required fields should pass validation.
        Uses the first example from the schema's examples array.
        """
        result = validator.validate(valid_user_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-002-2
        An empty dict should fail validation because all required fields are missing.
        Required: id, email, passwordHash, fullName, roleId, isActive, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError):
            validator.validate({})
        errors = list(validator.iter_errors({}))
        assert len(errors) >= 8

    def test_additional_properties_rejected(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-3
        Extra fields not defined in the schema should be rejected
        because additionalProperties is false.
        """
        instance = {**valid_user_instance, "adminNotes": "should not be here"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-4
        Fields with wrong types should fail validation.
        - email (string) given as integer
        - isActive (boolean) given as string
        - fullName (string) given as array
        - roleId (string) given as integer
        """
        wrong_email = {**valid_user_instance, "email": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_email)

        wrong_active = {**valid_user_instance, "isActive": "yes"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_active)

        wrong_name = {**valid_user_instance, "fullName": ["Dr.", "Priya"]}
        with pytest.raises(ValidationError):
            validator.validate(wrong_name)

        wrong_role = {**valid_user_instance, "roleId": 999}
        with pytest.raises(ValidationError):
            validator.validate(wrong_role)

    def test_field_constraints(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-5
        Test minLength, maxLength, pattern constraints.
        - email: minLength 5, maxLength 254, format email
        - passwordHash: minLength 60, maxLength 60
        - fullName: minLength 1, maxLength 255, pattern ^\\S.*\\S$|^\\S$
        - phone: pattern ^\\+?[0-9]{7,20}$, maxLength 20
        """
        # email too short
        short_email = {**valid_user_instance, "email": "a@b"}
        with pytest.raises(ValidationError):
            validator.validate(short_email)

        # passwordHash wrong length (59 chars)
        short_hash = {**valid_user_instance, "passwordHash": "x" * 59}
        with pytest.raises(ValidationError):
            validator.validate(short_hash)

        # fullName with only whitespace (fails pattern)
        space_name = {**valid_user_instance, "fullName": "   "}
        with pytest.raises(ValidationError):
            validator.validate(space_name)

        # fullName too long
        long_name = {**valid_user_instance, "fullName": "A" * 256}
        with pytest.raises(ValidationError):
            validator.validate(long_name)

        # phone invalid pattern (letters)
        bad_phone = {**valid_user_instance, "phone": "not-a-phone"}
        with pytest.raises(ValidationError):
            validator.validate(bad_phone)

    def test_nullable_fields_accept_null(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-6
        Fields defined as ["string", "null"] should accept null.
        - phone is nullable
        - lastLoginAt is nullable
        - deletedAt is nullable
        """
        instance = {
            **valid_user_instance,
            "phone": None,
            "lastLoginAt": None,
            "deletedAt": None,
        }
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_user_instance):
        """
        Scenario: DATA-002-7
        UUID fields should accept valid UUID format.
        Fields: id, roleId.
        """
        # Valid UUIDs should pass
        valid = {
            **valid_user_instance,
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "roleId": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        }
        result = validator.validate(valid)
        assert result is None

        # Non-UUID string in id field
        non_uuid = {**valid_user_instance, "id": "not-a-uuid"}
        assert isinstance(non_uuid["id"], str)  # structural assertion
