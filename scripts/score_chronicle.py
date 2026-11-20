"""Render the game's original stereo score and foley. Authoring only: NumPy and ffmpeg."""

import argparse
import subprocess
from pathlib import Path

import numpy as np

RATE = 32000
TAU = 2 * np.pi
TARGET = Path(__file__).resolve().parents[1] / "frontend/public/chronicle/sound"

# Each entry sets the onset (beats), pitch (MIDI), duration and dynamic of a phrase.
# The held breath after the opening three notes returns, inverted, in the last movement.
MOVEMENTS = {
    "question": (
        61,
        [50, 48, 46, 45, 43, 46, 48, 50],
        [
            [(0, 62, 1.3, 0.6), (1.5, 65, 0.7, 0.44), (2.6, 64, 2, 0.52)],
            [(1.3, 60, 1.6, 0.40), (3.2, 57, 1, 0.38)],
            [],
            [(0, 57, 1.2, 0.48), (1.4, 62, 1.7, 0.46), (3.4, 60, 0.7, 0.30)],
            [(1, 55, 3, 0.50)],
            [(2.2, 65, 1.8, 0.35)],
            [(0, 64, 1, 0.45), (1.3, 60, 1.1, 0.41), (3.1, 57, 1.3, 0.40)],
            [(1, 62, 2.5, 0.56)],
        ],
    ),
    "vigil": (
        48,
        [38, 38, 41, 39, 36, 41, 38, 38],
        [
            [],
            [(1, 57, 2.4, 0.42)],
            [(0.3, 60, 2, 0.48), (2.9, 58, 1.3, 0.39)],
            [],
            [(2.7, 55, 1.3, 0.32)],
            [(0, 57, 3.7, 0.44)],
            [(1, 53, 2, 0.30)],
            [(0, 52, 2.2, 0.27)],
        ],
    ),
    "afterlight": (
        69,
        [50, 53, 48, 46, 43, 45, 46, 50],
        [
            [(0, 69, 0.9, 0.42), (1.2, 65, 1.2, 0.52), (2.7, 67, 1.8, 0.5)],
            [(2, 60, 1.9, 0.4)],
            [(0.5, 67, 1, 0.4), (1.9, 69, 1.6, 0.46)],
            [(1.2, 65, 1.4, 0.55), (3, 62, 1, 0.44)],
            [(0, 62, 2.5, 0.42)],
            [(2, 64, 1.8, 0.40)],
            [(0.1, 65, 1.3, 0.42), (2.4, 60, 0.8, 0.3)],
            [(0, 62, 3.1, 0.45)],
        ],
    ),
}


# The second half changes register and sparsity; short conversations need not wait
# for a cadence and long reads do not replay the same phrase every half minute.
REPLIES = {
    "question": (
        [55, 53, 52, 48, 46, 43, 45, 50],
        [
            [(1.4, 67, 1.4, 0.52), (3.2, 69, 0.75, 0.33)],
            [(0, 65, 1, 0.51), (1.6, 64, 1, 0.44), (2.8, 60, 1.4, 0.4)],
            [],
            [(1, 60, 1.3, 0.38), (3, 55, 1, 0.4)],
            [(0, 58, 1.9, 0.48), (2.8, 60, 1, 0.36)],
            [],
            [(1.3, 57, 1.2, 0.41), (2.7, 61, 1.2, 0.36)],
            [(0, 62, 2.1, 0.42)],
        ],
    ),
    "vigil": (
        [41, 43, 46, 46, 41, 39, 38, 38],
        [
            [(1.2, 53, 2, 0.35)],
            [(1.6, 55, 2, 0.33)],
            [(0, 58, 2.5, 0.41), (3, 60, 0.9, 0.26)],
            [(0.6, 57, 2.2, 0.37)],
            [],
            [(2.6, 51, 0.9, 0.27)],
            [(0, 50, 2.7, 0.40)],
            [],
        ],
    ),
    "afterlight": (
        [55, 50, 53, 48, 46, 43, 45, 50],
        [
            [(0, 67, 1.15, 0.5), (1.7, 70, 1.9, 0.46)],
            [(0.2, 69, 1.25, 0.49), (2, 65, 1.3, 0.41)],
            [(2.3, 60, 1.3, 0.4)],
            [(0, 64, 2, 0.44)],
            [(0, 65, 0.8, 0.43), (1.1, 62, 1.4, 0.40), (3, 60, 0.9, 0.32)],
            [(1.2, 55, 2.4, 0.38)],
            [(1.7, 57, 1.3, 0.34)],
            [(0, 62, 2.7, 0.44)],
        ],
    ),
}


