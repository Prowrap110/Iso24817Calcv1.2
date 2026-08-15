DENT_WITH_CRACK = "Dent w/crack"
DENT_NO_CRACK = "Dent no-crack"

MECHANISM_CHOICES = (
    "Corrosion",
    DENT_WITH_CRACK,
    DENT_NO_CRACK,
    "Leak",
    "Crack",
)


def normalize_mechanism(value: object) -> str:
    text = "" if value is None else str(value).strip()
    if text not in MECHANISM_CHOICES:
        raise ValueError(f"Unsupported defect mechanism: {text or '(blank)'}")
    return text
