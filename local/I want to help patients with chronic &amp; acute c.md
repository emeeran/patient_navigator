<img src="https://r2cdn.perplexity.ai/pplx-full-logo-primary-dark%402x.png" style="height:64px;margin-right:32px"/>

# I want to help patients with chronic \& acute conditions, high-risk diseases to understand, guide them to get appropriate treatment, and get financial assistance. Help me get complete list of hospital in tamilnadu database, charity organisations both gvt \& pvt in india database

Here’s the key reality first: there is no single ready-made, fully complete, public CSV of all hospitals in Tamil Nadu or all charity/assistance organisations in India, but you can get to an almost-complete database by systematically combining several official and semi‑official sources. You can then ingest these into your own React + FastAPI stack and layer outreach workflows on top.[^1_1][^1_2]

Below is a pragmatic, implementation‑oriented plan plus where to get the data.

***

## 1. Where to get Tamil Nadu hospital data

### 1.1 District government “Hospitals” pages

Every TN district on `*.nic.in` usually has a “Hospitals” page listing government facilities (district HQ hospitals, taluk hospitals, non‑taluk hospitals, PHCs, UCHCs etc.).[^1_3][^1_4]

Examples:

- Tiruvannamalai district – public utility “Hospitals” page with government hospitals and PHCs plus phone numbers and pincodes.[^1_3]
- Karur district – similar page listing district HQ hospital, taluk hospitals, non‑taluk hospitals, PHCs and medical college hospital with emails/phones.[^1_4]

Usage for you:

- Treat each district page as a source of **govt facilities**.
- You’ll need to scrape these HTML lists and normalise into a single table.

***

### 1.2 National Health Mission (NHM) Tamil Nadu

The NHM TN site is the authoritative public‑health portal for the state. It does not expose a ready “all hospitals” CSV, but it is useful for:[^1_2]

- Validating categories and nomenclature (District Hospital, CHC, PHC, UCHC, etc.).[^1_2]
- Verifying facilities mentioned in Government Orders (e.g., orders establishing clinics or upgrading hospitals).[^1_5]

Usage:

- Use NHM as a **reference layer** to check that scraped facility names and types are consistent with official terminology.

***

### 1.3 Chennai urban health-centre open data

Chennai has open-data style datasets: e.g., a CKAN dataset of UPHCs/UCHCs and other health centres with CSV downloads.[^1_6]

- Datasets like “Chennai – List of UPHCs” and “Chennai – List of UCHCs” are directly in CSV.[^1_6]

Usage:

- Ingest these CSVs as-is and map fields to your schema (name, type, address, lat/long etc.).[^1_6]
- Use them as a model for how to structure other PHC/UCHC data.

***

### 1.4 Ayushman Bharat (PMJAY) empanelled hospitals in Tamil Nadu

The official PMJAY portal (`hospitals.pmjay.gov.in`) has a **“Find Hospitals”** tool.[^1_1]

- You can select State = Tamil Nadu, district, hospital type, speciality, etc., and get a list of empanelled hospitals (public + private).[^1_1]
- The portal allows download of the hospital list for Tamil Nadu as a PDF.[^1_1]

Usage:

- For each district, query and export the results, then parse PDFs into structured data: hospital name, address, district, hospital type, empanelment type.[^1_1]
- Tag these rows with `is_pmjay_empanelled = true`.

This is huge for your use case since these are the hospitals where **cashless PMJAY treatment** is available.

***

### 1.5 Insurer network hospital Excel lists

Some insurers publish **Excel lists of network hospitals**. For example, New India Assurance exposes a `Chennai.xlsx` containing hospitals with full addresses and identifiers.[^1_7]

Usage:

- Download and parse such `.xlsx` files for TN cities.[^1_7]
- Use them primarily to **augment private hospital coverage**, especially where district portals are thin on private facilities.
- Deduplicate against existing rows using fuzzy name + address matching.

***

