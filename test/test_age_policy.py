from datetime import date, timedelta

import pytest

from backend.age_policy import age_on_today, parse_date_of_birth, validate_minimum_age


def test_age_calculation():
    today = date.today()
    born = date(today.year - 16, today.month, today.day)
    assert age_on_today(born) == 16


def test_rejects_future_birth_date():
    future = (date.today() + timedelta(days=1)).isoformat()
    with pytest.raises(ValueError, match="future"):
        parse_date_of_birth(future)


def test_rejects_under_16():
    today = date.today()
    born = date(today.year - 15, today.month, today.day)
    with pytest.raises(ValueError, match="16 or older"):
        validate_minimum_age(born.isoformat())


def test_accepts_16():
    today = date.today()
    born = date(today.year - 16, today.month, today.day)
    validate_minimum_age(born.isoformat())
