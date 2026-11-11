"""Settings shared by all tests."""
import pytest

from systems import save


@pytest.fixture(autouse=True)
def save_in_a_temporary_folder(tmp_path, monkeypatch):
    """Every test saves into its own empty folder, never into the real saves/ folder."""
    monkeypatch.setattr(save, "SAVE_PATH", tmp_path / "save.json")
