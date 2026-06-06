"""Scraper service — thin facade delegating to focused modules.

Public API is preserved; existing imports continue to work.
- scraper_helpers: regexes, name cleaning, dedup utilities
- scraper_web: web scraping (OSM, DuckDuckGo, Bing, JustDuck, TN district)
- scraper_import: CSV parsing and bulk DB import
"""

import uuid

from sqlalchemy.ext.asyncio import AsyncSession

# Re-export public symbols for backward compatibility with tests and callers
from app.services.scraper_helpers import (  # noqa: F401
    EMAIL_RE,
    PHONE_RE,
    PIN_RE,
    _clean_entity_name,
    _extract_between,
    _is_valid_entity_name,
    dedup_records,
)
from app.services.scraper_import import (
    bulk_import_doctors,
    bulk_import_hospitals,
    bulk_import_ngos,
    parse_hospitals_csv,
    parse_ngos_csv,
)
from app.services.scraper_web import (
    scrape_city,
    scrape_tn_district,
)


class ScraperService:
    """TN district hospital scraper, CSV parsing, and bulk import.

    Delegates to scraper_web, scraper_import, and scraper_helpers modules.
    """

    def __init__(self, db: AsyncSession):
        self.db = db

    # ── TN District Hospital Scraper ────────────────────

    async def scrape_tn_district(self, url: str) -> list[dict]:
        """Scrape hospital listings from a TN district nic.in page."""
        return await scrape_tn_district(url)

    # ── City-based Scraper ────────────────────────────────

    async def scrape_city(
        self, city: str, entity_type: str, state: str | None = None
    ) -> list[dict]:
        """Scrape hospitals, NGOs, or doctors for a given city."""
        return await scrape_city(city, entity_type, state)

    # ── CSV Parsers ─────────────────────────────────────

    def parse_hospitals_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """Parse a CSV file of hospitals. Returns (records, errors)."""
        return parse_hospitals_csv(content)

    def parse_ngos_csv(self, content: bytes) -> tuple[list[dict], list[str]]:
        """Parse a CSV file of NGOs/funding programs. Returns (records, errors)."""
        return parse_ngos_csv(content)

    # ── Bulk Import ─────────────────────────────────────

    async def bulk_import_hospitals(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert hospitals. Deduplicates by name + city."""
        return await bulk_import_hospitals(self.db, records, actor_id)

    async def bulk_import_ngos(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert NGOs/funding programs. Deduplicates by name."""
        return await bulk_import_ngos(self.db, records, actor_id)

    async def bulk_import_doctors(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert doctors. Deduplicates by name + city."""
        return await bulk_import_doctors(self.db, records, actor_id)
