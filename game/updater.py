"""Verify and stage official desktop releases without modifying a running installation."""
from __future__ import annotations

import base64
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
from http.client import HTTPException
import json
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import shutil
import ssl
import stat
import subprocess
import sys
import tarfile
import tempfile
from zlib import error as CompressionError
from urllib.error import URLError
from urllib.parse import urlsplit
from urllib.request import build_opener, HTTPRedirectHandler, HTTPSHandler, Request
from zipfile import BadZipFile, ZipFile

import certifi
from cryptography.exceptions import InvalidSignature
from cryptography.hazmat.primitives.asymmetric.ed25519 import Ed25519PublicKey

from game.update_trust import PUBLIC_KEY_B64, VERSION


RELEASES = "https://github.com/TimTian1/no-alibi/releases"
FEED = RELEASES + "/latest/download/update.json"
PACKAGES = {
    "macos-arm64": ("no-alibi-macOS-arm64.zip", "局中事.app/Contents/Resources/VERSION",
                    "局中事.app/Contents/MacOS/juzhongshi", "局中事.app/Contents/MacOS/jzs-engine",
                    "局中事.app/Contents/Resources/web/index.html"),
    "windows-x64": ("no-alibi-Windows-x64.zip", "VERSION", "局中事.exe", "runtime/python.exe",
                    "game/main.py", "game/frontend/dist/index.html"),
    "linux-x86_64": ("no-alibi-Linux-x86_64.tar.gz", "局中事/VERSION", "局中事/局中事",
                     "局中事/runtime/bin/python3.12", "局中事/launcher.py", "局中事/app/frontend/dist/index.html"),
}
MAX_MANIFEST = 65536
MAX_DOWNLOAD = 4 * 1024**3
MAX_EXPANDED = 16 * 1024**3
MAX_ENTRIES = 100000
CHUNK = 1024 * 1024
VERSION_RE = re.compile(r"(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){2}")
RECEIPT = ".jzs-release.json"


class UpdateError(Exception):
    """A release could not be verified or safely installed."""


class OfflineError(UpdateError):
    """The official download service could not be reached."""


@dataclass(frozen=True)
class Asset:
    name: str
    size: int
    sha256: str


@dataclass(frozen=True)
class Release:
    version: str
    tag: str
    asset: Asset
    envelope: bytes = field(repr=False)


def _number(value):
    if not isinstance(value, str) or not VERSION_RE.fullmatch(value):
        raise ValueError("invalid version")
    return tuple(map(int, value.split(".")))


def _release(raw, platform):
    try:
        if len(raw) > MAX_MANIFEST:
            raise ValueError("oversized manifest")
        envelope = json.loads(raw.decode("utf-8"))
        manifest = envelope["manifest"]
        encoded = json.dumps(manifest, sort_keys=True, ensure_ascii=False, separators=(",", ":")).encode()
        key = Ed25519PublicKey.from_public_bytes(base64.b64decode(PUBLIC_KEY_B64, validate=True))
        key.verify(base64.b64decode(envelope["signature"], validate=True), encoded)
        if type(manifest["schema"]) is not int or manifest["schema"] != 1:
            raise ValueError("unknown schema")
        version, tag = manifest["version"], manifest["tag"]
        _number(version)
        if tag != "v" + version:
            raise ValueError("invalid tag")
        asset = Asset(**manifest["assets"][platform])
        if (asset.name != PACKAGES[platform][0] or type(asset.size) is not int
                or not 0 < asset.size <= MAX_DOWNLOAD or not re.fullmatch(r"[a-f0-9]{64}", asset.sha256)):
            raise ValueError("invalid asset")
        return Release(version, tag, asset, raw)
    except (InvalidSignature, KeyError, TypeError, ValueError, RecursionError) as exc:
        raise UpdateError("更新清单的发行签名或内容不正确。") from exc


