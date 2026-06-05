"""Unit tests for ScraperService — regex extraction, CSV parsing, no DB required."""

import pytest

from app.services.scraper_service import (
    EMAIL_RE,
    PHONE_RE,
    PIN_RE,
    ScraperService,
    _extract_between,
)


# ── Regex pattern tests ───────────────────────────────────


class TestPINRegex:
    """PIN code extraction from Indian address text."""

    def test_standard_6_digit(self):
        assert PIN_RE.findall("Address: 12 Main St, PIN: 600001") == ["600001"]

    def test_pin_with_space(self):
        assert PIN_RE.findall("PIN: 600 001") == ["600 001"]

    def test_multiple_pins_returns_all(self):
        matches = PIN_RE.findall("From 600001 to 641001")
        assert len(matches) == 2

    def test_no_pin(self):
        assert PIN_RE.findall("No pincode here") == []

    def test_rejects_zero_starting(self):
        """PIN codes starting with 0 are invalid."""
        assert PIN_RE.findall("012345") == []


class TestPhoneRegex:
    """Phone number extraction from Indian contact text."""

    def test_10_digit_mobile(self):
        assert PHONE_RE.findall("Phone: 9876543210") == ["9876543210"]

    def test_with_country_code(self):
        """The regex captures the 10-digit mobile part after +91 prefix."""
        assert "9876543210" in PHONE_RE.findall("+91-9876543210")[0]

    def test_with_spaces(self):
        matches = PHONE_RE.findall("+91 98765 43210")
        assert len(matches) >= 1

    def test_landline_format(self):
        matches = PHONE_RE.findall("044-23456789")
        assert len(matches) >= 1

    def test_no_phone(self):
        assert PHONE_RE.findall("No phone here") == []


class TestEmailRegex:
    """Email extraction."""

    def test_standard_email(self):
        assert EMAIL_RE.findall("Contact: hospital@tn.gov.in") == ["hospital@tn.gov.in"]

    def test_gmail(self):
        assert EMAIL_RE.findall("admin@gmail.com") == ["admin@gmail.com"]

    def test_no_email(self):
        assert EMAIL_RE.findall("no email here") == []


# ── _extract_between tests ────────────────────────────────


class TestExtractBetween:
    """Label-based substring extraction."""

    def test_basic_extraction(self):
        text = "Phone: 9876543210 Email: test@example.com"
        result = _extract_between(r"Phone\s*:", r"Email\s*:", text)
        assert "9876543210" in result.strip()

    def test_no_end_label_returns_rest(self):
        text = "Email: test@example.com rest of text"
        result = _extract_between(r"Email\s*:", None, text)
        assert "test@example.com" in result

    def test_start_label_not_found(self):
        text = "No label here"
        result = _extract_between(r"Missing\s*:", r"End\s*:", text)
        assert result == ""

    def test_case_insensitive(self):
        text = "PHONE: 1234567890 email: x@y.com"
        result = _extract_between(r"phone\s*:", r"email\s*:", text)
        assert "1234567890" in result.strip()


# ── CSV parsing tests ─────────────────────────────────────


class TestParseHospitalsCSV:
    """Hospital CSV parser — happy path, edge cases, errors."""

    def _make_service(self):
        """Create a ScraperService with a None db (not used for parsing)."""
        return ScraperService(db=None)

    def test_valid_csv(self):
        csv_content = b"name,city,state,address,phone,email\n"
        csv_content += b"City Hospital,Chennai,Tamil Nadu,12 Main St,9876543210,h@test.com\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert len(records) == 1
        assert errors == []
        assert records[0]["name"] == "City Hospital"
        assert records[0]["city"] == "Chennai"

    def test_multiple_rows(self):
        csv_content = b"name,city\nCity Hospital,Chennai\nTown Hospital,Madurai\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert len(records) == 2

    def test_missing_name_error(self):
        csv_content = b"name,city\n,Chennai\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert len(records) == 0
        assert len(errors) == 1
        assert "missing 'name'" in errors[0]

    def test_missing_city_error(self):
        csv_content = b"name,city\nCity Hospital,\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert len(records) == 0
        assert len(errors) == 1
        assert "missing 'city'" in errors[0]

    def test_financial_assistance_flags(self):
        csv_content = b"name,city,has_financial_assistance\nH1,C,true\nH2,C,false\nH3,C,yes\nH4,C,1\n"
        records, _ = self._make_service().parse_hospitals_csv(csv_content)
        assert records[0]["has_financial_assistance"] is True
        assert records[1]["has_financial_assistance"] is False
        assert records[2]["has_financial_assistance"] is True
        assert records[3]["has_financial_assistance"] is True

    def test_bom_prefixed_csv(self):
        """UTF-8 BOM should be handled gracefully."""
        csv_content = b"\xef\xbb\xbfname,city\nHosp,Chennai\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert len(records) == 1
        assert errors == []

    def test_empty_csv(self):
        csv_content = b"name,city\n"
        records, errors = self._make_service().parse_hospitals_csv(csv_content)
        assert records == []
        assert errors == []

    def test_optional_fields_default_to_none(self):
        csv_content = b"name,city\nHosp,Chennai\n"
        records, _ = self._make_service().parse_hospitals_csv(csv_content)
        r = records[0]
        assert r["state"] is None
        assert r["address"] is None
        assert r["phone"] is None
        assert r["email"] is None
        assert r["website"] is None
        assert r["specialties"] is None


class TestParseNgosCSV:
    """NGO/Funding program CSV parser."""

    def _make_service(self):
        return ScraperService(db=None)

    def test_valid_ngo_csv(self):
        csv_content = (
            b"name,description,provider,program_type,eligibility_criteria,"
            b"max_amount,min_amount,application_url,contact_email,contact_phone\n"
            b"Cancer Relief Fund,Provides financial aid,Trust,grant,Low income,500000,10000,"
            b"http://apply.org,fund@trust.org,9876543210\n"
        )
        records, errors = self._make_service().parse_ngos_csv(csv_content)
        assert len(records) == 1
        assert errors == []
        assert records[0]["name"] == "Cancer Relief Fund"
        assert records[0]["max_amount"] == 500000.0
        assert records[0]["min_amount"] == 10000.0

    def test_missing_name_error(self):
        csv_content = b"name,provider\n,SomeOrg\n"
        records, errors = self._make_service().parse_ngos_csv(csv_content)
        assert len(records) == 0
        assert len(errors) == 1
        assert "missing 'name'" in errors[0]

    def test_optional_amounts_default_to_none(self):
        csv_content = b"name,max_amount,min_amount\nFund Only,,\n"
        records, _ = self._make_service().parse_ngos_csv(csv_content)
        assert records[0]["max_amount"] is None
        assert records[0]["min_amount"] is None

    def test_empty_csv(self):
        csv_content = b"name\n"
        records, errors = self._make_service().parse_ngos_csv(csv_content)
        assert records == []
        assert errors == []
