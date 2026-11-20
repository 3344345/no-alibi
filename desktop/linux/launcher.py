"""Linux application-menu integration and single-user browser session."""

from __future__ import annotations

import os
import hashlib
import re
import selectors
import shutil
import socket
import subprocess
import sys
from pathlib import Path
import tempfile
import webbrowser

ROOT = Path(__file__).resolve().parent
PLATFORM = "linux-x86_64"


def read_version(path):
    try:
        value = path.read_text(encoding="ascii").rstrip("\r\n")
    except (OSError, UnicodeError):
        return None
    return value if re.fullmatch(r"(?:0|[1-9][0-9]{0,5})(?:\.(?:0|[1-9][0-9]{0,5})){2}", value) else None


def active_executable(profile, package=ROOT):
    updates = profile / "updates"
    next_version = read_version(updates / (PLATFORM + ".active"))
    current = read_version(package / "VERSION")
    if not current or not next_version:
        return None
    if tuple(map(int, next_version.split("."))) <= tuple(map(int, current.split("."))):
        return None
    folder = updates / "versions" / next_version / PLATFORM / "局中事"
    if read_version(folder / "VERSION") != next_version:
        return None
    executable = folder / "局中事"
    python = folder / "runtime/bin/python3"
    required = (executable, python, folder / "runtime/bin/python3.12", folder / "launcher.py",
                folder / "app/main.py", folder / "app/frontend/dist/index.html")
    try:
        complete = all(item.is_file() and item.stat().st_size > 0 for item in required)
    except OSError:
        return None
    return executable if complete and os.access(executable, os.X_OK) and os.access(python, os.X_OK) else None


def xdg(variable, default):
    value = os.environ.get(variable, "")
    return Path(value) if Path(value).is_absolute() else Path.home() / default


def install_shortcut():
    applications = xdg("XDG_DATA_HOME", ".local/share") / "applications"
    applications.mkdir(parents=True, exist_ok=True)
    # Exec is interpreted twice (desktop-entry strings, then argument quoting).
    executable = str(ROOT / "局中事").replace("%", "%%")
    for char in ('\\', '"', '`', '$'):
        executable = executable.replace(char, '\\' + char)
    executable = '"' + executable.replace('\\', '\\\\') + '"'
    icon = str(ROOT / "app/frontend/dist/game-icon.png").replace('\\', '\\\\')
    entry = (
        "[Desktop Entry]\nType=Application\nName=局中事\n"
        f"Exec={executable}\nIcon={icon}\nTerminal=false\n"
        "Categories=Game;Simulation;\nActions=Stop;\n\n"
        f"[Desktop Action Stop]\nName=退出局中事\nExec={executable} --stop\n"
    )
    with tempfile.NamedTemporaryFile(dir=applications, delete=False) as handle:
        handle.write(entry.encode())
    os.replace(handle.name, applications / "cn.juzhongshi.game.desktop")


def open_game(url):
    if not webbrowser.open(url):
        raise RuntimeError("请在系统设置中选择一个默认浏览器，再打开《局中事》。")


def run(stop, profile):
    # An abstract Unix socket survives neither crashes nor logout. Its peer UID
    # is checked in both directions before a launcher can open or end the game.
    key = hashlib.sha256(os.fsencode(profile)).hexdigest()[:24]
    address = f"\0cn.juzhongshi.game.v1.{os.getuid()}.{key}"
    with socket.socket(socket.AF_UNIX) as server:
        try:
            server.bind(address)
        except OSError as exc:
            import errno
            if exc.errno != errno.EADDRINUSE:
                raise
            with socket.socket(socket.AF_UNIX) as client:
                from time import monotonic, sleep
                deadline = monotonic() + 20
                while True:
                    try:
                        client.connect(address)
                        break
                    except ConnectionRefusedError:
                        if monotonic() >= deadline:
                            raise
                        sleep(0.05)
                check_user(client)
                client.settimeout(30)
                client.sendall(b"S" if stop else b"O")
                if client.recv(1) != b"Y":
                    raise RuntimeError("游戏尚未就绪，请稍后重试。")
            return
        if stop:
            return
        server.listen()
        server.settimeout(0.6)
        with subprocess.Popen(
            [sys.executable, "-EsB", str(ROOT / "app/main.py"), "--desktop"],
            stdin=subprocess.PIPE, stdout=subprocess.PIPE, text=True,
            env={**os.environ, "JUZHONGSHI_UPDATE_PLATFORM": PLATFORM,
                 "JUZHONGSHI_UPDATE_VERSION": read_version(ROOT / "VERSION") or "",
                 "JUZHONGSHI_UPDATE_ROOT": str(profile)},
        ) as engine:
            try:
                with selectors.DefaultSelector() as ready:
                    ready.register(engine.stdout, selectors.EVENT_READ)
                    if not ready.select(60):
                        raise RuntimeError("游戏启动超时。")
                    url = engine.stdout.readline().strip()
                if not url.startswith("http://127.0.0.1:") or "#session=" not in url:
                    raise RuntimeError("游戏未能启动。")
                open_game(url)
                while engine.poll() is None:
                    try:
                        client, _ = server.accept()
                    except TimeoutError:
                        continue
                    with client:
                        try:
                            check_user(client)
                            client.settimeout(2)
                            command = client.recv(1)
                            if command == b"O":
                                open_game(url)
                            client.sendall(b"Y" if command in (b"S", b"O") else b"N")
                            if command == b"S":
                                return
                        except (OSError, RuntimeError):
                            continue
                raise RuntimeError("游戏进程已退出，请重新打开。")
            finally:
                engine.stdin.close()
                try:
                    engine.wait(timeout=8)
                except subprocess.TimeoutExpired:
                    engine.kill()


def check_user(connection):
    import struct
    _pid, uid, _gid = struct.unpack(
        "3i", connection.getsockopt(socket.SOL_SOCKET, socket.SO_PEERCRED, 12)
    )
    if uid != os.getuid():
        raise PermissionError("会话属于其他用户。")


if __name__ == "__main__":
    flags = sys.argv[1:]
    if flags not in ([], ["--stop"], ["--install"]):
        sys.exit("用法：局中事 [--stop | --install]")
    try:
        sys.path.insert(0, str(ROOT / "app"))
        from main import default_data_dir
        profile = default_data_dir().resolve()
        # The user's menu continues to point to the installation they originally opened.
        if flags != ["--stop"] and not ROOT.is_relative_to(profile / "updates/versions"):
            install_shortcut()
        if not flags:
            active = active_executable(profile)
            if active:
                try:
                    os.execv(active, [str(active)])
                except OSError:
                    pass  # The staged binary was removed or cannot run. Use this copy.
        if flags != ["--install"]:
            run(flags == ["--stop"], profile)
    except (OSError, RuntimeError) as error:
        print(error, file=sys.stderr)
        if shutil.which("zenity") and (os.getenv("DISPLAY") or os.getenv("WAYLAND_DISPLAY")):
            subprocess.run(["zenity", "--error", "--title=局中事", "--text", str(error)])
        sys.exit(1)
