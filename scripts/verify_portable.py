"""Verify a packaged game through its local HTTP entry point and a fresh data directory.

Usage: python verify_portable.py --assets WEB_DIR -- ENGINE [ENGINE_ARGS ...]
"""

import argparse
from contextlib import contextmanager
import json
import os
from pathlib import Path
from queue import Empty, Queue
import re
import subprocess
from tempfile import TemporaryDirectory
from threading import Thread
from urllib.parse import urlsplit
from urllib.request import ProxyHandler, Request, build_opener


def require(condition, message):
    if not condition:
        raise RuntimeError(message)


@contextmanager
def engine_session(command, assets, profile):
    env = {k: v for k, v in os.environ.items() if not k.startswith("JUZHONGSHI_AI_")}
    with subprocess.Popen(
        [*command, "--desktop", "--assets", str(assets), "--data-dir", str(profile)],
        stdin=subprocess.PIPE,
        stdout=subprocess.PIPE,
        env=env,
    ) as engine:
        try:
            lines = Queue()
            reader = Thread(target=lambda: lines.put(engine.stdout.readline()), daemon=True)
            reader.start()
            try:
                line = lines.get(timeout=90)
            except Empty as exc:
                raise RuntimeError("Timed out waiting for the packaged engine") from exc
            require(line, "The packaged engine exited before reporting a session")
            url = urlsplit(line.decode("ascii").strip())
            require(
                url.scheme == "http" and url.hostname == "127.0.0.1" and url.port
                and url.path == "/" and re.fullmatch(r"session=[\w-]+", url.fragment),
                "The engine did not return a local game session",
            )
            origin = f"http://127.0.0.1:{url.port}"
            token = url.fragment.removeprefix("session=")
            opener = build_opener(ProxyHandler({}))

            def fetch(path, body=None, raw=False):
                require(path.startswith("/") and not path.startswith("//"), "Invalid local path")
                data = json.dumps(body).encode() if body is not None else None
                req = Request(origin + path, data=data, headers={
                    "Authorization": f"Bearer {token}",
                    "Content-Type": "application/json",
                })
                with opener.open(req, timeout=60) as reply:
                    wire = reply.read()
                return wire if raw else json.loads(wire)

            yield fetch
        finally:
            engine.stdin.close()  # Same orderly shutdown as closing the desktop shell.
            try:
                code = engine.wait(timeout=20)
            except subprocess.TimeoutExpired:
                engine.kill()
                engine.wait()
                raise RuntimeError("The packaged engine did not shut down after closing its input")
            require(code == 0, f"The packaged engine exited with status {code}")


def verify(command, assets, profile):
    with engine_session(command, assets, profile) as fetch:
        html = fetch("/", raw=True).decode()
        require("<title>局中事</title>" in html, "The game entry page is missing")
        for ext in ("js", "css"):
            ref = re.search(r'["\'](\.?/assets/[\w.-]+\.' + ext + r')["\']', html)
            require(ref, f"Missing bundled {ext} asset in the entry page")
            require(fetch(ref[1].removeprefix("."), raw=True), f"The bundled {ext} asset was empty")
        require(fetch("/api/worlds")["worlds"] == [], "The test profile should be empty")
        settings = fetch("/api/preferences", {"font_size": 20})
        require(settings["font_size"] == 20, "The settings write failed")
        world = fetch("/api/worlds", {"start": "S01", "name": "林青", "seed": "classic"})
        path = "/api/worlds/" + world["id"]
        current = fetch(path + "/commands", {
            "command_id": "first", "expected_revision": world["revision"],
            "kind": "reply", "args": {"mode": "defer"},
        })
        require(current["revision"] == world["revision"] + 1, "The first command did not commit")
        archive = fetch(path + "/export")

    with engine_session(command, assets, profile) as fetch:
        require(fetch("/api/preferences") == settings, "The settings changed after restart")
        require([row["id"] for row in fetch("/api/worlds")["worlds"]] == [world["id"]],
                "The career is missing from the menu after restart")
        resumed = fetch(path)
        # Confirmation tokens belong to one process and are freshly signed on restart.
        for view in (current, resumed):
            for action in view["actions"]:
                action.pop("confirmation_token", None)
        require(resumed == current, "The player view changed after restart")
        require(fetch(path + "/export") == archive, "The saved history changed after restart")
        after = fetch(path + "/commands", {
            "command_id": "after-restart", "expected_revision": current["revision"],
            "kind": "advance", "args": {"minutes": 30},
        })
        require(after["revision"] == current["revision"] + 1, "The restored career did not advance")
    return archive["checksum"], after["revision"]


def verify_import(command, assets, profile, save_file):
    with save_file.open(encoding="utf-8") as handle:
        original = json.load(handle)
    with engine_session(command, assets, profile) as fetch:
        restored = fetch("/api/import", original)
        exported = fetch("/api/worlds/" + restored["id"] + "/export")
        require(exported == original, "Import and re-export changed the original archive")
    return exported["checksum"]


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", type=Path, required=True)
    parser.add_argument("--import-save", type=Path, help="also verify an archive from another platform")
    parser.add_argument("engine", nargs=argparse.REMAINDER)
    args = parser.parse_args()
    command = args.engine[1:] if args.engine[:1] == ["--"] else args.engine
    if not command:
        parser.error("supply the packaged engine command after --")
    with TemporaryDirectory(prefix="juzhongshi-qa-") as tmp:
        assets = args.assets.resolve()
        checksum, revision = verify(command, assets, Path(tmp) / "career")
        if args.import_save:
            imported = verify_import(command, assets, Path(tmp) / "import", args.import_save)
            print(f"PASS: imported and re-exported the identical archive {imported}.")
    print(f"PASS: settings, bundled assets, save/restart, full archive equality, "
          f"and continued play (revision {revision}, archive {checksum}).")


if __name__ == "__main__":
    main()
