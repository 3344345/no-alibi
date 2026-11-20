"""Render the three original backstage cues for 《借我一张脸》. Requires ffmpeg."""
import array
import math
from pathlib import Path
import random
import subprocess

RATE = 32000
DEST = Path(__file__).resolve().parents[1] / "frontend/public/chronicle/sound"
TAU = 2 * math.pi


def render(name, strikes):
    rng = random.Random(1919)
    output = array.array("f", [0.0]) * (RATE * 5 * 2)
    for at, instrument, hz, gain, pan in strikes:
        gong = instrument == "gong"
        decay = 1.85 if gong else 0.12
        taps = [(0, 1.0, pan), (.052, .13, -pan), (.102, .06, 0)]
        for n in range(round(RATE * (2.5 if gong else .48))):
            t = n / RATE
            env = math.exp(-t * (2.6 if gong else 28)) * (1 - math.exp(-t * 660))
            # A small suspended brass gong has beating, inharmonic modes. The
            # much shorter bamboo and stage boards excite just two low modes.
            partials = [(1, .72), (1.39, .22), (1.97, .15), (2.48, .12), (3.57, .065)] if gong else [(1, .6), (2.73, .34)]
            bend = .024 * hz * (1 - math.exp(-t * 4)) if gong else 0
            y = env * sum(g * math.exp(-t / decay * (mult - 1)) *
                          math.sin(TAU * mult * (hz * t + bend)) for mult, g in partials)
            if gong:
                y *= .9 + .1 * math.cos(TAU * 4.3 * t)
            y += rng.uniform(-1, 1) * math.exp(-t * 105) * .09
            for delay, mix, direction in taps:
                i = 2 * (round((at + delay) * RATE) + n)
                if i < len(output):
                    output[i] += y * gain * mix * math.sqrt((1 - direction) / 2)
                    output[i + 1] += y * gain * mix * math.sqrt((1 + direction) / 2)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-f", "f32le", "-ar", str(RATE),
                    "-ac", "2", "-i", "-", "-codec:a", "libmp3lame", "-b:a", "112k",
                    str(DEST / ("booth_" + name + ".mp3"))], input=output.tobytes(), check=True)


if __name__ == "__main__":
    rod = (0.05, "wood", 580, .22, -.58)
    render("pull", [rod, (.26, "wood", 330, .18, .4), (.48, "wood", 325, .20, .42),
                    (.58, "gong", 348, .52, -.22), (1.48, "wood", 184, .26, .8)])
    render("double", [rod, (.31, "wood", 550, .24, .57), (.48, "wood", 267, .30, -.12),
                      (.82, "wood", 494, .20, .43), (1.10, "gong", 465, .36, -.55),
                      (1.63, "wood", 470, .22, .5), (1.82, "wood", 270, .18, -.18)])
    render("walk", [rod, (.32, "wood", 314, .27, -.12), (.7, "wood", 237, .18, .46),
                    (1.44, "gong", 285, .34, -.65), (1.90, "wood", 165, .10, .87)])
