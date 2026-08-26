from pathlib import Path

from backend.settings import SettingsManager


def test_settings_manager_reload_picks_up_external_save(tmp_path: Path):
    path = tmp_path / "settings.json"
    first = SettingsManager(path)
    second = SettingsManager(path)

    first.update(name="Nova Student", language="Spanish")

    assert second.get()["name"] == "Nova Student"
    assert second.get()["language"] == "Spanish"
