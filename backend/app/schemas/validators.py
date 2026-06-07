"""Reusable Pydantic model validator helpers."""

import re


def check_at_least_one(obj: object, *field_names: str) -> None:
    """Raise ValueError if all specified fields on *obj* are None.

    Use inside a Pydantic ``@model_validator(mode="after")`` method::

        @model_validator(mode="after")
        def validate_fields(self):
            check_at_least_one(self, "full_name", "email", "phone")
            return self
    """
    if all(getattr(obj, name, None) is None for name in field_names):
        raise ValueError("At least one field must be provided")


_PASSWORD_PATTERN = r"^(?=.*[a-z])(?=.*[A-Z])(?=.*\d)(?=.*[@$!%*?&^#])"


def check_password_complexity(password: str) -> None:
    """Raise ValueError if *password* doesn't meet complexity requirements."""
    if not re.search(_PASSWORD_PATTERN, password):
        raise ValueError(
            "Password must contain at least one uppercase letter, "
            "one lowercase letter, one digit, and one special character"
        )
