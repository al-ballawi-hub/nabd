"""DeepSeek-powered analysis of raw medical text.

Produces a structured record, extracted medications, and context-aware safety
conflicts (drug-drug, drug-disease, allergy) in a single call. Safety reasoning
(including medical negation) is delegated to the LLM with a strict structured
prompt, and the JSON shape is enforced by Pydantic.

The AI reply is parsed defensively (markdown fences tolerated, malformed JSON
never crashes) and external API calls are retried with exponential backoff.
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
from app.schemas import ConflictItem

VALID_RECORD_TYPES = {"lab", "prescription", "report", "scan"}

_SYSTEM_PROMPT = (
    "You are a clinical documentation assistant with a strong focus on patient "
    "safety. Respond with a single JSON object and nothing else."
)

_RETRYABLE = (RateLimitError, APITimeoutError, APIConnectionError, InternalServerError)


class MedicationItem(BaseModel):
    name: str = Field(min_length=1, max_length=120)
    dosage: str | None = None


class AnalysisResult(BaseModel):
    """Strict schema for the DeepSeek JSON reply."""

    title: str = Field(default="Medical Note", max_length=200)
    record_type: str = "report"
    content: str = Field(default="", max_length=5000)
    medications: list[MedicationItem] = Field(default_factory=list)
    conflicts: list[ConflictItem] = Field(default_factory=list)

    @field_validator("record_type")
    @classmethod
    def _coerce_record_type(cls, value: str) -> str:
        return value if value in VALID_RECORD_TYPES else "report"


def _mock_analysis(
    text: str,
    allergies: list[str],
    conditions: list[str],
    active_medications: list[str],
) -> dict:
    """Deterministic offline fallback (no API key).

    Minimal by design — only for local development and automated tests. It does
    not attempt negation handling; that is the LLM's responsibility on the
    live path.
    """
    t = text.lower()
    if any(k in t for k in ("lab", "blood", "glucose", "hba1c", "creatinine", "cbc", "hemoglobin")):
        record_type = "lab"
    elif any(
        k in t
        for k in ("prescrib", "dose", " mg", "tablet", "medication", "drug", "inhaler", "warfarin")
    ):
        record_type = "prescription"
    elif any(k in t for k in ("scan", "x-ray", " ct", "mri", "imaging", "radiology", "ultrasound")):
        record_type = "scan"
    else:
        record_type = "report"

    conflicts: list[dict] = []

    for allergy in allergies:
        if allergy.lower() in t:
            conflicts.append(
                {
                    "severity": "high",
                    "type": "allergy",
                    "message": f"'{allergy}' may trigger the patient's {allergy} allergy.",
                }
            )

    if "warfarin" in t and any("aspirin" in m.lower() for m in active_medications):
        conflicts.append(
            {
                "severity": "high",
                "type": "drug-drug",
                "message": "Warfarin combined with Aspirin increases bleeding risk.",
            }
        )

    if "ibuprofen" in t and any("asthma" in c.lower() for c in conditions):
        conflicts.append(
            {
                "severity": "high",
                "type": "drug-disease",
                "message": "Ibuprofen may worsen the patient's asthma.",
            }
        )

    medications = (
        [{"name": "Sample Medication", "dosage": None}]
        if record_type == "prescription"
        else []
    )

    return {
        "title": "Medical Note Summary (Mock)",
        "record_type": record_type,
        "content": text.strip()[:5000],
        "medications": medications,
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
    active_medications: list[str] | None = None,
) -> dict:
    """Return ``{title, record_type, content, medications, conflicts}``.

    The LLM cross-references any new prescription against the patient's active
    medications (drug-drug), chronic conditions (drug-disease) and allergies
    (allergy), respecting medical negation.
    """
    allergies = allergies or []
    conditions = conditions or []
    active_medications = active_medications or []

    if not settings.deepseek_api_key:
        return _mock_analysis(text, allergies, conditions, active_medications)

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    user_prompt = (
        "Analyze the medical text and produce a structured result.\n\n"
        "PATIENT CONTEXT:\n"
        f"- Active medications: {', '.join(active_medications) or 'none reported'}\n"
        f"- Allergies: {', '.join(allergies) or 'none reported'}\n"
        f"- Chronic conditions: {', '.join(conditions) or 'none reported'}\n\n"
        "Return JSON only with these keys:\n"
        '- "title": a short English title\n'
        '- "record_type": exactly one of: lab, prescription, report, scan\n'
        '- "content": a concise English medical summary\n'
        '- "medications": an array of {name, dosage} for any medication '
        "prescribed in this text (empty array if none)\n"
        '- "conflicts": an array of {severity, type, message} objects where '
        "severity is high|moderate|low and type is drug-drug|drug-disease|"
        "allergy, describing safety conflicts between the new prescription and "
        "the patient's active medications (drug-drug), chronic conditions "
        "(drug-disease), or allergies (allergy). Empty array if none.\n\n"
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
