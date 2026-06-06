"""Web scraping — OSM, DuckDuckGo, Bing, JustDuck, TN district pages."""

import asyncio
import logging
import re
from urllib.parse import quote, urlparse

import httpx
from bs4 import BeautifulSoup

from app.services.scraper_helpers import (
    EMAIL_RE,
    PHONE_RE,
    PIN_RE,
    SCRAPER_HEADERS,
    _clean_entity_name,
    _extract_between,
    _is_valid_entity_name,
)

logger = logging.getLogger(__name__)


# ── TN District Hospital Scraper ──────────────────────────


async def scrape_tn_district(url: str) -> list[dict]:
    """Scrape hospital listings from a TN district nic.in page.

    Returns a list of dicts ready for Hospital model insertion.
    Does NOT insert into the database — only returns parsed data.
    """
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

    content_root = soup.find("article") or soup.find("div", class_="field-items") or soup.body
    if not content_root:
        return []

    records = []
    for h2 in content_root.find_all("h2"):
        name = h2.get_text(strip=True)
        if not name or len(name) < 3:
            continue

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

        phone_block = _extract_between(
            r"Phone\s*:", r"Email\s*:|Pincode\s*:|Category|Type\s*:", details_text
        )
        email_block = _extract_between(
            r"Email\s*:", r"Phone\s*:|Pincode\s*:|Category|Type\s*:", details_text
        )

        if not phone_block.strip():
            phone_block = details_text
        if not email_block.strip():
            email_block = details_text

        phones = PHONE_RE.findall(phone_block)
        phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]
        phone = phones[0] if phones else None

        emails = EMAIL_RE.findall(email_block)
        email = emails[0] if emails else None

        pin_candidates = PIN_RE.findall(details_text)
        pin_candidates = [p.replace(" ", "") for p in pin_candidates]
        pincode = pin_candidates[-1] if pin_candidates else None

        category_match = re.search(
            r"Category\s*/\s*Type\s*:\s*(.+?)(?:\s{2,}|Phone|Email|Pincode|\Z)",
            details_text, re.IGNORECASE,
        )
        category = category_match.group(1).strip() if category_match else None

        addr_part = re.split(
            r"Phone\s*:|Email\s*:|Category\s*/\s*Type\s*:|Pincode\s*:",
            details_text, maxsplit=1,
        )[0].strip()
        address = addr_part if addr_part else None
        if pincode and address and pincode not in address:
            address = f"{address}, PIN: {pincode}"

        city = district_title
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


# ── City-based Scraping ──────────────────────────────────


async def scrape_city(city: str, entity_type: str, state: str | None = None) -> list[dict]:
    """Scrape hospitals, NGOs, or doctors for a given city from public web sources."""
    from app.services.scraper_import import dedup_records

    city_clean = city.strip().title()
    state_clean = (state or "").strip()

    if entity_type == "hospitals":
        results = await _scrape_hospitals_by_city(city_clean, state_clean)
    elif entity_type == "ngos":
        results = await _scrape_ngos_by_city(city_clean, state_clean)
    elif entity_type == "doctors":
        results = await _scrape_doctors_by_city(city_clean, state_clean)
    else:
        results = []

    return dedup_records(results)


# ── Doctor Scraper (OSM) ─────────────────────────────────


async def _scrape_doctors_by_city(city: str, state: str) -> list[dict]:
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
        async with httpx.AsyncClient(headers=SCRAPER_HEADERS, timeout=30.0) as client:
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

                specialty = (
                    tags.get("healthcare:speciality")
                    or tags.get("speciality")
                    or tags.get("medical_specialty")
                    or None
                )
                if specialty:
                    specialty = specialty.replace(";", ", ")

                operator = (tags.get("operator") or "").lower()
                is_govt = any(
                    w in operator for w in ["government", "govt", "gov ", "public", "municipal", "phc"]
                )

                qualification = None
                if "MBBS" in name.upper() or "MD" in name.upper() or "MS" in name.upper():
                    qual_match = re.search(
                        r"\b(MBBS|MD|MS|DNB|BDS|MDS|DDVL|DM|MCh|BAMS|BHMS)\b",
                        name, re.IGNORECASE,
                    )
                    if qual_match:
                        qualification = qual_match.group(1).upper()

                hospital_name = None
                if tags.get("addr:housename"):
                    hospital_name = tags["addr:housename"]
                name_parts = name.split()
                is_likely_person = (
                    any(p.endswith(".") or p.lower() in ("dr", "dr.", "doctor", "prof") for p in name_parts)
                    or name.lower().startswith("dr ")
                    or name.lower().startswith("dr.")
                )
                if not is_likely_person and "clinic" in name.lower() or "hospital" in name.lower() or "medical" in name.lower():
                    hospital_name = name

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


