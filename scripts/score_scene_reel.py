"""Original mono-source/stereo-mixed props and two chamber pieces for the story reader."""
import numpy as np
from score_chronicle import RATE, TAU, Tape, impact, note


def stroke(tape, at, duration, pan, level, high=1800):
    t = np.arange(int(RATE * duration)) / RATE
    wave = tape.air(duration, [(0, 0), (130, .05), (high, 1), (6500, .12), (14500, 0)])
    tape.lay(at, level * wave * np.sin(np.pi * t / duration) ** 2, pan)


def props():
    cup = Tape(3.4, 103)
    for at, scale, pan in [(0.13, .7, -.3), (.49, .38, -.15), (1.35, .16, .08)]:
        impact(cup, at, [(1430, .19, .5), (2661, .095, .24), (4812, .045, .2)], .85, scale, pan)
    stroke(cup, .61, .26, -.22, .034, 780)
    cup.export("cup_rim", .065)

    rods = Tape(4.7, 1919)
    for at, dur, side in [(.2,.23,-.48),(.67,.48,-.25),(1.8,.16,.36),(2.09,.72,.46),(3.32,.29,.05)]:
        stroke(rods, at, dur, side, .16, 1520)
        impact(rods, at+.04, [(732,.027,.5),(1800,.011,.3)], .19, .26, side)
    rods.export("paper_rods", .075)

    piano = Tape(7, 1992)
    note(piano, .13, 50, 2.8, .65, "felt", -.28)
    impact(piano, 2.81, [(68,.09,.4),(150,.036,.24)], .4, .2, .28)
    piano.export("piano_wire", .089)

    rain = Tape(5.2, 1986)
    for at, pan, pitch in [(.32,-.67,1290),(.53,-.52,1260),(1.75,.22,970),(2.42,.4,1370),(2.61,.57,920),(3.57,.18,1280),(4.01,-.08,1260)]:
        impact(rain, at, [(pitch,.072,.45),(pitch*2.09,.032,.15),(198,.053,.26)], .37, .5, pan)
        stroke(rain, at+.01, .056, pan, .11, 2900)
    rain.export("rain_tin", .061)


def score():
    # Giving the two lead voices different rhythms leaves room for the onstage sounds.
    shadow = Tape(48, 719)
    for at, pitch, length, gain in [(1.4,62,1,.22),(3.5,65,1.9,.21),(8,67,2.4,.3),(15,69,1.3,.26),(17.5,64,2.7,.22),
                                     (24.5,62,2,.2),(29.5,67,2.8,.29),(35.9,65,1.7,.25),(38,60,3.1,.25),(44,62,1.1,.14)]:
        note(shadow, at,pitch,length,gain,"reed",-.31)
        note(shadow, at+.16,pitch-12,length*.65,gain*.64,"felt",.22)
    for at,pitch in [(0,38),(10.3,43),(21.2,41),(32.4,36),(42.1,38)]:
        note(shadow,at,pitch,3,.31,"bow",.34)
    shadow.export("shadow_duet", .094)

    hammers = Tape(53, 992)
    for at, pitch, duration in [(1,50,2.8),(4.3,57,1.5),(6.8,53,1.4),(12.4,46,2.6),(15.2,55,1.5),
                                (22.6,50,1.5),(23.6,57,1.6),(27,60,2.3),(33.7,53,2.8),(40.9,48,3.4),(47.5,50,2.7)]:
        note(hammers, at, pitch, duration, .42, "felt", -.26 if pitch < 54 else .29)
    hammers.export("empty_hall", .087)

    held = Tape(6.5, 445)
    # A single felt hammer tails off into two bowed bass pitches drifting apart.
    note(held,.08,45,.56,.38,"felt",-.16)
    t = np.arange(int(RATE * 4.3))/RATE
    env = np.sin(np.pi*t/4.3)**2 * np.exp(-t*.45)
    for side,offset in [(-.5,-.16),(.5,.23)]:
        phase=TAU*((73.4+offset)*t-.51*t*t)
        held.lay(.44, env*(.55*np.sin(phase)+.15*np.sin(phase*2.003)),side)
    impact(held,4.7,[(230,.15,.4),(454,.045,.14)],.75,.12,.2)
    held.export("held_breath", .088)


if __name__ == "__main__":
    props()
    score()
