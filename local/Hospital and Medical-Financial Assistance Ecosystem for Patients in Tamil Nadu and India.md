# Hospital and Medical-Financial Assistance Ecosystem for Patients in Tamil Nadu and India

## Overview

This report outlines practical ways to obtain relatively complete hospital lists for Tamil Nadu and to discover charity and financial-assistance organisations (government and private) that support treatment for chronic, acute, and high-risk diseases in India. It focuses on sources that provide downloadable or searchable datasets, which can be ingested into a React + FastAPI application or internal database.[^1][^2]

## Data sources for hospitals in Tamil Nadu

### District e‑governance portals (Govt. of Tamil Nadu)

Every Tamil Nadu district website on the `*.nic.in` domain typically publishes a "Hospitals" public-utilities page listing government hospitals, primary health centres (PHCs), and related facilities. These pages include hospital names, locations, and often phone and email, but are HTML lists that must be scraped to build a unified database.[^3][^4]

Key characteristics:
- Separate page per district (for example, Tiruvannamalai and Karur districts show government hospitals, PHCs, and medical college hospitals).[^4][^3]
- Covers mainly government facilities (district hospitals, taluk hospitals, non‑taluk hospitals, PHCs, UCHCs, etc.).[^3][^4]
- No direct state‑wide CSV is provided; consolidation requires programmatic crawling and parsing.

### National Health Mission Tamil Nadu and allied portals

The National Health Mission (NHM) Tamil Nadu site is the main public health portal and links to government orders, programmes, and health facility information. While it does not directly expose a master hospital CSV, it is an authoritative reference for types and distribution of public facilities and for verifying facility names against official notifications.[^2][^5]

Relevant aspects:
- Official programme and facility announcements (e.g., establishing clinics or upgrading hospitals) help validate that a facility exists and is government‑recognised.[^5]
- Serves as a canonical reference for categorisation (district hospital, CHC, PHC, etc.) and higher‑level coverage statistics.[^2][^5]

### Urban health facilities (Chennai example)

For urban areas, some open‑data portals provide structured datasets, such as Chennai’s health centre datasets on the OpenCity CKAN platform. These expose CSVs for Urban Primary Health Centres (UPHCs) and Urban Community Health Centres (UCHCs), which include facility names and locations.[^6]

Key points:
- Data is already in CSV format for some categories of urban public facilities in Chennai.[^6]
- Useful as a template for schema design: facility name, type (UPHC/UCHC), address, and coordinates.[^6]

### Ayushman Bharat (PM‑JAY) empanelled hospitals in Tamil Nadu

The Ayushman Bharat – Pradhan Mantri Jan Arogya Yojana (AB‑PMJAY) portal provides a searchable list of empanelled hospitals by state and district, covering both public and private hospitals. Through the official PMJAY "Find Hospitals" interface, users can filter by state (Tamil Nadu), district, hospital type, specialty, and empanelment type, and can download the list as a PDF.[^1]

Key characteristics:
- Official government list of hospitals empanelled under PMJAY for Tamil Nadu, including private and government facilities.[^1]
- Downloadable as PDF from the official PMJAY site and from some secondary aggregators, enabling downstream extraction into structured tables.[^1]
- Fields typically include hospital name, address, hospital type, and empanelled insurance type.[^1]

### Insurance empanelment hospital lists (private sources)

Insurance companies sometimes publish Excel lists of network hospitals by city, which can be repurposed to augment the private‑hospital side of a Tamil Nadu database. For example, New India Assurance hosts an `.xlsx` file specifically listing network hospitals in Chennai with addresses and identifiers.[^7]

These lists can:
- Provide a partial but structured set of private hospitals and nursing homes in Chennai, including addresses and sometimes internal codes or contact details.[^7]
- Serve as a seed dataset for private facilities, later enriched and deduplicated against government and PMJAY lists.[^7][^1]

### Existing compiled lists (semi‑official / third‑party)

Third‑party compilations, such as a Scribd document containing a list of hospitals and medical colleges in Tamil Nadu, aggregate around 148 hospitals and nursing homes across the state. The list is primarily focused on larger hospitals and includes various segments: general hospitals, specialty centres, eye hospitals, and nursing homes.[^8]

Caveats and uses:
- Not an official government dataset, and may be outdated or incomplete.[^8]
- Still useful as a cross‑check and for capturing some private and specialty facilities not present in government‑only lists.[^8]

