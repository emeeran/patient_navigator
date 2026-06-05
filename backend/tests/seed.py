"""Test seed data — deterministic roles, users, patients, and cases for integration tests."""

import uuid

from sqlalchemy import delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.security import hash_password
from app.models.case import Case
from app.models.patient import Patient
from app.models.role import Role
from app.models.user import User

# Deterministic IDs for test assertions
SEED_ROLE_IDS = {
    "admin": uuid.UUID("a0000000-0000-0000-0000-000000000001"),
    "navigator": uuid.UUID("a0000000-0000-0000-0000-000000000002"),
    "clinician": uuid.UUID("a0000000-0000-0000-0000-000000000003"),
    "volunteer": uuid.UUID("a0000000-0000-0000-0000-000000000004"),
    "patient": uuid.UUID("a0000000-0000-0000-0000-000000000005"),
}

SEED_USER_IDS = {
    "admin": uuid.UUID("b0000000-0000-0000-0000-000000000001"),
    "navigator": uuid.UUID("b0000000-0000-0000-0000-000000000002"),
    "clinician": uuid.UUID("b0000000-0000-0000-0000-000000000003"),
    "volunteer": uuid.UUID("b0000000-0000-0000-0000-000000000004"),
    "patient": uuid.UUID("b0000000-0000-0000-0000-000000000005"),
    "disabled": uuid.UUID("b0000000-0000-0000-0000-000000000006"),
}

# Deterministic patient IDs
SEED_PATIENT_IDS = {
    "p001": uuid.UUID("c0000000-0000-0000-0000-000000000001"),
    "p002": uuid.UUID("c0000000-0000-0000-0000-000000000002"),
    "p003": uuid.UUID("c0000000-0000-0000-0000-000000000003"),
    "p_archived": uuid.UUID("c0000000-0000-0000-0000-000000000004"),
    "p_own": uuid.UUID("c0000000-0000-0000-0000-000000000005"),
}

# Deterministic case IDs
SEED_CASE_IDS = {
    "c001": uuid.UUID("d0000000-0000-0000-0000-000000000001"),
    "c002": uuid.UUID("d0000000-0000-0000-0000-000000000002"),
    "c003": uuid.UUID("d0000000-0000-0000-0000-000000000003"),
}

TEST_PASSWORD = "TestPass123!"
TEST_PASSWORD_HASH = hash_password(TEST_PASSWORD)