class _ReleaseRedirects(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        parsed = urlsplit(newurl)
        github_release = parsed.hostname == "github.com" and parsed.path.startswith("/TimTian1/no-alibi/releases/")
        cdn = parsed.hostname in {"release-assets.githubusercontent.com", "objects.githubusercontent.com",
                                  "github-releases.githubusercontent.com"}
        if (parsed.scheme != "https" or parsed.netloc != parsed.hostname or not (github_release or cdn)):
            raise UpdateError("更新地址未指向游戏的官方发行服务。")
        return super().redirect_request(req, fp, code, msg, headers, newurl)


@contextmanager
def _fetch(url):
    context = ssl.create_default_context()
    context.load_verify_locations(cafile=certifi.where())
    opener = build_opener(_ReleaseRedirects(), HTTPSHandler(context=context))
    req = Request(url, headers={"User-Agent": "Juzhongshi-Desktop-Updater", "Accept-Encoding": "identity"})
    try:
        with opener.open(req, timeout=25) as response:
            yield response
    except (URLError, TimeoutError, ConnectionError, HTTPException, ssl.SSLError) as exc:
        raise OfflineError("暂时连不上游戏的更新服务。") from exc


def _download(release, target):
    url = RELEASES + "/download/" + release.tag + "/" + release.asset.name
    count = 0
    digest = hashlib.sha256()
    with _fetch(url) as src, target.open("xb") as dst:
        while chunk := src.read(CHUNK):
            count += len(chunk)
            if count > release.asset.size:
                raise UpdateError("下载包大小与签名清单不符。")
            digest.update(chunk)
            dst.write(chunk)
    if count != release.asset.size or digest.hexdigest() != release.asset.sha256:
        raise UpdateError("下载包不完整或校验值不符。")


def _relative(name, platform):
    parts = name.removesuffix("/").split("/")
    if (not name or len(name) > 2048 or "\\" in name or ":" in name
            or any(p in {"", ".", ".."} or "\x00" in p for p in parts)):
        raise UpdateError("安装包里有不安全的文件路径。")
    if platform == "windows-x64" and any(
        p.endswith((" ", ".")) or PureWindowsPath(p).is_reserved() or any(
            c in '<>"|?*' or ord(c) < 32 for c in p) for p in parts
    ):
        raise UpdateError("安装包里有 Windows 无法安全创建的文件。")
    root = {"macos-arm64": "局中事.app", "linux-x86_64": "局中事"}.get(platform)
    if (root and parts[0] != root) or parts[0].casefold() == RECEIPT:
        raise UpdateError("安装包的顶层目录不符合发行格式。")
    return PurePosixPath(*parts)


class _Unpack:
    def __init__(self, root, platform):
        self.root = root
        self.platform = platform
        self.total = 0
        self.seen = set()

    def entry(self, name, size):
        path = _relative(name, self.platform)
        key = path.as_posix()
        if self.platform != "linux-x86_64":
            key = key.casefold()
        self.total += size
        if key in self.seen or size < 0 or self.total > MAX_EXPANDED or len(self.seen) >= MAX_ENTRIES:
            raise UpdateError("安装包内的文件重复或超出大小限制。")
        self.seen.add(key)
        return self.root.joinpath(*path.parts)

    def file(self, path, data, mode):
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("xb") as f:
            shutil.copyfileobj(data, f, CHUNK)
        path.chmod(0o755 if mode & 0o111 else 0o644)


def _unzip(archive, root, platform):
    unpack = _Unpack(root, platform)
    # ditto stores UTF-8 names even without the ZIP language flag.
    with ZipFile(archive, metadata_encoding="utf-8") as z:
        if len(z.infolist()) > MAX_ENTRIES:
            raise UpdateError("安装包内的文件数超出限制。")
        for member in z.infolist():
            if platform == "macos-arm64" and member.filename.split("/", 1)[0] == "__MACOSX":
                continue
            p = unpack.entry(member.orig_filename, member.file_size)
            mode = member.external_attr >> 16
            if member.flag_bits & 1:
                raise UpdateError("更新安装包使用了无法读取的加密格式。")
            if member.is_dir():
                p.mkdir(parents=True, exist_ok=True)
            elif stat.S_IFMT(mode) in (0, stat.S_IFREG):
                with z.open(member) as f:
                    unpack.file(p, f, mode)
            else:
                raise UpdateError("安装包包含未知的 ZIP 文件类型。")


def _untar(archive, root):
    unpack = _Unpack(root, "linux-x86_64")
    links = []
    with tarfile.open(archive, "r|gz") as tar:
        for m in tar:
            p = unpack.entry(m.name, m.size)
            if m.isdir():
                p.mkdir(parents=True, exist_ok=True)
            elif m.isfile():
                with tar.extractfile(m) as f:
                    unpack.file(p, f, m.mode)
            elif m.issym() or m.islnk():
                links.append((p, m.linkname, m.issym()))
            else:
                raise UpdateError("Linux 安装包包含不支持的文件类型。")
    # The portable interpreter uses relative links. Create them last, only to
    # already extracted regular files inside the package, never through a link.
    for p, link, symbolic in links:
        if Path(link).is_absolute() or "\\" in link or ":" in link:
            raise UpdateError("Linux 安装包包含外部链接。")
        target = ((p.parent if symbolic else root) / link).resolve()
        if not target.is_relative_to((root / "局中事").resolve()) or not target.is_file():
            raise UpdateError("Linux 安装包的链接目标无效。")
        p.parent.mkdir(parents=True, exist_ok=True)
        if symbolic:
            p.symlink_to(link)
        else:
            os.link(target, p)


def _layout(root, platform, version):
    _, marker, *files = PACKAGES[platform]
    try:
        return ((root / marker).stat().st_size <= 32
                and (root / marker).read_text(encoding="ascii").rstrip("\n") == version
                and all((root / name).is_file() and (root / name).stat().st_size > 0 for name in files))
    except (OSError, UnicodeError):
        return False


@contextmanager
def _install_lock(root, platform):
    # OS locks are released if an installer exits unexpectedly.
    with (root / (platform + ".lock")).open("a+b") as lock:
        try:
            if os.name == "nt":
                import msvcrt
                if lock.tell() == 0:
                    lock.write(b"x")
                    lock.flush()
                lock.seek(0)
                msvcrt.locking(lock.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(lock.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise UpdateError("另一个游戏窗口正在安装更新。") from exc
        yield


class DesktopUpdater:
    def __init__(self, data_dir: Path, platform: str, current_version: str = VERSION):
        if platform not in PACKAGES:
            raise ValueError("unsupported desktop platform")
        _number(current_version)
        self.platform = platform
        self.current_version = current_version
        self.root = Path(data_dir) / "updates"
        self.pointer = self.root / (platform + ".active")

    def _destination(self, version):
        return self.root / "versions" / version / self.platform

    def _owned(self, dest, version):
        try:
            with (dest / RECEIPT).open("rb") as saved:
                release = _release(saved.read(MAX_MANIFEST + 1), self.platform)
            return release.version == version
        except (OSError, UpdateError):
            return False

    def _usable(self, dest, version):
        return self._owned(dest, version) and _layout(dest, self.platform, version)

    def _active(self):
        try:
            if self.pointer.stat().st_size > 32:
                return None
            version = self.pointer.read_text(encoding="ascii").removesuffix("\n")
            _number(version)
            if self._usable(self._destination(version), version):
                return version
        except (OSError, ValueError):
            pass
        return None

    def ready_version(self):
        version = self._active()
        return version if version and _number(version) > _number(self.current_version) else None

    def check(self):
        with _fetch(FEED) as src:
            release = _release(src.read(MAX_MANIFEST + 1), self.platform)
        current = self.ready_version() or self.current_version
        return release if _number(release.version) > _number(current) else None

    def _prune(self, keep):
        for folder in (self.root / "versions").iterdir():
            if (not folder.is_dir() or folder.is_symlink() or folder.is_junction()
                    or folder.name in keep or not VERSION_RE.fullmatch(folder.name)):
                continue
            platform_dir = folder / self.platform
            if not platform_dir.is_symlink() and not platform_dir.is_junction() and self._owned(platform_dir, folder.name):
                shutil.rmtree(platform_dir, ignore_errors=True)
                try:
                    folder.rmdir()
                except OSError:
                    pass  # Other platform installations may share this directory.

    def install(self, release: Release):
        # Do not trust a cached Release object's mutable origin. Revalidate its
        # signed envelope and compare the version again while holding the lock.
        release = _release(release.envelope, self.platform)
        try:
            dest = self._destination(release.version)
            paths = (self.root, self.root / "versions", dest.parent, dest, self.pointer, self.root / (self.platform + ".lock"))
            if any(p.is_symlink() or p.is_junction() for p in paths):
                raise UpdateError("更新目录已被重定向，无法安全安装。")
            self.root.mkdir(mode=0o700, parents=True, exist_ok=True)
            with _install_lock(self.root, self.platform):
                previous = self._active()
                if _number(release.version) <= _number(self.current_version):
                    raise UpdateError("当前版本已包含这次更新。")
                if previous and _number(previous) >= _number(release.version):
                    return self._destination(previous)
                prefix = ".stage-" + self.platform + "-"
                for stale in self.root.glob(prefix + "*"):
                    if stale.is_dir() and not stale.is_symlink():
                        shutil.rmtree(stale, ignore_errors=True)
                dest.parent.mkdir(parents=True, exist_ok=True)
                with tempfile.TemporaryDirectory(dir=self.root, prefix=prefix) as stage:
                    temp = Path(stage)
                    if not self._usable(dest, release.version):
                        archive, tree = temp / "archive", temp / "package"
                        tree.mkdir()
                        _download(release, archive)
                        if self.platform == "linux-x86_64":
                            _untar(archive, tree)
                        else:
                            _unzip(archive, tree, self.platform)
                        if not _layout(tree, self.platform, release.version):
                            raise UpdateError("安装包缺少启动程序或发行版本不匹配。")
                        if self.platform == "macos-arm64" and sys.platform == "darwin":
                            result = subprocess.run(
                                ["/usr/bin/codesign", "--verify", "--deep", "--strict", str(tree / "局中事.app")],
                                capture_output=True, timeout=60,
                            )
                            if result.returncode:
                                raise UpdateError("Mac 应用的代码签名校验失败。")
                        (tree / RECEIPT).write_bytes(release.envelope)
                        if dest.exists():
                            # Replace only an incomplete side installation, never
                            # the running program, and restore it if the rename fails.
                            if not self._owned(dest, release.version):
                                raise UpdateError("更新目录里有同名文件，已保留原内容。")
                            displaced = temp / "incomplete"
                            dest.replace(displaced)
                            try:
                                tree.replace(dest)
                            except OSError:
                                displaced.replace(dest)
                                raise
                        else:
                            tree.replace(dest)
                    pointer = temp / "active"
                    pointer.write_bytes((release.version + "\n").encode("ascii"))
                    pointer.replace(self.pointer)
                try:
                    self._prune({self.current_version, previous, release.version})
                except OSError:
                    pass  # Cleanup must not undo a successfully activated update.
                return dest
        except (OSError, EOFError, BadZipFile, tarfile.TarError, NotImplementedError,
                CompressionError, subprocess.TimeoutExpired, UnicodeError) as exc:
            raise UpdateError("更新未安装，请检查磁盘空间后重试。") from exc
