"""Nonblocking, per-launch coordination for the desktop update menu."""

from pathlib import Path
from threading import Lock, Thread

from fastapi import APIRouter
from pydantic import BaseModel, ConfigDict

from game.update_trust import VERSION
from game.updater import DesktopUpdater, OfflineError, UpdateError


class UpdatePreference(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    automatic: bool


class UpdateSession:
    def __init__(self, engine=None, data_dir: Path | None = None, current=VERSION):
        self.engine = engine
        self.current = current
        self.disabled_flag = data_dir / "updates" / "automatic-off" if data_dir else None
        self.phase = "idle"
        self.message = ""
        self.latest = None
        self.started = False
        self.busy = False
        self.lock = Lock()

    @classmethod
    def packaged(cls, platform, data_dir):
        if platform not in {"macos-arm64", "windows-x64", "linux-x86_64"}:
            return cls()
        return cls(DesktopUpdater(data_dir, platform, VERSION), data_dir)

    def _automatic(self):
        return bool(self.disabled_flag) and not self.disabled_flag.exists()

    def _snapshot(self):
        return dict(
            supported=self.engine is not None,
            automatic=self._automatic(),
            current_version=self.current,
            latest_version=self.latest,
            phase=self.phase,
            message=self.message,
        )

    def _ready(self):
        ready = self.engine.ready_version()
        if ready and tuple(map(int, ready.split("."))) > tuple(map(int, self.current.split("."))):
            self.latest = ready
            self.phase = "ready"
            self.message = "新版已准备好。下次打开游戏时会自动使用新版。"
            return True
        return False

    def _start(self, manual):
        if not self.engine or self.busy:
            return
        self.started = True
        try:
            if self._ready() or (not manual and not self._automatic()):
                return
        except (OSError, UpdateError):
            self.phase, self.message = "error", "无法读取更新目录，仍可正常游玩。"
            return
        self.busy = True
        self.phase, self.message = "checking", "正在检查新版本。"
        Thread(target=self._run, args=(manual,), name="desktop-update", daemon=True).start()

    def _run(self, manual):
        try:
            release = self.engine.check()
            with self.lock:
                if release is None:
                    self.phase, self.message = "current", "已是最新版本。"
                    self.latest = self.current
                    return
                self.latest = release.version
                if not manual and not self._automatic():
                    self.phase, self.message = "idle", "已关闭启动时自动更新。"
                    return
                self.phase, self.message = "downloading", "正在后台下载新版，可以继续游玩。"
            self.engine.install(release)
            with self.lock:
                if not self._ready():
                    raise UpdateError("新版未能完成安装。")
        except OfflineError:
            with self.lock:
                self.phase, self.message = "offline", "暂时连不上更新服务器，可以继续玩，稍后再试。"
        except (UpdateError, OSError):
            with self.lock:
                self.phase, self.message = "error", "新版未能通过检查或写入磁盘。当前版本仍可使用，可以稍后重试。"
        finally:
            with self.lock:
                self.busy = False

    def status(self, manual=False):
        with self.lock:
            if manual or not self.started:
                self._start(manual)
            return self._snapshot()

    def preference(self, automatic):
        with self.lock:
            if self.disabled_flag is not None:
                try:
                    if automatic:
                        self.disabled_flag.unlink(missing_ok=True)
                        self._start(False)
                    else:
                        self.disabled_flag.parent.mkdir(parents=True, exist_ok=True)
                        self.disabled_flag.touch()
                        self.started = True
                except OSError:
                    self.phase, self.message = "error", "更新设置未能保存，请检查本机目录权限。"
            return self._snapshot()


def updates_router(session):
    router = APIRouter(prefix="/api/update")

    @router.get("")
    def status():
        return session.status()

    @router.post("/check")
    def check():
        return session.status(manual=True)

    @router.post("/preferences")
    def preferences(body: UpdatePreference):
        return session.preference(body.automatic)

    return router
