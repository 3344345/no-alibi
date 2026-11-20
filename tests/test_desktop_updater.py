import base64
from contextlib import contextmanager
from hashlib import sha256
from io import BytesIO
import json
from zipfile import ZipFile

import pytest
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PrivateKey

from game import updater


PLATFORM = "windows-x64"
ASSET = updater.PACKAGES[PLATFORM][0]


def application(version):
    packed = BytesIO()
    with ZipFile(packed, "w") as archive:
        archive.writestr("VERSION", version + "\n")
        for name in updater.PACKAGES[PLATFORM][2:]:
            archive.writestr(name, version)
    return packed.getvalue()


@pytest.fixture
def publisher(monkeypatch):
    key = Ed25519PrivateKey.generate()
    monkeypatch.setattr(updater, "PUBLIC_KEY_B64", base64.b64encode(key.public_key().public_bytes_raw()).decode())
    urls = {}

    @contextmanager
    def get(url):
        with BytesIO(urls[url]) as response:
            yield response

    monkeypatch.setattr(updater, "_fetch", get)

    def publish(version, *, package_version=None):
        data = application(package_version or version)
        tag = "v" + version
        assets = {PLATFORM: {"name": ASSET, "size": len(data), "sha256": sha256(data).hexdigest()}}
        manifest = {"schema": 1, "version": version, "tag": tag, "assets": assets}
        canonical = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        urls[updater.FEED] = json.dumps({"manifest": manifest, "signature": base64.b64encode(key.sign(canonical)).decode()}).encode()
        url = f"{updater.RELEASES}/download/{tag}/{ASSET}"
        urls[url] = data
        return url

    return publish, urls


def test_signed_update_keeps_save_and_stages_until_next_launch(publisher, tmp_path):
    publish, _ = publisher
    database = tmp_path / "生涯.sqlite"
    database.write_bytes(b"save slot 1")
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.2.1")
    release = engine.check()
    assert not engine.ready_version()
    installed = engine.install(release)
    assert installed == tmp_path / "updates/versions/4.2.1" / PLATFORM
    assert (installed / "局中事.exe").read_text() == "4.2.1"
    assert engine.ready_version() == "4.2.1"
    assert engine.install(release) == installed
    assert engine.check() is None

    running_new = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.1")
    assert running_new.ready_version() is None
    assert running_new.check() is None
    publish("4.1.9")
    assert engine.check() is None
    assert database.read_bytes() == b"save slot 1"


def test_retry_after_corrupt_download_or_wrong_package_version(publisher, tmp_path):
    publish, urls = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.2.1")
    engine.install(engine.check())
    first_pointer = engine.pointer.read_bytes()
    url = publish("4.3.0")
    signed = engine.check()
    good_package = urls[url]
    urls[url] = b"broken transfer"
    with pytest.raises(updater.UpdateError):
        engine.install(signed)
    assert engine.pointer.read_bytes() == first_pointer
    assert not engine._destination("4.3.0").exists()
    publish("4.3.0", package_version="4.2.1")
    with pytest.raises(updater.UpdateError):
        engine.install(engine.check())
    assert engine.ready_version() == "4.2.1"
    urls[url] = good_package
    engine.install(signed)
    assert engine.ready_version() == "4.3.0"


def test_future_update_releases_space_and_never_rolls_back(publisher, tmp_path):
    publish, _ = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.3.0")
    old = engine.check()
    a = engine.install(old)
    publish("4.4.0")
    b = engine.install(engine.check())
    assert a.is_dir() and b.is_dir()
    assert engine.install(old) == b
    new_engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.4.0")
    publish("4.5.0")
    c = new_engine.install(new_engine.check())
    assert not a.exists() and b.is_dir() and c.is_dir()


def test_unsigned_changes_cannot_change_download_or_version(publisher, tmp_path):
    publish, urls = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM)
    publish("5.0.0")
    tampered = json.loads(urls[updater.FEED])
    tampered["manifest"]["version"] = "6.0.0"
    urls[updater.FEED] = json.dumps(tampered).encode()
    with pytest.raises(updater.UpdateError, match="签名"):
        engine.check()
    assert not engine.root.exists()


def test_busy_installer_releases_lock_and_allows_retry(publisher, tmp_path):
    publish, _ = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.2.1")
    release = engine.check()
    engine.root.mkdir()
    with updater._install_lock(engine.root, PLATFORM):
        with pytest.raises(updater.UpdateError, match="另一个"):
            engine.install(release)
        assert engine.ready_version() is None
    assert engine.install(release).is_dir()


def test_incomplete_side_installation_is_not_reported_as_ready(publisher, tmp_path):
    publish, _ = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.2.1")
    release = engine.check()
    dest = engine.install(release)
    (dest / "局中事.exe").unlink()
    assert engine.ready_version() is None
    assert engine.install(engine.check()) == dest
    assert engine.ready_version() == "4.2.1"


def test_preserves_unrelated_folder_with_same_name(publisher, tmp_path):
    publish, _ = publisher
    engine = updater.DesktopUpdater(tmp_path, PLATFORM, "4.2.0")
    publish("4.2.1")
    existing = engine._destination("4.2.1")
    existing.mkdir(parents=True)
    personal_file = existing / "玩家笔记"
    personal_file.write_text("第一章")
    with pytest.raises(updater.UpdateError, match="已保留"):
        engine.install(engine.check())
    assert personal_file.read_text() == "第一章"
    assert engine.ready_version() is None
