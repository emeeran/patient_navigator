"""AI service — multi-provider medical text generation."""

import logging
from datetime import date

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.exceptions import NotFoundError
from app.models.case import Case
from app.models.document import Document
from app.models.medical_profile import MedicalProfile
from app.services.ai_providers import generate_text

logger = logging.getLogger(__name__)

MEDICAL_DISCLAIMER = (
    "This AI-generated content is for informational purposes only. "
    "It must be reviewed and approved by a qualified clinician before "
    "being used for any medical decisions."
)

LANGUAGE_INSTRUCTIONS: dict[str, str] = {
    "tamil": (
        " You MUST write your entire response in Tamil (தமிழ்). "
        "Use clear, simple Tamil that a layperson can understand."
    ),
}


def _language_suffix(language: str | None) -> str:
    """Return a prompt suffix for the requested output language."""
    if not language:
        return ""
    return LANGUAGE_INSTRUCTIONS.get(language.lower(), "")


class AIService:
    """Handles AI text generation via Ollama."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def _get_patient_medical_context(self, case_id) -> str | None:
        """Build a medical context string from the patient's medical profile."""
        case = await self.db.get(Case, case_id)
        if not case:
            return None

        result = await self.db.execute(
            select(MedicalProfile).where(
                MedicalProfile.patient_id == case.patient_id
            )
        )
        profile = result.scalar_one_or_none()
        if not profile:
            return None

        parts = []
        if profile.date_of_birth:
            exact_age = (date.today() - profile.date_of_birth).days // 365
            parts.append(f"Patient exact age: {exact_age} (DOB: {profile.date_of_birth})")
        if profile.height_cm and profile.weight_kg:
            height_m = profile.height_cm / 100
            bmi = round(profile.weight_kg / (height_m**2), 1)
            parts.append(
                f"Height: {profile.height_cm}cm, Weight: {profile.weight_kg}kg, BMI: {bmi}"
            )
        if profile.blood_type:
            parts.append(f"Blood type: {profile.blood_type}")
        if profile.chronic_conditions:
            parts.append(f"Chronic conditions: {', '.join(profile.chronic_conditions)}")
        if profile.current_medications:
            parts.append(f"Current medications: {', '.join(profile.current_medications)}")
        if profile.allergies:
            parts.append(f"Allergies: {', '.join(profile.allergies)}")
        if profile.past_medical_history:
            parts.append(f"Past medical history: {', '.join(profile.past_medical_history)}")
        if profile.family_medical_history:
            family_items = [
                f"{f.get('relation', 'relative')}: {f.get('condition', 'unknown')}"
                for f in profile.family_medical_history
            ]
            parts.append(f"Family history: {'; '.join(family_items)}")

        return "\n".join(parts) if parts else None

    async def summarize_case(
        self, case_id, document_ids=None, model=None, language=None
    ) -> dict:
        """Generate a medical summary for a case."""
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        # Collect document OCR text
        context_parts = [f"Diagnosis: {case.diagnosis}"]
        if case.notes:
            context_parts.append(f"Notes: {case.notes}")

        if document_ids:
            query = select(Document).where(
                Document.id.in_(document_ids), Document.case_id == case_id
            )
        else:
            query = select(Document).where(
                Document.case_id == case_id, Document.deleted_at.is_(None)
            )

        result = await self.db.execute(query)
        docs = result.scalars().all()
        for doc in docs:
            if doc.ocr_text:
                context_parts.append(f"Document '{doc.original_filename}': {doc.ocr_text}")

        context = "\n".join(context_parts)

        # Enrich with patient medical profile
        medical_context = await self._get_patient_medical_context(case_id)
        if medical_context:
            context = f"Patient Medical Profile:\n{medical_context}\n\nCase Information:\n{context}"

        prompt = (
            "You are a medical assistant. Generate a concise clinical summary "
            "based on the following case information. Include key findings, "
            "treatment considerations, and recommended next steps.\n\n"
            f"{context}"
            f"{_language_suffix(language)}"
        )

        content, provider = await generate_text(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or settings.DEFAULT_MODEL,
            "provider": provider,
        }

    async def explain_terms(self, text: str, model: str | None = None, language: str | None = None) -> dict:
        """Explain medical terms in plain language."""
        prompt = (
            "You are a medical educator. Explain the following medical text "
            "in simple, patient-friendly language:\n\n"
            f"{text}"
            f"{_language_suffix(language)}"
        )
        content, provider = await generate_text(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or settings.DEFAULT_MODEL,
            "provider": provider,
        }

    async def suggest_specialist(
        self, case_id, diagnosis=None, model=None, language=None
    ) -> dict:
        """Suggest a specialist type based on case info."""
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        diag = diagnosis or case.diagnosis or "unknown condition"

        # Include comorbidities and medications for better referral
        medical_context = await self._get_patient_medical_context(case_id)
        context_block = f"Diagnosis: {diag}"
        if medical_context:
            context_block += f"\n\nPatient Medical Context:\n{medical_context}"

        prompt = (
            "You are a medical referral assistant. Based on the following "
            "diagnosis and patient context, suggest the most appropriate "
            "specialist type and why:\n\n"
            f"{context_block}"
            f"{_language_suffix(language)}"
        )
        content, provider = await generate_text(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or settings.DEFAULT_MODEL,
            "provider": provider,
        }

    async def generate_questions(
        self, case_id, context=None, model=None, language=None
    ) -> dict:
        """Generate questions the patient should ask their doctor."""
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        prompt = (
            "You are a patient advocate. Generate a list of important questions "
            "that a patient should ask their doctor based on the following case:\n\n"
            f"Diagnosis: {case.diagnosis}\n"
        )
        if context:
            prompt += f"Additional context: {context}\n"
        if case.notes:
            prompt += f"Notes: {case.notes}\n"

        # Include full medical profile for personalized questions
        medical_context = await self._get_patient_medical_context(case_id)
        if medical_context:
            prompt += f"\nPatient Medical Profile:\n{medical_context}\n"
        if case.notes:
            prompt += f"Notes: {case.notes}\n"

        prompt += _language_suffix(language)

        content, provider = await generate_text(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or settings.DEFAULT_MODEL,
            "provider": provider,
        }
