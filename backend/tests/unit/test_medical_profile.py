"""Unit tests for MedicalProfile schemas and helpers."""

from datetime import date

import pytest

from app.schemas.medical_profile import (
    MedicalProfileCreateRequest,
    MedicalProfileUpdateRequest,
    _compute_bmi,
    medical_profile_to_dict,
)


# ── BMI Computation ─────────────────────────────────────


class TestComputeBmi:
    def test_normal_bmi(self):
        assert _compute_bmi(170, 70) == 24.2

    def test_obese_bmi(self):
        assert _compute_bmi(165, 100) == 36.7

    def test_underweight_bmi(self):
        assert _compute_bmi(180, 50) == 15.4

    def test_none_height(self):
        assert _compute_bmi(None, 70) is None

    def test_none_weight(self):
        assert _compute_bmi(170, None) is None

    def test_both_none(self):
        assert _compute_bmi(None, None) is None

    def test_zero_height(self):
        assert _compute_bmi(0, 70) is None

    def test_precision_one_decimal(self):
        bmi = _compute_bmi(175, 68)
        # 68 / (1.75^2) = 22.204...
        assert bmi == 22.2


# ── Schema Validation ───────────────────────────────────


class TestMedicalProfileCreateRequest:
    def test_valid_with_all_fields(self):
        req = MedicalProfileCreateRequest(
            date_of_birth=date(1990, 5, 15),
            height_cm=175.0,
            weight_kg=70.0,
            blood_type="O+",
            past_medical_history=["Appendectomy 2018"],
            family_medical_history=[{"relation": "father", "condition": "Diabetes"}],
            chronic_conditions=["Hypertension"],
            current_medications=["Metformin 500mg"],
            allergies=["Penicillin"],
            notes="Generally healthy",
        )
        assert req.height_cm == 175.0

    def test_valid_with_one_field(self):
        req = MedicalProfileCreateRequest(height_cm=170)
        assert req.height_cm == 170

    def test_empty_raises_validation_error(self):
        with pytest.raises(ValueError, match="At least one field"):
            MedicalProfileCreateRequest()

    def test_height_bounds(self):
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(height_cm=0)
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(height_cm=301)

    def test_weight_bounds(self):
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(weight_kg=0)
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(weight_kg=501)

    def test_blood_type_max_length(self):
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(blood_type="A" * 11)

    def test_notes_max_length(self):
        with pytest.raises(ValueError):
            MedicalProfileCreateRequest(notes="x" * 10001)


class TestMedicalProfileUpdateRequest:
    def test_valid_with_one_field(self):
        req = MedicalProfileUpdateRequest(weight_kg=75.0)
        assert req.weight_kg == 75.0

    def test_empty_raises_validation_error(self):
        with pytest.raises(ValueError, match="At least one field"):
            MedicalProfileUpdateRequest()


# ── ORM → Dict Helper ──────────────────────────────────


class TestMedicalProfileToDict:
    def test_includes_computed_bmi(self):
        class FakeProfile:
            id = "test-id"
            patient_id = "patient-id"
            date_of_birth = date(1990, 1, 1)
            height_cm = 180.0
            weight_kg = 80.0
            blood_type = "A+"
            past_medical_history = ["Appendectomy"]
            family_medical_history = [{"relation": "mother", "condition": "Asthma"}]
            chronic_conditions = ["Hypertension"]
            current_medications = ["Lisinopril"]
            allergies = ["Penicillin"]
            notes = "Some notes"
            created_at = "2024-01-01T00:00:00"
            updated_at = "2024-01-01T00:00:00"

        result = medical_profile_to_dict(FakeProfile())
        assert result["bmi"] == 24.7
        assert result["height_cm"] == 180.0
        assert result["chronic_conditions"] == ["Hypertension"]

    def test_bmi_none_when_missing_vitals(self):
        class FakeProfileNoVitals:
            id = "test-id"
            patient_id = "patient-id"
            date_of_birth = None
            height_cm = None
            weight_kg = None
            blood_type = None
            past_medical_history = None
            family_medical_history = None
            chronic_conditions = None
            current_medications = None
            allergies = None
            notes = None
            created_at = "2024-01-01T00:00:00"
            updated_at = "2024-01-01T00:00:00"

        result = medical_profile_to_dict(FakeProfileNoVitals())
        assert result["bmi"] is None
