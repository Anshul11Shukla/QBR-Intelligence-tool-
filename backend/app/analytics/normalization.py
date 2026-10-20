
import math
import re


UNIT_ALIASES = {
    "%": "%",
    "percent": "%",
    "percentage": "%",
    "hours": "hours",
    "hour": "hours",
    "hrs": "hours",
    "hr": "hours",
    "count": "count",
    "number": "count",
    "inr": "INR",
    "rs": "INR",
    "₹": "INR",
    "score": "score",
}


def normalize_metric(value: object) -> str:
    name = re.sub(r"\s+", " ", str(value or "").strip())
    if not name:
        raise ValueError("Metric name cannot be empty")
    return name


def metric_key(value: str) -> str:
    return normalize_metric(value).casefold()


def normalize_unit(value: object) -> str:
    raw = str(value or "").strip().lower()
    if not raw:
        raise ValueError("Unit is required")
    return UNIT_ALIASES.get(raw, raw)


def normalize_direction(value: object) -> str:
    raw = str(value or "").strip().lower()
    aliases = {
        "higher": "higher",
        "higher is better": "higher",
        "lower": "lower",
        "lower is better": "lower",
    }
    if raw not in aliases:
        raise ValueError(
            "Direction must be 'higher' or 'lower'"
        )
    return aliases[raw]


def parse_number(value: object) -> float | None:
    if value is None or str(value).strip() == "":
        return None

    if isinstance(value, bool):
        raise ValueError("Boolean is not a numeric KPI value")

    if isinstance(value, str):
        cleaned = value.strip().replace(",", "")
        cleaned = cleaned.replace("₹", "")
        if cleaned.endswith("%"):
            cleaned = cleaned[:-1]
        value = cleaned

    try:
        result = float(value)
    except (ValueError, TypeError) as exc:
        raise ValueError(
            f"Invalid numeric value: {value}"
        ) from exc

    if not math.isfinite(result):
        raise ValueError("Numeric value must be finite")

    return result
