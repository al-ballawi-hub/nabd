"""Rule-based safety guardrails for record assignment.

Checks new medical content against a patient's allergies and chronic
conditions and returns a list of human-readable warnings. This is a
deterministic heuristic layer (a demo safety engine), not a substitute for
clinical judgment.
"""

ALLERGY_KEYWORDS: dict[str, list[str]] = {
    "penicillin": ["penicillin", "amoxicillin", "ampicillin"],
    "aspirin": ["aspirin"],
    "nsaid": ["ibuprofen", "naproxen", "diclofenac", "celecoxib", "ketorolac", "nsaid"],
    "sulfa": ["sulfa", "sulfamethoxazole", "bactrim", "sulfonamide"],
    "nuts": ["peanut", "nuts", "almond", "walnut", "cashew"],
}

CONDITION_CONFLICTS: dict[str, list[str]] = {
    "asthma": ["propranolol", "metoprolol", "atenolol", "nsaid", "aspirin", "ibuprofen", "naproxen"],
    "hypertension": ["pseudoephedrine", "phenylephrine"],
    "diabetes": ["prednisone", "prednisolone", "corticosteroid", "glucocorticoid"],
    "heart failure": ["nsaid", "ibuprofen", "naproxen", "pioglitazone", "verapamil"],
    "kidney": ["nsaid", "ibuprofen", "naproxen", "metformin"],
}

_EMPTY_VALUES = {"none", "n/a", "no known", "no known allergies"}


def _split_list(value: str | None) -> list[str]:
    return [
        item.strip()
        for item in (value or "").split(",")
        if item.strip() and item.strip().lower() not in _EMPTY_VALUES
    ]


def _keywords_for_allergy(allergy: str) -> list[str]:
    key = allergy.lower()
    for name, keywords in ALLERGY_KEYWORDS.items():
        if name in key:
            return keywords
    return [key]


def check_record_safety(patient, text: str, content: str) -> list[str]:
    """Return a list of safety warnings for the proposed record."""
    combined = f"{text} {content}".lower()

    allergies = _split_list(patient.allergies)
    conditions = _split_list(patient.chronic_conditions)

    warnings: list[str] = []

    for allergy in allergies:
        for keyword in _keywords_for_allergy(allergy):
            if keyword in combined:
                warnings.append(
                    f"'{keyword.title()}' may trigger the patient's {allergy} allergy."
                )
                break

    for condition in conditions:
        condition_key = next(
            (k for k in CONDITION_CONFLICTS if k in condition.lower()),
            None,
        )
        if not condition_key:
            continue
        for med in CONDITION_CONFLICTS[condition_key]:
            if med in combined:
                warnings.append(
                    f"'{med.title()}' is contraindicated for the patient's {condition}."
                )

    return list(dict.fromkeys(warnings))
