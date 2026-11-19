"""Device presentation settings live outside the simulated world and its history."""

from contextlib import contextmanager
import os
from pathlib import Path
from tempfile import NamedTemporaryFile
from threading import Lock
from typing import Annotated, Literal

if os.name == "nt":
    import msvcrt
else:
    import fcntl

from fastapi import APIRouter, HTTPException
from pydantic import BaseModel, ConfigDict, Field, ValidationError


FontSize = Literal[14, 16, 18, 20, 22]
Volume = Annotated[int, Field(ge=0, le=100)]


class Preferences(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    font_size: FontSize = 16
    sound_volume: Volume = 0
    reduced_motion: bool | None = None
    detailed_narration: bool = True
    show_hints: bool = True


class PreferencePatch(Preferences):
    """model_fields_set selects the exact keys the caller wants to change."""


class PreferencesFile:
    def __init__(self, path: Path | None):
        self.path = path
        self.lock = Lock()
        self.memory = Preferences()

    def read(self) -> Preferences:
        try:
            with self._guard():
                return self._read_unlocked()
        except OSError as exc:
            raise HTTPException(503, "本机阅读设置暂时无法读取。") from exc

    def _read_unlocked(self) -> Preferences:
        if self.path is None:
            return self.memory.model_copy()
        try:
            return Preferences.model_validate_json(self.path.read_bytes())
        except FileNotFoundError:
            return Preferences()
        except (OSError, ValidationError) as exc:
            raise HTTPException(503, "本机阅读设置暂时无法读取。") from exc

    @contextmanager
    def _guard(self):
        with self.lock:
            if self.path is None:
                yield
                return
            self.path.parent.mkdir(parents=True, exist_ok=True)
            with open(self.path.with_suffix(".lock"), "a+b") as guard:
                if os.name == "nt":
                    # Windows byte-range locks can extend past EOF. Each process
                    # locks byte zero; closing the handle releases it on every exit.
                    guard.seek(0)
                    msvcrt.locking(guard.fileno(), msvcrt.LK_LOCK, 1)
                else:
                    fcntl.flock(guard, fcntl.LOCK_EX)
                yield

    def update(self, patch: PreferencePatch) -> Preferences:
        tmp = None
        try:
            with self._guard():
                new = Preferences.model_validate(
                    {**self._read_unlocked().model_dump(), **patch.model_dump(exclude_unset=True)}
                )
                if self.path is None:
                    self.memory = new
                    return new
                with NamedTemporaryFile(
                    dir=self.path.parent,
                    prefix=".read-settings-",
                    mode="w",
                    encoding="utf-8",
                    delete=False,
                ) as handle:
                    tmp = Path(handle.name)
                    handle.write(new.model_dump_json())
                    handle.flush()
                    os.fsync(handle.fileno())
                os.replace(tmp, self.path)
                return new
        except OSError as exc:
            raise HTTPException(503, "本机阅读设置暂时无法保存。") from exc
        finally:
            if tmp is not None:
                tmp.unlink(missing_ok=True)


def preferences_router(path: Path | None) -> APIRouter:
    router = APIRouter()
    prefs = PreferencesFile(path)
    router.add_api_route(
        "/api/preferences", prefs.read, methods=["GET"], response_model=Preferences
    )
    router.add_api_route(
        "/api/preferences", prefs.update, methods=["POST"], response_model=Preferences
    )
    return router
