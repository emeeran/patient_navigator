"""Quick seed — creates roles, users, patients, cases via parameterized SQL."""

import asyncio
import os

os.environ["DEBUG"] = "false"

from sqlalchemy import text
from app.core.database import engine
from app.core.security import hash_password

PWD = hash_password("TestPass123!")

ROLES = [
    ("a0000000-0000-0000-0000-000000000001", "admin", "Admin", {
        "patients": "full", "cases": "full", "documents": "full",
        "hospitals": "full", "funding": "full", "followups": "full",
        "ai": "full", "reports": "full", "users": "full", "audit": "full", "settings": "full",
    }),
    ("a0000000-0000-0000-0000-000000000002", "navigator", "Navigator", {
        "patients": "full", "cases": "full", "documents": "full",
        "hospitals": "read", "funding": "read", "followups": "full",
        "ai": "full", "reports": "read",
    }),
    ("a0000000-0000-0000-0000-000000000003", "clinician", "Clinician", {
        "patients": "read", "cases": "read", "documents": "read",
        "hospitals": "read", "funding": "read", "followups": "read",
        "ai": "review", "reports": "read",
    }),
    ("a0000000-0000-0000-0000-000000000004", "volunteer", "Volunteer", {
        "patients": "read", "cases": "read", "documents": "none",
        "hospitals": "read", "funding": "read", "followups": "read",
    }),
    ("a0000000-0000-0000-0000-000000000005", "patient", "Patient", {
        "patients": "own", "cases": "own", "documents": "own",
        "hospitals": "read", "funding": "read", "followups": "own",
    }),
]

USERS = [
    ("b0000000-0000-0000-0000-000000000001", "admin@test.com", "Test Admin", "a0000000-0000-0000-0000-000000000001", True),
    ("b0000000-0000-0000-0000-000000000002", "navigator@test.com", "Test Navigator", "a0000000-0000-0000-0000-000000000002", True),
    ("b0000000-0000-0000-0000-000000000003", "clinician@test.com", "Test Clinician", "a0000000-0000-0000-0000-000000000003", True),
    ("b0000000-0000-0000-0000-000000000004", "volunteer@test.com", "Test Volunteer", "a0000000-0000-0000-0000-000000000004", True),
    ("b0000000-0000-0000-0000-000000000005", "patient@test.com", "Test Patient", "a0000000-0000-0000-0000-000000000005", True),
    ("b0000000-0000-0000-0000-000000000006", "disabled@test.com", "Disabled Navigator", "a0000000-0000-0000-0000-000000000002", False),
]

PATIENTS = [
    ("c0000000-0000-0000-0000-000000000001", "Aarav Mehta", 45, "male", "+919876543210", "aarav@example.org", "123 Main St, Mumbai", "Priya Mehta", "+919876543211", "active"),
    ("c0000000-0000-0000-0000-000000000002", "Arun Kumar", 32, "male", "+919998887776", None, None, None, None, "active"),
    ("c0000000-0000-0000-0000-000000000003", "Priya Sharma", 28, "female", "+919112233445", "priya@example.org", None, None, None, "active"),
]

CASES = [
    ("d0000000-0000-0000-0000-000000000001", "c0000000-0000-0000-0000-000000000001", "Stage 2B Oral Cancer", "new", "high", "Biopsy confirmed"),
    ("d0000000-0000-0000-0000-000000000002", "c0000000-0000-0000-0000-000000000001", "Hypertension", "under_review", "medium", None),
    ("d0000000-0000-0000-0000-000000000003", "c0000000-0000-0000-0000-000000000002", "Type 2 Diabetes", "closed", "low", None),
]

NAV_ID = "b0000000-0000-0000-0000-000000000002"


async def seed():
    import json

    async with engine.begin() as conn:
        # Roles
        for rid, name, desc, perms in ROLES:
            await conn.execute(
                text("""
                    INSERT INTO roles (id, name, description, permissions)
                    VALUES (CAST(:id AS uuid), :name, :desc, CAST(:perms AS jsonb))
                    ON CONFLICT (id) DO UPDATE SET permissions = EXCLUDED.permissions
                """),
                {"id": rid, "name": name, "desc": desc, "perms": json.dumps(perms)},
            )
        print("Roles seeded")

        # Users
        for uid, email, full, role_id, active in USERS:
            await conn.execute(
                text("""
                    INSERT INTO users (id, email, password_hash, full_name, role_id, is_active)
                    VALUES (:id, :email, :pwd, :name, :role, :active)
                    ON CONFLICT (id) DO UPDATE SET
                        password_hash = EXCLUDED.password_hash,
                        is_active = EXCLUDED.is_active,
                        role_id = EXCLUDED.role_id
                """),
                {"id": uid, "email": email, "pwd": PWD, "name": full, "role": role_id, "active": active},
            )
        print("Users seeded")

        # Patients
        for pid, name, age, gender, phone, email, addr, ec_name, ec_phone, status in PATIENTS:
            await conn.execute(
                text("""
                    INSERT INTO patients (id, full_name, age, gender, phone, email, address,
                        emergency_contact_name, emergency_contact_phone, status, created_by)
                    VALUES (:id, :name, :age, :gender, :phone, :email, :addr,
                        :ec_name, :ec_phone, :status, :created_by)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": pid, "name": name, "age": age, "gender": gender,
                    "phone": phone, "email": email, "addr": addr,
                    "ec_name": ec_name, "ec_phone": ec_phone, "status": status,
                    "created_by": NAV_ID,
                },
            )
        print("Patients seeded")

        # Cases
        for cid, pat_id, diag, status, priority, notes in CASES:
            await conn.execute(
                text("""
                    INSERT INTO cases (id, patient_id, diagnosis, status, priority, notes, created_by)
                    VALUES (:id, :pat_id, :diag, :status, :priority, :notes, :created_by)
                    ON CONFLICT (id) DO NOTHING
                """),
                {
                    "id": cid, "pat_id": pat_id, "diag": diag,
                    "status": status, "priority": priority, "notes": notes,
                    "created_by": NAV_ID,
                },
            )
        print("Cases seeded")

    print("\nDone! Login credentials:")
    print("  admin@test.com      / TestPass123!")
    print("  navigator@test.com  / TestPass123!")


asyncio.run(seed())
