from pathlib import Path

import pytest

import main


@pytest.fixture
def user_home(tmp_path, monkeypatch):
    monkeypatch.setattr(Path, "home", classmethod(lambda cls: tmp_path))
    for key in ("JUZHONGSHI_DATA_DIR", "LOCALAPPDATA", "XDG_DATA_HOME"):
        monkeypatch.delenv(key, raising=False)
    return tmp_path


def test_windows_uses_local_appdata(user_home, monkeypatch):
    monkeypatch.setattr(main.sys, "platform", "win32")
    assert main.default_data_dir() == user_home / "AppData" / "Local" / "局中事"
    custom = user_home / "本机数据"
    monkeypatch.setenv("LOCALAPPDATA", str(custom))
    assert main.default_data_dir() == custom / "局中事"


def test_mac_keeps_original_location(user_home, monkeypatch):
    monkeypatch.setattr(main.sys, "platform", "darwin")
    assert main.default_data_dir() == user_home / "Library" / "Application Support" / "局中事"


def test_linux_resolves_xdg_and_preserves_existing_games(user_home, monkeypatch):
    monkeypatch.setattr(main.sys, "platform", "linux")
    monkeypatch.setenv("XDG_DATA_HOME", "relative")
    assert main.default_data_dir() == user_home / ".local" / "share" / "juzhongshi"
    data = user_home / "本机数据"
    monkeypatch.setenv("XDG_DATA_HOME", str(data))
    target = data / "juzhongshi"
    assert main.default_data_dir() == target
    legacy = user_home / "Library" / "Application Support" / "局中事"
    legacy.mkdir(parents=True)
    (legacy / "careers.sqlite3").touch()
    assert main.default_data_dir() == legacy
    target.mkdir(parents=True)
    (target / "careers.sqlite3").touch()
    assert main.default_data_dir() == target


def test_explicit_data_dir_has_priority(user_home, monkeypatch):
    custom = user_home / "单独存档"
    monkeypatch.setenv("JUZHONGSHI_DATA_DIR", str(custom))
    assert main.default_data_dir() == custom
