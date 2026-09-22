"""DeepSeek-powered analysis of raw medical text.

Turns free-text medical notes into a structured record with a title, a
record type (lab | prescription | report | scan) and a concise summary.

The AI reply is parsed defensively (markdown fences tolerated, malformed JSON
never crashes) and validated against a Pydantic schema. External API calls are
retried with exponential backoff for rate limits and transient failures.
"""

import json
import re
from typing import Any

from openai import (
    APIConnectionError,
    APITimeoutError,
    InternalServerError,
    OpenAI,
    RateLimitError,
)
from pydantic import BaseModel, Field, field_validator
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings

VALID_RECORD_TYPES = {"lab", "prescription", "report", "scan"}

_SYSTEM_PROMPT = (
    "You are a clinical documentation assistant. Analyze the medical text and "
    "respond with a single JSON object and nothing else."
)

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


class AnalysisResult(BaseModel):
    """Strict schema for the DeepSeek JSON reply."""

    title: str = Field(default="Medical Note", max_length=200)
    record_type: str = "report"
    content: str = Field(default="", max_length=5000)

    @field_validator("record_type")
    @classmethod
    def _coerce_record_type(cls, value: str) -> str:
        return value if value in VALID_RECORD_TYPES else "report"


def _mock_analysis(text: str) -> dict:
    """Deterministic fallback used when no DeepSeek API key is configured."""
    t = text.lower()
    if any(k in t for k in ("lab", "blood", "glucose", "hba1c", "creatinine", "cbc", "hemoglobin")):
        record_type = "lab"
    elif any(
        k in t
        for k in ("prescrib", "dose", " mg", "tablet", "medication", "drug", "inhaler")
    ):
        record_type = "prescription"
    elif any(k in t for k in ("scan", "x-ray", " ct", "mri", "imaging", "radiology", "ultrasound")):
        record_type = "scan"
    else:
        record_type = "report"

    return {
        "title": "Medical Note Summary (Mock)",
        "record_type": record_type,
        "content": text.strip()[:5000],
    }


def _extract_json(raw: str) -> dict:
    """Parse the model's reply, tolerating markdown code fences."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


@retry(
    retry=retry_if_exception_type(_RETRYABLE),
    wait=wait_exponential(multiplier=1, min=1, max=20),
    stop=stop_after_attempt(3),
    reraise=True,
)
def _call_deepseek(client: OpenAI, model: str, messages: list[dict]) -> Any:
    return client.chat.completions.create(
        model=model,
        messages=messages,
        temperature=0.2,
        response_format={"type": "json_object"},
    )


def analyze_medical_text(text: str) -> dict:
    """Return ``{title, record_type, content}`` for the given medical text.

    Falls back to a deterministic mock when no API key is configured.
    """
    if not settings.deepseek_api_key:
        return _mock_analysis(text)

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    user_prompt = (
        "Analyze the following medical text and respond with JSON only "
        "(no extra text) using these keys:\n"
        '- "title": a short title in English\n'
        '- "record_type": exactly one of: lab, prescription, report, scan\n'
        '- "content": a concise medical summary in English\n\n'
        f"Medical text:\n{text}"
    )

    resp = _call_deepseek(
        client,
        settings.deepseek_model,
        [
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
    )

    raw = resp.choices[0].message.content or "{}"
    try:
        data = _extract_json(raw)
    except (json.JSONDecodeError, ValueError):
        data = {"content": text.strip()[:5000]}

    result = AnalysisResult.model_validate(data)
    return result.model_dump()
