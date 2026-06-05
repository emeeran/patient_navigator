"""PII masking utilities — role-based field masking per DATA-003 x-masking rules."""

import re


def mask_phone(phone: str) -> str:
    """Partial mask: keeps first 3 and last 4 chars, replaces middle with ****.

    '+919876543210' -> '+91****3210'
    """
    if len(phone) <= 7:
        return "****"
    return phone[:3] + "****" + phone[-4:]


def mask_email(email: str) -> str:
    """Partial mask: keeps first char and domain.

    'patient@example.org' -> 'p***@example.org'
    """
    if "@" not in email:
        return "***@***.***"
    local, domain = email.split("@", 1)
    if not local:
        return f"***@{domain}"
    return f"{local[0]}***@{domain}"


def mask_full_name(name: str) -> str:
    """Full mask for volunteer role: 'Aarav Mehta' -> 'A**** M****'."""
    parts = name.split()
    masked = []
    for part in parts:
        if len(part) <= 1:
            masked.append("*")
        else:
            masked.append(part[0] + "*" * (len(part) - 1))
    return " ".join(masked)


def mask_phone_full(phone: str) -> str:
    """Full mask for volunteer role: replaces all digits with *."""
    return re.sub(r"\d", "*", phone)


def mask_patient_response(data: dict, role: str) -> dict:
    """Apply PII masking to a patient response dict based on viewer role.

    Roles and their masking levels:
    - admin, navigator: no masking (full visibility)
    - clinician: partial masking (phone, email)
    - volunteer: full masking (phone, email, name, address, contacts)
    - patient: no masking (own records only, enforced at route level)
    """
    if role in ("admin", "navigator"):
        return data

    result = dict(data)

    if role == "clinician":
        if result.get("phone"):
            result["phone"] = mask_phone(result["phone"])
        if result.get("email"):
            result["email"] = mask_email(result["email"])
        # Address, emergency contacts visible to clinician
        return result

    if role == "volunteer":
        if result.get("full_name"):
            result["full_name"] = mask_full_name(result["full_name"])
        if result.get("phone"):
            result["phone"] = mask_phone_full(result["phone"])
        if result.get("email"):
            result["email"] = "***@***.***"
        if result.get("address"):
            result["address"] = "***"
        if result.get("emergency_contact_name"):
            result["emergency_contact_name"] = "***"
        if result.get("emergency_contact_phone"):
            result["emergency_contact_phone"] = "***"
        return result

    return result
