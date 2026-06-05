"""Scraper service — TN district hospital pages, CSV parsing, bulk import."""

import csv
import io
import logging
import re
import uuid
from urllib.parse import urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.funding_program import FundingProgram
from app.models.hospital import Hospital
from app.services.auth_service import write_audit_log

logger = logging.getLogger(__name__)

# ── Regex patterns (from reference docs) ───────────────

PIN_RE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
PHONE_RE = re.compile(r"\b(?:\+91[-\s]?)?(?:[6-9]\d{9}|[0-9]{3,5}[-\s]?[0-9]{5,8})\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")


def _extract_between(label_start: str, label_end: str | None, text: str) -> str:
    """Return substring between label_start and label_end (or end of text)."""
    start = re.search(label_start, text, flags=re.IGNORECASE)
    if not start:
        return ""
    start_idx = start.end()
    if label_end:
        end = re.search(label_end, text, flags=re.IGNORECASE)
        end_idx = end.start() if end else len(text)
    else:
        end_idx = len(text)
    return text[start_idx:end_idx]


class ScraperService:
    """TN district hospital scraper, CSV parsing, and bulk import."""

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── TN District Hospital Scraper ────────────────────

    async def scrape_tn_district(self, url: str) -> list[dict]:
        """Scrape hospital listings from a TN district nic.in page.

        Returns a list of dicts ready for Hospital model insertion.
        Does NOT insert into the database — only returns parsed data.
        """
        # Derive district name from URL
        parsed = urlparse(url)
        hostname = parsed.hostname or ""
        district = hostname.replace(".nic.in", "").replace("www.", "")
        district_title = district.replace("-", " ").title()

        try:
            async with httpx.AsyncClient(timeout=15.0, follow_redirects=True) as client:
                response = await client.get(url)
                response.raise_for_status()
                html = response.text
        except httpx.HTTPError as e:
            raise ValueError(f"Failed to fetch page: {e}") from e

        soup = BeautifulSoup(html, "lxml")

        # Find content root — article or body
        content_root = soup.find("article") or soup.find("div", class_="field-items") or soup.body
        if not content_root:
            return []

        records = []
        for h2 in content_root.find_all("h2"):
            name = h2.get_text(strip=True)
            if not name or len(name) < 3:
                continue

            # Collect sibling text until next h2
            details_nodes = []
            for sib in h2.find_next_siblings():
                if sib.name == "h2":
                    break
                if sib.name in ("p", "div", "ul", "li", "span"):
                    details_nodes.append(sib.get_text(" ", strip=True))

            details_text = " ".join(details_nodes)

            # Deobfuscate [at] and [dot] patterns
            details_text = details_text.replace("[at]", "@").replace("[dot]", ".")
            details_text = details_text.replace("(at)", "@").replace("(dot)", ".")

            # Extract phone and email — order-agnostic label extraction
            phone_block = _extract_between(r"Phone\s*:", r"Email\s*:|Pincode\s*:|Category|Type\s*:", details_text)
            email_block = _extract_between(r"Email\s*:", r"Phone\s*:|Pincode\s*:|Category|Type\s*:", details_text)

            # If blocks are empty, try extracting from full text
            if not phone_block.strip():
                phone_block = details_text
            if not email_block.strip():
                email_block = details_text

            phones = PHONE_RE.findall(phone_block)
            phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]
            phone = phones[0] if phones else None

            emails = EMAIL_RE.findall(email_block)
            email = emails[0] if emails else None

            # Extract pincode for address context
            pin_candidates = PIN_RE.findall(details_text)
            pin_candidates = [p.replace(" ", "") for p in pin_candidates]
            pincode = pin_candidates[-1] if pin_candidates else None

            # Extract category/type
            category_match = re.search(r"Category\s*/\s*Type\s*:\s*(.+?)(?:\s{2,}|Phone|Email|Pincode|\Z)", details_text, re.IGNORECASE)
            category = category_match.group(1).strip() if category_match else None

            # Build address from text before phone/email labels
            addr_part = re.split(r"Phone\s*:|Email\s*:|Category\s*/\s*Type\s*:|Pincode\s*:", details_text, maxsplit=1)[0].strip()
            address = addr_part if addr_part else None
            if pincode and address and pincode not in address:
                address = f"{address}, PIN: {pincode}"

            # Determine city — use category or district name
            city = district_title

            # Determine facility type for specialties
            specialties = None
            if category:
                type_lower = category.lower()
                if "medical college" in type_lower:
                    specialties = "Medical College, Multi-Specialty"
                elif "district" in type_lower and "hospital" in type_lower:
                    specialties = "General Medicine, Surgery, Emergency"
                elif "taluk" in type_lower:
                    specialties = "General Medicine, Emergency"
                elif "primary health" in type_lower or "phc" in type_lower:
                    specialties = "Primary Care"

            records.append({
                "name": name,
                "city": city,
                "state": "Tamil Nadu",
                "address": address,
                "phone": phone,
                "email": email,
                "website": url,
                "specialties": specialties,
                "has_financial_assistance": False,
            })

        return records

    # ── CSV Parsers ─────────────────────────────────────

    def parse_hospitals_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """Parse a CSV file of hospitals. Returns (records, errors)."""
        text = content.decode("utf-8-sig")
        reader = csv.DictReader(io.StringIO(text))
        records = []
        errors = []
        for i, row in enumerate(reader, start=2):  # line 2 = first data row
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

    def parse_ngos_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
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

    # ── Bulk Import ─────────────────────────────────────

    async def bulk_import_hospitals(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert hospitals. Deduplicates by name + city."""
        imported = 0
        skipped = 0
        errors = []

        for rec in records:
            try:
                # Check for duplicate
                existing = await self.db.execute(
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
                self.db.add(hospital)
                imported += 1
            except Exception as e:
                errors.append(f"{rec.get('name', '?')}: {str(e)}")

        await self.db.flush()

        if imported > 0:
            await write_audit_log(
                self.db,
                action="import.hospitals",
                user_id=actor_id,
                description=f"Bulk imported {imported} hospitals (skipped {skipped})",
            )

        return {"imported": imported, "skipped": skipped, "errors": errors}

    async def bulk_import_ngos(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert NGOs/funding programs. Deduplicates by name."""
        imported = 0
        skipped = 0
        errors = []

        for rec in records:
            try:
                # Check for duplicate
                existing = await self.db.execute(
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
                self.db.add(program)
                imported += 1
            except Exception as e:
                errors.append(f"{rec.get('name', '?')}: {str(e)}")

        await self.db.flush()

        if imported > 0:
            await write_audit_log(
                self.db,
                action="import.ngos",
                user_id=actor_id,
                description=f"Bulk imported {imported} NGOs (skipped {skipped})",
            )

        return {"imported": imported, "skipped": skipped, "errors": errors}
