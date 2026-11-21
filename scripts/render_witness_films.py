"""Render the 25 original historical chapter prologues, their foley, and captions.

Run with Python 3 + Pillow + NumPy; FFmpeg/ffprobe must be on PATH. By default
the published picture and sound are rendered together. Pass chapter slugs to
render an individual reel. JZS_MOTION_FONT may name a Chinese typeface.
"""

import math
import os
import subprocess
import sys
import tempfile
import wave
import zlib
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageDraw, ImageFilter, ImageFont, ImageOps

ROOT = Path(__file__).resolve().parents[1]
ART = ROOT / "frontend/public/chronicle"
OUT = ROOT / "frontend/public/motion"
W, H, FPS, SECONDS = 960, 540, 24, 7
# Each sequence goes from its chapter's painted setting to the object which
# becomes the first playable dilemma. Cues below are descriptions, never quotes.
# slug, alternate painting, illumination, first beat, second beat, foley
SHOTS = [
    (
        "tan_sitong",
        None,
        "paper",
        "会馆窗下，旧封皮压着半页手稿。",
        "折痕摊开。纸角盖住了信封上收信人的位置。",
        "fold",
    ),
    (
        "zhan_tianyou",
        None,
        "iron",
        "青龙桥外，铁轨朝两个方向分开。",
        "扳杆越过中点。指示牌转向另一股道。",
        "switch",
    ),
    (
        "sun_yatsen",
        None,
        "paper",
        "桌上还空着一格，铜印悬在纸面上。",
        "印落下去。抬起来时，纸上留下方方正正的一圈红。",
        "seal",
    ),
    (
        "chen_duxiu",
        None,
        "paper",
        "游艺场的灯还亮着，一卷传单摆上桌。",
        "纸卷往前走了半圈。一支铅笔挡在信封前。",
        "roll",
    ),
    (
        "gu_zhenghong",
        None,
        "iron",
        "夜班的人到了，纱锭还在转。",
        "皮带松了。最后一根棉线落下来。",
        "spool",
    ),
    (
        "shen_junru",
        None,
        "wood",
        "探视的一排座位，有一处空隙。",
        "帽子从膝头放上空椅。椅脚在地上响了一声。",
        "chair",
    ),
    (
        "zhang_xueliang",
        "still_xian",
        "wood",
        "西安的门边，提箱上扣着一根皮带。",
        "铜扣松开，箱盖起了一线。箱子仍在门边。",
        "latch",
    ),
    (
        "minnie_vautrin",
        None,
        "cloth",
        "教室地板上的席子，隔着一道窄缝。",
        "一床铺盖向旁边摊开。两床之间刚好挤下一个枕头。",
        "cloth",
    ),
    (
        "chongqing_talks",
        None,
        "wood",
        "桂园桌旁，三把椅子朝着三个方向。",
        "空椅往里挪了半尺。三只茶盏终于能围成一圈。",
        "cup",
    ),
    (
        "shanghai_prices",
        None,
        "wood",
        "米店门边，价牌还在轻轻晃。",
        "小牌绕轴翻面，背面剩着两个粉笔字。",
        "board",
    ),
    (
        "liu_qingshan",
        "river_grain",
        "wood",
        "伙房的碗沿还冒着热气。",
        "碗往边上挪。一叠藏着的钱露出了一角。",
        "bowl",
    ),
    (
        "lushan_peng",
        None,
        "wood",
        "木升歪向桌边，里面看起来还盛着粮。",
        "谷粒落进掌宽的小圈里。末了，掉出几片空壳。",
        "grain",
    ),
    (
        "lin_zhao",
        None,
        "paper",
        "窗边的信封张着口，两页稿子叠在一起。",
        "一页慢慢滑进去，另一页仍留在桌上。",
        "slip",
    ),
    (
        "bian",
        None,
        "cloth",
        "一副折好的眼镜，搁在手帕的折角。",
        "一侧镜腿弹开，镜片上晃过窗框的一线白光。",
        "glasses",
    ),
    (
        "entrance_exam",
        None,
        "iron",
        "修理台上，收音机的刻度只亮了一半。",
        "指针跨过两格。沙沙声里冒出一小段干净的音。",
        "radio",
    ),
    (
        "hu_fuming",
        None,
        "iron",
        "排字架上还差一枚铅字。",
        "小铅块落进空位，挤紧的一行字碰在一起。",
        "type",
    ),
    (
        "xiaogang",
        "household_field",
        "paper",
        "灯下摊开的纸，留着几处墨迹。",
        "又一枚红手印压进纸纤维。灯焰在指纹旁晃了晃。",
        "print",
    ),
    (
        "yuan_geng",
        None,
        "iron",
        "最后一车进了地秤，秤杆翘起来。",
        "秤砣挪过两道刻线。杆头终于平了。",
        "scale",
    ),
    (
        "deng_xiaoping",
        None,
        "iron",
        "便笺边放着长途电话的计时器。",
        "秒针又走过一格。听筒那头的人还在等。",
        "timer",
    ),
    (
        "southern_tour",
        None,
        "iron",
        "国贸大厦的楼层窗停在十二。",
        "数字向上翻。电梯门将要开时，报社的稿纸还留着空行。",
        "lift",
    ),
    (
        "shang_aiyun",
        None,
        "cloth",
        "门槛里摆着一双鞋。",
        "门外有脚步，影子经过。门槛里那双鞋没有动。",
        "shoes",
    ),
    (
        "gao",
        "still_ridge",
        "earth",
        "田埂上，管口对着一小块干土。",
        "一滴水掉下来。湿痕很快收在土缝里。",
        "drop",
    ),
    (
        "deng",
        None,
        "earth",
        "操场边，丈量的卷尺才铺开。",
        "卷尺伸到白线，围绳还横在跑道上。",
        "measure",
    ),
    (
        "xu_zhiyong",
        None,
        "paper",
        "摊开的纸旁，有三支笔。",
        "第三支笔靠到纸边，与前两支排在一起。",
        "pens",
    ),
    (
        "jiang_yanyong",
        None,
        "iron",
        "旧科室的电话，拨号盘刚被转过。",
        "拨号盘一格一格退回，第一声回铃才响起。",
        "dial",
    ),
]
INK = (44, 43, 33)
EDGE = (104, 86, 53)
BRASS = (171, 142, 79)
GOLD = (209, 180, 112)
PAPER = (189, 168, 120)
PALE = (221, 203, 159)
RED = (130, 60, 41)
DARK = (24, 27, 24)