class Tape:
    def __init__(self, duration, seed):
        self.frames = int(RATE * duration)
        self.signal = np.zeros((self.frames, 2), dtype=np.float32)
        self.rng = np.random.default_rng(seed)

    def lay(self, seconds, wave, pan=0):
        # Fold release tails and room reflections over the splice.
        n = int(seconds * RATE) % self.frames
        for channel, gain in enumerate(
            (np.cos((pan + 1) * np.pi / 4), np.sin((pan + 1) * np.pi / 4))
        ):
            samples = wave * gain
            first = min(len(samples), self.frames - n)
            self.signal[n : n + first, channel] += samples[:first]
            self.signal[: len(samples) - first, channel] += samples[first:]

    def air(self, seconds, color):
        t = np.arange(int(seconds * RATE)) / RATE
        noise = self.rng.standard_normal(len(t))
        bins = np.fft.rfftfreq(len(t), 1 / RATE)
        band = np.interp(bins, *zip(*color))
        wave = np.fft.irfft(np.fft.rfft(noise) * band, n=len(t))
        return wave / (np.sqrt(np.mean(wave**2)) + 1e-10)

    def export(self, name, rms):
        # Two soft early reflections and a diffuse tail; no borrowed recordings.
        direct = self.signal.copy()
        for lag, gain in (
            (0.037, 0.13),
            (0.061, 0.10),
            (0.091, 0.08),
            (0.127, 0.07),
            (0.181, 0.05),
            (0.237, 0.038),
            (0.311, 0.025),
            (0.419, 0.016),
        ):
            self.signal += np.roll(direct[:, ::-1], int(lag * RATE), axis=0) * gain
        self.signal *= min(
            rms / max(0.00001, np.sqrt(np.mean(self.signal**2))),
            0.65 / np.max(np.abs(self.signal)),
        )
        TARGET.mkdir(parents=True, exist_ok=True)
        subprocess.run(
            [
                "ffmpeg",
                "-loglevel",
                "error",
                "-y",
                "-f",
                "f32le",
                "-ar",
                str(RATE),
                "-ac",
                "2",
                "-i",
                "pipe:0",
                "-codec:a",
                "libmp3lame",
                "-b:a",
                "128k",
                str(TARGET / (name + ".mp3")),
            ],
            input=self.signal.astype("<f4").tobytes(),
            check=True,
        )


def note(tape, at, midi, length, dynamic, voice, pan):
    release = 1.7 if voice == "felt" else 0.85
    t = np.arange(int((length + release) * RATE)) / RATE
    hz = 440 * 2 ** ((midi - 69) / 12)
    decay = np.exp(-np.maximum(t - length, 0) / (release / 7))
    if voice == "felt":
        wave = np.zeros(len(t))
        for h, strength in enumerate((1, 0.37, 0.15, 0.12, 0.054, 0.045), 1):
            phase = TAU * hz * h * np.sqrt(1 + 0.00017 * h * h) * t
            # An imperfect unison, with the upper partials dying away first.
            wave += (
                strength
                * np.exp(-t * (0.56 + 0.34 * h))
                * (np.sin(phase) + 0.38 * np.sin(phase * 1.0012))
            )
        wave *= 1 - np.exp(-t / 0.008)
    else:
        vibrato = 0.09 if voice == "reed" else 0.16
        phase = TAU * hz * t + vibrato * np.sin(TAU * (4.6 + 0.15 * pan) * t) * (
            1 - np.exp(-t / 0.45)
        )
        strengths = (
            (1, 0.14, 0.26, 0.07, 0.11)
            if voice == "reed"
            else (1, 0.4, 0.21, 0.13, 0.07, 0.055, 0.035)
        )
        wave = sum(v * np.sin(i * phase) for i, v in enumerate(strengths, 1))
        wave *= (1 - np.exp(-t / (0.36 if voice == "reed" else 0.8))) * (
            1 + 0.054 * np.sin(TAU * 0.63 * t)
        )
    tape.lay(at, wave * decay * dynamic, pan)


def movement(name):
    tempo, bass, phrases = MOVEMENTS[name]
    beat = 60 / tempo
    answer_bass, answer_melody = REPLIES[name]
    bass = bass + answer_bass
    phrases = phrases + answer_melody
    tape = Tape(len(bass) * 4 * beat, 391)
    for bar, (root, melody) in enumerate(zip(bass, phrases)):
        t = bar * 4 * beat
        note(tape, t, root - 12, beat * 3.2, 0.20, "bow", -0.22)
        if name == "question":
            for when, interval, level in (
                (0.5, 7, 0.22),
                (2, 12, 0.13),
                (3.4, 7, 0.10),
            ):
                note(
                    tape,
                    t + when * beat,
                    root + interval,
                    beat * 0.8,
                    level,
                    "felt",
                    0.32,
                )
        elif name == "afterlight":
            for when, interval, level in (
                (0.6, 7, 0.24),
                (1.6, 12, 0.22),
                (3.5, 7, 0.10),
            ):
                note(
                    tape,
                    t + when * beat,
                    root + interval,
                    beat * 1.2,
                    level,
                    "felt",
                    -0.34,
                )
        else:
            note(tape, t + beat * 0.4, root + 7, beat * 2.1, 0.14, "bow", 0.36)
        for when, pitch, duration, level in melody:
            voice = "reed" if name == "afterlight" else "felt"
            note(tape, t + when * beat, pitch, beat * duration, level, voice, 0.12)
    tape.export(name, 0.115)