### 1.6 Third‑party compiled lists (cross-check only)

There are compiled lists like a Scribd document “List of Hospitals and Medical Colleges in Tamilnadu” with about 148 hospitals and nursing homes.[^1_8]

Usage:

- Treat these as **auxiliary**: use them to detect big hospitals/nursing homes that may have been missed.[^1_8]
- Verify each new facility against official or primary sources before adding.[^1_8]

***

### 1.7 Reality check

You won’t find a single official master CSV of all TN hospitals (govt + private) on one site. The robust approach is multi‑source ingestion + dedupe + manual curation, which fits nicely with your engineering background.[^1_2][^1_1]

***

## 2. Concrete data-pipeline plan (for your React + FastAPI stack)

### 2.1 Canonical schema

Minimal columns to start:

- `id` (internal UUID)
- `name`
- `district`, `city_or_town`, `state = Tamil Nadu`
- `address`, `pincode`
- `phone`, `email`, `website`
- `ownership` (enum: government / private / trust / other)
- `facility_type` (district hospital / taluk / non‑taluk / PHC / UCHC / UPHC / medical college hospital / specialty hospital / nursing home, etc.)
- `is_pmjay_empanelled` (bool)
- `pmjay_empanelment_type` (govt/private etc.)
- `insurer_network` (JSON/child table: which insurer lists it)
- `specialities` (array/tags: oncology, cardiology, nephrology, ICU, transplant, etc. – fill gradually)

This schema is fully compatible with a FastAPI + PostgreSQL backend and a filterable React frontend.

***

### 2.2 Data collection phases

**Phase 1 – Government/public backbone**

- Scrape all district “Hospitals” pages (`*.nic.in/public-utility-category/hospitals/`) similar to Tiruvannamalai and Karur pages.[^1_4][^1_3]
- Ingest Chennai UPHC/UCHC CSVs from OpenCity.[^1_6]
- Add PMJAY Tamil Nadu hospitals from the official PMJAY portal and mark `is_pmjay_empanelled`.[^1_1]

**Phase 2 – Private coverage**

- Ingest insurer network hospital `.xlsx` files for Chennai and other cities where available (e.g., New India’s Chennai file).[^1_7]
- Cross‑check large private hospitals via the Scribd list and hospital websites, adding missing facilities if confirmed.[^1_8]

**Phase 3 – Enrichment**

- For each hospital, gradually add specialities and scheme info:
    - PMJAY: already known from PMJAY list.[^1_1]
    - RAN/HMCPF: mark hospitals that are among the 13 RAN super‑specialty institutions or the 27 regional cancer centres (from official docs – you’d pull from MoHFW / RAN docs, which the Milaap explainer summarises).[^1_9]
- Validate names/types using NHM TN and Government Orders (especially for new or upgraded facilities).[^1_5][^1_2]

This will give you a hospital DB that is strong enough to power patient-facing search and outreach.

***

## 3. Government financial-assistance schemes you should build into the knowledge layer

### 3.1 Rashtriya Arogya Nidhi (RAN)

- Central government umbrella scheme offering financial assistance to **BPL patients with life‑threatening diseases** in certain enlisted super‑specialty government hospitals.[^1_9]
- Typical assistance: one‑time grant around **₹2 lakh, extendable up to about ₹5 lakh**, no reimbursement of already incurred expenses.[^1_9]
- Requires application, income proof, ration card, and medical estimate; strictly for treatment at designated government institutions.[^1_9]


### 3.2 Health Minister’s Cancer Patients Fund (HMCPF)

- Sub‑scheme under RAN focused on cancer patients below poverty line being treated at **27 regional cancer centres**.[^1_9]
- One‑time grant similar to RAN (₹2–5 lakh range), no reimbursement for past expenses.[^1_9]


### 3.3 Health Minister’s Discretionary Grant (HMDG)

