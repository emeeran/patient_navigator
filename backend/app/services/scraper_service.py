"""Scraper service — city-based scraping, TN district pages, CSV parsing, bulk import."""

import asyncio
import csv
import io
import logging
import re
import uuid
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.doctor import Doctor
from app.models.funding_program import FundingProgram
from app.models.hospital import Hospital
from app.services.auth_service import write_audit_log

logger = logging.getLogger(__name__)

# ── Regex patterns (from reference docs) ───────────────

PIN_RE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
PHONE_RE = re.compile(r"\b(?:\+91[-\s]?)?(?:[6-9]\d{9}|[0-9]{3,5}[-\s]?[0-9]{5,8})\b")
EMAIL_RE = re.compile(r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b")

# ── Name filtering for search results ───────────────────

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


def _is_valid_entity_name(name: str) -> bool:
    """Filter out directory pages, listicles, and non-entity search results."""
    lower = name.lower().strip()
    if len(lower) < 4:
        return False
    # Skip purely generic directory/listing titles
    if lower in _SKIP_NAME_EXACT:
        return False
    # Skip titles that are clearly list/directory pages
    for part in _SKIP_NAME_PARTS:
        if part in lower and len(lower) < 80:
            return False
    return True


def _clean_entity_name(name: str) -> str:
    """Clean up scraped entity name by removing site cruft."""
    # Remove common suffixes from search titles
    name = re.split(r"\s*[-–|·]\s*", name)[0].strip()
    # Remove trailing ellipsis or dots
    name = name.rstrip(".… ")
    # Remove " - Address | Phone" type suffixes
    name = re.split(r"\s+(?:Address|Phone|Contact|Location|Direction)", name, flags=re.IGNORECASE)[0].strip()
    # Remove parenthetical site names
    name = re.sub(r"\s*[\(\[](?:PDF|Updated \d{4}|List|Directory)[^)\]]*[\)\]]", "", name).strip()
    return name[:255]


# Headers for external web scraping
_SCRAPER_HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
        "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36"
    ),
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}


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

    # ── City-based Scraper ────────────────────────────────

    async def scrape_city(
        self, city: str, entity_type: str, state: str | None = None
    ) -> list[dict]:
        """Scrape hospitals or NGOs for a given city from public web sources.

        Args:
            city: City name (e.g. "Chennai", "Coimbatore").
            entity_type: "hospitals" or "ngos".
            state: Optional state name for better search results.

        Returns:
            List of dicts ready for import (hospital or NGO schema).
        """
        city_clean = city.strip().title()
        state_clean = (state or "").strip()
        results: list[dict] = []

        if entity_type == "hospitals":
            results = await self._scrape_hospitals_by_city(city_clean, state_clean)
        elif entity_type == "ngos":
            results = await self._scrape_ngos_by_city(city_clean, state_clean)
        elif entity_type == "doctors":
            results = await self._scrape_doctors_by_city(city_clean, state_clean)

        return self._dedup(results)

    # ── Doctor Scraper ────────────────────────────────────

    async def _scrape_doctors_by_city(
        self, city: str, state: str
    ) -> list[dict]:
        """Scrape doctors/clinics for a city from OpenStreetMap."""
        results: list[dict] = []
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f"""[out:json][timeout:25];
area["name"="{city}"]->.a;
(
  node["healthcare"="doctor"](area.a);
  node["amenity"="doctors"](area.a);
  node["healthcare"="dentist"](area.a);
  node["amenity"="dentist"](area.a);
  node["healthcare"="clinic"](area.a);
  node["amenity"="clinic"](area.a);
  way["healthcare"="doctor"](area.a);
  way["amenity"="doctors"](area.a);
  way["healthcare"="clinic"](area.a);
  way["amenity"="clinic"](area.a);
);
out center body;"""
            async with httpx.AsyncClient(
                headers=_SCRAPER_HEADERS, timeout=30.0
            ) as client:
                resp = await client.post(overpass_url, data={"data": query})
                if resp.status_code != 200:
                    logger.warning(f"Overpass returned {resp.status_code} for doctors in {city}")
                    return results

                data = resp.json()
                for elem in data.get("elements", []):
                    tags = elem.get("tags", {})
                    name = tags.get("name", "").strip()
                    if not name or len(name) < 2:
                        continue

                    # Skip generic names
                    if name.lower() in ("clinic", "doctor", "dentist", "pharmacy",
                                        "hospital", "doctor's", "doctors"):
                        continue

                    phone = tags.get("phone") or tags.get("contact:phone") or ""
                    if phone:
                        phone_digits = re.sub(r"[^\d]", "", phone)
                        phone = phone_digits[-10:] if len(phone_digits) >= 7 else None
                    else:
                        phone = None

                    email = tags.get("email") or tags.get("contact:email") or None
                    website = tags.get("website") or tags.get("contact:website") or None

                    # Build address
                    addr_parts = []
                    if tags.get("addr:housenumber"):
                        addr_parts.append(tags["addr:housenumber"])
                    if tags.get("addr:street"):
                        addr_parts.append(tags["addr:street"])
                    if tags.get("addr:suburb"):
                        addr_parts.append(tags["addr:suburb"])
                    if tags.get("addr:city"):
                        addr_parts.append(tags["addr:city"])
                    if tags.get("addr:postcode"):
                        addr_parts.append(tags["addr:postcode"])
                    address = ", ".join(addr_parts) if addr_parts else None

                    # Specialty
                    specialty = (
                        tags.get("healthcare:speciality")
                        or tags.get("speciality")
                        or tags.get("medical_specialty")
                        or None
                    )
                    if specialty:
                        specialty = specialty.replace(";", ", ")

                    # Determine practice type
                    healthcare_type = tags.get("healthcare") or tags.get("amenity") or ""
                    operator = (tags.get("operator") or "").lower()
                    is_govt = any(
                        w in operator for w in ["government", "govt", "gov ", "public", "municipal", "phc"]
                    )

                    # Qualification
                    qualification = None
                    if "MBBS" in name.upper() or "MD" in name.upper() or "MS" in name.upper():
                        # Try to extract from name
                        qual_match = re.search(r"\b(MBBS|MD|MS|DNB|BDS|MDS|DDVL|DM|MCh|BAMS|BHMS)\b", name, re.IGNORECASE)
                        if qual_match:
                            qualification = qual_match.group(1).upper()

                    # Hospital / clinic name
                    hospital_name = None
                    if tags.get("addr:housename"):
                        hospital_name = tags["addr:housename"]
                    # If name doesn't look like a person name, it might be a clinic
                    name_parts = name.split()
                    is_likely_person = (
                        any(p.endswith(".") or p.lower() in ("dr", "dr.", "doctor", "prof") for p in name_parts)
                        or name.lower().startswith("dr ")
                        or name.lower().startswith("dr.")
                    )
                    if not is_likely_person and "clinic" in name.lower() or "hospital" in name.lower() or "medical" in name.lower():
                        # It's a clinic/hospital name, not a doctor's name
                        hospital_name = name

                    # Coordinates
                    lat = elem.get("lat") or elem.get("center", {}).get("lat")
                    lon = elem.get("lon") or elem.get("center", {}).get("lon")

                    results.append({
                        "name": name[:255],
                        "city": city,
                        "state": state or None,
                        "address": address,
                        "phone": phone,
                        "email": email,
                        "website": website,
                        "specialty": specialty,
                        "qualification": qualification,
                        "registration_number": None,
                        "medical_council": None,
                        "hospital_name": hospital_name,
                        "practice_type": "government" if is_govt else "private",
                        "latitude": float(lat) if lat else None,
                        "longitude": float(lon) if lon else None,
                    })

                logger.info(f"Overpass: found {len(results)} doctors/clinics for {city}")

        except Exception as e:
            logger.warning(f"Overpass doctor scrape error for {city}: {e}")

        return results

    async def _scrape_hospitals_by_city(
        self, city: str, state: str
    ) -> list[dict]:
        """Scrape hospitals from multiple web sources for a city."""
        results: list[dict] = []

        # Source 1: OpenStreetMap Overpass API (primary — reliable, free, structured)
        osm_results = await self._scrape_osm_hospitals(city, state)
        results.extend(osm_results)

        # Source 2: Web search (supplementary)
        async with httpx.AsyncClient(
            headers=_SCRAPER_HEADERS, timeout=20.0, follow_redirects=True
        ) as client:
            web_results = await self._scrape_google_hospitals(client, city, state)
            results.extend(web_results)
            await asyncio.sleep(1.5)

            # Source 3: Justdial
            jd_results = await self._scrape_justdial_hospitals(client, city)
            results.extend(jd_results)

        return results

    async def _scrape_osm_hospitals(self, city: str, state: str) -> list[dict]:
        """Scrape hospitals from OpenStreetMap Overpass API."""
        results: list[dict] = []
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            # Search by city name area
            query = f"""
[out:json][timeout:25];
area["name"="{city}"]->.searchArea;
(
  node["amenity"="hospital"](area.searchArea);
  way["amenity"="hospital"](area.searchArea);
  relation["amenity"="hospital"](area.searchArea);
);
out center body;
"""
            async with httpx.AsyncClient(
                headers=_SCRAPER_HEADERS, timeout=30.0
            ) as client:
                resp = await client.post(overpass_url, data={"data": query})
                if resp.status_code != 200:
                    logger.warning(f"Overpass API returned {resp.status_code}")
                    return results

                data = resp.json()
                for elem in data.get("elements", []):
                    tags = elem.get("tags", {})
                    name = tags.get("name", "").strip()
                    if not name or len(name) < 2:
                        continue

                    # Skip generic names
                    if name.lower() in ("hospital", "clinica", " dispensary"):
                        continue

                    phone = tags.get("phone") or tags.get("contact:phone") or ""
                    if phone:
                        phone_digits = re.sub(r"[^\d+]", "", phone)
                        if len(phone_digits) > 10:
                            phone_digits = phone_digits[-10:]
                        phone = phone_digits if len(phone_digits) >= 7 else None
                    else:
                        phone = None

                    email = tags.get("email") or tags.get("contact:email") or None
                    website = tags.get("website") or tags.get("contact:website") or None

                    # Build address from OSM tags
                    addr_parts = []
                    if tags.get("addr:street"):
                        addr_parts.append(tags["addr:street"])
                    if tags.get("addr:city"):
                        addr_parts.append(tags["addr:city"])
                    if tags.get("addr:postcode"):
                        addr_parts.append(tags["addr:postcode"])
                    address = ", ".join(addr_parts) if addr_parts else None

                    # Determine specialties
                    specialties = tags.get("healthcare:speciality") or None
                    if specialties:
                        specialties = specialties.replace(";", ", ")

                    # Check if government
                    operator = (tags.get("operator") or "").lower()
                    is_govt = any(
                        w in operator for w in ["government", "govt", "gov ", "public", "municipal"]
                    ) or tags.get("ownership") == "government"

                    # Get coordinates
                    lat = elem.get("lat") or elem.get("center", {}).get("lat")
                    lon = elem.get("lon") or elem.get("center", {}).get("lon")

                    results.append({
                        "name": name[:255],
                        "city": city,
                        "state": state or None,
                        "address": address,
                        "phone": phone,
                        "email": email,
                        "website": website,
                        "specialties": specialties,
                        "has_financial_assistance": is_govt,
                        "latitude": float(lat) if lat else None,
                        "longitude": float(lon) if lon else None,
                    })

                logger.info(f"Overpass: found {len(results)} hospitals for {city}")

        except Exception as e:
            logger.warning(f"Overpass API error for {city}: {e}")

        return results

    async def _scrape_google_hospitals(
        self, client: httpx.AsyncClient, city: str, state: str
    ) -> list[dict]:
        """Scrape hospital names from DuckDuckGo HTML search results."""
        results: list[dict] = []
        location = f"{city} {state}".strip()
        queries = [
            f"list of hospitals in {location}",
            f"government hospitals in {location}",
            f"top hospitals in {location}",
        ]

        for query in queries:
            # Try DuckDuckGo HTML (more scraper-friendly)
            try:
                url = f"https://html.duckduckgo.com/html/?q={quote(query)}"
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for result_div in soup.select(".result"):
                        title_el = result_div.select_one(".result__title a, .result__a")
                        if not title_el:
                            continue
                        name = _clean_entity_name(title_el.get_text(strip=True))
                        if not _is_valid_entity_name(name):
                            continue

                        skip_words = ["wikipedia", "youtube", "facebook", "twitter", "instagram",
                                      "linkedin", "play store", "app store", "news", "images",
                                      "justdial", "practo", "lybrate", "credence", "policybazaar",
                                      "docindia", "medindia", "medicine india", "scribd"]
                        if any(w in name.lower() for w in skip_words):
                            continue

                        # Extract snippet
                        snippet_el = result_div.select_one(".result__snippet")
                        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                        # Extract phone/email from snippet
                        phones = PHONE_RE.findall(snippet)
                        phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None
                        emails = EMAIL_RE.findall(snippet)
                        email = emails[0] if emails else None

                        # Check if government
                        combined = (name + " " + snippet).lower()
                        is_govt = any(w in combined for w in ["government", "govt", "gov.", "public hospital", "esic", "esi ", "medical college"])

                        # Try to extract specialties
                        specialties = None
                        spec_match = re.search(
                            r"(?:speciali[sz]|department|service|treatment)[:\s]+([^.;]+)",
                            snippet, re.IGNORECASE,
                        )
                        if spec_match:
                            specialties = spec_match.group(1).strip()[:200]

                        results.append({
                            "name": name[:255],
                            "city": city,
                            "state": state or None,
                            "address": None,
                            "phone": phone,
                            "email": email,
                            "website": None,
                            "specialties": specialties,
                            "has_financial_assistance": is_govt,
                        })
            except Exception as e:
                logger.warning(f"DuckDuckGo scrape error for '{query}': {e}")

            await asyncio.sleep(1.0)

            # Also try Bing
            try:
                url = f"https://www.bing.com/search?q={quote(query)}&count=30"
                resp = await client.get(url)
                if resp.status_code == 200:
                    soup = BeautifulSoup(resp.text, "lxml")
                    for li in soup.select("#b_results > li.b_algo"):
                        title_el = li.find("h2")
                        if not title_el:
                            continue
                        name = _clean_entity_name(title_el.get_text(strip=True))
                        if not _is_valid_entity_name(name):
                            continue

                        skip_words = ["wikipedia", "youtube", "facebook", "twitter", "instagram",
                                      "linkedin", "justdial", "practo", "lybrate", "policybazaar",
                                      "docindia", "medindia", "medicine india", "scribd"]
                        if any(w in name.lower() for w in skip_words):
                            continue

                        snippet_el = li.find("p") or li.select_one(".b_caption p")
                        snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                        phones = PHONE_RE.findall(snippet)
                        phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None
                        emails = EMAIL_RE.findall(snippet)
                        email = emails[0] if emails else None

                        combined = (name + " " + snippet).lower()
                        is_govt = any(w in combined for w in ["government", "govt", "gov.", "public hospital", "esic", "esi ", "medical college"])

                        results.append({
                            "name": name[:255],
                            "city": city,
                            "state": state or None,
                            "address": None,
                            "phone": phone,
                            "email": email,
                            "website": None,
                            "specialties": None,
                            "has_financial_assistance": is_govt,
                        })
            except Exception as e:
                logger.warning(f"Bing scrape error for '{query}': {e}")

            await asyncio.sleep(1.0)

        return results

    async def _scrape_justdial_hospitals(
        self, client: httpx.AsyncClient, city: str
    ) -> list[dict]:
        """Scrape hospital listings from Justdial for a city."""
        results: list[dict] = []
        city_slug = city.lower().replace(" ", "-")
        urls = [
            f"https://www.justdial.com/{city_slug}/Hospitals-in-{city_slug}/nct-10180326",
            f"https://www.justdial.com/{city_slug}/Government-Hospitals-in-{city_slug}/nct-10180326",
        ]

        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Justdial returned {resp.status_code} for {url}")
                    continue

                soup = BeautifulSoup(resp.text, "lxml")

                for card in soup.select(".cntanr, .store-details, [class*='listbox']"):
                    name_el = card.select_one(
                        ".store-name, .lng_cont_name, [class*='jcn'], span.fn"
                    )
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if not name or len(name) < 3:
                        continue

                    addr_el = card.select_one(
                        ".address-text, .cnt_addr, [class*='address'], .addr"
                    )
                    address = addr_el.get_text(strip=True) if addr_el else None

                    phone_el = card.select_one(
                        ".contact-info, .phone-no, [class*='tel'], .tooltip"
                    )
                    phone_text = phone_el.get_text(strip=True) if phone_el else ""
                    phones = PHONE_RE.findall(phone_text)
                    phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None

                    results.append({
                        "name": name[:255],
                        "city": city,
                        "state": None,
                        "address": address,
                        "phone": phone,
                        "email": None,
                        "website": None,
                        "specialties": None,
                        "has_financial_assistance": False,
                    })

                await asyncio.sleep(1.5)
            except Exception as e:
                logger.warning(f"Justdial scrape error for {url}: {e}")

        return results

    async def _scrape_ngos_by_city(
        self, city: str, state: str
    ) -> list[dict]:
        """Scrape NGO/funding program listings for a city."""
        results: list[dict] = []

        # Source 1: OpenStreetMap Overpass API
        try:
            overpass_url = "https://overpass-api.de/api/interpreter"
            query = f"""[out:json][timeout:25];
area["name"="{city}"]->.a;
(
  node["office"="ngo"](area.a);
  node["office"="charity"](area.a);
  node["office"="association"](area.a);
  node["social_facility"](area.a);
  node["amenity"="social_facility"](area.a);
  way["office"="ngo"](area.a);
  way["office"="charity"](area.a);
  way["social_facility"](area.a);
);
out center body;
"""
            async with httpx.AsyncClient(
                headers=_SCRAPER_HEADERS, timeout=30.0
            ) as client:
                resp = await client.post(overpass_url, data={"data": query})
                if resp.status_code == 200:
                    data = resp.json()
                    for elem in data.get("elements", []):
                        tags = elem.get("tags", {})
                        name = tags.get("name", "").strip()
                        if not name or len(name) < 2:
                            continue

                        email = tags.get("email") or tags.get("contact:email") or None
                        phone = tags.get("phone") or tags.get("contact:phone") or ""
                        if phone:
                            phone = re.sub(r"[^\d]", "", phone)[-10:]
                        else:
                            phone = None
                        website = tags.get("website") or tags.get("contact:website") or None

                        # Determine type
                        office = tags.get("office", "")
                        if "charity" in office or "trust" in name.lower():
                            program_type = "charitable_trust"
                        elif "foundation" in name.lower():
                            program_type = "foundation"
                        elif "society" in name.lower():
                            program_type = "society"
                        else:
                            program_type = "ngo"

                        description = tags.get("description") or tags.get("note") or None

                        results.append({
                            "name": name[:255],
                            "description": description,
                            "provider": name[:255],
                            "program_type": program_type,
                            "eligibility_criteria": None,
                            "max_amount": None,
                            "min_amount": None,
                            "application_url": website,
                            "contact_email": email,
                            "contact_phone": phone,
                        })
                    logger.info(f"Overpass: found {len(results)} NGOs for {city}")
        except Exception as e:
            logger.warning(f"Overpass NGO error for {city}: {e}")

        # Source 2: Web search (supplementary — only add meaningful results)
        async with httpx.AsyncClient(
            headers=_SCRAPER_HEADERS, timeout=20.0, follow_redirects=True
        ) as client:
            location = f"{city} {state}".strip()
            queries = [
                f"NGO healthcare medical assistance {location}",
                f"charitable trust hospital funding {location}",
            ]

            for query_text in queries:
                # DuckDuckGo
                try:
                    url = f"https://html.duckduckgo.com/html/?q={quote(query_text)}"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        for result_div in soup.select(".result"):
                            title_el = result_div.select_one(".result__a")
                            if not title_el:
                                continue
                            name = _clean_entity_name(title_el.get_text(strip=True))
                            if not _is_valid_entity_name(name):
                                continue
                            skip_words = ["wikipedia", "youtube", "facebook", "twitter",
                                          "instagram", "linkedin", "justdial", "dictionary",
                                          "meaning", "definition", "adjective"]
                            if any(w in name.lower() for w in skip_words):
                                continue

                            snippet_el = result_div.select_one(".result__snippet")
                            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                            emails = EMAIL_RE.findall(snippet)
                            contact_email = emails[0] if emails else None
                            phones = PHONE_RE.findall(snippet)
                            contact_phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None

                            snippet_lower = snippet.lower()
                            if "trust" in snippet_lower:
                                program_type = "charitable_trust"
                            elif "foundation" in snippet_lower:
                                program_type = "foundation"
                            elif "society" in snippet_lower:
                                program_type = "society"
                            else:
                                program_type = "ngo"

                            results.append({
                                "name": name[:255],
                                "description": snippet[:300].strip() or None,
                                "provider": name[:255],
                                "program_type": program_type,
                                "eligibility_criteria": None,
                                "max_amount": None,
                                "min_amount": None,
                                "application_url": None,
                                "contact_email": contact_email,
                                "contact_phone": contact_phone,
                            })
                except Exception as e:
                    logger.warning(f"NGO DuckDuckGo error for '{query_text}': {e}")

                await asyncio.sleep(1.0)

                # Bing
                try:
                    url = f"https://www.bing.com/search?q={quote(query_text)}&count=20"
                    resp = await client.get(url)
                    if resp.status_code == 200:
                        soup = BeautifulSoup(resp.text, "lxml")
                        for li in soup.select("#b_results > li.b_algo"):
                            title_el = li.find("h2")
                            if not title_el:
                                continue
                            name = _clean_entity_name(title_el.get_text(strip=True))
                            if not _is_valid_entity_name(name):
                                continue
                            skip_words = ["wikipedia", "youtube", "facebook", "twitter",
                                          "instagram", "linkedin", "justdial", "dictionary",
                                          "meaning", "definition", "adjective"]
                            if any(w in name.lower() for w in skip_words):
                                continue

                            snippet_el = li.find("p") or li.select_one(".b_caption p")
                            snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                            emails = EMAIL_RE.findall(snippet)
                            contact_email = emails[0] if emails else None
                            phones = PHONE_RE.findall(snippet)
                            contact_phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None

                            snippet_lower = snippet.lower()
                            if "trust" in snippet_lower:
                                program_type = "charitable_trust"
                            elif "foundation" in snippet_lower:
                                program_type = "foundation"
                            elif "society" in snippet_lower:
                                program_type = "society"
                            else:
                                program_type = "ngo"

                            results.append({
                                "name": name[:255],
                                "description": snippet[:300].strip() or None,
                                "provider": name[:255],
                                "program_type": program_type,
                                "eligibility_criteria": None,
                                "max_amount": None,
                                "min_amount": None,
                                "application_url": None,
                                "contact_email": contact_email,
                                "contact_phone": contact_phone,
                            })
                except Exception as e:
                    logger.warning(f"NGO Bing error for '{query_text}': {e}")

                await asyncio.sleep(1.0)

        return results

    @staticmethod
    def _dedup(records: list[dict]) -> list[dict]:
        """Deduplicate records by case-insensitive name, merging fields."""
        seen: dict[str, dict] = {}
        for rec in records:
            key = rec.get("name", "").lower().strip()
            if not key:
                continue
            if key not in seen:
                seen[key] = rec
            else:
                # Merge — fill missing fields from duplicate
                existing = seen[key]
                for field, val in rec.items():
                    if not existing.get(field) and val:
                        existing[field] = val
        return list(seen.values())

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

    async def bulk_import_doctors(
        self, records: list[dict], actor_id: uuid.UUID
    ) -> dict:
        """Bulk insert doctors. Deduplicates by name + city."""
        imported = 0
        skipped = 0
        errors = []

        for rec in records:
            try:
                existing = await self.db.execute(
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
                self.db.add(doctor)
                imported += 1
            except Exception as e:
                errors.append(f"{rec.get('name', '?')}: {str(e)}")

        await self.db.flush()

        if imported > 0:
            await write_audit_log(
                self.db,
                action="import.doctors",
                user_id=actor_id,
                description=f"Bulk imported {imported} doctors (skipped {skipped})",
            )

        return {"imported": imported, "skipped": skipped, "errors": errors}