def impact(tape, at, partials, duration, level, pan):
    t = np.arange(int(RATE * duration)) / RATE
    wave = sum(
        np.exp(-t / decay) * np.sin(TAU * pitch * t) * gain
        for pitch, decay, gain in partials
    )
    tape.lay(at, level * wave * (1 - np.exp(-t / 0.0009)), pan)


def environment(name, seed):
    length = 43
    tape = Tape(length, seed)
    for side in (-0.65, 0.65):
        air = tape.air(
            length,
            [
                (0, 0),
                (45, 0.18),
                (165, 1),
                (350, 0.63),
                (800, 0.15),
                (4200, 0.025),
                (7600, 0),
            ],
        )
        tape.lay(0, air * 0.045, side)
    if name == "exchange":
        # Plug collars, two double rings on a neighbouring switchboard and spring return.
        for at in (4.1, 4.39, 11.7, 18.9, 26.8, 27.3, 38.2):
            impact(
                tape,
                at,
                [(218, 0.035, 1), (783, 0.044, 0.42), (2411, 0.016, 0.24)],
                0.3,
                0.29,
                -0.35,
            )
        for at in (7, 7.44, 32.5, 32.94):
            for n in range(6):
                impact(
                    tape,
                    at + 0.049 * n,
                    [(1032, 0.060, 1), (1382, 0.055, 0.5), (2725, 0.038, 0.15)],
                    0.28,
                    0.10,
                    0.68,
                )
    elif name == "projector":
        # Film gate chatter drifts minutely against the low motor every revolution.
        for i in range(24 * length):
            at = i / 24 + 0.0009 * np.sin(i * 0.19)
            impact(
                tape,
                at,
                [(196, 0.008, 1), (526, 0.003, 0.6), (1607, 0.003, 0.26)],
                0.035,
                (0.046 if i % 4 else 0.069) * (1 + 0.1 * np.sin(i * 0.037)),
                0.36,
            )
        t = np.arange(tape.frames) / RATE
        tape.lay(
            0,
            0.041 * np.sin(TAU * 72 * t + 0.09 * np.sin(TAU * t))
            + 0.023 * np.sin(TAU * 144 * t),
            0.3,
        )
    elif name == "platform":
        # Pneumatic doors and an engine passing from curbside to down the block.
        for at, dur, pan in (
            (6.7, 1.4, -0.53),
            (20.3, 0.85, 0.45),
            (34.1, 1.15, -0.24),
        ):
            t = np.arange(int(dur * RATE)) / RATE
            hiss = tape.air(
                dur, [(0, 0), (350, 0.04), (1550, 1), (3400, 0.22), (6500, 0)]
            )
            tape.lay(at, 0.18 * hiss * np.sin(np.pi * t / dur) ** 2, pan)
            impact(
                tape,
                at + dur,
                [(76, 0.080, 1), (188, 0.046, 0.65), (1026, 0.012, 0.25)],
                0.65,
                0.8,
                pan,
            )
        t = np.arange(9 * RATE) / RATE
        phase = TAU * (62 * t + 1.23 * t * t + 2.5 * np.sin(0.54 * t))
        passby = (
            np.sin(phase) + 0.32 * np.sin(2 * phase) + 0.20 * np.sin(3 * phase)
        ) * np.sin(np.pi * t / 9) ** 2
        tape.lay(12, 0.12 * passby * (1 - t / 9), -0.7)
        tape.lay(12.12, 0.12 * passby * t / 9, 0.7)
    elif name == "courtyard":
        # A sparrow lands twice; the next phrase answers from the far wall.
        for at, pan in ((4.3, -0.50), (6.1, -0.46), (25.6, 0.62), (36.3, -0.7)):
            for offset, dur, freq in (
                (0, 0.12, 2650),
                (0.23, 0.16, 3100),
                (0.55, 0.09, 2900),
            ):
                t = np.arange(int(RATE * dur)) / RATE
                phase = TAU * (freq * t + 4800 * t * t + 0.38 * np.sin(38 * t))
                tape.lay(
                    at + offset,
                    0.083 * np.sin(phase) * np.sin(np.pi * t / dur) ** 2,
                    pan,
                )
    elif name == "room":
        for at, pan in ((7.4, -0.66), (15.2, 0.23), (30.7, -0.41)):
            dur = 0.78
            t = np.arange(int(RATE * dur)) / RATE
            grain = tape.air(
                dur,
                [(0, 0), (440, 0.22), (1110, 0.85), (2300, 1), (4900, 0.15), (8000, 0)],
            )
            tape.lay(
                at,
                0.09
                * grain
                * np.sin(np.pi * t / dur) ** 2
                * (0.65 + 0.35 * np.sin(28 * t)),
                pan,
            )
    tape.export(name, 0.055)