async def seed_test_data(db: AsyncSession) -> dict:
    """Insert seed roles, users, patients, and cases. Returns a dict of created objects."""
    # Seed roles (with deterministic IDs)
    for name, role_id in SEED_ROLE_IDS.items():
        role = await db.get(Role, role_id)
        if not role:
            permissions = _get_permissions(name)
            role = Role(
                id=role_id,
                name=name,
                description=f"Test role: {name}",
                permissions=permissions,
            )
            db.add(role)
    await db.flush()

    # Seed users (create or update to ensure correct role assignment)
    users = {}
    for role_name in ["admin", "navigator", "clinician", "volunteer", "patient"]:
        user_id = SEED_USER_IDS[role_name]
        user = await db.get(User, user_id)
        if not user:
            user = User(
                id=user_id,
                email=f"{role_name}@test.com",
                password_hash=TEST_PASSWORD_HASH,
                full_name=f"Test {role_name.title()}",
                role_id=SEED_ROLE_IDS[role_name],
                is_active=True,
            )
            db.add(user)
        else:
            # Ensure existing user has correct role and active status
            user.role_id = SEED_ROLE_IDS[role_name]
            user.is_active = True
            user.password_hash = TEST_PASSWORD_HASH
        users[role_name] = user

    # Disabled user
    disabled_id = SEED_USER_IDS["disabled"]
    user = await db.get(User, disabled_id)
    if not user:
        user = User(
            id=disabled_id,
            email="disabled@test.com",
            password_hash=TEST_PASSWORD_HASH,
            full_name="Disabled Navigator",
            role_id=SEED_ROLE_IDS["navigator"],
            is_active=False,
        )
        db.add(user)
    else:
        user.role_id = SEED_ROLE_IDS["navigator"]
        user.is_active = False
        user.password_hash = TEST_PASSWORD_HASH
    users["disabled"] = user

    await db.flush()

    # Seed patients
    navigator_id = SEED_USER_IDS["navigator"]

    patients_seed = [
        {
            "id": SEED_PATIENT_IDS["p001"],
            "full_name": "Aarav Mehta",
            "age": 45,
            "gender": "male",
            "phone": "+919876543210",
            "email": "aarav@example.org",
            "address": "123 Main St, Mumbai",
            "emergency_contact_name": "Priya Mehta",
            "emergency_contact_phone": "+919876543211",
            "status": "active",
            "created_by": navigator_id,
        },
        {
            "id": SEED_PATIENT_IDS["p002"],
            "full_name": "Arun Kumar",
            "age": 32,
            "gender": "male",
            "phone": "+919998887776",
            "status": "active",
            "created_by": navigator_id,
        },
        {
            "id": SEED_PATIENT_IDS["p003"],
            "full_name": "Priya Sharma",
            "age": 28,
            "gender": "female",
            "phone": "+919112233445",
            "email": "priya@example.org",
            "status": "active",
            "created_by": navigator_id,
        },
        {
            "id": SEED_PATIENT_IDS["p_archived"],
            "full_name": "Old Patient",
            "age": 60,
            "gender": "female",
            "status": "archived",
            "created_by": navigator_id,
            "deleted_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        },
        {
            "id": SEED_PATIENT_IDS["p_own"],
            "full_name": "Own Patient",
            "age": 40,
            "gender": "male",
            "phone": "+919000000001",
            "status": "active",
            "created_by": navigator_id,
        },
    ]

    patients = {}
    for pdata in patients_seed:
        patient = await db.get(Patient, pdata["id"])
        if not patient:
            patient = Patient(**pdata)
            db.add(patient)
        patients[pdata["id"]] = patient
    await db.flush()

    # Seed cases
    cases_seed = [
        {
            "id": SEED_CASE_IDS["c001"],
            "patient_id": SEED_PATIENT_IDS["p001"],
            "diagnosis": "Stage 2B Oral Cancer",
            "status": "new",
            "priority": "high",
            "notes": "Biopsy confirmed",
            "created_by": navigator_id,
        },
        {
            "id": SEED_CASE_IDS["c002"],
            "patient_id": SEED_PATIENT_IDS["p001"],
            "diagnosis": "Hypertension",
            "status": "under_review",
            "priority": "medium",
            "created_by": navigator_id,
        },
        {
            "id": SEED_CASE_IDS["c003"],
            "patient_id": SEED_PATIENT_IDS["p002"],
            "diagnosis": "Type 2 Diabetes",
            "status": "closed",
            "priority": "low",
            "created_by": navigator_id,
            "closed_at": __import__("datetime").datetime.now(__import__("datetime").timezone.utc),
        },
    ]

    cases = {}
    for cdata in cases_seed:
        case = await db.get(Case, cdata["id"])
        if not case:
            case = Case(**cdata)
            db.add(case)
        cases[cdata["id"]] = case
    await db.flush()

    return {"users": users, "patients": patients, "cases": cases}


async def cleanup_test_artifacts(db: AsyncSession) -> None:
    """Remove non-seed users and refresh tokens created by registration tests."""
    seed_user_ids = list(SEED_USER_IDS.values())
    await db.execute(
        delete(User).where(User.id.notin_(seed_user_ids))
    )
    await db.flush()


def _get_permissions(role_name: str) -> dict:
    """Return the permission matrix for a role."""
    matrices = {
        "admin": {
            "patients": "full", "cases": "full", "documents": "full",
            "hospitals": "full", "funding": "full", "followups": "full",
            "ai": "full", "reports": "full", "users": "full", "audit": "full",
        },
        "navigator": {
            "patients": "full", "cases": "full", "documents": "full",
            "hospitals": "read", "funding": "read", "followups": "full",
            "ai": "full", "reports": "read", "users": "none", "audit": "none",
        },
        "clinician": {
            "patients": "read", "cases": "read", "documents": "read",
            "hospitals": "read", "funding": "read", "followups": "read",
            "ai": "review", "reports": "read", "users": "none", "audit": "none",
        },
        "volunteer": {
            "patients": "read", "cases": "read", "documents": "none",
            "hospitals": "read", "funding": "read", "followups": "read",
            "ai": "none", "reports": "none", "users": "none", "audit": "none",
        },
        "patient": {
            "patients": "own", "cases": "own", "documents": "own",
            "hospitals": "read", "funding": "read", "followups": "own",
            "ai": "own", "reports": "own", "users": "none", "audit": "none",
        },
    }
    return matrices.get(role_name, {})
