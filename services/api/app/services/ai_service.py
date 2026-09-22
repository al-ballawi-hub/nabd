"""DeepSeek-powered analysis of raw medical text.

Turns free-text medical notes into a structured record with a title, a
record type (lab | prescription | report | scan) and a concise summary.
"""

import json
import re

from openai import OpenAI

from app.core.config import settings

VALID_RECORD_TYPES = {"lab", "prescription", "report", "scan"}

_SYSTEM_PROMPT = (
    "You are a clinical documentation assistant. Analyze the medical text and "
    "respond with a single JSON object and nothing else."
)


def _mock_analysis(text: str) -> dict:
    """Deterministic fallback used when no DeepSeek API key is configured."""
    t = text.strip()
    if any(k in t for k in ("تحليل", "مختبر", "سكر", "دم", "hba1c", "كرياتينين")):
        record_type = "lab"
    elif any(k in t for k in ("وصفة", "دواء", "علاج", "جرعة", "قرص")):
        record_type = "prescription"
    elif any(k in t for k in ("أشعة", "تصوير", "scan", "x-ray", "ct", "mri")):
        record_type = "scan"
    else:
        record_type = "report"

    return {
        "title": "ملخص نص طبي (محاكاة)",
        "record_type": record_type,
        "content": t[:300],
    }


def _extract_json(raw: str) -> dict:
    """Parse the model's reply, tolerating markdown code fences."""
    cleaned = re.sub(r"^```(?:json)?\s*", "", raw.strip())
    cleaned = re.sub(r"\s*```$", "", cleaned)
    return json.loads(cleaned)


def analyze_medical_text(text: str) -> dict:
    """Return ``{title, record_type, content}`` for the given medical text.

    Falls back to a deterministic mock when no API key is configured, so the
    UI can be exercised without external credentials.
    """
    if not settings.deepseek_api_key:
        return _mock_analysis(text)

    client = OpenAI(
        api_key=settings.deepseek_api_key,
        base_url=settings.deepseek_base_url,
    )

    user_prompt = (
        "حلّل النص الطبي التالي وأعد النتيجة بصيغة JSON فقط (بدون أي نص إضافي) "
        "بالمفاتيح التالية:\n"
        '- "title": عنوان مختصر بالعربية\n'
        '- "record_type": قيمة واحدة فقط من: lab, prescription, report, scan\n'
        '- "content": ملخص طبي موجز بالعربية\n\n'
        f"النص الطبي:\n{text}"
    )

    resp = client.chat.completions.create(
        model=settings.deepseek_model,
        messages=[
            {"role": "system", "content": _SYSTEM_PROMPT},
            {"role": "user", "content": user_prompt},
        ],
        temperature=0.2,
        response_format={"type": "json_object"},
    )

    data = _extract_json(resp.choices[0].message.content or "{}")

    record_type = data.get("record_type", "report")
    if record_type not in VALID_RECORD_TYPES:
        record_type = "report"

    return {
        "title": data.get("title") or "ملخص طبي",
        "record_type": record_type,
        "content": data.get("content") or "",
    }