def switchboard_foley(name):
    # A caller's location heard through the handset. No voices or field recordings.
    tape = Tape(2.7, 1989)
    if name == "line_son":
        rim = [(760, .11, .7), (1750, .076, 1), (2190, .05, .3)]
        for at, level in [(0.12, .15), (.39, .12), (.57, .10), (.69, .086), (.77, .067), (.82, .052)]:
            impact(tape, at, rim, .36, level, -.08)
        impact(tape, .98, [(230, .09, 1), (386, .16, .6), (1470, .08, .34)], .63, .35, .12)
    elif name == "line_baker":
        blade = [(225, .095, 1), (460, .12, .55), (777, .09, .32), (1330, .047, .25)]
        for at, level in ((.24, .42), (.64, .30)):
            impact(tape, at, blade, .6, level, .13)
        time = np.arange(int(.43 * RATE)) / RATE
        scrape = tape.air(.43, [(0, 0), (460, .18), (1180, .6), (2800, 1), (5500, 0)])
        tape.lay(1.03, scrape * np.sin(np.pi * time / .43) ** 3 * .013, .11)
    else:
        bell = [(689, .36, .55), (1490, .30, 1), (1799, .21, .59), (2960, .17, .19)]
        impact(tape, .16, [(f, tail * .26, gain) for f, tail, gain in bell], .35, .25, -.08)
        impact(tape, .56, bell, 1.25, .36, -.08)
        impact(tape, 1.12, bell, 1.14, .25, -.1)
    tape.export(name, .048)


def kitchen_waltz():
    # A family recording heard on-air in act two. Her left hand misses the bass,
    # twice; the child finds the beat again while the bellows keep moving.
    tape = Tape(13.8, 423)
    beat = 0.48
    melody = [
        (0, 62, 0.85),
        (1, 65, 0.73),
        (2, 69, 0.72),
        (3, 70, 2),
        (5.2, 69, 0.53),
        (6, 67, 0.85),
        (7, 64, 0.67),
        (8, 62, 0.68),
        (9, 60, 1.8),
        (11, 62, 0.60),
        (12, 65, 0.75),
        (13, 69, 0.75),
        (14, 72, 0.70),
        (15, 69, 1.7),
        (17, 65, 0.72),
        (18, 64, 1.8),
        (20, 60, 0.72),
        (21, 62, 2.4),
    ]
    for pulse, pitch, length in melody:
        note(tape, 0.35 + pulse * beat, pitch, length * beat, 0.46, "reed", -0.12)
    for bar, bass in enumerate((50, 46, 48, 45, 50, 46, 45, 50)):
        for offset, interval in ((0, 0), (1, 7), (2, 12)):
            accidental = -1 if (bar, offset) in ((1, 1), (3, 2)) else 0
            note(
                tape,
                0.31 + (bar * 3 + offset) * beat,
                bass + interval + accidental,
                0.22,
                0.24,
                "reed",
                -0.27,
            )
    for pulse in (4.3, 5.5, 7.2, 8.1, 10.1, 11.04, 13, 14, 16, 17, 19, 20, 22):
        clap = tape.air(
            0.085, [(0, 0), (650, 0.16), (1250, 1), (2400, 0.75), (6700, 0)]
        )
        t = np.arange(len(clap)) / RATE
        tape.lay(
            0.33 + pulse * beat,
            0.22 * clap * (1 - np.exp(-t / 0.002)) * np.exp(-t / 0.018),
            0.48,
        )
    tape.export("kitchen_waltz", 0.15)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("tracks", nargs="*")
    selected = parser.parse_args().tracks
    if not selected or "kitchen_waltz" in selected:
        kitchen_waltz()
    for title in ("line_son", "line_baker", "line_conductor"):
        if not selected or title in selected:
            switchboard_foley(title)
    for title in MOVEMENTS:
        if not selected or title in selected:
            movement(title)
    for index, title in enumerate(
        ("room", "exchange", "platform", "projector", "courtyard")
    ):
        if not selected or title in selected:
            environment(title, 1919 + index)
