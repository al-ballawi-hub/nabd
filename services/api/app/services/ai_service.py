"""DeepSeek-powered analysis of raw medical text.

Produces a structured record AND context-aware safety conflicts in a single
call. Safety reasoning (including medical negation such as "no history of
asthma") is delegated to the LLM with a strict structured prompt — there is no
naive substring/negation heuristic in the codebase.

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
    "You are a clinical documentation assistant with a strong focus on patient "
    "safety. Respond with a single JSON object and nothing else."
)

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


class AnalysisResult(BaseModel):
    """Strict schema for the DeepSeek JSON reply."""

    title: str = Field(default="Medical Note", max_length=200)
    record_type: str = "report"
    content: str = Field(default="", max_length=5000)
    conflicts: list[str] = Field(default_factory=list)

    @field_validator("record_type")
    @classmethod
    def _coerce_record_type(cls, value: str) -> str:
        return value if value in VALID_RECORD_TYPES else "report"


def _mock_analysis(text: str, allergies: list[str]) -> dict:
    """Deterministic offline fallback (no API key).

    This is intentionally minimal and is only used for local development and
    automated tests. It performs a plain allergy-name lookup — it does NOT
    attempt negation handling, which is the LLM's responsibility on the live
    path.
    """
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

    conflicts = [
        f"'{a}' may trigger the patient's {a} allergy."
        for a in allergies
        if a.lower() in t
    ]

    return {
        "title": "Medical Note Summary (Mock)",
        "record_type": record_type,
        "content": text.strip()[:5000],
        "conflicts": conflicts,
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


def analyze_medical_text(
    text: str,
    allergies: list[str] | None = None,
    conditions: list[str] | None = None,
) -> dict:
    """Return ``{title, record_type, content, conflicts}`` for the text.

    The LLM is given the patient's allergies and chronic conditions and asked
    to flag safety conflicts while respecting medical negation. Falls back to a
    deterministic mock when no API key is configured.
    """
    allergies = allergies or []
    conditions = conditions or []

    if not settings.deepseek_api_key:
        return _mock_analysis(text, allergies)

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    user_prompt = (
        "Analyze the medical text and produce a structured result.\n\n"
        "PATIENT CONTEXT:\n"
        f"- Allergies: {', '.join(allergies) or 'none reported'}\n"
        f"- Chronic conditions: {', '.join(conditions) or 'none reported'}\n\n"
        "Return JSON only with these keys:\n"
        '- "title": a short English title\n'
        '- "record_type": exactly one of: lab, prescription, report, scan\n'
        '- "content": a concise English medical summary\n'
        '- "conflicts": an array of strings describing any safety conflicts '
        "between the text and the patient's allergies or conditions. Empty "
        "array if none.\n\n"
        "CRITICAL negation rule: respect medical negation. Phrases such as "
        '"no history of asthma", "denies penicillin allergy", "not allergic to '
        'X", or "no known drug allergies" mean there is NO conflict.\n\n'
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