### Limitations: no single "complete" public master list

There is currently no single, official, state‑wide CSV of every public and private hospital in Tamil Nadu that is freely downloadable for programmatic use. Achieving a "complete" list requires combining multiple sources: district hospital lists, PMJAY empanelment lists, urban health‑centre datasets, and insurance/network lists, with deduplication and manual validation.[^2][^1]

## Recommended approach to build a Tamil Nadu hospital database

### 1. Scrape district hospital pages

- Enumerate all district `*.nic.in` sites for Tamil Nadu and identify "Hospitals" or "Public Utilities → Hospitals" pages similar to the Tiruvannamalai and Karur examples.[^4][^3]
- Use a scraping pipeline to extract facility name, type, address (or location text), phone, and email where present.[^3][^4]
- Normalise facility type categories according to NHM/Health Department nomenclature (District Hospital, Taluk Hospital, Non‑Taluk Hospital, PHC, UCHC, etc.).[^5][^2]

### 2. Ingest Ayushman Bharat (PM‑JAY) Tamil Nadu list

- Use the official PMJAY "Find Hospitals" interface to query for state = Tamil Nadu and iterate over districts, then export PDFs for each or use automated downloading where allowed.[^1]
- Parse the PDF(s) into structured data capturing hospital name, district, address, hospital type, and empanelment type.[^1]
- Tag these entries with an "AB‑PMJAY empanelled" flag, so downstream applications know which hospitals can directly accept PMJAY patients.[^1]

### 3. Integrate Chennai and other urban health‑centre CSVs

- Download the Chennai UCHC and UPHC CSVs from the OpenCity CKAN dataset.[^6]
- Map columns to the canonical schema used for other facilities (facility name, category, address, latitude/longitude if present).[^6]
- Use these as authoritative for public primary/urban health centres in Chennai, reducing manual data entry.[^6]

### 4. Augment with insurer network hospital Excel lists

- Download city‑ or state‑specific network hospital lists from insurers that publish Excel files (e.g., New India Assurance hospital list for Chennai).[^7]
- Clean the data and deduplicate against existing facility names and addresses, keeping track of the insurer name and any internal hospital IDs.[^7]
- Use this channel primarily for private hospitals and specialty centres, recognising that coverage may be partial.

### 5. Cross‑check with third‑party compilations

- Use lists like the Scribd "List of Hospitals and Medical Colleges in Tamilnadu" purely as auxiliary sources to detect missing larger hospitals or medical colleges.[^8]
- When a new facility is discovered via such a list, verify it against more authoritative sources such as district portals, NHM notifications, or the hospital’s own website before including it.

### 6. Data model and API considerations (for React + FastAPI stack)

A practical schema for a unified hospital database might include:
- Core fields: `id`, `name`, `district`, `city_or_town`, `address`, `pincode`, `phone`, `email`, `website`.
- Classification: `ownership` (government / private / trust), `facility_type` (district hospital, taluk hospital, medical college hospital, PHC, UCHC, UPHC, specialty hospital, nursing home), `is_pmay_empanelled`, `is_insurer_network` (with a link table for insurer mappings).
- Clinical focus flags: booleans or tags for key specialities (oncology, cardiology, nephrology, intensive care, transplantation, etc.), populated gradually as data is enriched.

This schema can be exposed via a FastAPI backend with filters on district, speciality, ownership, and schemes, and consumed by a React frontend that allows patients or volunteers to search for appropriate hospitals and see which financial schemes may apply.

## Government schemes for medical financial assistance in India

### Rashtriya Arogya Nidhi (RAN) and components

Rashtriya Arogya Nidhi (RAN) is an umbrella scheme of the Government of India that provides financial assistance to patients below the poverty line suffering from major life‑threatening diseases, for treatment in certain enlisted super‑specialty government hospitals. Under RAN, eligible patients can receive a one‑time grant typically around ₹2 lakh, extendable up to about ₹5 lakh depending on urgency, strictly for treatment in designated government institutions and without reimbursement of expenses already incurred.[^9]

Sub‑schemes under RAN include:
- Health Minister’s Cancer Patients Fund (HMCPF), which provides similar one‑time grants (around ₹2–5 lakh) for cancer patients below the poverty line being treated in regional cancer centres.[^9]
- Health Minister’s Discretionary Grant (HMDG), offering up to around ₹1.25 lakh for poor patients with rare illnesses and low annual income, again for treatment expenses in government hospitals and not as reimbursement.[^9]

