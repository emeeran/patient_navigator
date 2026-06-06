#!/usr/bin/env python3
"""Scrape Chennai hospitals (govt + private) and import into the database.

Usage:
    cd backend
    python scripts/scrape_chennai_hospitals.py          # scrape + import
    python scripts/scrape_chennai_hospitals.py --dry-run # preview only
"""

import argparse
import asyncio
import csv
import io
import json
import logging
import re
import sys
import time
from pathlib import Path

import httpx
from bs4 import BeautifulSoup

# ── Add project root to path so we can import app modules ──────────────────
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
logger = logging.getLogger(__name__)

PHONE_RE = re.compile(r"(?:\+91[-\s]?)?(?:[6-9]\d{9}|\d{3,5}[-\s]?\d{5,8})")
EMAIL_RE = re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}")
PIN_RE = re.compile(r"\b600\d{3}\b")  # Chennai pincodes start with 600xxx

HEADERS = {
    "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 "
                  "(KHTML, like Gecko) Chrome/125.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "en-US,en;q=0.5",
}

CHENNAI_GOV_HOSPITALS = [
    # Well-known Government Hospitals in Chennai
    {"name": "Government General Hospital (Rajiv Gandhi Govt. General Hospital)", "address": "EVR Salai, Park Town, Chennai", "phone": "04425340501", "specialties": "Multi-Specialty, General Medicine, Surgery, Trauma Care, Cardiology, Neurology, Nephrology", "website": "https://chennai.nic.in/hospitals/", "category": "government"},
    {"name": "Government Stanley Medical College Hospital", "address": "Old Jail Road, Stanley Nagar, Chennai 600001", "phone": "04425261333", "specialties": "Medical College, General Medicine, Surgery, Orthopaedics, Paediatrics, OBG, Burns & Plastic Surgery", "website": "https://stanleymedicalcollege.com", "category": "government"},
    {"name": "Kilpauk Medical College Hospital", "address": "49, EVR Salai, Kilpauk, Chennai 600010", "phone": "04426441111", "specialties": "Medical College, General Medicine, Surgery, Cardiology, Neurology, Dermatology", "website": "https://kilpaukmc.tn.gov.in", "category": "government"},
    {"name": "Madras Medical College & Government General Hospital", "address": "EV Salai, Park Town, Chennai 600003", "phone": "04425340501", "specialties": "Medical College, Multi-Specialty, Research", "website": "https://mmc.ac.in", "category": "government"},
    {"name": "Government Royapettah Hospital", "address": "Westcott Road, Royapettah, Chennai 600014", "phone": "04428483111", "specialties": "General Medicine, Surgery, Paediatrics, OBG", "category": "government"},
    {"name": "Government RSRM Hospital (Raja Sir Ramaswamy Mudaliar)", "address": "RSRM Hospital Road, Royapuram, Chennai 600013", "phone": "04425951350", "specialties": "General Medicine, Surgery, Paediatrics, OBG, Neonatal Care", "category": "government"},
    {"name": "Government Women and Children Hospital (Egmore)", "address": "Pantheon Road, Egmore, Chennai 600008", "phone": "04428190133", "specialties": "Paediatrics, Obstetrics & Gynaecology, Neonatal Intensive Care", "category": "government"},
    {"name": "Institute of Child Health and Hospital for Children", "address": "Halls Road, Egmore, Chennai 600008", "phone": "04428190133", "specialties": "Paediatrics, Paediatric Surgery, Neonatology, Paediatric Cardiology", "category": "government"},
    {"name": "Institute of Obstetrics and Gynaecology (IOG)", "address": "Pantheon Road, Egmore, Chennai 600008", "phone": "04428191008", "specialties": "Obstetrics, Gynaecology, Reproductive Medicine, Neonatal Care", "category": "government"},
    {"name": "Government Peripheral Hospital (Anna Nagar)", "address": "21, 3rd Main Road, Anna Nagar East, Chennai 600102", "phone": "04426203533", "specialties": "General Medicine, Surgery, Emergency Care", "category": "government"},
    {"name": "Government Tuberculosis Hospital (Tambaram)", "address": "Tambaram, Chennai 600047", "phone": "04422260202", "specialties": "Pulmonology, TB Treatment, Respiratory Medicine", "category": "government"},
    {"name": "Government Hospital of Thoracic Medicine (Tambaram)", "address": "Tambaram Sanatorium, Chennai 600047", "phone": "04422260202", "specialties": "Pulmonology, Thoracic Surgery, HIV/AIDS Treatment, Respiratory Medicine", "category": "government"},
    {"name": "ESI Hospital (KK Nagar)", "address": "7th Street, KK Nagar, Chennai 600078", "phone": "04424733777", "specialties": "General Medicine, Surgery, Orthopaedics, OBG", "category": "government"},
    {"name": "ESI Hospital (Ayanavaram)", "address": "Konnur High Road, Ayanavaram, Chennai 600023", "phone": "04426740808", "specialties": "General Medicine, Emergency Care", "category": "government"},
    {"name": "Corporation Hospital (Ripon Building)", "address": "EV Salai, Chennai 600003", "phone": "04425610200", "specialties": "General Medicine, Primary Health Care", "category": "government"},
    {"name": "Urban Health Centre (Tondiarpet)", "address": "Tondiarpet, Chennai 600081", "phone": "04425951558", "specialties": "Primary Care, General Medicine", "category": "government"},
    {"name": "Government Ophthalmic Hospital (Egmore)", "address": "163, EVR Salai, Chennai 600008", "phone": "04428190401", "specialties": "Ophthalmology, Eye Surgery, Cataract Treatment", "category": "government"},
    {"name": "Regional Institute of Ophthalmology", "address": "163, EVR Salai, Chennai 600008", "phone": "04428190401", "specialties": "Ophthalmology, Research, Eye Care", "category": "government"},
    {"name": "Government Mental Hospital (Kilpauk)", "address": "Poonamallee High Road, Kilpauk, Chennai 600010", "phone": "04426421178", "specialties": "Psychiatry, Psychology, Mental Health", "category": "government"},
    {"name": "Institute of Mental Health (Kilpauk)", "address": "Poonamallee High Road, Kilpauk, Chennai 600010", "phone": "04426421178", "specialties": "Psychiatry, Clinical Psychology, De-addiction, Psychosocial Rehabilitation", "category": "government"},
    {"name": "Primary Health Centre (Adyar)", "address": "Adyar, Chennai 600020", "phone": "04424410256", "specialties": "Primary Care, General Medicine, Immunisation", "category": "government"},
    {"name": "Primary Health Centre (Velachery)", "address": "Velachery, Chennai 600042", "specialties": "Primary Care, General Medicine", "category": "government"},
    {"name": "Primary Health Centre (T Nagar)", "address": "Thyagaraya Nagar, Chennai 600017", "specialties": "Primary Care, General Medicine", "category": "government"},
    {"name": "Primary Health Centre (Mylapore)", "address": "Mylapore, Chennai 600004", "specialties": "Primary Care, General Medicine", "category": "government"},
    {"name": "Communicable Diseases Hospital (Tondiarpet)", "address": "Tondiarpet, Chennai 600081", "phone": "04425950444", "specialties": "Infectious Diseases, General Medicine", "category": "government"},
]