# ── Hospital Scrapers (OSM + Web) ────────────────────────


async def _scrape_hospitals_by_city(city: str, state: str) -> list[dict]:
    """Scrape hospitals from multiple web sources for a city."""
    results: list[dict] = []

    osm_results = await _scrape_osm_hospitals(city, state)
    results.extend(osm_results)

    async with httpx.AsyncClient(
        headers=SCRAPER_HEADERS, timeout=20.0, follow_redirects=True
    ) as client:
        web_results = await _scrape_google_hospitals(client, city, state)
        results.extend(web_results)
        await asyncio.sleep(1.5)

        jd_results = await _scrape_justdial_hospitals(client, city)
        results.extend(jd_results)

    return results


async def _scrape_osm_hospitals(city: str, state: str) -> list[dict]:
    """Scrape hospitals from OpenStreetMap Overpass API."""
    results: list[dict] = []
    try:
        overpass_url = "https://overpass-api.de/api/interpreter"
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
        async with httpx.AsyncClient(headers=SCRAPER_HEADERS, timeout=30.0) as client:
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

                addr_parts = []
                if tags.get("addr:street"):
                    addr_parts.append(tags["addr:street"])
                if tags.get("addr:city"):
                    addr_parts.append(tags["addr:city"])
                if tags.get("addr:postcode"):
                    addr_parts.append(tags["addr:postcode"])
                address = ", ".join(addr_parts) if addr_parts else None

                specialties = tags.get("healthcare:speciality") or None
                if specialties:
                    specialties = specialties.replace(";", ", ")

                operator = (tags.get("operator") or "").lower()
                is_govt = any(
                    w in operator for w in ["government", "govt", "gov ", "public", "municipal"]
                ) or tags.get("ownership") == "government"

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
    client: httpx.AsyncClient, city: str, state: str
) -> list[dict]:
    """Scrape hospital names from DuckDuckGo and Bing HTML search results."""
    results: list[dict] = []
    location = f"{city} {state}".strip()
    queries = [
        f"list of hospitals in {location}",
        f"government hospitals in {location}",
        f"top hospitals in {location}",
    ]

    for query in queries:
        # DuckDuckGo
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

                    snippet_el = result_div.select_one(".result__snippet")
                    snippet = snippet_el.get_text(" ", strip=True) if snippet_el else ""

                    phones = PHONE_RE.findall(snippet)
                    phone = re.sub(r"[^\d]", "", phones[0])[-10:] if phones else None
                    emails = EMAIL_RE.findall(snippet)
                    email = emails[0] if emails else None

                    combined = (name + " " + snippet).lower()
                    is_govt = any(
                        w in combined
                        for w in ["government", "govt", "gov.", "public hospital", "esic", "esi ", "medical college"]
                    )

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

        # Bing
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
                    is_govt = any(
                        w in combined
                        for w in ["government", "govt", "gov.", "public hospital", "esic", "esi ", "medical college"]
                    )

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
    client: httpx.AsyncClient, city: str
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


# ── NGO Scrapers (OSM + Web) ─────────────────────────────


async def _scrape_ngos_by_city(city: str, state: str) -> list[dict]:
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
        async with httpx.AsyncClient(headers=SCRAPER_HEADERS, timeout=30.0) as client:
            resp = await client.post(overpass_url, data={"data": query})
            if resp.status_code == 200:
                data = resp.json()
                for elem in data.get("elements", []):
                    tags = elem.get("tags", {})
                    name = tags.get("name", "").strip()
                    if not name or len(name) < 2:
                        continue

                    email = tags.get("email") or tags.get("contact:email") or None
                    raw_phone = tags.get("phone") or tags.get("contact:phone") or ""
                    phone = re.sub(r"[^\d]", "", raw_phone)[-10:] if raw_phone else None
                    website = tags.get("website") or tags.get("contact:website") or None

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

    # Source 2: Web search (supplementary)
    async with httpx.AsyncClient(
        headers=SCRAPER_HEADERS, timeout=20.0, follow_redirects=True
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