### Prime Minister’s National Relief Fund (PMNRF)

The Prime Minister’s National Relief Fund (PMNRF) provides financial assistance to underprivileged patients suffering from major life‑threatening diseases, typically to support treatment in government or PMNRF‑enlisted hospitals. Applications require a formal submission addressed to the Prime Minister, along with income proof, ration card, medical certificate stating the disease, cost estimates, and photographs of the patient.[^9]

### Ayushman Bharat – PMJAY

Ayushman Bharat – Pradhan Mantri Jan Arogya Yojana (PMJAY) is a large national health insurance scheme that provides cashless treatment coverage up to a specified amount per family per year, at empanelled public and private hospitals, with specific eligibility criteria based on deprivation and occupational categories. The PMJAY hospital search portal allows patients to locate empanelled hospitals in Tamil Nadu, which is essential for routing low‑income patients to facilities where they can receive cashless care.[^1]

## Non‑governmental and private charity medical funds

### NGO‑managed medical financial assistance funds

A number of NGOs operate dedicated medical financial assistance programmes. Youth For Seva’s "Arogya Nidhi Medical Fund" is an example: it provides financial support for underprivileged patients nationwide who suffer from major life‑threatening illnesses and need help with hospitalisation expenses, long‑term medicines, emergency care, and post‑hospitalisation rehabilitation. Patients or their caregivers can contact the NGO via email or phone to seek assistance, and the fund itself is supported through individual and corporate donations.[^10]

Other NGOs, such as the Sadguru Foundation, also run programmes that raise funds for urgent medical cases, support surgeries and medicines, and connect donors directly with patients needing financial help for treatment. These NGOs typically cover a range of conditions, from paediatric cancers to accidents, using donor‑funded grants rather than government budgets.[^11]

### NGO directories and discovery platforms

Because NGOs are numerous and decentralised, central directories are useful for discovery. Medindia maintains a list of over 7,500 NGOs across India, browsable by state and focused on health and related causes. Separately, specialised foundations like MOHAN Foundation compile lists of NGOs working on specific medical themes, such as organ donation, searchable by city or state.[^12][^13]

Furthermore, philanthropy platforms like Give.do curate lists and describe the work of health‑focused NGOs that have significantly impacted healthcare in India, providing a curated entry point into credible organisations for partnerships or referrals. These platforms can help identify NGOs that already have strong track records in areas like rural primary care, cancer care, or child health.[^14]

## Practical strategy for your outreach‑focused project

### Building and maintaining the hospital database

Given the absence of a single authoritative state‑wide CSV of all hospitals, a realistic roadmap is:
- Phase 1: Automate scraping of district "Hospitals" pages, integrate Chennai urban health‑centre CSVs, and ingest Tamil Nadu’s PMJAY empanelled hospital list.[^4][^3][^6][^1]
- Phase 2: Augment with insurer network hospital Excel datasets and cross‑check with third‑party compiled lists, performing deduplication and normalisation.[^8][^7]
- Phase 3: Gradually enrich facilities with speciality tags (oncology, cardiology, etc.) and scheme compatibility (PMJAY, RAN‑eligible institutions, regional cancer centres) using information from NHM, government notifications, and hospital websites.[^2][^9][^1]

### Creating a directory of financial‑assistance options

For financial assistance and charity support, the recommended steps are:
- Catalogue national‑level government schemes (RAN and its sub‑schemes, PMNRF, PMJAY) with eligibility rules, required documents, and links to application processes.[^9][^1]
- Map NGO‑run medical funds (such as Arogya Nidhi and Sadguru Foundation) with contact details, diseases covered, and geographical scope, starting with pan‑India organisations.[^10][^11]
- Use NGO directories (Medindia NGO list, MOHAN Foundation NGO listings, and curated NGO lists on philanthropy platforms) to discover additional health‑focused NGOs that provide direct financial assistance or subsidised care, prioritising those working in Tamil Nadu and neighbouring states.[^13][^12][^14]

### Integrating into an application workflow

