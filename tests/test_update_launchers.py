import importlib.util
from pathlib import Path

import pytest


def linux_launcher():
    source = Path(__file__).resolve().parents[1] / "desktop/linux/launcher.py"
    spec = importlib.util.spec_from_file_location("jzs_linux_launcher", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_linux_original_shortcut_selects_a_complete_newer_package(tmp_path):
    launcher = linux_launcher()
    base, user = tmp_path / "解压目录", tmp_path / "游戏档案"
    base.mkdir()
    (base / "VERSION").write_text("4.9.1\n")
    updates = user / "updates"
    stage = updates / "versions/4.10.0/linux-x86_64/局中事"
    stage.mkdir(parents=True)
    pointer = updates / "linux-x86_64.active"
    pointer.write_text("4.10.0\n")
    (stage / "VERSION").write_text("4.10.0\n")
    assert launcher.active_executable(user, base) is None
    for path in ("局中事", "runtime/bin/python3.12", "launcher.py", "app/main.py", "app/frontend/dist/index.html"):
        item = stage / path
        item.parent.mkdir(parents=True, exist_ok=True)
        item.write_bytes(b"fixture")
    python = stage / "runtime/bin/python3.12"
    python.chmod(0o755)
    (stage / "runtime/bin/python3").symlink_to(python.name)
    (stage / "局中事").chmod(0o755)
    assert launcher.active_executable(user, base) == stage / "局中事"
    assert launcher.active_executable(user, stage) is None
    python.chmod(0o644)
    assert launcher.active_executable(user, base) is None
    python.chmod(0o755)
    index = stage / "app/frontend/dist/index.html"
    index.write_bytes(b"")
    assert launcher.active_executable(user, base) is None
    index.write_bytes(b"fixture")
    (stage / "VERSION").write_text("4.10.1\n")
    assert launcher.active_executable(user, base) is None
    for bad in ("4.9.1", "4.2.0", "04.10.0", "../4.10.0", "4.10.0.5"):
        pointer.write_text(bad)
        assert launcher.active_executable(user, base) is None


@pytest.mark.parametrize("bad", ["4.2", "4.0.０", "4.2.0-beta", "4.2.0/../../run", "4.1000000.0"])
def test_version_files_cannot_supply_paths_or_noncanonical_numbers(tmp_path, bad):
    path = tmp_path / "VERSION"
    path.write_text(bad)
    assert linux_launcher().read_version(path) is None