- Another RAN component giving up to about **₹1.25 lakh** to poor patients with rare illnesses and annual income below a threshold, for expenses in govt hospitals.[^1_9]
- Excludes common diseases with inexpensive treatment and does not reimburse past expenses.[^1_9]


### 3.4 Prime Minister’s National Relief Fund (PMNRF)

- Provides financial aid to underprivileged patients with major life‑threatening diseases, for treatment at government or PMNRF‑enlisted hospitals.[^1_9]
- Application process: letter to PM, income certificate, ration card copy, patient photos, medical certificate specifying disease and cost estimation.[^1_9]


### 3.5 Ayushman Bharat – PMJAY

- National health insurance scheme providing **cashless treatment up to a defined annual coverage per family** at empanelled hospitals, including government and private.[^1_1]
- Eligibility is based on deprivation/occupation criteria; PMJAY portal allows state/district search and hospital downloads.[^1_1]
- For Tamil Nadu, use PMJAY “Find Hospitals” both as a data source and a routing aid.[^1_1]

These schemes should be part of your backend “knowledge base” so that for each patient profile you can quickly compute what they’re likely eligible for.

***

## 4. NGO and private charity side – how to discover and structure them

### 4.1 NGO-run medical funds (examples)

- **Youth For Seva – Arogya Nidhi Medical Fund**: provides medical financial assistance across India for BPL patients needing hospitalisation, long‑term medicines, emergency care, and post‑hospitalisation rehabilitation; contact via email/phone; funded by individual and corporate donors.[^1_10]
- **Sadguru Foundation**: raises funds for urgent medical cases (surgeries, medicines, diagnostics) and connects donors to patients, often for cases like child cancer or accident victims.[^1_11]

For each such NGO, you’ll want:

- Name, website, contact details (phone, email).[^1_10][^1_11]
- Types of conditions covered (e.g., oncology, paediatrics, accidents).[^1_11][^1_10]
- Eligibility (BPL only, PAN‑India vs regional, etc.).[^1_10]
- How to apply (documents, referral needed?).[^1_11][^1_10]


### 4.2 NGO directories

- **Medindia NGO list** – claims information on ~7,565 NGOs across India, browsable by state, with focus on health‑related NGOs.[^1_12]
- **MOHAN Foundation NGO list** – specialised directory for NGOs in the organ donation and transplant space, searchable by city/state.[^1_13]
- Philanthropy platforms like **Give.do** highlight health NGOs that have significantly impacted healthcare (curated list for discovering credible partners).[^1_14]

Usage:

- Build a crawler/scraper for these directories with filters for health/medical NGOs.
- Create your own NGO table: name, focus area, state(s) of operation, funding type (direct grants vs subsidised care), contact details, plus any tags like “supports hospital bills” or “runs own hospital/clinic”.[^1_12][^1_13][^1_14]

***

## 5. How to use all this for outreach and guidance

With your background, you can turn this into both a **data product** and an **operations playbook**.

### 5.1 Data architecture

Backend (FastAPI + DB):

- `hospitals` table (schema above).
- `schemes` table (PMJAY, RAN, HMCPF, HMDG, PMNRF, plus state schemes once you add them) with fields: name, type (insurance/relief/grant), min/max coverage, eligibility summary, allowed facility types.[^1_9][^1_1]
- `ngos` table for health/medical NGOs and their programmes, with coverage area and application details.[^1_13][^1_12][^1_10][^1_11]
- Link tables:
    - `hospital_schemes` to map which schemes apply at which hospitals (e.g., PMJAY empanelment, RAN super‑specialty centres).[^1_1][^1_9]
    - `hospital_ngos` or at least region‑based matching for NGOs that fund treatments in specific districts.

Frontend (React):

- Patient/volunteer view: search hospital by district + speciality + scheme (“show PMJAY hospitals for oncology in Chennai”).[^1_6][^1_1]
- Scheme explorer: for given patient profile (BPL, cancer, Tamil Nadu), show “Possible schemes” with basic description and link to official application/portal.[^1_9][^1_1]
- NGO explorer: list NGOs that can fund similar cases, with contact info and basic triage notes.[^1_10][^1_11]