A React + FastAPI application to support patients and volunteers could:
- Provide search and filter for hospitals in Tamil Nadu by district, speciality, ownership, and scheme empanelment (e.g., PMJAY hospital near the patient’s location).[^6][^1]
- Surface government schemes and NGO funds relevant to a patient’s condition, along with basic eligibility criteria and links or contacts to apply.[^10][^9][^1]
- Maintain a backend knowledge base that links hospitals to schemes (e.g., hospitals that are PMJAY‑empanelled or are among RAN’s super‑specialty institutions) to guide patients towards facilities where their financial assistance options are valid.[^9][^1]

By combining multi‑source hospital datasets with a structured catalogue of government and NGO schemes, your system can both direct patients to appropriate treatment centres in Tamil Nadu and help them navigate realistic options for financial support.

---

## References

1. [Ayushman Bharat Hospitals List in Tamil Nadu - Download PDF](https://www.hexahealth.com/hospitals/insurance/ayushman-bharat-hospitals-list-tamil-nadu) - To download the Ayushman card hospital list in Tamil Nadu PDF, visit the official website here. Sele...

2. [Home | National Health Mission Tamil Nadu, Department of Health ...](http://www.nhm.tn.gov.in) - 'This Website belongs to Department National Health Mission Tamil Nadu Department of Health & Family...

3. [Hospitals | Tiruvannamalai District, Govt. of Tamil Nadu | India](https://tiruvannamalai.nic.in/public-utility-category/hospitals/) - Government Hospital, Arni Govt. Hospital, Arni Taluk, Tiruvannamalai District-632301 Phone : 04173-2...

4. [Hospitals | Karur District, Government of Tamil Nadu | India](https://karur.nic.in/public-utility-category/hospitals/) - Government Head Quarters Hospital, Kulithalai · Government Hospital, Aravakurichi · Government Hospi...

5. [Government Orders | 2 - National Health Mission Tamil Nadu](https://www.nhm.tn.gov.in/en/government-orders?field_gov_order_year_target_id=All&page=1) - Announcement - Establishment of Diabetic Foot Clinic in 21 Government Medical College Hospitals at a...

6. [Chennai Health Centres - Dataset - CKAN](https://data.opencity.in/dataset/chennai-healthcare-uphcs-and-uchcs) - List and maps of health centres in Chennai. UPHCs UCHCs, TB Centres, Maternity Hospitals VPHCs and A...

7. [[XLS] Download Hospital List - New India Assurance](https://www.newindia.co.in/assets/docs/hospitals-list/Chennai.xlsx) - SRM SPECIALITY HOSPITALS PRIVATE LIMITED. R2FV+6Q7, Potheri, SRM Nagar, Kattankulathur, Tamil Nadu 6...

8. [Tamil Nadu Government Hospitals List | PDF - Scribd](https://www.scribd.com/document/459104042/List-of-Hospitals-and-Medical-Colleges-in-Tamilnadu) - The document lists 148 hospitals and nursing homes in Tamilnadu. It includes the name of each medica...

9. [Financial Support For Life-Threatening Diseases: 4 National - Milaap](https://milaap.org/articles/schemes/financial-support-for-life-threatening-diseases-4-national-schemes-to-know) - Under the umbrella scheme of Rashtriya Arogya Nidhi, patients living below poverty line and sufferin...

10. [Arogya Nidhi Medical Fund - - Youth For Seva](https://youthforseva.org/programs/arogya-nidhi/) - Arogya Nidhi provides critical financial assistance for medical treatments. Contribute to our health...

11. [Financial Help for Poor Patients | Support Treatment India](https://www.sadgurufoundation.com/blog/financial-help-for-poor-patients/) - NGOs like Sadguru Foundation play a transformative role: Raising funds for urgent medical cases; Pro...

12. [Find A Non-government Organization(NGO) - Medindia](https://www.medindia.net/directories/ngos/index.htm) - Find a NGO. Medindia's NGO list has information on 7565 NGOs across India. The comprehensive NGO lis...

13. [NGOs List in India - MOHAN Foundation](https://www.mohanfoundation.org/ngos-list.asp) - Charity Status: MOHAN Foundation is a registered non-profit charitable trust and the Registration No...

14. [10 NGOs which have revolutionised healthcare in India - - Give.do](https://give.do/blog/10-ngos-which-have-revolutionised-healthcare-in-india/) - 1. Doctors For You ... Doctors for You (DFY) was founded in 2007 by doctors, medical students and li...