def smooth(x):
    x = min(1, max(0, x))
    return x * x * (3 - 2 * x)


def col(a, b, f):
    return tuple(round(x * (1 - f) + y * f) for x, y in zip(a, b))


@lru_cache(None)
def face(size):
    for path in (
        os.environ.get("JZS_MOTION_FONT"),
        "/System/Library/Fonts/Supplemental/Songti.ttc",
        "/usr/share/fonts/opentype/noto/NotoSerifCJK-Regular.ttc",
        "C:/Windows/Fonts/simsun.ttc",
    ):
        if path and Path(path).is_file():
            return ImageFont.truetype(path, size)
    raise RuntimeError("Set JZS_MOTION_FONT to a font containing Chinese characters.")


def label(d, xy, s, size=24, c=INK):
    d.text(xy, s, font=face(size), fill=c)


def line(d, pts, c=INK, w=3):
    d.line(pts, fill=c, width=w, joint="curve")


def ellipse(d, x, y, rx, ry, c, o=None, w=1):
    d.ellipse((x - rx, y - ry, x + rx, y + ry), fill=c, outline=o, width=w)


def box(d, x, y, w, h, c, o=None, r=0):
    d.rounded_rectangle((x, y, x + w, y + h), radius=r, fill=c, outline=o, width=2)


def shadow(d, x, y, rx, ry):
    ellipse(d, x + 4, y + 8, rx, ry, (23, 24, 20))


def sheet(d, x, y, w, h, ruled=False):
    d.polygon(
        [(x + 3, y + 7), (x + w + 6, y + 3), (x + w + 2, y + h + 7), (x, y + h + 10)],
        fill=(51, 46, 34),
    )
    d.polygon(
        [(x, y), (x + w, y - 3), (x + w - 2, y + h), (x - 4, y + h + 2)],
        fill=PAPER,
        outline=(139, 119, 80),
    )
    line(d, [(x + 2, y + 3), (x + w - 4, y + 1)], PALE, 2)
    if ruled:
        for yy in range(25, int(h) - 8, 21):
            line(d, [(x + 15, y + yy), (x + w - 17, y + yy - 2)], (161, 135, 97), 1)


def envelope(d, x, y, w, h):
    sheet(d, x, y, w, h)
    line(
        d, [(x, y + 2), (x + w * 0.50, y + h * 0.67), (x + w, y - 2)], (126, 103, 67), 3
    )
    line(d, [(x + 2, y + h), (x + w * 0.38, y + h * 0.53)], (153, 129, 87), 2)
    line(d, [(x + w - 2, y + h), (x + w * 0.64, y + h * 0.53)], (153, 129, 87), 2)


def screw(d, x, y):
    ellipse(d, x + 1, y + 1, 6, 5, (29, 30, 26))
    ellipse(d, x, y, 5, 5, (153, 137, 102))
    line(d, [(x - 3, y + 2), (x + 3, y - 2)], (65, 64, 50), 1)


def chair(d, x, y, s):
    def p(dx, dy):
        return x + dx * s, y + dy * s

    for a, b in [
        ((-50, 13), (-59, 104)),
        ((42, 13), (57, 105)),
        ((-46, -86), (-34, 13)),
        ((48, -91), (53, 15)),
    ]:
        line(d, [p(*a), p(*b)], (37, 32, 23), max(2, int(13 * s)))
        line(d, [p(*a), p(*b)], (126, 91, 49), max(2, int(6 * s)))
    d.polygon(
        [p(-50, -87), p(47, -92), p(47, -57), p(-47, -51)],
        fill=(120, 88, 48),
        outline=(158, 121, 67),
    )
    d.polygon(
        [p(-51, 6), p(47, -3), p(66, 15), p(-43, 27)],
        fill=(166, 117, 60),
        outline=(199, 151, 82),
    )


def teacup(d, x, y, s=1):
    ellipse(d, x, y + 20 * s, 42 * s, 9 * s, (66, 60, 40))
    ellipse(
        d,
        x + 28 * s,
        y - 6 * s,
        17 * s,
        15 * s,
        None,
        (177, 170, 132),
        max(2, int(4 * s)),
    )
    d.polygon(
        [
            (x - 27 * s, y - 16 * s),
            (x + 29 * s, y - 16 * s),
            (x + 18 * s, y + 18 * s),
            (x - 17 * s, y + 18 * s),
        ],
        fill=(179, 177, 145),
    )
    ellipse(
        d,
        x,
        y - 15 * s,
        29 * s,
        9 * s,
        (75, 64, 42),
        (214, 208, 166),
        max(1, int(3 * s)),
    )