### 5.2 Process flow for a single patient

1. Capture basic profile: location, disease type, income/BPL status.
2. Suggest hospitals:
    - Search your TN hospital DB by district + speciality; filter to PMJAY or govt hospitals if relevant.[^1_6][^1_1]
3. Suggest schemes:
    - If BPL + life‑threatening disease: check RAN/HMCPF/HMDG/PMNRF applicability.[^1_9]
    - If PMJAY‑eligible: show PMJAY empanelled hospitals near them.[^1_1]
4. Suggest NGOs:
    - Filter NGOs by disease type and state (Tamil Nadu/nearby), show fund contact channels.[^1_12][^1_13][^1_11][^1_10]
5. Output a simple “action plan” that your volunteers can follow: which hospital to approach, which documents to collect, which schemes/NGOs to apply to first.

***

## 6. About the “complete list” expectation

You asked for a “complete list of hospitals in Tamil Nadu database” and “charity organisations both govt \& pvt in India database.” In practice:

- Hospitals: You can get close to exhaustive for **government + PMJAY‑empanelled + major private** hospitals via the combined approach above. Ultra‑small nursing homes and clinics might always need incremental manual addition.[^1_3][^1_4][^1_6][^1_1]
- Charity/NGOs: No single canonical DB exists, but starting from Medindia, MOHAN, and curated platforms gives you a broad, structured base; you can add more over time as you encounter them.[^1_14][^1_13][^1_12]

***

## Next steps you can take immediately

Given your stack preference, here is a minimal actionable path:

1. Start with **PMJAY Tamil Nadu hospital list**: download PDFs per district and build your first `hospitals` table.[^1_1]
2. Add **Chennai UPHC/UCHC CSVs** to cover public primary/urban facilities.[^1_6]
3. Implement a **district nic.in scraper** for “Hospitals” pages, at least for a few districts as POC.[^1_4][^1_3]
4. In parallel, catalogue **RAN, HMCPF, HMDG, PMNRF, PMJAY** in a `schemes` table with machine-readable eligibility fields.[^1_9][^1_1]
5. Seed an `ngos` table with 10–20 pan‑India medical NGOs (Arogya Nidhi, Sadguru Foundation, etc.), plus items discovered through Medindia and MOHAN lists.[^1_13][^1_12][^1_11][^1_10]

Once you’re ready, mention if you’d like:

- Example FastAPI models and DB schema for `hospitals`, `schemes`, and `ngos`; or
- A scraping strategy (selectors, anti‑fragile parsing) specifically tuned for TN district hospital pages.
<span style="display:none">[^1_15][^1_16][^1_17][^1_18][^1_19][^1_20][^1_21][^1_22][^1_23][^1_24][^1_25][^1_26][^1_27][^1_28]</span>

<div align="center">⁂</div>

[^1_1]: https://www.hexahealth.com/hospitals/insurance/ayushman-bharat-hospitals-list-tamil-nadu

[^1_2]: http://www.nhm.tn.gov.in

[^1_3]: https://tiruvannamalai.nic.in/public-utility-category/hospitals/

[^1_4]: https://karur.nic.in/public-utility-category/hospitals/

[^1_5]: https://www.nhm.tn.gov.in/en/government-orders?field_gov_order_year_target_id=All\&page=1

[^1_6]: https://data.opencity.in/dataset/chennai-healthcare-uphcs-and-uchcs

[^1_7]: https://www.newindia.co.in/assets/docs/hospitals-list/Chennai.xlsx

[^1_8]: https://www.scribd.com/document/459104042/List-of-Hospitals-and-Medical-Colleges-in-Tamilnadu

[^1_9]: https://milaap.org/articles/schemes/financial-support-for-life-threatening-diseases-4-national-schemes-to-know

