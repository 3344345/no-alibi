from threading import Event
from time import monotonic, sleep
from types import SimpleNamespace

from api.updates import UpdateSession
from game.updater import OfflineError


def settled(session):
    end = monotonic() + 2
    while monotonic() < end:
        state = session.status()
        if state["phase"] not in {"checking", "downloading"}:
            return state
        sleep(0.01)
    raise AssertionError("update session did not settle")


class Service:
    def __init__(self):
        self.calls = 0
        self.online = False
        self.finish = Event()
        self.ready = None

    def check(self):
        self.calls += 1
        if not self.online:
            raise OfflineError()
        return SimpleNamespace(version="4.3.0")

    def install(self, release):
        assert self.finish.wait(2)
        self.ready = release.version

    def ready_version(self):
        return self.ready


def test_auto_start_offline_manual_retry_and_reopen_with_staged_package(tmp_path):
    service = Service()
    session = UpdateSession(service, tmp_path)
    assert session.status()["phase"] == "checking"
    assert settled(session)["phase"] == "offline"
    service.online = True
    session.status(manual=True)
    for _ in range(3):
        assert session.status(manual=True)["phase"] in {"checking", "downloading"}
    service.finish.set()
    assert settled(session)["latest_version"] == "4.3.0"
    assert session.status()["phase"] == "ready"
    assert UpdateSession(service, tmp_path).status()["phase"] == "ready"
    assert service.calls == 2


def test_automatic_preference_survives_restart_and_manual_check_still_works(tmp_path):
    service = Service()
    before = UpdateSession(service, tmp_path)
    assert not before.preference(False)["automatic"]
    reopened = UpdateSession(service, tmp_path)
    assert reopened.status()["phase"] == "idle"
    assert service.calls == 0
    reopened.status(manual=True)
    assert settled(reopened)["phase"] == "offline"
    assert service.calls == 1
    assert reopened.preference(True)["automatic"]
    assert settled(reopened)["phase"] == "offline"
    assert service.calls == 2
