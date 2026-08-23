from pathlib import Path


def test_user_settings_are_isolated(tmp_path, monkeypatch):
    monkeypatch.setenv("NOVA_USER_SETTINGS_DIR", str(tmp_path / "settings"))
    import backend.user_settings as user_settings

    token_a = user_settings.set_current_user("a@example.com")
    try:
        user_settings.UserSettingsProxy().update(name="Alice")
    finally:
        user_settings.reset_current_user(token_a)

    token_b = user_settings.set_current_user("b@example.com")
    try:
        assert user_settings.UserSettingsProxy().get()["name"] == ""
        user_settings.UserSettingsProxy().update(name="Bob")
    finally:
        user_settings.reset_current_user(token_b)

    token_a = user_settings.set_current_user("a@example.com")
    try:
        assert user_settings.UserSettingsProxy().get()["name"] == "Alice"
    finally:
        user_settings.reset_current_user(token_a)

    files = list(Path(tmp_path / "settings").rglob("settings.json"))
    assert len(files) == 2