[^1_10]: https://youthforseva.org/programs/arogya-nidhi/

[^1_11]: https://www.sadgurufoundation.com/blog/financial-help-for-poor-patients/

[^1_12]: https://www.medindia.net/directories/ngos/index.htm

[^1_13]: https://www.mohanfoundation.org/ngos-list.asp

[^1_14]: https://give.do/blog/10-ngos-which-have-revolutionised-healthcare-in-india/

[^1_15]: https://github.com/OneFourthLabs/CoViD19-Viz/blob/master/hospitals.csv

[^1_16]: https://www.clinicspots.com/blog/government-hospitals-in

[^1_17]: https://tncea.dmrhs.tn.gov.in/list_of_institution.php

[^1_18]: https://www.scribd.com/document/828620630/List-of-NGO-2

[^1_19]: https://prognohealth.com/blog/list-of-government-hospitals-in-chennai/

[^1_20]: https://www.scribd.com/document/475524544/tn-hopitaux-prives-1

[^1_21]: https://www.justdial.com/Mumbai/NGOS-For-Money-Donation/nct-12567135

[^1_22]: https://tnaiota.org/government-hospitals

[^1_23]: https://www.scribd.com/document/831960250/TAMILNADU-HOSPITALS-LIST

[^1_24]: https://www.scribd.com/doc/297274898/Gov-Approved-Hospitals-Chennai

[^1_25]: https://www.nhm.tn.gov.in/en/for-find-hospital

[^1_26]: https://services.india.gov.in/service/detail/search-ngo

[^1_27]: https://chennaicorporation.gov.in/gcc/covid-vaccine/govt-hospital/

[^1_28]: https://tnhealth.tn.gov.in/tngovin/dme/dme.php


---

# A scraping strategy (selectors, anti‑fragile parsing) specifically tuned for TN district hospital pages

The TN district “Hospitals” pages are regular enough that you can treat each **H2 block as one hospital** and parse everything until the next H2 as field text, using label‑based extraction instead of brittle CSS selectors.

***

## Observed pattern on TN district hospital pages

From Tiruvannamalai and Karur pages:

- Each hospital is a second‑level heading (`## Government Hospital, Arni`, `## Primary Health Centre, Ayyampalayam`, etc.).
- The details are in the following lines, with fields marked by labels like `Phone :`, `Email :`, `Category/Type:`, and `Pincode:` often styled as bold, followed by values.
- Some entries also include a free‑text line with the full address or description right after the heading.

This is ideal for a **heading + following siblings** pattern and **label/value parsing**, rather than tight class‑based selectors.

***

## High‑level strategy (anti‑fragile)

1. **Locate the main content area**, but avoid depending on exact class names:
    - Start with the `<article>` element or the primary content container (often WordPress/GovCMS style).
    - If you cannot rely on classes, just work on the whole `<body>` and restrict to `h2`–`p` sequences.
2. **Treat every `<h2>` inside that content as the start of a hospital record**:
    - `name` = text of `<h2>` (normalize whitespace and commas).
3. **Collect all sibling elements until the next `<h2>`**:
    - Most commonly `p` tags or inline fragments where the details live.
    - Concatenate their text and then parse out fields using regex/key‑word detection.
4. **Extract structured fields via label matching, not DOM structure**:
    - Look for substrings like `Phone :`, `Email :`, `Category/Type:`, `Pincode:` in the combined text block and split on `:`.
    - Anything that looks like a 6‑digit number can be candidate `pincode` if label is absent.
    - If a line has no label but contains the district name and a 6‑digit code, treat it as address.
5. **Fallbacks**:
    - If `Category/Type:` absent, use keywords in name: “Primary Health Centre” vs “Government Medical College Hospital” etc.
    - If `Email` missing, leave null; do not assume.
```
This reduces breakage if the CMS changes CSS classes, wraps content differently, or moves from `<strong>` to `<b>` etc.
```


