from __future__ import annotations

from datetime import date, datetime
import unicodedata


KNOWN_DATE_FORMATS = ("%Y-%m-%d", "%d/%m/%Y")


def brl(value: float) -> str:
    return f"R$ {value:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")


def to_float(raw_value) -> float:
    if raw_value is None:
        return 0.0

    as_text = str(raw_value).strip()
    if not as_text:
        return 0.0

    if "," in as_text:
        as_text = as_text.replace(".", "").replace(",", ".")

    try:
        return float(as_text)
    except Exception:
        return 0.0


def safe_int(raw_value) -> int:
    try:
        return int(str(raw_value).strip())
    except Exception:
        return 0


def parse_date_any(raw_value) -> date | None:
    if raw_value is None:
        return None

    as_text = str(raw_value).strip()
    if not as_text:
        return None

    for date_format in KNOWN_DATE_FORMATS:
        try:
            return datetime.strptime(as_text, date_format).date()
        except ValueError:
            continue

    return None


def normalize_token(raw_value) -> str:
    as_text = str(raw_value or "").strip().lower()
    normalized = unicodedata.normalize("NFKD", as_text)
    return "".join(char for char in normalized if not unicodedata.combining(char))
