"""The driver's timetable. The same run sheet powers the dial, log and later scenes."""

from dataclasses import dataclass


def clock(offset):
    hours, minutes = divmod(22 * 60 + 40 + offset, 60)
    return f"{hours:02}:{minutes:02}"


@dataclass(frozen=True)
class Run:
    delay: int
    baths: bool

    @property
    def route(self):
        return "baths" if self.baths else "bridge"

    @property
    def label(self):
        return "绕澡堂" if self.baths else "沿河直行"

    @property
    def arrival(self):
        return self.delay + (18 if self.baths else 13)

    @property
    def nurses(self):
        # At South Gate: apprentice at +6, two colleagues at +12. The baths
        # are four minutes away on foot and ten minutes away by the bus loop.
        ready = (6, 12, 12)
        return sum(
            self.delay >= minute or self.baths and self.delay + 10 >= minute + 4
            for minute in ready
        )

    @property
    def transfer(self):
        return self.arrival <= 20

    @property
    def target(self):
        if not self.transfer:
            return "dispatch_late"
        return "dispatch_doors" if self.arrival >= 18 else "dispatch_platform"

    def key(self, rehearsal):
        return f"{'paper' if rehearsal else 'run'}_{self.route}_{self.delay}"

    def slip(self, rehearsal, seen):
        return {
            "key": self.key(rehearsal),
            "route": self.route,
            "label": self.label,
            "leave": clock(self.delay),
            "bath_at": clock(self.delay + 10) if self.baths else None,
            "arrive": clock(self.arrival),
            "nurses": self.nurses,
            "transfer": self.transfer,
            "marked": not rehearsal and self.key(True) in seen,
        }

    def account(self):
        staff = {
            0: "三个护工都留在了路上。",
            1: "小陶上了车，两位替老人翻完身才走的师傅没赶上。",
            3: "三个护工都上了车。小陶把窗边的座位留给了膝盖不好的师傅。",
        }[self.nurses]
        bath = (
            "过澡堂时，老葛把收音机塞进棉袄，腾出手拉住扶手。"
            if self.baths else "七路拐向河堤时，澡堂的老葛还在门口等。"
        )
        bridge = (
            "三名工友看见接班车还在，赶紧往前门挪。"
            if self.transfer else "桥头只剩尾气，车里三名工友谁都没按下车铃。"
        )
        return f"七路{clock(self.delay)}离开南门。{staff}{bath}到北桥是{clock(self.arrival)}。{bridge}"


RUNS = tuple(Run(delay, baths) for baths in (False, True) for delay in (0, 6, 12))
LIVE_RUNS = {run.key(False): run for run in RUNS}
ARRIVALS = {run.target for run in RUNS}
BOARDS = {"dispatch_rehearsal", "dispatch_live"}


def slips(node, seen):
    if node in BOARDS:
        return [run.slip(node == "dispatch_rehearsal", seen) for run in RUNS]
    return []
