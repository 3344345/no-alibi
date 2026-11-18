"""Build the Windows x64 portable ZIP. From a source checkout with Python, pip and pnpm:
python scripts/build_windows.py
Cross-packaging is supported with --launcher pointing to the same Windows-compiled launcher.
"""

import argparse
from hashlib import sha256
import os
from pathlib import Path
import shutil
import subprocess
import sys
from tempfile import TemporaryDirectory
from urllib.request import urlopen
from zipfile import ZIP_DEFLATED, ZipFile

ROOT = Path(__file__).resolve().parents[1]
BUILD = ROOT / ".artifacts/windows"
SOURCE = ROOT / "desktop/windows"
VERSION = "3.13.17"
EMBED = f"python-{VERSION}-embed-amd64.zip"
DIGEST = "9e35319bffedab8b36ad44d8f377cb4f1733bcec257a0b6d04d94f01486ddb38"


def embedded_python():
    package = BUILD / EMBED
    if not package.exists() or sha256(package.read_bytes()).hexdigest() != DIGEST:
        temporary = package.with_suffix(".part")
        try:
            with urlopen(f"https://www.python.org/ftp/python/{VERSION}/{EMBED}", timeout=180) as response:
                with temporary.open("wb") as stream:
                    shutil.copyfileobj(response, stream)
            if sha256(temporary.read_bytes()).hexdigest() != DIGEST:
                raise RuntimeError("The Windows Python runtime checksum does not match python.org")
            temporary.replace(package)
        finally:
            temporary.unlink(missing_ok=True)
    return package


def build_runtime(stage):
    runtime = stage / "runtime"
    with ZipFile(embedded_python()) as archive:
        archive.extractall(runtime)
    # The embeddable distribution resolves these paths relative to its DLL and ignores user installs.
    (runtime / "python313._pth").write_text("python313.zip\n.\nsite-packages\n../game\n", encoding="ascii")
    wheels = BUILD / "wheels"
    wheels.mkdir(exist_ok=True)
    pip = [sys.executable, "-m", "pip", "--disable-pip-version-check"]
    target = ["--platform", "win_amd64", "--python-version", "3.13", "--implementation", "cp",
              "--only-binary=:all:", "-r", str(ROOT / "requirements.txt"), "-c", str(ROOT / "requirements-dev.lock")]
    # Explicit Windows dependency also makes the cross-build path independent of host platform markers.
    target.append("colorama==0.4.6")
    subprocess.run([*pip, "download", "--dest", str(wheels), *target], check=True)
    subprocess.run([*pip, "install", "--no-index", "--find-links", str(wheels), "--no-compile",
                    "--target", str(runtime / "site-packages"), *target], check=True)
    # Developer command-line entry points would refer to the packager's interpreter.
    for name in ("bin", "Scripts"):
        shutil.rmtree(runtime / "site-packages" / name, ignore_errors=True)


def build_launcher(destination, compiled):
    if compiled:
        shutil.copyfile(compiled, destination)
        return
    if os.name != "nt":
        raise RuntimeError("Compile desktop/windows/Launcher.cs on Windows or pass --launcher")
    csc = Path(os.environ["SystemRoot"]) / "Microsoft.NET/Framework64/v4.0.30319/csc.exe"
    subprocess.run([str(csc), "/nologo", "/target:winexe", "/platform:x64", "/optimize+",
                    "/codepage:65001", "/win32icon:game.ico", "/reference:System.Windows.Forms.dll",
                    "/reference:System.Drawing.dll", "/out:" + str(destination), "Launcher.cs"],
                   cwd=SOURCE, check=True)


def copy_game(stage):
    game = stage / "game"
    game.mkdir()
    for name in ("main.py", "config.py", "PARAMETER_REGISTRY.json"):
        shutil.copyfile(ROOT / name, game / name)
    for name in ("ai", "api", "content", "contracts", "domain", "events", "game", "judgment", "storage"):
        for source in (ROOT / name).rglob("*.py"):
            destination = game / source.relative_to(ROOT)
            destination.parent.mkdir(parents=True, exist_ok=True)
            shutil.copyfile(source, destination)
    frontend = ROOT / "frontend"
    if not (frontend / "dist/index.html").is_file():
        raise RuntimeError("The compiled frontend is missing")
    shutil.copytree(frontend / "dist", game / "frontend/dist", ignore=shutil.ignore_patterns(".DS_Store"))
    for name in ("svelte", "vite"):
        shutil.copyfile(frontend / "node_modules" / name / "LICENSE.md", game / "frontend" / f"LICENSE-{name}.md")
    svelte_modules = (frontend / "node_modules/svelte").resolve().parent
    for name, license_name in (("clsx", "license"), ("esm-env", "LICENSE")):
        shutil.copyfile(svelte_modules / name / license_name, game / "frontend" / f"LICENSE-{name}.txt")
    shutil.copyfile(SOURCE / "使用说明.txt", stage / "使用说明.txt")


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--launcher", type=Path, help="compiled x64 desktop/windows/Launcher.cs with game.ico")
    parser.add_argument("--frontend-ready", action="store_true", help="use the existing production frontend build")
    args = parser.parse_args()
    BUILD.mkdir(parents=True, exist_ok=True)
    if not args.frontend_ready:
        pnpm = shutil.which("pnpm")
        if not pnpm:
            raise RuntimeError("pnpm is required to build the frontend")
        for command in (["install", "--frozen-lockfile"], ["build"]):
            subprocess.run([pnpm, *command], check=True, cwd=ROOT / "frontend")
    target = ROOT / "release/局中事-Windows-x64.zip"
    target.parent.mkdir(exist_ok=True)
    with TemporaryDirectory(dir=BUILD) as tmp:
        stage = Path(tmp) / "package"
        stage.mkdir()
        build_launcher(stage / "局中事.exe", args.launcher)
        build_runtime(stage)
        copy_game(stage)
        archive = Path(tmp) / target.name
        with ZipFile(archive, "w", compression=ZIP_DEFLATED, compresslevel=7) as output:
            for path in sorted(stage.rglob("*")):
                if path.is_file():
                    output.write(path, path.relative_to(stage).as_posix())
        archive.replace(target)
    print(f"{target}\nSHA-256 {sha256(target.read_bytes()).hexdigest()}")


if __name__ == "__main__":
    main()
