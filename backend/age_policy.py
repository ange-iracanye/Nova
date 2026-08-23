from __future__ import annotations

from datetime import date, datetime

MINIMUM_AGE = 16


def parse_date_of_birth(value: str) -> date:
    """Parse an ISO date without retaining it."""
    if not isinstance(value, str):
        raise ValueError("Date of birth is required.")
    try:
        born = date.fromisoformat(value.strip())
    except ValueError as exc:
        raise ValueError("Please provide a valid date of birth.") from exc
    if born > date.today():
        raise ValueError("Date of birth cannot be in the future.")
    return born


def age_on_today(born: date) -> int:
    today = date.today()
    return today.year - born.year - ((today.month, today.day) < (born.month, born.day))


def validate_minimum_age(value: str, minimum_age: int = MINIMUM_AGE) -> None:
    """Validate age at registration. The birth date is not stored by Nova."""
    born = parse_date_of_birth(value)
    if age_on_today(born) < minimum_age:
        raise ValueError(f"Nova V1 is available to users aged {minimum_age} or older.")