***

## Selector and parsing detail (Python/BeautifulSoup outline)

Assuming `html` is the page HTML (via `requests` or `httpx`):

```python
from bs4 import BeautifulSoup
import re

soup = BeautifulSoup(html, "lxml")

# 1. pick a content root – simple but robust
content_root = soup.find("article") or soup.body

records = []

for h2 in content_root.find_all("h2"):
    name = h2.get_text(strip=True)
    # 2. collect siblings until next h2
    details_nodes = []
    for sib in h2.find_next_siblings():
        if sib.name == "h2":
            break
        if sib.name in ("p", "div"):
            details_nodes.append(sib.get_text(" ", strip=True))
    details_text = " ".join(details_nodes)

    # 3. label-based extraction
    def extract_label(label, text):
        m = re.search(rf"{label}\s*:?(\s*)([^*]+?)(\s{2,}|\Z)", text, flags=re.IGNORECASE)
        return m.group(2).strip() if m else None

    phone = extract_label("Phone", details_text)
    email = extract_label("Email", details_text)
    category = extract_label("Category/Type", details_text)
    pincode = extract_label("Pincode", details_text)

    # 4. address heuristic: first line without label + any 6-digit code
    address = None
    if not category or not pincode:
        # split by "Phone", "Email" etc., take first portion as address candidate
        addr_candidate = re.split(r"Phone\s*:|Email\s*:|Category/Type\s*:|Pincode\s*:", details_text, maxsplit=1)[0].strip()
        if addr_candidate:
            address = addr_candidate

    records.append({
        "name": name,
        "phone": phone,
        "email": email,
        "category": category,
        "pincode": pincode,
        "address": address,
        "raw": details_text,
    })
```

Key anti‑fragility points:

- You never depend on exact `<strong>` wrappers; you only look at text levels.
- You treat **labels as tokens** in the text, so even if the CMS wraps them differently, the text `Phone :` still exists.

```
- `find_next_siblings()` from each `<h2>` isolates per‑hospital blocks; if they introduce extra `<div>`s, the logic still works as long as they remain siblings.
```


***

## Handling cross-district variability

Some districts will include more/less fields, or reorder labels. The above approach copes because:

- You’re not relying on order; you simply search the aggregated text for `Phone`, `Email`, etc.
- New labels (e.g., `Fax :`, `Mobile :`) can be accommodated by extending the label list.
- If a district adds a long single line like
`Government PHC-Akkur, Tiruvannamalai District. Phone : 8939676383 Pincode: 631701`
your regex still picks both `Phone` and `Pincode` correctly.

For quality, you can:

- Log any records where you fail to extract `phone` or `pincode` and inspect them manually.
- Store `raw` text for each record so you can revisit parsing strategy later without re‑scraping.

***

## Extending beyond TN “Hospitals” pages

Once this pattern is stable, you can reuse the same **H2 + following siblings + label parsing** approach for:

- Other public‑utility categories (e.g., health centres, labs) which use similar templates on `*.nic.in`.
- Other states using similar NIC templates, modifying only the label vocabulary if they differ.

If you want, I can next help you refine the regexes to better handle multi‑pincode lines and mixed `Email`/`Phone` on the same line, based on how you want the DB cleaned.

---

# help me refine the regexes to better handle multi‑pincode lines and mixed Email/Phone on the same line, based on how i want the DB cleaned

You can make this quite robust by (a) decoupling extraction from labels, and (b) using **separate passes** for PIN, phone, and email, with well‑scoped text slices.

Below are refined regexes + patterns and how to wire them into your scraper.

***

## 1. Refined PIN code extraction (multi‑PIN safe)

For Indian PINs, you want:

- Exactly 6 digits
- First digit not 0
- Optional space in the middle (e.g., `600 001`)

A good pattern is:

```python
PIN_RE = re.compile(r"\b[1-9][0-9]{2}\s?[0-9]{3}\b")
```

