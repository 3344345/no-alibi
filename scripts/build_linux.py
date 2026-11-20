"""Build the x86-64 glibc Linux desktop package using Python 3.12+ and pip.

Build the UI with pnpm install --frozen-lockfile and pnpm build in frontend
first. Linux amd64 uses cc. Other Unix hosts need clang and ld.lld (or set
LINUX_LD to rust-lld). Artifacts and downloaded wheels are cached locally.
"""

from __future__ import annotations

import hashlib
import os
import platform
import shutil
import subprocess
import sys
import tarfile
import tempfile
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
CACHE = ROOT / ".artifacts/linux"
RUNTIME = (
    "https://github.com/astral-sh/python-build-standalone/releases/download/"
    "20261110/cpython-3.12.16%2B20261110-x86_64-unknown-linux-gnu-install_only_stripped.tar.gz",
    "6a9e62dad033790aef722dbd370e0ce76ce17b73627ba3ae679f537049350b39",
)
NOTICES = (
    "https://codeload.github.com/astral-sh/python-build-standalone/tar.gz/refs/tags/20261110",
    "63b8166347616283ee6d3ed449e957bc71b65368bc60945d21ab957e6fcaee49",
)


def download(name, url, digest):
    target = CACHE / name

    def valid(path):
        with path.open("rb") as f:
            return hashlib.file_digest(f, "sha256").hexdigest() == digest

    if target.is_file() and valid(target):
        return target
    with tempfile.NamedTemporaryFile(dir=CACHE, delete=False) as f:
        pending = Path(f.name)
    try:
        with urllib.request.urlopen(url, timeout=120) as response, pending.open("wb") as f:
            shutil.copyfileobj(response, f)
        if not valid(pending):
            raise ValueError(f"SHA-256 mismatch for {name}")
        pending.replace(target)
    finally:
        pending.unlink(missing_ok=True)
    return target


def native_entry(folder):
    source = ROOT / "desktop/linux/entry.S"
    target = folder / "局中事"
    if sys.platform == "linux" and platform.machine() == "x86_64":
        subprocess.run(["cc", "-nostdlib", "-static", "-Wl,-z,noexecstack", source, "-o", target], check=True)
        return
    linker = os.environ.get("LINUX_LD", "ld.lld")
    obj = folder.parent / "entry.o"
    subprocess.run(["clang", "--target=x86_64-linux-gnu", "-c", source, "-o", obj], check=True)
    flavor = ["-flavor", "gnu"] if Path(linker).name == "rust-lld" else []
    subprocess.run([linker, *flavor, "-m", "elf_x86_64", "-z", "noexecstack", "-o", target, obj], check=True)


def add_runtime(folder):
    with tarfile.open(download("cpython.tar.gz", *RUNTIME)) as archive:
        # terminfo contains pairs of names differing only in case. It is
        # unused by the GUI and cannot be staged on the default macOS volume.
        members = (item for item in archive if not item.name.startswith("python/share/terminfo/"))
        archive.extractall(folder, members=members, filter="data")
    runtime = folder / "runtime"
    (folder / "python").rename(runtime)
    # pip runs only on the build machine. All installed Python packages, source
    # and individual wheel license notices remain within the portable runtime.
    wheels = CACHE / "wheels"
    wheels.mkdir(exist_ok=True)
    pip = [sys.executable, "-m", "pip", "--disable-pip-version-check", "--isolated"]
    target = [
        "--only-binary=:all:", "--platform", "manylinux_2_28_x86_64",
        "--platform", "manylinux_2_17_x86_64", "--platform", "manylinux2014_x86_64",
        "--python-version", "3.12", "--implementation", "cp", "--abi", "cp312",
        "-r", str(ROOT / "requirements.txt"), "-c", str(ROOT / "requirements-dev.lock"),
    ]
    subprocess.run([*pip, "download", "--index-url", "https://pypi.org/simple", "-d", wheels, *target], check=True)
    site = runtime / "lib/python3.12/site-packages"
    subprocess.run([*pip, "install", "--no-index", "--find-links", wheels, "--no-compile", "--target", site, *target], check=True)


def add_notices(folder):
    notices = folder / "licenses"
    notices.mkdir()
    with tarfile.open(download("pbs-notices.tar.gz", *NOTICES)) as archive:
        for entry in archive:
            name = Path(entry.name)
            if len(name.parts) == 2 and entry.isfile() and (
                name.name.startswith("LICENSE") or name.name == "python-licenses.rst"
            ):
                (notices / name.name).write_bytes(archive.extractfile(entry).read())
    for package in ("svelte", "esm-env", "clsx"):
        folder = ROOT / "frontend/node_modules/.pnpm"
        pkg, = folder.glob(f"{package}@[0-9]*/node_modules/{package}")
        for path in (*pkg.glob("LICENSE*"), *pkg.glob("license*")):
            shutil.copyfile(path, notices / f"{package}-{path.name}")


def build(folder):
    folder.mkdir()
    shutil.copyfile(ROOT / "VERSION", folder / "VERSION")
    native_entry(folder)
    add_runtime(folder)
    add_notices(folder)
    app = folder / "app"
    app.mkdir()
    for name in ("main.py", "config.py", "PARAMETER_REGISTRY.json"):
        shutil.copyfile(ROOT / name, app / name)
    for name in ("game", "api", "ai", "domain", "contracts", "content", "events", "judgment", "storage"):
        shutil.copytree(ROOT / name, app / name, ignore=shutil.ignore_patterns("__pycache__", "*.pyc", ".DS_Store"))
    shutil.copytree(ROOT / "frontend/dist", app / "frontend/dist", ignore=shutil.ignore_patterns(".DS_Store"))
    shutil.copyfile(ROOT / "desktop/linux/launcher.py", folder / "launcher.py")
    shutil.copyfile(ROOT / "desktop/linux/游玩说明.txt", folder / "游玩说明.txt")


if __name__ == "__main__":
    if sys.version_info < (3, 12):
        sys.exit("Python 3.12+ is required for this build.")
    if not (ROOT / "frontend/dist/game-icon.png").is_file():
        sys.exit("Build the frontend before packaging.")
    CACHE.mkdir(parents=True, exist_ok=True)
    release = ROOT / "release"
    release.mkdir(exist_ok=True)
    with tempfile.TemporaryDirectory(dir=CACHE) as temp:
        stage = Path(temp) / "局中事"
        build(stage)
        packed = Path(temp) / "局中事-Linux-x86_64.tar.gz"
        with tarfile.open(packed, "w:gz", compresslevel=6) as archive:
            archive.add(stage, arcname=stage.name)
        packed.replace(release / packed.name)
        print(release / packed.name)
