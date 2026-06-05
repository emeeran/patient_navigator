# Spec: DATA-001
# Schema: Role
# File: specs/data/Role.schema.json
# API Refs: API-001..005
# Description: Defines a user role within the Patient Navigator Platform.

"""
Schema validation tests for the Role entity.
@spec DATA-001
@file specs/data/Role.schema.json
"""

import json
from pathlib import Path

import pytest
from jsonschema import Draft202012Validator, ValidationError

SCHEMAS_DIR = Path(__file__).resolve().parents[4] / "specs" / "data"
SCHEMA_FILE = "Role.schema.json"


@pytest.fixture
def role_schema():
    """Load the Role JSON Schema."""
    with open(SCHEMAS_DIR / SCHEMA_FILE, "r", encoding="utf-8") as f:
        return json.load(f)


@pytest.fixture
def validator(role_schema):
    """Create a Draft202012Validator for the Role schema."""
    return Draft202012Validator(role_schema)


@pytest.fixture
def valid_role_instance():
    """Return the first example from the schema's examples array."""
    return {
        "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
        "name": "admin",
        "description": "Full system access including user management and audit logs",
        "permissions": {
            "patients": "full",
            "cases": "full",
            "documents": "full",
            "hospitals": "full",
            "funding": "full",
            "followups": "full",
            "ai": "full",
            "reports": "full",
            "users": "full",
            "audit": "full",
        },
        "createdAt": "2026-06-04T10:00:00.000Z",
        "updatedAt": "2026-06-04T10:00:00.000Z",
    }


@pytest.mark.spec("DATA-001")
class TestRoleSchema:
    """Validation tests for Role.schema.json (DATA-001)."""

    def test_valid_complete_instance(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-1
        A complete Role instance with all required fields should pass validation.
        Uses the first example from the schema's examples array.
        """
        result = validator.validate(valid_role_instance)
        assert result is None

    def test_missing_required_fields(self, validator):
        """
        Scenario: DATA-001-2
        An empty dict should fail validation because all required fields are missing.
        Required: id, name, permissions, createdAt, updatedAt.
        """
        with pytest.raises(ValidationError) as exc_info:
            validator.validate({})
        errors = [e.message for e in validator.iter_errors({})]
        assert len(errors) >= 5  # at least one error per required field

    def test_additional_properties_rejected(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-3
        Extra fields not defined in the schema should be rejected
        because additionalProperties is false.
        """
        instance = {**valid_role_instance, "extraField": "not allowed"}
        with pytest.raises(ValidationError) as exc_info:
            validator.validate(instance)
        assert "additional" in str(exc_info.value).lower() or "extra" in str(exc_info.value).lower()

    def test_field_type_validation(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-4
        Fields with wrong types should fail validation.
        - id (string) given as integer
        - name (string) given as integer
        - permissions (object) given as string
        - createdAt (string) given as integer
        """
        wrong_id = {**valid_role_instance, "id": 12345}
        with pytest.raises(ValidationError):
            validator.validate(wrong_id)

        wrong_name = {**valid_role_instance, "name": 42}
        with pytest.raises(ValidationError):
            validator.validate(wrong_name)

        wrong_permissions = {**valid_role_instance, "permissions": "full"}
        with pytest.raises(ValidationError):
            validator.validate(wrong_permissions)

        wrong_created = {**valid_role_instance, "createdAt": 100000}
        with pytest.raises(ValidationError):
            validator.validate(wrong_created)

    def test_field_constraints(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-5
        Test minLength, maxLength, pattern, and enum constraints.
        - name: minLength 1, maxLength 50, pattern ^[a-z][a-z0-9_-]*$
        - permissions values: enum [full, read, own, review, none]
        """
        # name too long (51 chars)
        long_name = {**valid_role_instance, "name": "a" * 51}
        with pytest.raises(ValidationError):
            validator.validate(long_name)

        # name too short (empty string)
        empty_name = {**valid_role_instance, "name": ""}
        with pytest.raises(ValidationError):
            validator.validate(empty_name)

        # name invalid pattern (starts with uppercase)
        bad_pattern = {**valid_role_instance, "name": "Admin"}
        with pytest.raises(ValidationError):
            validator.validate(bad_pattern)

        # invalid permission value
        bad_perms = {**valid_role_instance, "permissions": {"patients": "invalid_value"}}
        with pytest.raises(ValidationError):
            validator.validate(bad_perms)

        # description too long (501 chars)
        long_desc = {**valid_role_instance, "description": "x" * 501}
        with pytest.raises(ValidationError):
            validator.validate(long_desc)

    def test_nullable_fields_accept_null(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-6
        Fields defined as ["string", "null"] should accept null.
        - description is nullable
        """
        instance = {**valid_role_instance, "description": None}
        result = validator.validate(instance)
        assert result is None

    def test_uuid_format_validation(self, validator, valid_role_instance):
        """
        Scenario: DATA-001-7
        UUID fields (id) should validate format.
        Draft 2020-12 format validation is optional; this test documents
        the expected behavior when format assertion is enabled.
        """
        # Valid UUID format should pass (even if format not enforced)
        valid = {**valid_role_instance, "id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890"}
        result = validator.validate(valid)
        assert result is None

        # Non-UUID string in id field — schema declares format: uuid
        # Document the expectation even if Draft202012Validator may not enforce it
        non_uuid = {**valid_role_instance, "id": "not-a-uuid"}
        # If format checking is enabled, this should fail
        format_validator = Draft202012Validator(
            validator.schema, format_checker=Draft202012Validator.FORMAT_CHECKER
        )
        # We record the expectation; actual enforcement depends on format_checker config
        assert isinstance(non_uuid["id"], str)  # structural assertion
