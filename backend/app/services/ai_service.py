"""AI service — Ollama integration for medical text generation."""

import logging

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError
from app.models.case import Case
from app.models.document import Document

logger = logging.getLogger(__name__)

OLLAMA_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "medgemma:4b"

MEDICAL_DISCLAIMER = (
    "This AI-generated content is for informational purposes only. "
    "It must be reviewed and approved by a qualified clinician before "
    "being used for any medical decisions."
)


class AIService:
    """Handles AI text generation via Ollama."""

    def __init__(self, db: AsyncSession):
        self.db = db

    async def summarize_case(
        self, case_id, document_ids=None, model=None
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
        prompt = (
            "You are a medical assistant. Generate a concise clinical summary "
            "based on the following case information. Include key findings, "
            "treatment considerations, and recommended next steps.\n\n"
            f"{context}"
        )

        content = await _call_ollama(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or DEFAULT_MODEL,
        }

    async def explain_terms(self, text: str, model: str | None = None) -> dict:
        """Explain medical terms in plain language."""
        prompt = (
            "You are a medical educator. Explain the following medical text "
            "in simple, patient-friendly language:\n\n"
            f"{text}"
        )
        content = await _call_ollama(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or DEFAULT_MODEL,
        }

    async def suggest_specialist(
        self, case_id, diagnosis=None, model=None
    ) -> dict:
        """Suggest a specialist type based on case info."""
        case = await self.db.get(Case, case_id)
        if not case:
            raise NotFoundError("Case not found")

        diag = diagnosis or case.diagnosis or "unknown condition"
        prompt = (
            "You are a medical referral assistant. Based on the following "
            "diagnosis, suggest the most appropriate specialist type and why:\n\n"
            f"Diagnosis: {diag}"
        )
        content = await _call_ollama(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or DEFAULT_MODEL,
        }

    async def generate_questions(
        self, case_id, context=None, model=None
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

        content = await _call_ollama(prompt, model)
        return {
            "content": content,
            "disclaimer": MEDICAL_DISCLAIMER,
            "model": model or DEFAULT_MODEL,
        }


async def _call_ollama(prompt: str, model: str | None = None) -> str:
    """Call the Ollama API to generate text.

    Falls back to a placeholder if Ollama is not available.
    """
    import httpx

    model = model or DEFAULT_MODEL
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"{OLLAMA_BASE_URL}/api/generate",
                json={
                    "model": model,
                    "prompt": prompt,
                    "stream": False,
                },
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            logger.warning(f"Ollama returned {response.status_code}")
    except httpx.ConnectError:
        logger.warning("Ollama not available — returning placeholder response")
    except Exception as e:
        logger.error(f"Ollama call failed: {e}")

    # Fallback: return a helpful placeholder
    return (
        "[AI summary placeholder — Ollama service not available] "
        "Please ensure Ollama is running locally with a supported model."
    )
