"""Bundle the build's dependency attributions without recording developer-machine paths."""

from __future__ import annotations

import argparse
import hashlib
from importlib import metadata
import json
from pathlib import Path
import subprocess
import sys
from packaging.requirements import Requirement


def render(target):
    root = Path(__file__).resolve().parents[1]
    inventory = []
    texts = {}

    def add(name, version, expression, files):
        ids = []
        for path in sorted(set(files)):
            if not path.is_file() or path.stat().st_size > 1_000_000:
                continue
            text = path.read_text(encoding="utf-8", errors="replace").strip()
            if not text:
                continue
            key = hashlib.sha256(text.encode()).hexdigest()[:16]
            texts[key] = text
            if key not in ids:
                ids.append(key)
        inventory.append(
            (name, version, expression or "see upstream license", ",".join(ids))
        )

    packages = json.loads(
        subprocess.check_output(
            [
                "cargo",
                "metadata",
                "--locked",
                "--format-version",
                "1",
                "--filter-platform",
                "aarch64-apple-darwin",
                "--manifest-path",
                str(root / "src-tauri/Cargo.toml"),
            ]
        )
    )
    for p in packages["packages"]:
        if p["source"] is None:
            continue
        folder = Path(p["manifest_path"]).parent
        files = (
            list(folder.glob("LICENSE*"))
            + list(folder.glob("COPYING*"))
            + list(folder.glob("NOTICE*"))
        )
        if p["license_file"]:
            files.append(folder / p["license_file"])
        add("Rust / " + p["name"], p["version"], p["license"], files)
    dependencies = (root / "requirements.txt").read_text().splitlines()
    todo = [Requirement(line).name for line in dependencies if line.strip()] + ["pyinstaller"]
    seen = set()
    while todo:
        name = todo.pop().lower()
        if name in seen:
            continue
        seen.add(name)
        d = metadata.distribution(name)
        files = []
        for row in d.files or ():
            if (
                row.name.upper().startswith(("LICENSE", "COPYING", "NOTICE"))
                or "licenses" in row.parts
            ):
                files.append(Path(d.locate_file(row)))
        add(
            "Python / " + name,
            d.version,
            d.metadata.get("License-Expression") or d.metadata.get("License"),
            files,
        )
        for dep in d.requires or ():
            req = Requirement(dep)
            if not req.marker or req.marker.evaluate({"extra": ""}):
                todo.append(req.name)
    frontend = root / "frontend/node_modules"
    runtime_deps = (frontend / "svelte").resolve().parent
    for folder in [frontend / "svelte", frontend / "vite", runtime_deps / "clsx", runtime_deps / "esm-env"]:
        pkg = json.loads((folder / "package.json").read_text())
        add(
            "JavaScript / " + pkg["name"],
            pkg["version"],
            pkg.get("license"),
            [file for file in folder.iterdir() if file.name.lower().startswith("license")],
        )
    import sysconfig

    add(
        "CPython",
        sys.version.split()[0],
        "Python-2.0",
        [Path(sysconfig.get_path("stdlib")) / "LICENSE.txt"],
    )
    with target.open("w", encoding="utf-8") as out:
        out.write(
            "局中事 · 第三方组件与许可\n构建依赖图含平台和构建期组件。下列编号对应原始许可及通知文本。\n\n"
        )
        for row in sorted(inventory):
            out.write(" | ".join(row) + "\n")
        for key, value in sorted(texts.items()):
            out.write(f"\n[{key}]\n{value}\n")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("output", type=Path)
    render(parser.parse_args().output)
