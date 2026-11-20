"""Original stereo cues for the foyer, booth, failed screening and coda."""
import numpy as np
from score_chronicle import RATE, TAU, Tape, note


def transient(tape, at, pitch, decay, strength, pan):
    t = np.arange(int(RATE * decay * 7)) / RATE
    # A sprung wooden seat with several independently decaying resonances.
    tap = np.exp(-t / decay) * (0.52 * np.sin(TAU * pitch * t)
          + 0.25 * np.sin(TAU * pitch * 2.72 * t)
          + 0.11 * np.sin(TAU * pitch * 5.61 * t))
    tape.lay(at, strength * tap * np.minimum(t * 450, 1), pan)


def cinema(venue):
    length = {"foyer": 16, "booth": 14, "turn": 18, "after": 22}[venue]
    tape = Tape(length, 273 + len(venue))
    t = np.arange(tape.frames) / RATE
    env = np.minimum(t / .4, 1) * np.minimum((length - t) / 1.8, 1)
    hiss = tape.air(length, [(0,0),(90,.01),(460,.25),(1700,1),(5000,.18),(10000,0)])
    tape.lay(0, env * hiss * (.003 if venue == "after" else .013), -.24)
    if venue in {"booth","turn"}:
        speed = .72 + .28 * (1 - np.exp(-t / .8))
        if venue == "turn":
            speed *= np.exp(-np.maximum(0, t - 4.6) / .38)
        phase = TAU * np.cumsum(23.8 * speed * (1 + .012 * np.sin(.9 * t))) / RATE
        gate = (.5 + .5 * np.sin(phase)) ** 14
        tape.lay(0, env * speed * (gate * (.062*hiss + .033) + .043*np.sin(phase*2.5)), .38)
    if venue == "foyer":
        for idx,(at,pitch) in enumerate([(1,191),(1.42,246),(3.9,202),(6.1,154),(9.8,183)]):
            transient(tape,at,pitch,.084,.23, .64 - idx*.27)
        note(tape, 9.9, 62, 2.5, .13, "felt", -.4)
        note(tape, 12.0, 57, 1.9, .12, "felt", -.32)
    elif venue == "booth":
        for at,pitch in [(1.1,511),(2.5,453),(7.2,290),(10.8,455)]:
            transient(tape, at, pitch, .022, .13, -.35)
    elif venue == "turn":
        # As the projector dies, the room falls silent before the bowed pedal arrives.
        transient(tape,4.86,180,.065,.18,.54)
        note(tape, 7.5, 36, 4.0, .54, "bow", -.18)
        note(tape, 8.15, 43, 3.7, .35, "bow", .36)
        note(tape, 12.4, 53, 1.5, .21, "felt", -.3)
    else:
        for idx,(at,midi,duration) in enumerate([(1.1,62,1.4),(4.1,57,2.2),(9.2,60,1.7),(13.3,55,3.3),(16.65,62,2.2)]):
            note(tape,at,midi,duration,.28 if idx in (0,3) else .20,"felt",(-1)**idx*.28)
        transient(tape, 18.1, 197, .11, .21, .52)
    tape.export("county_cinema_" + venue, .086 if venue in {"booth","turn"} else .065)


if __name__ == "__main__":
    for name in ("foyer","booth","turn","after"):
        cinema(name)