def pen(d, x, y, length, angle, c):
    ca, sa = math.cos(angle), math.sin(angle)

    def p(a, b):
        return (x + a * ca - b * sa, y + a * sa + b * ca)

    d.polygon(
        [p(0, 0), p(18, -6), p(length, -6), p(length, 6), p(18, 6)],
        fill=c,
        outline=(44, 42, 30),
    )
    d.polygon([p(0, 0), p(18, -6), p(18, 6)], fill=BRASS)
    line(d, [p(25, -3), p(length - 4, -3)], col(c, PALE, 0.35), 2)


def dial_ticks(d, x, y, r, steps, lo, hi):
    for k in range(steps):
        a = math.radians(lo + (hi - lo) * k / (steps - 1))
        line(
            d,
            [
                (
                    x + (r - (14 if k % 4 == 0 else 8)) * math.cos(a),
                    y + (r - (14 if k % 4 == 0 else 8)) * math.sin(a),
                ),
                (x + r * math.cos(a), y + r * math.sin(a)),
            ],
            INK,
            2,
        )


def action(d, kind, p, t):
    # p runs over the central action, t starts at the close-up. Co-ordinates
    # are physical objects on the set; shots have no embedded interface.
    if kind == "fold":
        envelope(d, 245, 267, 302, 141)
        label(d, (262, 361), "长沙寄", 22)
        sheet(d, 470, 220, 234, 152, True)
        label(d, (494, 236), "仁　学", 29)
        x = 450 + 139 * p
        d.polygon(
            [(420, 379), (x, 302), (580, 395)],
            fill=col((117, 94, 63), PALE, p),
            outline=(147, 125, 85),
        )
        pen(d, 655, 412, 140, -0.16, (73, 58, 40))
    elif kind == "switch":
        for y in range(197, 500, 36):
            line(d, [(245, y), (748, y - 32)], (78, 59, 38), 19)
        for x in (340, 453, 532, 640):
            line(d, [(x - 139, 524), (x + 83, 169)], (32, 34, 31), 14)
            line(d, [(x - 140, 524), (x + 82, 169)], (135, 134, 111), 5)
        box(d, 440, 358, 121, 49, (67, 66, 51), BRASS, 7)
        screw(d, 454, 385)
        screw(d, 548, 385)
        a = -2.45 + 1.72 * p
        x, y = 496 + 168 * math.cos(a), 372 + 168 * math.sin(a)
        line(d, [(496, 373), (x, y)], (27, 28, 24), 19)
        line(d, [(494, 370), (x, y)], (139, 117, 76), 9)
        ellipse(d, x, y, 17, 17, (154, 113, 61), BRASS, 2)
        ellipse(d, 496, 372, 14, 14, (115, 105, 76), GOLD, 3)
        box(d, 682, 215, 52, 81, (72, 73, 60), EDGE, 2)
        line(d, [(708, 220), (708, 280)], BRASS, 4)
        dx = max(3, 23 * abs(math.cos(math.pi * p)))
        box(d, 708 - dx, 231, 2 * dx, 22, (175, 138, 68) if p < 0.5 else (137, 67, 43))
    elif kind == "seal":
        sheet(d, 269, 261, 424, 165, True)
        label(d, (303, 285), "交　接", 35)
        down = smooth(p / 0.46)
        up = smooth((p - 0.53) / 0.38)
        y = 201 + 92 * down - 115 * up
        if p > 0.44:
            box(d, 526, 321, 81, 55, None, RED, 1)
            for a, b in [(534, 574), (550, 584), (562, 597)]:
                line(d, [(a, 331), (a, 362), (b, 362), (b, 335)], RED, 3)
        box(d, 514, y + 39, 107, 39, (73, 55, 35), BRASS, 3)
        box(d, 518, y + 36, 100, 12, (170, 139, 71), GOLD, 2)
        ellipse(d, 568, y + 32, 25, 13, (129, 103, 57), BRASS, 2)
        box(d, 552, y, 33, 35, (163, 122, 62), None, 7)
        ellipse(d, 569, y, 28, 15, (194, 155, 79), EDGE, 2)
    elif kind == "roll":
        envelope(d, 472, 270, 244, 140)
        label(d, (622, 361), "收", 25)
        width = 83 + 123 * p
        sheet(d, 284, 282, width, 110)
        for n in range(4):
            line(
                d, [(300, 306 + 17 * n), (281 + width, 305 + 17 * n)], (113, 97, 67), 2
            )
        x = 282 + width
        box(d, x - 20, 263, 40, 142, (178, 153, 102), EDGE, 9)
        for k in range(5):
            ellipse(
                d,
                x,
                268,
                18 - 3 * k,
                8 - k,
                (122 + 9 * k, 101 + 7 * k, 69 + 5 * k),
                EDGE,
                1,
            )
        pen(d, 488, 411, 167, -0.29, (121, 88, 48))
    elif kind == "spool":
        for i in range(3):
            x = 305 + 150 * i
            shadow(d, x, 423, 50, 13)
            box(d, x - 4, 208, 8, 210, (96, 80, 52))
            box(d, x - 33, 244, 66, 148, (173, 151, 106), BRASS, 8)
            for k in range(29):
                s = 3 * math.sin(t * 11 * (1 - p) + k * 0.5 + i)
                line(
                    d,
                    [(x - 31, 247 + k * 4.8), (x + 31, 247 + k * 4.8 + s)],
                    (115, 101, 74),
                    1,
                )
            for y in (237, 389):
                ellipse(d, x, y, 45, 11, (122, 91, 53), BRASS, 2)
        slack = 58 * p
        pts = [
            (605 - 218 * k / 40, 275 + 1.85 * k + slack * math.sin(k * math.pi / 40))
            for k in range(41)
        ]
        line(d, pts, (223, 203, 151), 2)
        line(d, [(235, 438), (693, 421)], (51, 45, 33), 14)
    elif kind == "chair":
        for x, s in [
            (162, 0.54),
            (258, 0.59),
            (359, 0.68),
            (474, 0.77),
            (604, 0.91),
            (767, 0.95),
        ]:
            chair(d, x, 309, s)
        dx = 604 + 20 * (1 - p)
        dy = 313 - 106 * (1 - p)
        ellipse(d, dx, dy, 57, 12, (76, 65, 43), EDGE, 2)
        box(d, dx - 32, dy - 26, 65, 27, (76, 64, 46), EDGE, 10)
        line(d, [(dx - 29, dy - 5), (dx + 30, dy - 5)], (37, 36, 27), 5)
    elif kind == "latch":
        shadow(d, 489, 436, 230, 19)
        box(d, 264, 300, 425, 133, (84, 59, 41), EDGE, 12)
        box(d, 266, 261 - 11 * p, 422, 54, (101, 73, 47), BRASS, 9)
        box(d, 421, 228 - 11 * p, 120, 34, None, (47, 38, 29), 10)
        for x in [304, 622]:
            box(d, x, 259 - 11 * p, 29, 161, (68, 49, 36), (128, 99, 64), 4)
            for y in range(271, 409, 10):
                line(d, [(x + 4, y), (x + 4, y + 3)], BRASS, 1)
        box(d, 463, 303, 50, 47, (41, 38, 29), BRASS, 4)
        r = 34
        a = -math.pi / 2 - 0.96 * p
        xx, yy = 489 + r * math.cos(a), 322 + r * math.sin(a)
        line(d, [(489, 321), (xx, yy)], BRASS, 13)
        ellipse(d, 489, 322, 5, 5, GOLD)
    elif kind == "cloth":
        for x in (188, 509):
            d.polygon(
                [(x, 266), (x + 185, 249), (x + 247, 426), (x + 24, 447)],
                fill=(118, 107, 74),
                outline=(152, 137, 90),
            )
            for k in range(23):
                line(
                    d,
                    [(x + 8 + 2 * k, 275 + 7 * k), (x + 188 + 2 * k, 258 + 7 * k)],
                    (86, 87, 61),
                    2,
                )
        x = 460 + 85 * p
        d.polygon(
            [(314, 290), (x, 274), (x + 37, 412), (338, 428)],
            fill=(142, 116, 81),
            outline=(183, 150, 103),
        )
        for k in range(6):
            line(
                d,
                [(327 + k * 2, 302 + k * 20), (x - 4 + k * 5, 289 + k * 20)],
                (112, 93, 68),
                1,
            )
        box(d, 466, 260, 79, 28, (184, 167, 124), EDGE, 8)
    elif kind == "cup":
        chair(d, 292, 242, 0.61)
        chair(d, 660, 236, 0.62)
        d.polygon(
            [(274, 271), (640, 250), (728, 377), (233, 396)],
            fill=(118, 78, 43),
            outline=BRASS,
        )
        teacup(d, 335, 300, 0.72)
        teacup(d, 598, 287, 0.68)
        teacup(d, 486, 343, 0.81)
        chair(d, 499 + 71 * (1 - p), 416 - 19 * p, 1.03)
    elif kind == "board":
        line(d, [(344, 243), (476, 168), (627, 243)], (149, 125, 81), 3)
        h = 144 * abs(math.cos(math.pi * p)) + 4
        box(d, 335, 307 - h / 2, 302, h, (47, 58, 49), BRASS, 5)
        if h > 36:
            s = "每升" if p < 0.5 else "卖光"
            label(d, (416, 307 - h * 0.32), s, int(h * 0.45), (208, 203, 167))
        ellipse(d, 477, 171, 6, 6, BRASS)
    elif kind == "bowl":
        for i in range(5):
            x = 451 + i * 2
            y = 337 - i * 3
            box(d, x, y, 171, 64, (156, 150, 109), EDGE, 2)
            box(d, x + 7, y + 7, 156, 50, None, (107, 113, 82), 1)
        x = 481 - 96 * p
        y = 309
        shadow(d, x + 8, y + 92, 122, 14)
        d.polygon(
            [
                (x - 113, y),
                (x + 113, y),
                (x + 73, y + 68),
                (x + 37, y + 85),
                (x - 43, y + 85),
                (x - 76, y + 62),
            ],
            fill=(153, 157, 132),
            outline=(199, 192, 153),
        )
        ellipse(d, x, y, 114, 30, (98, 77, 48), (212, 202, 165), 5)
        for dx in (-47, 6, 48):
            ellipse(d, x + dx, y - 2 + dx * 0.12, 29, 10, (169, 135, 78), BRASS)
        for k in range(3):
            pts = [
                (x - 45 + 45 * k + 3 * math.sin(y * 0.15 + t + k), y)
                for y in range(221 + k * 8, 283, 3)
            ]
            line(d, pts, (148, 149, 119), 1)
    elif kind == "grain":
        a = -0.24 - 0.32 * p
        cx, cy = 409, 292

        def q(x, y):
            return cx + x * math.cos(a) - y * math.sin(a), cy + x * math.sin(
                a
            ) + y * math.cos(a)

        d.polygon(
            [q(-121, -60), q(76, -58), q(109, -14), q(95, 66), q(-112, 78)],
            fill=(128, 88, 50),
            outline=BRASS,
        )
        d.polygon(
            [q(-121, -60), q(76, -58), q(109, -14), q(-88, 0)],
            fill=(50, 44, 31),
            outline=BRASS,
        )
        for k in range(19):
            line(d, [q(-101, 6 + k * 3), q(92, 1 + k * 2.7)], (106, 75, 45), 1)
        for k in range(33):
            f = smooth((p - k * 0.017) / 0.29)
            x = 482 + k * 1.7 + 49 * f
            y = 283 + (145 + (k % 4) * 3) * f
            ellipse(
                d,
                x,
                y,
                5 + (k % 3),
                2 if k > 24 else 3,
                (188, 153, 82) if k < 23 else (155, 137, 85),
            )
    elif kind == "slip":
        sheet(d, 257, 273, 192, 155, True)
        label(d, (281, 292), "诗稿", 26)
        y = 208 + 91 * p
        sheet(d, 481, y, 164, 142, True)
        label(d, (499, y + 13), "家书", 25)
        d.polygon(
            [(459, 320), (655, 320), (676, 429), (442, 429)],
            fill=(165, 139, 93),
            outline=EDGE,
        )
        line(d, [(444, 426), (552, 363), (674, 426)], (127, 102, 66), 2)
    elif kind == "glasses":
        d.polygon(
            [(239, 310), (557, 200), (736, 363), (361, 455)],
            fill=(157, 150, 122),
            outline=(200, 185, 147),
        )
        for k in range(5):
            line(d, [(255 + k * 6, 312), (361 + k * 5, 440)], (121, 125, 105), 1)
        for x in (403, 550):
            ellipse(d, x, 341, 67, 47, (122, 126, 108), (80, 67, 43), 7)
            ellipse(d, x, 341, 63, 43, None, (188, 167, 111), 3)
            line(d, [(x - 31 + 18 * p, 313), (x - 2 + 18 * p, 319)], (182, 180, 147), 3)
        d.arc((464, 328, 491, 354), 180, 354, fill=BRASS, width=5)
        a = math.pi + 1.64 * p
        line(
            d,
            [(617, 336), (617 + 130 * math.cos(a), 336 + 114 * math.sin(a))],
            BRASS,
            6,
        )
        line(d, [(337, 337), (268, 269), (252, 270)], (98, 78, 50), 5)
    elif kind == "radio":
        box(d, 231, 248, 508, 168, (92, 67, 43), BRASS, 16)
        box(d, 252, 266, 459, 65, (52, 63, 48), EDGE, 5)
        for k in range(59):
            x = 275 + 7 * k
            line(
                d, [(x, 283), (x, 283 + (13 if k % 5 == 0 else 5))], (192, 182, 132), 2
            )
        x = 319 + 255 * p
        line(d, [(x, 272), (x, 321)], (205, 110, 64), 4)
        for k in range(15):
            line(d, [(319 + 19 * k, 353), (319 + 19 * k, 395)], (49, 42, 31), 5)
        for x in (272, 689):
            ellipse(d, x, 370, 20, 20, (75, 70, 53), BRASS, 3)
    elif kind == "type":
        box(d, 241, 271, 453, 112, (60, 62, 54), BRASS, 7)
        for j, char in enumerate(["实", "践", "是", "检", "验"]):
            x = 268 + j * 80
            y = 281 if j != 3 else 201 + 80 * p
            box(d, x, y, 62, 75, (123, 125, 111), EDGE, 2)
            box(d, x + 3, y + 3, 57, 57, (165, 164, 138), (107, 106, 89), 2)
            # In letterpress the printing face is reversed.
            char_img = Image.new("L", (48, 48))
            ImageDraw.Draw(char_img).text((1, -2), char, font=face(39), fill=255)
            d.bitmap((x + 7, y + 4), ImageOps.mirror(char_img), fill=INK)
    elif kind == "print":
        sheet(d, 266, 251, 421, 175, True)
        label(d, (304, 266), "分田到户", 31)
        for j, (x, y) in enumerate(((339, 375), (419, 366), (523, 371), (608, 361))):
            f = 1 if j < 3 else p
            for k in range(8):
                rw = 4 + k * 2.5
                rh = 6 + k * 3
                if f > 0.005:
                    d.arc(
                        (x - rw, y - rh, x + rw, y + rh),
                        18,
                        18 + int(321 * f),
                        fill=col(PAPER, RED, 0.72 if j < 3 else f),
                        width=2,
                    )
    elif kind == "scale":
        box(d, 344, 379, 277, 38, (79, 70, 49), BRASS, 6)
        d.polygon(
            [(474, 363), (447, 376), (533, 376), (514, 363), (499, 262), (486, 262)],
            fill=(132, 112, 66),
            outline=BRASS,
        )
        tilt = 0.14 * (1 - p) + 0.017 * math.sin(t * 8) * (1 - p)

        def q(x):
            return (x, 281 + (x - 491) * tilt)

        line(d, [q(247), q(718)], BRASS, 12)
        for i in range(34):
            x = 301 + 10 * i
            y = q(x)[1]
            line(d, [(x, y - 5), (x, y + 4)], (75, 61, 40), 1)
        x = 563 + 63 * p
        y = q(x)[1]
        box(d, x - 12, y - 15, 24, 30, (82, 73, 49), BRASS, 5)
        line(d, [(x, y + 14), (x, y + 43)], BRASS, 3)
        box(d, x - 26, y + 39, 52, 36, (112, 97, 61), BRASS, 7)
    elif kind == "timer":
        sheet(d, 261, 292, 224, 114, True)
        label(d, (280, 309), "长途", 27)
        for r, c in [
            (104, (43, 45, 40)),
            (98, BRASS),
            (93, (62, 67, 56)),
            (85, (184, 174, 131)),
        ]:
            ellipse(d, 582, 311, r, r, c)
        dial_ticks(d, 582, 311, 78, 41, 125, 415)
        a = -2.24 + 0.13 * math.floor(t * 2.4)
        line(d, [(582, 311), (582 + 69 * math.cos(a), 311 + 69 * math.sin(a))], RED, 5)
        line(d, [(582, 311), (550, 335)], INK, 7)
        ellipse(d, 582, 311, 5, 5, BRASS)
    elif kind == "lift":
        box(d, 272, 216, 407, 213, (91, 90, 76), BRASS, 9)
        for x in (291, 661):
            for y in (234, 406):
                screw(d, x, y)
        box(d, 370, 246, 210, 87, (40, 44, 37), EDGE, 5)
        label(d, (387, 250), "1", 56, (193, 181, 135))
        a = min(2.999, 3 * p)
        v = 2 + math.floor(a)
        off = (a % 1) * 62
        window = Image.new("RGB", (61, 59), (40, 44, 37))
        ww = ImageDraw.Draw(window)
        for k in (0, 1):
            label(ww, (3, -8 - off + 62 * k), str(v + k), 53, (202, 190, 142))
        d._image.paste(window, (474, 264))
        for x in (449, 507):
            ellipse(d, x, 375, 17, 17, (143, 130, 93), BRASS, 3)
        d.polygon([(442, 379), (449, 368), (456, 379)], fill=INK)
    elif kind == "shoes":
        line(d, [(180, 275), (776, 250)], (106, 85, 57), 19)
        # Passing feet cast a moving shadow behind the threshold.
        x = 94 + 757 * p
        d.polygon(
            [(x - 65, 170), (x + 2, 156), (x + 145, 261), (x + 98, 267)],
            fill=(51, 52, 45),
        )
        d.polygon(
            [(x - 125, 172), (x - 70, 163), (x + 40, 267), (x - 4, 270)],
            fill=(49, 49, 41),
        )
        for x, y, a in [(405, 353, -20), (552, 343, 14)]:
            ellipse(d, x + 7, y + 34, 53, 72, (30, 33, 28))
            ellipse(d, x, y, 47, 76, (73, 65, 48), (128, 111, 76), 3)
            ellipse(d, x, y - 41, 31, 25, (39, 42, 33), (111, 97, 65), 2)
            for i in range(4):
                line(
                    d,
                    [(x - 16, y - 17 + 9 * i), (x + 17, y - 12 + 9 * i)],
                    (160, 143, 98),
                    2,
                )
    elif kind == "drop":
        d.polygon(
            [
                (262, 188),
                (529, 189),
                (544, 211),
                (544, 263),
                (506, 265),
                (502, 226),
                (260, 227),
            ],
            fill=(87, 98, 85),
            outline=(146, 151, 122),
        )
        line(d, [(265, 195), (517, 198), (530, 212)], (151, 155, 125), 5)
        ellipse(d, 525, 263, 20, 6, (38, 46, 38), EDGE, 2)
        f = smooth((p - 0.22) / 0.39)
        hit = smooth((p - 0.59) / 0.3)
        if f < 1:
            ellipse(d, 525, 270 + 110 * f, 5, 5 + 4 * f, (166, 183, 164))
        if hit > 0:
            ellipse(d, 526, 384, 8 + 25 * hit, 3 + 5 * hit, (63, 65, 47))
            ellipse(
                d,
                526,
                383,
                14 + 49 * hit,
                4 + 11 * hit,
                None,
                col((142, 150, 115), (96, 94, 67), hit),
                1,
            )
        for pts in [
            [(210, 434), (362, 395), (488, 409), (526, 391)],
            [(637, 366), (593, 386), (544, 386)],
            [(690, 414), (616, 404), (593, 386)],
        ]:
            line(d, pts, (63, 58, 40), 2)
    elif kind == "measure":
        line(d, [(278, 444), (610, 190)], (174, 158, 109), 8)
        line(d, [(258, 237), (705, 260)], (132, 93, 53), 8)
        for n in range(19):
            line(
                d,
                [(260 + 23 * n, 233 + n), (267 + 23 * n, 239 + n)],
                (207, 174, 106),
                2,
            )
        width = 28 + 270 * p
        box(d, 328, 359, width, 21, (181, 159, 96), EDGE)
        for n in range(int(width / 8)):
            line(
                d,
                [(333 + 8 * n, 361), (333 + 8 * n, 369 + (6 if n % 5 == 0 else 0))],
                INK,
                1,
            )
        box(d, 269, 328, 76, 65, (74, 91, 72), BRASS, 15)
        ellipse(d, 306, 357, 17, 17, (112, 124, 93), BRASS)
    elif kind == "pens":
        sheet(d, 254, 240, 455, 184, True)
        label(d, (286, 257), "审查建议", 33)
        for x, y, ang, c in [
            (404, 370, -1.09, (47, 56, 47)),
            (469, 373, -1.14, (89, 67, 44)),
            (
                534 + 132 * (1 - p),
                375 - 24 * (1 - p),
                -1.29 + 0.42 * (1 - p),
                (70, 71, 58),
            ),
        ]:
            pen(d, x, y, 126, ang, c)
    elif kind == "dial":
        box(d, 285, 242, 395, 196, (53, 59, 48), (106, 112, 87), 17)
        box(d, 318, 214, 326, 45, (39, 44, 39), EDGE, 17)
        for x in (335, 622):
            ellipse(d, x, 235, 38, 26, (46, 50, 42), EDGE, 3)
        for r, c in [(83, (39, 44, 38)), (76, (156, 151, 114)), (66, (100, 107, 88))]:
            ellipse(d, 486, 335, r, r, c)
        theta = 1.6 * (1 - smooth((p - 0.18) / 0.72))
        for i in range(10):
            a = -0.71 - i * 0.492 + theta
            x = 486 + 56 * math.cos(a)
            y = 335 + 56 * math.sin(a)
            ellipse(d, x, y, 10, 10, (45, 50, 41), (180, 173, 134), 2)
        ellipse(d, 486, 335, 28, 28, (166, 154, 111), BRASS, 2)
        box(d, 541, 363, 24, 11, (161, 155, 118), EDGE, 4)