This is essentially the `[1-9]\d{5}` pattern with an optional space after the first three digits.[^3_1][^3_2][^3_3]

**Usage for multi‑pincode lines:**

```python
pin_candidates = PIN_RE.findall(details_text)
# e.g., ["600001", "600 002"]

# Normalise (strip spaces)
pin_candidates = [p.replace(" ", "") for p in pin_candidates]

# Strategy 1: keep all as list field
pincodes = sorted(set(pin_candidates))  # for a multi-valued column

# Strategy 2: pick one canonical PIN per hospital
pincode = pincodes[-1] if pincodes else None  # e.g., last one in the line/block
```

For your DB:

- Store `pincode` (single) as the canonical one you choose.
- Optionally have `pincode_all` as a JSON array if you want to preserve all matches for QC later.

Because PINs are 6‑digit and phones are 10‑digit, this regex will **not** collide with Indian mobile numbers.[^3_4]

***

## 2. Phone and email extraction when they share a line

### 2.1 Base regexes

**Email** (simple, robust enough for scraped pages):

```python
EMAIL_RE = re.compile(
    r"\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b"
)
```

This is in line with common email-detection patterns used in automation tools.[^3_5]

**Indian phone (mobile + optional +91 / 0):**

```python
PHONE_RE = re.compile(
    r"\b(?:\+91[-\s]?)?[6-9]\d{9}\b"
)
```

Pattern aligns with standard Indian phone rules: 10 digits, starting 6–9, with optional `+91`/0.[^3_6][^3_1]

You can later extend `PHONE_RE` if you want to also capture landlines like `044-22223333`.

***

### 2.2 Scope by labels: “Phone” vs “Email”

Instead of running `PHONE_RE` and `EMAIL_RE` over the entire block, scope by labels:

```python
def extract_between(label_start, label_end, text):
    """
    Return substring between label_start and label_end (or end of text).
    """
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

details_text = details_text or ""

# 1. Get the phone block: between 'Phone' and 'Email' (if present)
phone_block = extract_between(r"Phone\s*:", r"Email\s*:", details_text)

# 2. Get the email block: from 'Email' to end
email_block = extract_between(r"Email\s*:", None, details_text)

phones = PHONE_RE.findall(phone_block)
emails = EMAIL_RE.findall(email_block)

phone = phones[^3_0] if phones else None
email = emails[^3_0] if emails else None
```

So a line like:

`Phone : 9876543210, 044-22223333 Email : info@hospital.org`

will be split into:

- `phone_block = " 9876543210, 044-22223333 "`
- `email_block = " info@hospital.org"`

Your `PHONE_RE` picks the mobile; you can optionally add a second regex for landlines.

***

## 3. Handling multiple phones and emails

In real pages you may see:

`Phone : 9876543210 / 9444433221 Email : admin@hosp.org, help@hosp.org`

Refine behavior:

```python
phones = PHONE_RE.findall(phone_block)
emails = EMAIL_RE.findall(email_block)

# Normalise phones: remove spaces/dashes from Indian format
phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]  # keep last 10 digits

# DB cleaning policies
primary_phone = phones[^3_0] if phones else None
all_phones = sorted(set(phones))  # optional JSON list

primary_email = emails[^3_0] if emails else None
all_emails = sorted(set(emails))
```

You can decide:

- For `hospital.phone`: store `primary_phone`.
- For `hospital.phone_all`: keep all as JSON list for future outreach tooling.

Same for emails.

***

## 4. Making label-based extraction more tolerant

District pages sometimes vary label spacing and case: `Phone :`, `Phone:`, `PHONE :`. Use a label regex like:

```python
PHONE_LABEL = r"Phone\s*:?"
EMAIL_LABEL = r"Email\s*:?"
PIN_LABEL   = r"Pincode\s*:?"
```

Then your general extractor:

