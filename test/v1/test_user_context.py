from backend.user_context import (
    clear_active_user,
    get_active_user,
    normalize_user,
    set_active_user,
    user_context,
)


def test_normalize_user_handles_empty_and_mixed_case_values():
    assert normalize_user(None) is None
    assert normalize_user("  ") is None
    assert normalize_user("  Student@Example.COM ") == "student@example.com"


def test_user_context_restores_previous_user_after_scope():
    clear_active_user()
    set_active_user("first@example.com")

    with user_context("SECOND@example.com") as active:
        assert active == "second@example.com"
        assert get_active_user() == "second@example.com"

    assert get_active_user() == "first@example.com"
    clear_active_user()


def test_user_context_restores_context_after_exception():
    clear_active_user()
    try:
        with user_context("temporary@example.com"):
            assert get_active_user() == "temporary@example.com"
            raise RuntimeError("simulated failure")
    except RuntimeError:
        pass

    assert get_active_user() is None


def test_nested_user_context_restores_outer_scope():
    clear_active_user()
    with user_context("outer@example.com"):
        with user_context("inner@example.com"):
            assert get_active_user() == "inner@example.com"
        assert get_active_user() == "outer@example.com"
    assert get_active_user() is None
