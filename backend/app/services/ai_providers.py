"""Multi-provider AI text generation with automatic fallback.

Provider chain:
1. Local Ollama (try to auto-start if down)
2. Groq Cloud API (fast, OpenAI-compatible)
3. Google Gemini API

Each provider is tried in order until one succeeds.
"""

import logging

import httpx

from app.core.config import settings

logger = logging.getLogger(__name__)


async def _try_ollama(prompt: str, model: str | None = None) -> str | None:
    """Try local Ollama. Auto-starts if not running. Returns None on failure."""
    import asyncio
    import shutil
    import subprocess

    model = model or settings.DEFAULT_MODEL
    base_url = settings.OLLAMA_BASE_URL

    # Quick connectivity check — auto-start if needed
    try:
        async with httpx.AsyncClient(timeout=5.0) as client:
            resp = await client.get(f"{base_url}/api/tags")
            if resp.status_code != 200:
                return None
    except Exception:
        # Not running — try to start (dev only)
        if not settings.is_production and shutil.which("ollama"):
            logger.info("Ollama not reachable, attempting auto-start...")
            try:
                subprocess.Popen(
                    ["ollama", "serve"],
                    stdout=subprocess.DEVNULL,
                    stderr=subprocess.DEVNULL,
                    start_new_session=True,
                )
                # Wait up to 15s for startup
                for _ in range(15):
                    await asyncio.sleep(1)
                    try:
                        async with httpx.AsyncClient(timeout=2.0) as c:
                            if (await c.get(f"{base_url}/api/tags")).status_code == 200:
                                break
                    except Exception:
                        continue
            except Exception as exc:
                logger.warning("Ollama auto-start failed: %s", exc)
        else:
            return None

    # Generate
    try:
        async with httpx.AsyncClient(timeout=float(settings.OLLAMA_TIMEOUT)) as client:
            response = await client.post(
                f"{base_url}/api/generate",
                json={"model": model, "prompt": prompt, "stream": False},
            )
            if response.status_code == 200:
                return response.json().get("response", "").strip()
            logger.warning("Ollama returned %d", response.status_code)
    except Exception as exc:
        logger.warning("Ollama call failed: %s", exc)
    return None


async def _try_groq(prompt: str, model: str | None = None) -> str | None:
    """Try Groq Cloud API. Returns None on failure."""
    if not settings.GROQ_API_KEY:
        return None

    model = model or settings.GROQ_MODEL
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                "https://api.groq.com/openai/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model": model,
                    "messages": [
                        {"role": "system", "content": "You are a medical AI assistant."},
                        {"role": "user", "content": prompt},
                    ],
                    "max_tokens": 2048,
                    "temperature": 0.3,
                },
            )
            if response.status_code == 200:
                return (
                    response.json()
                    .get("choices", [{}])[0]
                    .get("message", {})
                    .get("content", "")
                    .strip()
                )
            logger.warning("Groq returned %d: %s", response.status_code, response.text[:200])
    except Exception as exc:
        logger.warning("Groq call failed: %s", exc)
    return None


async def _try_google(prompt: str, model: str | None = None) -> str | None:
    """Try Google Gemini API. Returns None on failure."""
    if not settings.GOOGLE_AI_API_KEY:
        return None

    model = model or settings.GOOGLE_AI_MODEL
    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(
                f"https://generativelanguage.googleapis.com/v1beta/models/{model}:generateContent",
                params={"key": settings.GOOGLE_AI_API_KEY},
                json={
                    "contents": [{"parts": [{"text": prompt}]}],
                    "generationConfig": {"temperature": 0.3, "maxOutputTokens": 2048},
                },
            )
            if response.status_code == 200:
                candidates = response.json().get("candidates", [])
                if candidates:
                    return (
                        candidates[0]
                        .get("content", {})
                        .get("parts", [{}])[0]
                        .get("text", "")
                        .strip()
                    )
            logger.warning("Google AI returned %d", response.status_code)
    except Exception as exc:
        logger.warning("Google AI call failed: %s", exc)
    return None


# Provider registry — keyed by name from AI_PROVIDER_ORDER
_PROVIDERS = {
    "ollama": _try_ollama,
    "groq": _try_groq,
    "google": _try_google,
}


async def generate_text(prompt: str, model: str | None = None) -> tuple[str, str]:
    """Generate text using the provider chain. Returns (content, provider_name).

    Tries providers in configured order until one succeeds.
    """
    provider_order = [p.strip() for p in settings.AI_PROVIDER_ORDER.split(",")]

    for provider_name in provider_order:
        provider_fn = _PROVIDERS.get(provider_name)
        if not provider_fn:
            logger.warning("AI provider '%s' not found in registry", provider_name)
            continue

        logger.info("Trying AI provider: %s", provider_name)
        try:
            result = await provider_fn(prompt, model)
        except Exception as exc:
            logger.error("AI provider '%s' raised exception: %s", provider_name, exc)
            result = None
        logger.info("AI provider '%s' result: %s", provider_name, repr(result)[:80] if result else "None")
        if result:
            return result, provider_name

    return (
        "[AI unavailable — all providers failed] "
        "Please check that Ollama is running or configure a cloud provider "
        "(Groq, Google AI) in Settings.",
        "none",
    )