```python
def extract_label_value(label_regex, text):
    # Captures text after label up to next label or line break
    pattern = rf"{label_regex}\s*(?P<value>[^:]+?)(?=(Phone\s*:|Email\s*:|Pincode\s*:|\n|\r|$))"
    m = re.search(pattern, text, flags=re.IGNORECASE)
    return m.group("value").strip() if m else None
```

For `Pincode`, you can then run `PIN_RE.findall(value)` to support multiple PINs in the “pincode line”.

***

## 5. Putting it together in your scraper

Combining everything into your previous `records.append` logic:

```python
details_text = " ".join(details_nodes)

# 1) Pincodes
pin_candidates = PIN_RE.findall(details_text)
pin_candidates = [p.replace(" ", "") for p in pin_candidates]
pincodes_all = sorted(set(pin_candidates))
pincode = pincodes_all[-1] if pincodes_all else None

# 2) Scoped phone/email
phone_block = extract_between(r"Phone\s*:", r"Email\s*:", details_text)
email_block = extract_between(r"Email\s*:", None, details_text)

phones = PHONE_RE.findall(phone_block)
phones = [re.sub(r"[^\d]", "", p)[-10:] for p in phones]  # normalise
phone = phones[^3_0] if phones else None

emails = EMAIL_RE.findall(email_block)
email = emails[^3_0] if emails else None

record = {
    "name": name,
    "address": address,
    "pincode": pincode,
    "pincodes_all": pincodes_all,
    "phone": phone,
    "phones_all": sorted(set(phones)),
    "email": email,
    "emails_all": sorted(set(emails)),
}
```

This setup:

- Avoids mis‑classifying phone digits as pincodes by using 6‑digit vs 10‑digit patterns and word boundaries.[^3_3][^3_1]
- Works whether `Phone` and `Email` are on the same line or not, as long as labels exist.
- Gives you single “clean” values plus optional arrays for QC and multi‑contact usage.

If you share a sample `details_text` block from one of the trickier districts, I can tune the patterns further to that exact variation.
<span style="display:none">[^3_10][^3_11][^3_12][^3_13][^3_14][^3_15][^3_7][^3_8][^3_9]</span>

<div align="center">⁂</div>

[^3_1]: https://stackoverflow.com/questions/76825512/write-regex-for-pincode-of-6-digits-ie-indian-pincode

[^3_2]: https://stackoverflow.com/questions/33865525/indian-pincode-validation-regex-only-six-digits-shouldnt-start-with-0

[^3_3]: https://regexpattern.com/indian-postal-pin-zip-code/

[^3_4]: https://en.wikipedia.org/wiki/Postal_Index_Number

[^3_5]: https://forum.uipath.com/t/how-to-extract-email-phone-number-from-a-text/544582

[^3_6]: https://gist.github.com/bkanhu/bf07ba56db19669a353a1bd94080dc15

[^3_7]: https://forum.keyboardmaestro.com/t/regex-help-extract-f-l-name-email-phone-and-text-message/13568/2

[^3_8]: https://stackoverflow.com/questions/75209722/extract-phone-numbers-from-email-signature-regex

[^3_9]: https://forum.bubble.io/t/detecting-emails-phone-numbers-and-links-via-extract-with-regex/17448

[^3_10]: https://www.emailparser.com/d/email-parser/capturing-text-with-regular-expressions

[^3_11]: https://stackoverflow.com/questions/365487/parse-email-content-with-regular-expressions

[^3_12]: https://stackoverflow.com/questions/72123498/regex-to-match-a-few-specific-6-digit-numbers-indian-pin-codes

[^3_13]: https://github.com/captn3m0/india-pincode-regex

[^3_14]: https://regex101.com/library/J0pFbM?orderBy=MOST_RECENT\&search=email\&page=5

[^3_15]: https://www.geeksforgeeks.org/dsa/how-to-validate-pin-code-of-india-using-regular-expression/

