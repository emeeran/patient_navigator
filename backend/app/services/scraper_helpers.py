"""Shared scraper utilities — regexes, name cleaning, dedup."""

import re

# ── Regex patterns ───────────────────────────────────────

PIN_RE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
PHONE_RE = re.compile(r"\b(?:\+91[-\s]?)?(?:[6-9]\d{9}|[0-9]{3,5}[-\s]?[0-9]{5,8})\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# ── Name filtering ───────────────────────────────────────

_SKIP_NAME_PARTS = [
    "list of", "top 10", "top 5", "top 20", "best hospital",
    "directory", "updated list", "pdf", "docindia", "medindia",
    "medicine india", "scribd", "hospital near me", "full contact",
    "hospitals near me", "find hospital", "search hospital",
    "innayat", "book appointment", "compare hospital",
]
_SKIP_NAME_EXACT = [
    "hospitals", "hospital", "ngo", "ngos", "hospital in", "hospitals in",
]

# ── HTTP headers ─────────────────────────────────────────

SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


def _is_valid_entity_name(name: str) -> bool:
    """Filter out directory pages, listicles, and non-entity search results."""
    lower = name.lower().strip()
    if len(lower) < 4:
        return False
    if lower in _SKIP_NAME_EXACT:
        return False
    return all(not (part in lower and len(lower) < 80) for part in _SKIP_NAME_PARTS)


def _clean_entity_name(name: str) -> str:
    """Clean up scraped entity name by removing site cruft."""
    name = re.split(r"\s*[-–|·]\s*", name)[0].strip()
    name = name.rstrip(".… ")
    name = re.split(r"\s+(?:Address|Phone|Contact|Location|Direction)", name, flags=re.IGNORECASE)[0].strip()
    name = re.sub(r"\s*[\(\[](?:PDF|Updated \d{4}|List|Directory)[^)\]]*[\)\]]", "", name).strip()
    return name[:255]


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


def dedup_records(records: list[dict]) -> list[dict]:
    """Deduplicate records by case-insensitive name, merging fields."""
    seen: dict[str, dict] = {}
    for rec in records:
        key = rec.get("name", "").lower().strip()
        if not key:
            continue
        if key not in seen:
            seen[key] = rec
        else:
            existing = seen[key]
            for field, val in rec.items():
                if not existing.get(field) and val:
                    existing[field] = val
    return list(seen.values())