CHENNAI_PRIVATE_HOSPITALS = [
    # Major Private / Multi-Specialty Hospitals
    {"name": "Apollo Hospitals (Greams Road)", "address": "21, Greams Lane, Off Greams Road, Chennai 600006", "phone": "04428290200", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, Neurology, Oncology, Organ Transplant, Urology, Gastroenterology", "website": "https://apollohospitals.com", "email": "info@apollohospitals.com", "category": "private"},
    {"name": "Apollo Children's Hospital", "address": "15/17, Greams Lane, Chennai 600006", "phone": "04428290200", "specialties": "Paediatrics, Paediatric Cardiology, Paediatric Surgery, Neonatology", "website": "https://apollohospitals.com", "category": "private"},
    {"name": "Apollo Proton Cancer Centre", "address": "20, Poonamallee High Road, Chennai 600084", "phone": "04440455555", "specialties": "Oncology, Radiation Therapy, Proton Therapy, Cancer Surgery", "website": "https://apolloprotoncancercentre.com", "category": "private"},
    {"name": "MIOT International", "address": "4/112, Mount Poonamallee Road, Manapakkam, Chennai 600089", "phone": "04422492288", "specialties": "Multi-Specialty, Orthopaedics, Cardiology, Oncology, Nephrology, Urology, Gastroenterology, Neurosurgery", "website": "https://miotinternational.com", "email": "info@miotinternational.com", "category": "private"},
    {"name": "Fortis Malar Hospital", "address": "52, 1st Main Road, Gandhi Nagar, Adyar, Chennai 600020", "phone": "04442892222", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, Neurology, Urology, General Surgery", "website": "https://fortishealthcare.com", "category": "private"},
    {"name": "Sri Ramachandra Medical Centre (SRMC)", "address": "No.1, Mount Poonamallee Road, Sri Ramachandra Nagar, Porur, Chennai 600116", "phone": "04424768480", "specialties": "Multi-Specialty, Cardiac Sciences, Neurosciences, Orthopaedics, Oncology, Organ Transplant, Gastroenterology", "website": "https://sriramachandra.edu.in", "email": "info@sriramachandra.edu.in", "category": "private"},
    {"name": "Billroth Hospitals", "address": "43, Lakshmi Talkies Road, Shenoy Nagar, Chennai 600030", "phone": "04442854555", "specialties": "Multi-Specialty, General Surgery, Urology, Gastroenterology, Obstetrics & Gynaecology", "website": "https://billrothhospitals.com", "category": "private"},
    {"name": "Kauvery Hospital (Alwarpet)", "address": "81, TTK Road, Alwarpet, Chennai 600018", "phone": "04440094009", "specialties": "Multi-Specialty, Cardiology, Neurology, Orthopaedics, Nephrology, Emergency Care", "website": "https://kauveryhospital.com", "category": "private"},
    {"name": "Kauvery Hospital (Radial Road)", "address": "321, Radial Road, Anna Nagar, Chennai 600040", "phone": "04442854488", "specialties": "Multi-Specialty, Cardiac Sciences, Neurosciences, Orthopaedics", "website": "https://kauveryhospital.com", "category": "private"},
    {"name": "Global Hospitals (Perumbakkam)", "address": "439, Cheran Nagar, Perumbakkam, Chennai 600100", "phone": "04442854488", "specialties": "Multi-Specialty, Liver Transplant, Hepatology, Nephrology, Oncology, Cardiology", "website": "https://globalhospitalsindia.com", "category": "private"},
    {"name": "Vijaya Hospital (Vadapalani)", "address": "398, Arcot Road, Vadapalani, Chennai 600026", "phone": "04424732057", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, General Surgery, OBG", "website": "https://vijayamedical.com", "category": "private"},
    {"name": "Vijaya Heart Foundation", "address": "398, Arcot Road, Vadapalani, Chennai 600026", "phone": "04424732057", "specialties": "Cardiology, Cardiac Surgery, Interventional Cardiology", "website": "https://vijayamedical.com", "category": "private"},
    {"name": "SIMS Hospital (Vadapalani)", "address": "1, 179, Jawaharlal Nehru Salai, Vadapalani, Chennai 600026", "phone": "04442892222", "specialties": "Multi-Specialty, Cardiac Sciences, Neurosciences, Orthopaedics, Oncology, Nephrology", "website": "https://simshospitals.com", "category": "private"},
    {"name": "Prashanth Super Speciality Hospital", "address": "525, Kundrathur Main Road, Porur, Chennai 600116", "phone": "04422492288", "specialties": "Multi-Specialty, Orthopaedics, Cardiology, Urology, General Surgery", "website": "https://prashanthhospitals.com", "category": "private"},
    {"name": "Chennai Meenakshi Multi-Specialty Hospital", "address": "513, EVR Salai, Aminijikarai, Chennai 600106", "phone": "04423742222", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, General Surgery, OBG", "website": "https://chennaimeenakshihospital.com", "category": "private"},
    {"name": "Sankara Nethralaya", "address": "18, College Road, Nungambakkam, Chennai 600006", "phone": "04428271616", "specialties": "Ophthalmology, Eye Surgery, Vitreo-Retinal Surgery, Cataract, Glaucoma, Cornea", "website": "https://sankaranethralaya.org", "email": "mail@sankaranethralaya.org", "category": "private"},
    {"name": "Sankara Nethralaya (Rangarajapuram)", "address": "41, CST Road, Rangarajapuram, Chennai 600015", "phone": "04424842222", "specialties": "Ophthalmology, Eye Care", "website": "https://sankaranethralaya.org", "category": "private"},
    {"name": "Agarwal's Eye Hospital", "address": "19, Cathedral Road, Chennai 600086", "phone": "04428113100", "specialties": "Ophthalmology, LASIK, Cataract Surgery, Retina, Glaucoma", "website": "https://dragarwal.com", "category": "private"},
    {"name": "Dr. Agarwal's Eye Hospital (Anna Nagar)", "address": "B30, 4th Avenue, Anna Nagar, Chennai 600040", "phone": "04426203030", "specialties": "Ophthalmology, Eye Surgery", "website": "https://dragarwal.com", "category": "private"},
    {"name": "Vasan Eye Care Hospital (Chennai)", "address": "Old No.3, New No.6, Dr. Nair Road, T. Nagar, Chennai 600017", "phone": "04424341010", "specialties": "Ophthalmology, Eye Surgery, LASIK", "website": "https://vasaneyecare.com", "category": "private"},
    {"name": "Madras Institute of Orthopaedics and Traumatology (MIOT)", "address": "4/112, Mount Poonamallee Road, Manapakkam, Chennai 600089", "phone": "04422492288", "specialties": "Orthopaedics, Traumatology, Joint Replacement, Spine Surgery", "website": "https://miotinternational.com", "category": "private"},
    {"name": "Hindu Mission Hospital", "address": "260, GST Road, Tambaram, Chennai 600045", "phone": "04422262020", "specialties": "General Medicine, Surgery, Paediatrics, OBG, Orthopaedics", "website": "https://hindumissionhospital.org", "category": "private"},
    {"name": "C.M. Hospital (Anna Nagar)", "address": "23, 3rd Main Road, Anna Nagar East, Chennai 600102", "phone": "04426201666", "specialties": "Obstetrics & Gynaecology, Fertility, Neonatal Care", "category": "private"},
    {"name": "Sundaram Medical Foundation (Dr. Rangarajan Memorial Hospital)", "address": "4, Cathedral Road, Chennai 600086", "phone": "04428113600", "specialties": "General Medicine, Cardiology, Diabetology, Nephrology, OBG", "website": "https://smfhospital.org", "category": "private"},
    {"name": "B.M. Hospital", "address": "5, First Cross Street, Gandhi Nagar, Adyar, Chennai 600020", "phone": "04424411433", "specialties": "General Medicine, Paediatrics, OBG", "category": "private"},
    {"name": "Apollo Spectra Hospital (Alwarpet)", "address": "39, Giri Road, Alwarpet, Chennai 600018", "phone": "04440455555", "specialties": "Multi-Specialty Day Care, General Surgery, Urology, Orthopaedics", "website": "https://apollospectra.com", "category": "private"},
    {"name": "Motherhood Hospital (Chennai)", "address": "5, Vaikundam Street, Kodambakkam, Chennai 600024", "phone": "04440339999", "specialties": "Obstetrics & Gynaecology, Fertility, Neonatal Care, Paediatrics", "website": "https://motherhoodindia.com", "category": "private"},
    {"name": "Cloudnine Hospital (Chennai)", "address": "Old No.40, New No.10, Gillander Avenue, Chennai 600104", "phone": "04440339999", "specialties": "Obstetrics & Gynaecology, Fertility, NICU, Paediatrics", "website": "https://cloudninecare.com", "category": "private"},
    {"name": "Prashanth Hospitals (Velachery)", "address": "154, Velachery Main Road, Velachery, Chennai 600042", "phone": "04422431111", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, General Surgery", "website": "https://prashanthhospitals.com", "category": "private"},
    {"name": "K.R. Hospital (Tambaram)", "address": "1, Kamarajar Street, Tambaram, Chennai 600045", "phone": "04422263888", "specialties": "General Medicine, Surgery, Paediatrics", "category": "private"},
    {"name": "Lifeline Hospitals (Kilpauk)", "address": "5/639, Old Mahabalipuram Road, Sholinganallur, Chennai 600119", "phone": "04424501444", "specialties": "Multi-Specialty, Gastroenterology, General Surgery, Urology", "website": "https://lifelinehospitals.com", "category": "private"},
    {"name": "Sooriya Hospital (Chennai)", "address": "4/130, Poonamallee High Road, Kilpauk, Chennai 600084", "phone": "04442867777", "specialties": "Multi-Specialty, General Medicine, Surgery, OBG", "category": "private"},
    {"name": "Devadoss Hospital (Chennai)", "address": "76, Peters Road, Royapettah, Chennai 600014", "phone": "04428483344", "specialties": "Multi-Specialty, Orthopaedics, Cardiology, Neurology", "category": "private"},
    {"name": "GG Hospital (Chennai)", "address": "205, EVR Salai, Kilpauk, Chennai 600010", "phone": "04426441222", "specialties": "General Medicine, Surgery, OBG, Paediatrics", "category": "private"},
    {"name": "Apollo Indraprastha Hospital", "address": "655, Anna Salai, Chennai 600035", "phone": "04428290200", "specialties": "Multi-Specialty, Emergency, General Medicine", "website": "https://apollohospitals.com", "category": "private"},
    {"name": "Kamakshi Memorial Hospital", "address": "1, Pillayar Koil Street, Pallikaranai, Chennai 600100", "phone": "04422781122", "specialties": "General Medicine, Surgery, Paediatrics, OBG", "category": "private"},
    {"name": "Pattan Hospital", "address": "120, Peters Road, Royapettah, Chennai 600014", "phone": "04428480207", "specialties": "General Medicine, Surgery", "category": "private"},
    {"name": "Madras Medical Mission Hospital", "address": "4A, Dr. J. Jayalalithaa Nagar, Mogappair, Chennai 600037", "phone": "04426565555", "specialties": "Cardiology, Cardiac Surgery, Nephrology, Urology", "website": "https://mmh.org.in", "category": "private"},
    {"name": "Bharath Hospital (Chennai)", "address": "12, GN Chetty Road, T. Nagar, Chennai 600017", "phone": "04424342222", "specialties": "General Medicine, ENT, OBG, Paediatrics", "category": "private"},
    {"name": "Sri Ramachandra Institute of Higher Education and Research", "address": "No.1, Mount Poonamallee Road, Porur, Chennai 600116", "phone": "04424765650", "specialties": "Multi-Specialty, Medical Research, Cardiology, Neurology, Oncology", "website": "https://sriramachandra.edu.in", "category": "private"},
    {"name": "Dr. Mehta's Hospitals (Chetpet)", "address": "12, McNichols Road, Chetpet, Chennai 600031", "phone": "04442271111", "specialties": "Multi-Specialty, General Surgery, Cardiology, Orthopaedics", "website": "https://drmehtashospitals.com", "category": "private"},
    {"name": "Deepam Hospital (Chennai)", "address": "200, GST Road, Chromepet, Chennai 600044", "phone": "04422383333", "specialties": "General Medicine, Surgery, Paediatrics, OBG, Orthopaedics", "website": "https://deepamhospital.com", "category": "private"},
    {"name": "Alpha Hospital & Research Centre", "address": "19, 1st Cross Street, CIT Colony, Mylapore, Chennai 600004", "phone": "04424660112", "specialties": "Multi-Specialty, General Medicine, Surgery", "category": "private"},
    {"name": "Ortho One Orthopaedic Speciality Centre", "address": "654, GST Road, Chromepet, Chennai 600044", "phone": "04422260808", "specialties": "Orthopaedics, Joint Replacement, Arthroscopy, Spine Surgery, Sports Medicine", "website": "https://orthoone.in", "category": "private"},
    {"name": "MGM Healthcare (Chennai)", "address": "72, 1st Main Road, Nehru Nagar, Chromepet, Chennai 600044", "phone": "04422260111", "specialties": "Multi-Specialty, Cardiology, Orthopaedics, General Surgery, Neurology", "website": "https://mgmhealthcare.in", "category": "private"},
    {"name": "St. Isabel's Hospital", "address": "19, Dr. Radhakrishnan Salai, Mylapore, Chennai 600004", "phone": "04424981234", "specialties": "General Medicine, Surgery, OBG, Paediatrics, ENT", "category": "private"},
    {"name": "K.J. Hospital (Chennai)", "address": "Kilpauk Garden Road, Kilpauk, Chennai 600010", "phone": "04426441555", "specialties": "General Medicine, Surgery, Urology", "category": "private"},
    {"name": "Asian Bharath Hospital & Research Institute", "address": "26, Mangadu Road, Kattupakkam, Chennai 600056", "phone": "04426791234", "specialties": "Multi-Specialty, General Medicine, Surgery, Cardiology", "category": "private"},
    {"name": "Balan Hospital (Chennai)", "address": "34, Peters Road, Royapettah, Chennai 600014", "phone": "04428481111", "specialties": "General Medicine, Surgery, OBG", "category": "private"},
    {"name": "Medway Hospitals (Chennai)", "address": "47, Nelson Manickam Road, Aminjikarai, Chennai 600029", "phone": "04423744444", "specialties": "Multi-Specialty, Gastroenterology, Pulmonology, General Medicine", "website": "https://medwayhospitals.com", "category": "private"},
    {"name": "Rainbow Children's Hospital (Chennai)", "address": "21, 1st Main Road, Gandhi Nagar, Adyar, Chennai 600020", "phone": "04440339999", "specialties": "Paediatrics, Paediatric Surgery, Neonatology, Paediatric Cardiology", "website": "https://rainbowhospitals.in", "category": "private"},
    {"name": "Isabelle Hospital (Chennai)", "address": "64, Marshalls Road, Egmore, Chennai 600008", "phone": "04428271717", "specialties": "General Medicine, Surgery, OBG, ENT", "category": "private"},
    {"name": "Apollo Cradle & Children's Hospital (Chennai)", "address": "54, Dr. Thomas Road, T. Nagar, Chennai 600017", "phone": "04428110600", "specialties": "Obstetrics & Gynaecology, Fertility, Paediatrics, Neonatal Care", "website": "https://apollocradle.com", "category": "private"},
    {"name": "KG Hospital (Chennai)", "address": "1040, Poonamallee High Road, Anna Nagar West, Chennai 600101", "phone": "04426546666", "specialties": "General Medicine, Surgery, OBG", "category": "private"},
    {"name": "Mullai Hospital (Chennai)", "address": "38, Vembuli Amman Koil Street, Chromepet, Chennai 600044", "phone": "04422260444", "specialties": "General Medicine, Paediatrics, OBG", "category": "private"},
    {"name": "Shenoy Nagar Health Centre", "address": "Shenoy Nagar, Chennai 600030", "specialties": "Primary Care, General Medicine", "category": "government"},
    {"name": "Government Upgraded Primary Health Centre (Perungudi)", "address": "Perungudi, Chennai 600096", "specialties": "Primary Care, General Medicine, Immunisation", "category": "government"},
    {"name": "Nagarathinam Angammal Hospital", "address": "Poonamallee High Road, Kilpauk, Chennai 600010", "phone": "04426441444", "specialties": "General Medicine, ENT, OBG", "category": "private"},
    {"name": "Cancer Institute (WIA) Adyar", "address": "38, Canal Road, Gandhi Nagar, Adyar, Chennai 600020", "phone": "04424912542", "specialties": "Oncology, Radiation Therapy, Surgical Oncology, Medical Oncology, Palliative Care", "website": "https://cancerinstitutewia.org", "category": "private"},
    {"name": "Sri Venkateswara Dental College & Hospital", "address": "Off ECR, Injambakkam, Chennai 600115", "phone": "04424542244", "specialties": "Dentistry, Oral Surgery, Orthodontics, Periodontics", "category": "private"},
    {"name": "Tagore Dental College & Hospital", "address": "300, EVR Periyar Salai, Vepery, Chennai 600007", "phone": "04426421010", "specialties": "Dentistry, Oral & Maxillofacial Surgery, Prosthodontics", "category": "private"},
    {"name": "Sri Ramachandra Dental College & Hospital", "address": "Mount Poonamallee Road, Porur, Chennai 600116", "phone": "04424765650", "specialties": "Dentistry, Oral Surgery, Conservative Dentistry", "website": "https://sriramachandra.edu.in", "category": "private"},
    {"name": "Sree Balaji Medical College and Hospital", "address": "7, Works Road, Chromepet, Chennai 600044", "phone": "04422260909", "specialties": "Medical College, Multi-Specialty, General Medicine, Surgery, Orthopaedics", "website": "https://sreebalajimch.com", "category": "private"},
    {"name": "ACS Medical College and Hospital", "address": "Velappanchavadi, Chennai 600077", "phone": "04426580101", "specialties": "Medical College, Multi-Specialty, General Medicine, Surgery", "category": "private"},
]


async def scrape_justdial_chennai() -> list[dict]:
    """Attempt to scrape Justdial Chennai hospitals page."""
    results = []
    urls = [
        "https://www.justdial.com/Chennai/Government-Hospitals-in-Chennai/nct-10180326",
        "https://www.justdial.com/Chennai/Private-Hospitals-in-Chennai/nct-10180325",
        "https://www.justdial.com/Chennai/Multi-Specialty-Hospitals-in-Chennai/nct-10180327",
    ]
    async with httpx.AsyncClient(headers=HEADERS, timeout=20.0, follow_redirects=True) as client:
        for url in urls:
            try:
                resp = await client.get(url)
                if resp.status_code != 200:
                    logger.warning(f"Justdial returned {resp.status_code} for {url}")
                    continue
                soup = BeautifulSoup(resp.text, "lxml")

                # Justdial listing cards
                for card in soup.select(".cntanr, .store-details, [class*='listbox']"):
                    name_el = card.select_one(".store-name, .lng_cont_name, [class*='jcn']")
                    if not name_el:
                        continue
                    name = name_el.get_text(strip=True)
                    if not name or len(name) < 3:
                        continue

                    addr_el = card.select_one(".address-text, .cnt_addr, [class*='address']")
                    address = addr_el.get_text(strip=True) if addr_el else None

                    phone_el = card.select_one(".contact-info, .phone-no, [class*='tel']")
                    phone_text = phone_el.get_text(strip=True) if phone_el else ""
                    phones = PHONE_RE.findall(phone_text)
                    phone = phones[0] if phones else None

                    results.append({
                        "name": name,
                        "city": "Chennai",
                        "state": "Tamil Nadu",
                        "address": address,
                        "phone": phone,
                        "specialties": None,
                        "category": "private",
                    })

                await asyncio.sleep(1.5)  # be polite
            except Exception as e:
                logger.warning(f"Failed to scrape Justdial ({url}): {e}")

    return results


def normalize_hospital(h: dict) -> dict:
    """Normalize a hospital record for import."""
    name = h.get("name", "").strip()
    if not name:
        return None

    phone = h.get("phone", "").strip() if h.get("phone") else None
    if phone:
        # Clean to digits only, keep last 10
        phone_digits = re.sub(r"[^\d]", "", phone)
        if len(phone_digits) > 10:
            phone_digits = phone_digits[-10:]
        phone = phone_digits if len(phone_digits) >= 7 else None

    email = h.get("email", "").strip() if h.get("email") else None
    website = h.get("website", "").strip() if h.get("website") else None

    category = h.get("category", "")
    has_financial = category == "government"

    return {
        "name": name,
        "city": "Chennai",
        "state": "Tamil Nadu",
        "address": h.get("address", "").strip() or None,
        "phone": phone,
        "email": email or None,
        "website": website or None,
        "specialties": h.get("specialties", "").strip() or None,
        "has_financial_assistance": has_financial,
    }


async def scrape_chennai_hospitals() -> list[dict]:
    """Aggregate Chennai hospitals from curated list + web scraping."""
    all_hospitals = []

    # 1. Curated government hospitals
    for h in CHENNAI_GOV_HOSPITALS:
        rec = normalize_hospital(h)
        if rec:
            all_hospitals.append(rec)
    logger.info(f"Curated government hospitals: {len(CHENNAI_GOV_HOSPITALS)}")

    # 2. Curated private hospitals
    for h in CHENNAI_PRIVATE_HOSPITALS:
        rec = normalize_hospital(h)
        if rec:
            all_hospitals.append(rec)
    logger.info(f"Curated private hospitals: {len(CHENNAI_PRIVATE_HOSPITALS)}")

    # 3. Web scraping attempt (Justdial)
    try:
        jd_hospitals = await scrape_justdial_chennai()
        for h in jd_hospitals:
            rec = normalize_hospital(h)
            if rec:
                all_hospitals.append(rec)
        logger.info(f"Justdial scraped: {len(jd_hospitals)}")
    except Exception as e:
        logger.warning(f"Web scraping skipped: {e}")

    # Deduplicate by name (case-insensitive)
    seen = {}
    deduped = []
    for h in all_hospitals:
        key = h["name"].lower().strip()
        if key not in seen:
            seen[key] = h
            deduped.append(h)
        else:
            # Merge — keep the one with more data
            existing = seen[key]
            for field in ("phone", "email", "website", "address", "specialties"):
                if not existing.get(field) and h.get(field):
                    existing[field] = h[field]

    logger.info(f"Total unique hospitals after dedup: {len(deduped)}")
    return deduped


async def import_via_api(hospitals: list[dict], backend_url: str) -> None:
    """Import hospitals through the admin bulk import API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        # First login to get a token
        login_resp = await client.post(
            f"{backend_url}/auth/login",
            json={"email": "admin@test.com", "password": "TestPass123!"},
        )
        if login_resp.status_code != 200:
            logger.error(f"Login failed: {login_resp.status_code} {login_resp.text}")
            return

        token = login_resp.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}

        # Import in batches of 50
        batch_size = 50
        total_imported = 0
        total_skipped = 0

        for i in range(0, len(hospitals), batch_size):
            batch = hospitals[i : i + batch_size]
            resp = await client.post(
                f"{backend_url}/admin/import/hospitals",
                json={"hospitals": batch},
                headers=headers,
            )
            if resp.status_code == 200:
                result = resp.json()
                total_imported += result.get("imported", 0)
                total_skipped += result.get("skipped", 0)
                errors = result.get("errors", [])
                if errors:
                    for e in errors[:5]:
                        logger.warning(f"Import error: {e}")
                logger.info(f"Batch {i // batch_size + 1}: imported={result.get('imported', 0)}, skipped={result.get('skipped', 0)}")
            else:
                logger.error(f"Import API error: {resp.status_code} {resp.text[:200]}")

        logger.info(f"\n{'='*50}")
        logger.info(f"IMPORT COMPLETE")
        logger.info(f"  Imported: {total_imported}")
        logger.info(f"  Skipped (duplicates): {total_skipped}")
        logger.info(f"{'='*50}")


async def main():
    parser = argparse.ArgumentParser(description="Scrape Chennai hospitals and import to DB")
    parser.add_argument("--dry-run", action="store_true", help="Print results without importing")
    parser.add_argument("--output", type=str, help="Save results to JSON file")
    parser.add_argument("--backend-url", type=str, default="http://localhost:8002", help="Backend URL")
    args = parser.parse_args()

    logger.info("Scraping Chennai hospitals...")
    hospitals = await scrape_chennai_hospitals()

    # Categorize
    gov_count = sum(1 for h in hospitals if h.get("has_financial_assistance"))
    pvt_count = len(hospitals) - gov_count
    logger.info(f"\nGovernment hospitals: {gov_count}")
    logger.info(f"Private hospitals: {pvt_count}")
    logger.info(f"Total: {len(hospitals)}\n")

    if args.output:
        with open(args.output, "w") as f:
            json.dump(hospitals, f, indent=2, ensure_ascii=False)
        logger.info(f"Saved to {args.output}")

    if args.dry_run:
        logger.info("Dry run — printing first 10 hospitals:")
        for h in hospitals[:10]:
            logger.info(f"  {h['name']}")
            if h.get("address"):
                logger.info(f"    Address: {h['address']}")
            if h.get("phone"):
                logger.info(f"    Phone: {h['phone']}")
            if h.get("specialties"):
                logger.info(f"    Specialties: {h['specialties']}")
            logger.info("")
        logger.info(f"... and {len(hospitals) - 10} more")
        return

    await import_via_api(hospitals, args.backend_url)


if __name__ == "__main__":
    asyncio.run(main())
