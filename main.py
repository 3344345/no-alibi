"""Launch the local game server, optionally opening the player's default browser."""

from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import secrets
import socket
import sys
import threading
import webbrowser

import uvicorn

from api.routes import make_app
from game.chronicle import ChronicleStore
from game.store import GameStore


def default_data_dir() -> Path:
    override = os.environ.get("JUZHONGSHI_DATA_DIR")
    if override:
        return Path(override)
    home = Path.home()
    mac_path = home / "Library" / "Application Support" / "局中事"
    if sys.platform == "darwin":
        return mac_path
    if sys.platform == "win32":
        local = os.environ.get("LOCALAPPDATA") or home / "AppData" / "Local"
        return Path(local) / "局中事"
    xdg = os.environ.get("XDG_DATA_HOME")
    data = Path(xdg) if xdg and Path(xdg).is_absolute() else home / ".local" / "share"
    new_path = data / "juzhongshi"
    # Early source builds used the Mac layout on Linux as well.
    if not (new_path / "careers.sqlite3").exists() and (mac_path / "careers.sqlite3").is_file():
        return mac_path
    return new_path


def restore_archive(store: GameStore, path: Path):
    with path.open(encoding="utf-8") as archive:
        data = json.load(archive)
    if isinstance(data, dict) and data.get("format") in ("juzhongshi-chronicle/1","juzhongshi-chronicle/2","juzhongshi-chronicle/3"):
        return ChronicleStore(store).restore(data)
    return store.restore(data)


def launch() -> None:
    parser = argparse.ArgumentParser(description="局中事 · 本地游戏")
    parser.add_argument("--desktop", action="store_true", help="使用桌面窗口握手")
    parser.add_argument("--no-browser", action="store_true", help="仅显示本机入口")
    parser.add_argument(
        "--assets",
        type=Path,
        default=Path(__file__).resolve().parent / "frontend" / "dist",
    )
    parser.add_argument(
        "--data-dir",
        type=Path,
        default=default_data_dir(),
    )
    parser.add_argument("--restore-file", type=Path, help=argparse.SUPPRESS)
    args = parser.parse_args()
    if not (args.assets / "index.html").is_file():
        parser.exit(
            2,
            "缺少游戏界面资源。源码版请先在 frontend 目录运行 pnpm install --frozen-lockfile 和 pnpm build。\n",
        )
    args.data_dir.mkdir(parents=True, exist_ok=True, mode=0o700)
    store = GameStore(args.data_dir / "careers.sqlite3")
    if args.restore_file is not None:
        try:
            restore_archive(store, args.restore_file)
        except (OSError, ValueError):
            parser.exit(3, "备份未通过版本或完整性校验。\n")
    token = secrets.token_urlsafe(32)
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.bind(("127.0.0.1", 0))
        port = sock.getsockname()[1]
        url = f"http://127.0.0.1:{port}/#session={token}"
        server = uvicorn.Server(
            uvicorn.Config(
                make_app(
                    store, token, args.assets, port, args.data_dir / "preferences.json"
                ),
                access_log=False,
                log_level="error",
                loop="asyncio",
                http="h11",
                ws="none",
            )
        )
        if args.desktop:

            def watch_parent():
                # EOF from the launcher also occurs if the desktop process is terminated.
                sys.stdin.buffer.read(1)
                server.should_exit = True

            threading.Thread(target=watch_parent, daemon=True).start()
        sock.listen(64)
        if args.desktop or args.no_browser:
            print(url, flush=True)
        else:
            threading.Thread(target=lambda: webbrowser.open(url), daemon=True).start()
        server.run(sockets=[sock])


if __name__ == "__main__":
    launch()
