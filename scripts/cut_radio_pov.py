"""Replace the night-radio master’s bookend shots while keeping its original audio.

Pass a 21-second release master and an output path. The reel and chair inserts
can also be rebuilt into a fresh master using their original production files.
The two game-owned POV plates are in frontend/public/viewer/.
"""

import argparse
import math
import subprocess
import tempfile
from pathlib import Path

from PIL import Image, ImageEnhance, ImageOps

WIDTH, HEIGHT, FPS = 1280, 720, 24
VIEWER = Path(__file__).resolve().parents[1] / "frontend/public/viewer"


def smooth(v):
    v = min(1.0, max(0.0, v))
    return v * v * (3 - 2 * v)


def deformed(image, fields):
    """Move local clusters of fingers or the ear cup; all plate edges stay put."""

    def source(x, y):
        dx, dy = 0.0, 0.0
        for cx, cy, rx, ry, displacement_x, displacement_y in fields:
            weight = math.exp(
                -(((x / WIDTH - cx) / rx) ** 2) - ((y / HEIGHT - cy) / ry) ** 2
            )
            dx += displacement_x * weight
            dy += displacement_y * weight
        return x - dx, y - dy

    mesh = []
    for y in range(0, HEIGHT, 40):
        y2 = min(y + 40, HEIGHT)
        for x in range(0, WIDTH, 40):
            x2 = min(x + 40, WIDTH)
            quad = (*source(x, y), *source(x, y2), *source(x2, y2), *source(x2, y))
            mesh.append(((x, y, x2, y2), quad))
    return image.transform(
        image.size, Image.Transform.MESH, mesh, Image.Resampling.BILINEAR
    )


def render(name, count, output):
    opening = name == "radio-seat"
    image = ImageOps.fit(
        Image.open(VIEWER / (name + ".webp")).convert("RGB"), (WIDTH, HEIGHT)
    )
    cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y",
        "-f",
        "rawvideo",
        "-pix_fmt",
        "rgb24",
        "-s",
        f"{WIDTH}x{HEIGHT}",
        "-r",
        str(FPS),
        "-i",
        "-",
        "-an",
        "-c:v",
        "libx264",
        "-threads",
        "3",
        "-preset",
        "fast",
        "-crf",
        "17",
        "-pix_fmt",
        "yuv420p",
        str(output),
    ]
    proc = subprocess.Popen(cmd, stdin=subprocess.PIPE)
    for i in range(count):
        t = i / FPS
        if opening:
            reach = smooth((t - 0.6) / 1.12)
            gaze = smooth((t - 2.65) / 1.65)
            fields = [
                (0.792, 0.245, 0.076, 0.144, 4.4 * reach, -5.8 * reach),
                (
                    0.682,
                    0.21,
                    0.117,
                    0.197,
                    0.9 * math.sin(t * 1.3),
                    1.75 * math.sin(t * 1.3),
                ),
                (
                    0.74,
                    0.846,
                    0.091,
                    0.13,
                    -2.5 * smooth(t / 2.8),
                    2.1 * smooth(t / 2.8),
                ),
            ]
            zoom = 0.023 + 0.015 * gaze
            anchor_x = 0.70 - 0.57 * gaze
            anchor_y = 0.37 + 0.12 * gaze
            exposure = 0.19 + 0.81 * smooth((i + 1) / 9)
        else:
            settle = smooth((t - 0.25) / 0.83)
            release = smooth((t - 2.45) / 1.32)
            finger = settle * (1 - release * 0.62)
            fields = [
                (0.644, 0.603, 0.055, 0.073, 1.4 * finger, 5.7 * finger),
                (0.735, 0.706, 0.111, 0.118, 1.8 * finger, 2.65 * finger),
                (0.251, 0.524, 0.070, 0.105, -1.6 * settle, 1.5 * settle),
            ]
            zoom = 0.021 + 0.015 * smooth(t / 4)
            anchor_x = 0.48 + 0.13 * settle
            anchor_y = 0.56 + 0.10 * settle
            exposure = 1 - smooth((t - 3.78) / 0.64)
        frame = deformed(image, fields)
        crop_x, crop_y = WIDTH * zoom, HEIGHT * zoom
        left = crop_x * anchor_x
        top = crop_y * anchor_y
        frame = frame.resize(
            (WIDTH, HEIGHT),
            Image.Resampling.BICUBIC,
            box=(left, top, WIDTH - crop_x + left, HEIGHT - crop_y + top),
        )
        if exposure < 1.0:
            frame = ImageEnhance.Brightness(frame).enhance(exposure)
        proc.stdin.write(frame.tobytes())
    proc.stdin.close()
    if proc.wait():
        raise RuntimeError("Failed rendering " + name)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("previous", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if not args.previous.is_file():
        parser.error("Previous release master is missing")
    with tempfile.TemporaryDirectory(dir=args.output.resolve().parent) as tmp:
        temp = Path(tmp)
        a = temp / "open.mp4"
        b = temp / "coda.mp4"
        out = temp / "cut.mp4"
        render("radio-seat", 108, a)
        render("radio-keys", 132, b)
        # Frames 108 through 371 are exactly the authored six-second tape close-up
        # and five-second chair insert. Stream-copy the whole original soundtrack.
        vf = "[0:v]setpts=PTS-STARTPTS,setsar=1[a];[1:v]trim=start_frame=108:end_frame=372,setpts=PTS-STARTPTS,setsar=1[m];[2:v]setpts=PTS-STARTPTS,setsar=1[b];[a][m][b]concat=n=3:v=1:a=0[v]"
        subprocess.run(
            [
                "ffmpeg",
                "-y",
                "-hide_banner",
                "-loglevel",
                "error",
                "-i",
                str(a),
                "-i",
                str(args.previous),
                "-i",
                str(b),
                "-filter_complex",
                vf,
                "-map",
                "[v]",
                "-map",
                "1:a:0",
                "-c:v",
                "libx264",
                "-threads",
                "3",
                "-preset",
                "fast",
                "-crf",
                "17",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "copy",
                "-movflags",
                "+faststart",
                str(out),
            ],
            check=True,
        )
        out.replace(args.output)


if __name__ == "__main__":
    main()
