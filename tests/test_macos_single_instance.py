"""Exercise simultaneous cold starts on an explicitly selected macOS release bundle."""

import os
from pathlib import Path
import signal
import subprocess
import sys
import time

import pytest


@pytest.mark.skipif(
    sys.platform != "darwin" or not os.environ.get("JZS_TEST_APP"),
    reason="requires an Apple Silicon Mac and JZS_TEST_APP pointing to a built release",
)
def test_concurrent_launch_and_crash_cleanup(tmp_path):
    binary = Path(os.environ["JZS_TEST_APP"]) / "Contents" / "MacOS" / "juzhongshi"
    profile = tmp_path / "中文 档案"
    env = {**os.environ, "JUZHONGSHI_DATA_DIR": str(profile)}
    launchers = []
    try:
        for _ in range(8):
            launchers.append(subprocess.Popen([binary], env=env))
        deadline = time.monotonic() + 30
        while time.monotonic() < deadline:
            active = [proc for proc in launchers if proc.poll() is None]
            if len(active) == 1 and (profile / "careers.sqlite3").is_file():
                break
            time.sleep(0.1)
        assert len(active) == 1
        assert all(proc is active[0] or proc.returncode == 0 for proc in launchers)
        launcher = active[0]

        # PyInstaller's one-file bootloader owns one running Python child.
        def only_engine_child(parent):
            children = subprocess.check_output(
                ["pgrep", "-P", str(parent), "-x", "jzs-engine"], text=True
            ).splitlines()
            assert len(children) == 1
            return children[0]

        wrapper = only_engine_child(launcher.pid)
        server = only_engine_child(wrapper)
        launcher.send_signal(signal.SIGKILL)
        launcher.wait(timeout=5)
        deadline = time.monotonic() + 10
        while time.monotonic() < deadline:
            remaining = subprocess.run(
                ["ps", "-p", f"{wrapper},{server}", "-o", "pid="],
                capture_output=True,
                text=True,
                check=False,
            ).stdout.strip()
            if not remaining:
                break
            time.sleep(0.1)
        assert not remaining
    finally:
        for proc in launchers:
            if proc.poll() is None:
                proc.kill()
            proc.wait(timeout=5)
