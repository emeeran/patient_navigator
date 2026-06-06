"""CSV parsing and bulk import for hospitals, NGOs, and doctors."""

import csv
import io
import uuid

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.doctor import Doctor
from app.models.funding_program import FundingProgram
from app.models.hospital import Hospital
from app.services.auth_service import write_audit_log

# ── CSV Parsers ──────────────────────────────────────────


def parse_hospitals_csv(content: bytes) -> tuple[list[dict], list[str]]:
    """Parse a CSV file of hospitals. Returns (records, errors)."""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    records = []
    errors = []
    for i, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        city = row.get("city", "").strip()
        if not name:
            errors.append(f"Row {i}: missing 'name'")
            continue
        if not city:
            errors.append(f"Row {i}: missing 'city'")
            continue

        fin_aid = row.get("has_financial_assistance", "false").strip().lower()
        records.append({
            "name": name,
            "city": city,
            "state": row.get("state", "").strip() or None,
            "address": row.get("address", "").strip() or None,
            "phone": row.get("phone", "").strip() or None,
            "email": row.get("email", "").strip() or None,
            "website": row.get("website", "").strip() or None,
            "specialties": row.get("specialties", "").strip() or None,
            "has_financial_assistance": fin_aid in ("true", "1", "yes"),
        })
    return records, errors


def parse_ngos_csv(content: bytes) -> tuple[list[dict], list[str]]:
    """Parse a CSV file of NGOs/funding programs. Returns (records, errors)."""
    text = content.decode("utf-8-sig")
    reader = csv.DictReader(io.StringIO(text))
    records = []
    errors = []
    for i, row in enumerate(reader, start=2):
        name = row.get("name", "").strip()
        if not name:
            errors.append(f"Row {i}: missing 'name'")
            continue

        max_amt = (row.get("max_amount") or "").strip()
        min_amt = (row.get("min_amount") or "").strip()

        records.append({
            "name": name,
            "description": row.get("description", "").strip() or None,
            "provider": row.get("provider", "").strip() or None,
            "program_type": row.get("program_type", "").strip() or None,
            "eligibility_criteria": row.get("eligibility_criteria", "").strip() or None,
            "max_amount": float(max_amt) if max_amt else None,
            "min_amount": float(min_amt) if min_amt else None,
            "application_url": row.get("application_url", "").strip() or None,
            "contact_email": row.get("contact_email", "").strip() or None,
            "contact_phone": row.get("contact_phone", "").strip() or None,
        })
    return records, errors


# ── Bulk Import ──────────────────────────────────────────


async def bulk_import_hospitals(
    db: AsyncSession, records: list[dict], actor_id: uuid.UUID
) -> dict:
    """Bulk insert hospitals. Deduplicates by name + city."""
    imported = 0
    skipped = 0
    errors = []

    for rec in records:
        try:
            existing = await db.execute(
                select(Hospital).where(
                    Hospital.name == rec["name"],
                    Hospital.city == rec["city"],
                    Hospital.is_active.is_(True),
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            hospital = Hospital(
                name=rec["name"],
                city=rec["city"],
                state=rec.get("state"),
                address=rec.get("address"),
                phone=rec.get("phone"),
                email=rec.get("email"),
                website=rec.get("website"),
                specialties=rec.get("specialties"),
                has_financial_assistance=rec.get("has_financial_assistance", False),
                is_active=True,
            )
            db.add(hospital)
            imported += 1
        except Exception as e:
            errors.append(f"{rec.get('name', '?')}: {str(e)}")

    await db.flush()

    if imported > 0:
        await write_audit_log(
            db,
            action="import.hospitals",
            user_id=actor_id,
            description=f"Bulk imported {imported} hospitals (skipped {skipped})",
        )

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def bulk_import_ngos(
    db: AsyncSession, records: list[dict], actor_id: uuid.UUID
) -> dict:
    """Bulk insert NGOs/funding programs. Deduplicates by name."""
    imported = 0
    skipped = 0
    errors = []

    for rec in records:
        try:
            existing = await db.execute(
                select(FundingProgram).where(
                    FundingProgram.name == rec["name"],
                    FundingProgram.is_active.is_(True),
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            program = FundingProgram(
                name=rec["name"],
                description=rec.get("description"),
                provider=rec.get("provider"),
                program_type=rec.get("program_type"),
                eligibility_criteria=rec.get("eligibility_criteria"),
                max_amount=rec.get("max_amount"),
                min_amount=rec.get("min_amount"),
                application_url=rec.get("application_url"),
                contact_email=rec.get("contact_email"),
                contact_phone=rec.get("contact_phone"),
                is_active=True,
            )
            db.add(program)
            imported += 1
        except Exception as e:
            errors.append(f"{rec.get('name', '?')}: {str(e)}")

    await db.flush()

    if imported > 0:
        await write_audit_log(
            db,
            action="import.ngos",
            user_id=actor_id,
            description=f"Bulk imported {imported} NGOs (skipped {skipped})",
        )

    return {"imported": imported, "skipped": skipped, "errors": errors}


async def bulk_import_doctors(
    db: AsyncSession, records: list[dict], actor_id: uuid.UUID
) -> dict:
    """Bulk insert doctors. Deduplicates by name + city."""
    imported = 0
    skipped = 0
    errors = []

    for rec in records:
        try:
            existing = await db.execute(
                select(Doctor).where(
                    Doctor.name == rec["name"],
                    Doctor.city == rec["city"],
                    Doctor.is_active.is_(True),
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            doctor = Doctor(
                name=rec["name"],
                city=rec["city"],
                state=rec.get("state"),
                address=rec.get("address"),
                phone=rec.get("phone"),
                email=rec.get("email"),
                website=rec.get("website"),
                specialty=rec.get("specialty"),
                qualification=rec.get("qualification"),
                registration_number=rec.get("registration_number"),
                medical_council=rec.get("medical_council"),
                hospital_name=rec.get("hospital_name"),
                practice_type=rec.get("practice_type"),
                latitude=rec.get("latitude"),
                longitude=rec.get("longitude"),
                is_active=True,
            )
            db.add(doctor)
            imported += 1
        except Exception as e:
            errors.append(f"{rec.get('name', '?')}: {str(e)}")

    await db.flush()

    if imported > 0:
        await write_audit_log(
            db,
            action="import.doctors",
            user_id=actor_id,
            description=f"Bulk imported {imported} doctors (skipped {skipped})",
        )

    return {"imported": imported, "skipped": skipped, "errors": errors}