def make_foley(kind, seed, path):
    hz = 48000
    n = hz * SECONDS
    rng = np.random.default_rng(seed)
    out = np.zeros((n, 2))
    # Start, timbre and envelope describe the object's mechanism. The room tone
    # joins the establishing frame to the close-up without narration.
    profiles = {
        "fold": ("rub", [2.7, 3.5, 4.5, 5.3], 480, 0.21),
        "switch": ("metal", [2.45, 4.28, 4.58], 205, 0.17),
        "seal": ("wood", [4.02, 4.14, 5.28], 149, 0.12),
        "roll": ("rub", [2.66, 3.65, 4.65], 390, 0.31),
        "spool": (
            "motor",
            [1.95, 2.17, 2.4, 2.65, 2.94, 3.3, 3.75, 4.35, 5.15],
            225,
            0.093,
        ),
        "chair": ("wood", [3.68, 4.65, 5.17], 129, 0.16),
        "latch": ("metal", [3.36, 3.49, 4.43, 5.57], 345, 0.14),
        "cloth": ("rub", [2.94, 3.73, 4.62, 5.32], 210, 0.37),
        "cup": ("ceramic", [3.27, 4.54, 5.33], 817, 0.24),
        "board": ("wood", [2.8, 3.98, 5.44], 183, 0.16),
        "bowl": ("ceramic", [3.36, 3.67, 4.93], 623, 0.26),
        "grain": ("grain", [2.4 + i * 0.106 for i in range(31)], 441, 0.04),
        "slip": ("rub", [2.72, 3.29, 4.62, 5.29], 640, 0.21),
        "glasses": ("metal", [3.35, 3.50, 4.86], 985, 0.095),
        "radio": ("tune", [2.43, 3.64, 4.15, 4.93, 5.73], 370, 0.29),
        "type": ("metal", [3.09, 3.4, 4.58, 5.61], 530, 0.11),
        "print": ("cloth", [2.9, 3.83, 4.92], 231, 0.16),
        "scale": ("metal", [2.66, 3.20, 3.93, 4.64, 5.24], 380, 0.145),
        "timer": ("tick", [1.9 + i * 0.418 for i in range(11)], 887, 0.058),
        "lift": ("motor", [2.76, 3.02, 3.91, 4.11, 5.21, 5.39, 5.63], 228, 0.12),
        "shoes": ("wood", [1.96, 2.63, 3.32, 4.11, 4.92, 5.85], 98, 0.20),
        "drop": ("water", [4.73, 4.79], 553, 0.21),
        "measure": ("metal", [2.77, 3.43, 4.09, 4.74, 5.41], 590, 0.085),
        "pens": ("wood", [3.18, 3.36, 4.46, 5.26], 406, 0.111),
        "dial": ("tick", [3.68 + i * 0.155 for i in range(13)], 612, 0.068),
    }
    mode, events, fr, dur = profiles[kind]
    ts = np.arange(n) / hz
    noise = rng.normal(size=(n // 120 + 2, 2))
    for ch in (0, 1):
        out[:, ch] = 0.008 * np.interp(
            np.arange(n) / 120, np.arange(len(noise)), noise[:, ch]
        ) + 0.004 * np.sin(2 * np.pi * (43 + seed % 19) * ts)
    for idx, when in enumerate(events):
        count = int(dur * hz * 3)
        x = np.arange(count) / hz
        f = fr * rng.uniform(0.88, 1.14)
        noise = rng.normal(size=count)
        noise = np.convolve(noise, np.ones(5) / 5, "same")
        fundamental = np.sin(2 * np.pi * f * x)
        if mode in ("metal", "ceramic", "tick"):
            sound = (
                0.58 * fundamental
                + 0.23 * np.sin(2 * np.pi * 2.73 * f * x)
                + 0.13 * np.sin(2 * np.pi * 4.25 * f * x)
            ) * np.exp(-x / (dur * 0.59)) + 0.46 * noise * np.exp(-x / 0.009)
        elif mode in ("rub", "cloth"):
            sound = (
                noise
                * (0.48 + 0.38 * np.sin(2 * np.pi * (18 + idx) * x) ** 2)
                * np.sin(np.pi * np.minimum(1, x / (dur * 2.2))) ** 1.2
            )
        elif mode == "water":
            sound = np.sin(2 * np.pi * f * (x + 2.1 * x * x)) * np.exp(
                -x / 0.054
            ) + 0.42 * noise * np.exp(-x / 0.036)
        elif mode == "tune":
            sound = (
                noise * 0.45 + np.sin(2 * np.pi * (f * x + 125 * x * x)) * 0.21
            ) * np.sin(np.pi * np.minimum(1, x / (dur * 2.1))) ** 2
        else:
            sound = (
                0.65 * np.sin(2 * np.pi * f * (x + 0.0008 * (1 - np.exp(-x / 0.01))))
                + 0.28 * noise
            ) * np.exp(-x / (dur * 0.38))
        amp = 0.115 if kind == "grain" else 0.20
        pan = (idx / max(1, len(events) - 1) - 0.5) * 0.64
        start = int(when * hz)
        end = min(n, start + count)
        for ch, g in enumerate((math.sqrt((1 - pan) / 2), math.sqrt((1 + pan) / 2))):
            out[start:end, ch] += amp * g * sound[: end - start]
    ramp = np.minimum(1, np.minimum(ts / 0.35, (SECONDS - ts) / 0.7)).clip(0, 1)
    samples = (out * ramp[:, None] * 32767).clip(-32000, 32000).astype("<i2")
    with wave.open(str(path), "wb") as w:
        w.setparams((2, 2, hz, n, "NONE", "not compressed"))
        w.writeframes(samples.tobytes())


def build(spec):
    slug, art, material, first, last, kind = spec
    seed = zlib.crc32(slug.encode())
    rng = np.random.default_rng(seed)
    name = "witness_" + slug
    OUT.mkdir(exist_ok=True, parents=True)
    original = ImageOps.fit(
        Image.open(ART / ((art or name) + ".webp")).convert("RGB"), (W, H)
    )
    yy, xx = np.mgrid[:H, :W]
    grain = rng.normal(0, 1.8, (H, W))
    salts = {
        "wood": (97, 75, 48),
        "paper": (99, 78, 52),
        "iron": (68, 72, 59),
        "cloth": (88, 87, 72),
        "earth": (106, 86, 58),
    }
    if material == "cloth":
        grain += 1.7 * np.sin(xx * 2) + 1.9 * np.cos(yy * 1.7)
    elif material in ("earth", "iron"):
        grain += 0.8 * np.sin(xx * 0.8) + 0.9 * np.sin(yy * 0.7)
    else:
        grain += 2.75 * np.cos(
            yy * 0.53 + 1.8 * np.sin(xx / 160 + yy / 62)
        ) + 1.65 * np.sin(yy * 0.72 + xx / 130)
    illum = 0.63 + 0.48 * np.exp(
        -(((xx - (270 + seed % 420)) / 360) ** 2) - ((yy - 328) / 207) ** 2
    )
    table = np.uint8(
        (illum[:, :, None] * np.array(salts[material]) + grain[:, :, None]).clip(0, 255)
    )
    rear = original.filter(ImageFilter.GaussianBlur(6))
    m = np.uint8(np.clip((yy - (195 + 0.044 * (xx - 480))) / 33, 0, 1) * 255)
    plate = Image.composite(Image.fromarray(table), rear, Image.fromarray(m))
    # A single grain plate gives all inserted foreground surfaces the same stock.
    texture = np.uint8(np.clip(127 + (grain - 1) * 3.0 + 17 * (illum - 0.9), 0, 255))
    tex = Image.fromarray(texture).convert("RGB")
    with tempfile.TemporaryDirectory() as tmp:
        wav = Path(tmp) / "object.wav"
        make_foley(kind, seed, wav)
        target = Path(tmp) / "scene.mp4"
        proc = subprocess.Popen(
            [
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
                f"{W}x{H}",
                "-r",
                str(FPS),
                "-i",
                "-",
                "-i",
                str(wav),
                "-map",
                "0:v",
                "-map",
                "1:a",
                "-c:v",
                "libx264",
                "-threads",
                "2",
                "-preset",
                "veryfast",
                "-crf",
                "19",
                "-pix_fmt",
                "yuv420p",
                "-c:a",
                "aac",
                "-b:a",
                "112k",
                "-movflags",
                "+faststart",
                str(target),
            ],
            stdin=subprocess.PIPE,
        )
        for i in range(FPS * SECONDS):
            t = i / FPS
            transition = smooth((t - 1.65) / 0.48)
            if transition < 1:
                q = 0.038 * smooth(t / 2.15)
                opening = original.resize(
                    (W, H),
                    Image.Resampling.BICUBIC,
                    box=(
                        W * q * 0.47,
                        H * q * 0.43,
                        W * (1 - q * 0.53),
                        H * (1 - q * 0.57),
                    ),
                )
            if transition > 0:
                framed = plate.copy()
                d = ImageDraw.Draw(framed)
                action(d, kind, smooth((t - 2.1) / 3.67), max(0, t - 1.9))
                framed = Image.blend(framed, tex, 0.075)
                q = 0.025 * smooth((t - 2.2) / 4.8)
                framed = framed.resize(
                    (W, H),
                    Image.Resampling.BILINEAR,
                    box=(
                        W * q * 0.49,
                        H * q * 0.60,
                        W * (1 - q * 0.51),
                        H * (1 - q * 0.40),
                    ),
                )
            image = (
                framed
                if transition == 1
                else opening
                if transition == 0
                else Image.blend(opening, framed, transition)
            )
            proc.stdin.write(image.tobytes())
        proc.stdin.close()
        if proc.wait():
            raise RuntimeError(name)
        (OUT / (name + ".mp4")).write_bytes(target.read_bytes())
    (OUT / (name + ".vtt")).write_text(
        "WEBVTT\n\n00:00:00.000 --> 00:00:02.900\n"
        + first
        + "\n\n00:00:02.900 --> 00:00:07.000\n"
        + last
        + "\n",
        encoding="utf-8",
    )
    print(name, flush=True)


if __name__ == "__main__":
    items = [s for s in SHOTS if not sys.argv[1:] or s[0] in sys.argv[1:]]
    if not items:
        raise SystemExit("No matching chapter slug.")
    with ProcessPoolExecutor(max_workers=min(3, len(items))) as pool:
        list(pool.map(build, items))
