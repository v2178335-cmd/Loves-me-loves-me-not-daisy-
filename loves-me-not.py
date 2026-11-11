"""Loves me, loves me not — pixel daisy, software-render version.
Same look as the HTML/Canvas build: low-res put-pixel buffer, no draw.ellipse/rotate.

Run:  pip install pygame
      python loves-me-not.py
Click / Space = pluck, R = restart.
"""
import math
import random
import sys

import pygame

W, H = 168, 236
SCALE = 3
GROUND_Y = H - 44
FLOWER_X, FLOWER_Y = W // 2 + 2, 118

# ---- palette (same as index.html) ----
SKY_TOP = (19, 26, 77)
SKY_MID = (43, 47, 122)
SKY_HOR = (75, 74, 150)
STAR_DIM = (159, 178, 255)
MOON = (253, 246, 192)
MOON_SH = (233, 226, 164)
MT1 = (32, 38, 92)
MT2 = (21, 27, 71)
FLY_CORE = (255, 248, 186)
FLY_GLOW = (230, 240, 154)
GRASS = (43, 110, 43)
GRASS_DK = (31, 79, 32)
GRASS_LT = (63, 154, 58)
BLADE = (126, 217, 87)
STEM_DK = (44, 138, 52)
STEM_LT = (84, 200, 90)
PETAL = (201, 220, 245)
PETAL_HI = (244, 250, 255)
PETAL_SH = (169, 198, 234)
CENTER_DK = (110, 63, 14)
CENTER = (245, 165, 46)
CENTER_HI = (255, 210, 94)
CENTER_SH = (198, 122, 26)
HEART = (255, 107, 138)
PINK = (255, 158, 199)
PINK_DK = (161, 58, 104)
BLUE = (142, 203, 255)
BLUE_DK = (44, 77, 122)

# 5x7 pixel font, only glyphs we need: L O V E S M N T
FONT = {
    "L": ["10000", "10000", "10000", "10000", "10000", "10000", "11111"],
    "O": ["01110", "10001", "10001", "10001", "10001", "10001", "01110"],
    "V": ["10001", "10001", "10001", "10001", "10001", "01010", "00100"],
    "E": ["11111", "10000", "10000", "11110", "10000", "10000", "11111"],
    "S": ["01111", "10000", "10000", "01110", "00001", "00001", "11110"],
    "M": ["10001", "11011", "10101", "10101", "10001", "10001", "10001"],
    "N": ["10001", "11001", "10101", "10011", "10001", "10001", "10001"],
    "T": ["11111", "00100", "00100", "00100", "00100", "00100", "00100"],
    " ": ["00000"] * 7,
}


def put(surf, x, y, color):
    x, y = int(round(x)), int(round(y))
    if 0 <= x < W and 0 <= y < H:
        surf.set_at((x, y), color)


def fill_circle(surf, cx, cy, r, color):
    r = int(r)
    for dy in range(-r - 1, r + 2):
        for dx in range(-r - 1, r + 2):
            if dx * dx + dy * dy <= r * r:
                put(surf, cx + dx, cy + dy, color)


def draw_text(surf, text, cx, y, main, dark, px=2):
    """Centered pixel text with 8-dir outline, px = pixel size."""
    glyphs = [FONT.get(ch, FONT[" "]) for ch in text]
    adv = (5 + 1) * px
    total = len(glyphs) * adv - px
    x0 = int(cx - total / 2)
    for ox, oy in [(-1, 0), (1, 0), (0, -1), (0, 1), (-1, -1), (1, -1), (-1, 1), (1, 1)]:
        _blit_text(surf, glyphs, x0 + ox * px, y + oy * px, dark, px)
    _blit_text(surf, glyphs, x0, y, main, px)


def _blit_text(surf, glyphs, x0, y0, color, px):
    for gi, g in enumerate(glyphs):
        for row in range(7):
            for col in range(5):
                if g[row][col] == "1":
                    for dy in range(px):
                        for dx in range(px):
                            put(surf, x0 + gi * 6 * px + col * px + dx, y0 + row * px + dy, color)


def draw_petal(surf, cx, cy, rot, length, width):
    """Software-rotated petal, same colors as HTML drawPetalShape."""
    a = length / 2.0
    b = width / 2.0
    ai = max(0.5, a - 1.0)
    bi = max(0.5, b - 1.2)
    cos_r, sin_r = math.cos(rot), math.sin(rot)
    rad = int(max(a, b)) + 2
    for wy in range(int(cy) - rad, int(cy) + rad + 1):
        for wx in range(int(cx) - rad, int(cx) + rad + 1):
            dx, dy = wx - cx, wy - cy
            lx = dx * cos_r + dy * sin_r - 0.5
            ly = -dx * sin_r + dy * cos_r + 1.0
            if (lx / a) ** 2 + ((ly - 0.5) / b) ** 2 <= 1.0:
                col = PETAL
                if (lx / ai) ** 2 + (ly / bi) ** 2 <= 1.0:
                    col = PETAL_HI
                if 1 <= ly <= 2 and -a + 5 <= lx <= a - 6:
                    col = PETAL_SH
                if -2 <= ly <= -1 and -a + 6 <= lx <= a - 7:
                    col = (255, 255, 255)
                put(surf, wx, wy, col)


def draw_leaf(surf, bx, by, direction):
    # flat ellipse leaf pointing sideways, rotated slightly up
    for dy in range(-5, 6):
        for dx in range(-2, 20):
            ex, ey = (dx - 9) / 9.0, (dy + 1) / 4.0 if direction > 0 else (dy + 1) / 4.0
            if ex * ex + ey * ey <= 1.0:
                x = bx + direction * dx
                y = by + dy - dx * 0.18
                put(surf, x, y, STEM_DK)
                if ((dx - 9) / 7.0) ** 2 + ((dy + 2) / 2.4) ** 2 <= 1.0:
                    put(surf, x, y - 1, STEM_LT)


def build_sky():
    """Static gradient + mountains, computed once."""
    s = pygame.Surface((W, H))
    for y in range(H):
        k = y / H
        if k < 0.55:
            f = k / 0.55
            r = 19 + (43 - 19) * f
            g = 26 + (47 - 26) * f
            b = 77 + (122 - 77) * f
        elif k < 0.78:
            f = (k - 0.55) / 0.23
            r = 43 + (75 - 43) * f
            g = 47 + (74 - 47) * f
            b = 122 + (150 - 122) * f
        else:
            f = (k - 0.78) / 0.22
            r = 75 + (40 - 75) * f
            g = 74 + (60 - 74) * f
            b = 150 + (50 - 150) * f
        s.fill((int(r), int(g), int(b)), (0, y, W, 1))
    for x in range(W):
        y1 = int(158 + math.sin(x * 0.08) * 7 + math.sin(x * 0.023 + 2) * 8)
        for y in range(y1, 190):
            if 0 <= y < H:
                s.set_at((x, y), MT1)
        y2 = int(170 + math.sin(x * 0.06 + 1) * 6)
        for y in range(y2, 195):
            if 0 <= y < H:
                s.set_at((x, y), MT2)
    return s


def build_grass_base():
    rnd = random.Random(1234)
    s = pygame.Surface((W, H - GROUND_Y))
    s.fill(GRASS)
    for _ in range(220):
        x = rnd.randrange(W)
        y = rnd.randrange(s.get_height())
        s.set_at((x, y), GRASS_DK)
    for _ in range(90):
        x = rnd.randrange(W)
        y = rnd.randrange(s.get_height())
        s.set_at((x, y), GRASS_LT)
    return s


def pixel_heart(surf, x, y, color=HEART):
    m = ["0110110", "1111111", "1111111", "0111110", "0011100", "0001000"]
    for j, row in enumerate(m):
        for i, ch in enumerate(row):
            if ch == "1":
                put(surf, x + i - 3, y + j - 3, color)


def reset():
    petals = []
    n = 9 + random.randrange(5)  # 9..13: odd => LOVES ME, even => NOT
    for i in range(n):
        a = -math.pi / 2 + i * (math.pi * 2 / n) + (random.random() - 0.5) * 0.1
        petals.append({"a": a, "len": 31 + random.random() * 3, "wid": 8.6 + random.random() * 1.2})
    stars = [{"x": random.random() * W, "y": random.random() * 150,
              "p": random.random() * 6.28, "s": 2 if random.random() < 0.2 else 1}
             for _ in range(110)]
    flies = [{"x": 10 + random.random() * (W - 20), "y": 40 + random.random() * 110,
              "p": random.random() * 6.28, "sp": 0.4 + random.random() * 0.8}
             for _ in range(7)]
    return {"petals": petals, "falling": [], "landed": [], "hearts": [],
            "stars": stars, "flies": flies, "turn": 0, "loves": True,
            "over": False, "t": 0.0, "tears": []}


def pluck(st):
    if st["over"] or not st["petals"]:
        return
    idx = st["turn"] % len(st["petals"])
    p = st["petals"].pop(idx)
    st["turn"] += 1
    st["loves"] = (st["turn"] % 2 == 1)
    d = 1 if st["turn"] % 2 == 1 else -1
    st["falling"].append({
        "x": FLOWER_X + math.cos(p["a"]) * p["len"],
        "y": FLOWER_Y + math.sin(p["a"]) * p["len"] * 0.82,
        "vx": d * (0.3 + random.random() * 0.9), "vy": -0.8 - random.random() * 1.0,
        "rot": p["a"], "vr": d * (0.05 + random.random() * 0.15),
        "len": p["len"], "wid": p["wid"], "wob": random.random() * 6.28,
        "wobAmp": 0.3 + random.random() * 0.5})
    if not st["petals"]:
        st["over"] = True
        if st["loves"]:
            for _ in range(16):
                st["hearts"].append({"x": FLOWER_X + (random.random() - 0.5) * 22,
                                     "y": FLOWER_Y - 4, "vy": -0.5 - random.random() * 0.7,
                                     "p": random.random() * 6.28})


def main():
    pygame.init()
    pygame.display.set_caption("Loves me, loves me not")
    screen = pygame.display.set_mode((W * SCALE, H * SCALE))
    clock = pygame.time.Clock()
    buf = pygame.Surface((W, H))
    sky = build_sky()
    grass = build_grass_base()
    # precomputed vignette (same look as HTML)
    vig = pygame.Surface((W, H), pygame.SRCALPHA)
    _r = max(W, H) * 0.75
    for _yy in range(H):
        for _xx in range(W):
            _d = ((((_xx - W / 2) / _r) ** 2 + ((_yy - H * 0.45) / _r) ** 2) ** 0.5) / 0.75
            if _d > 0.45:
                vig.set_at((_xx, _yy), (5, 5, 25, int(100 * (_d - 0.45) / 0.55)))
    st = reset()

    running = True
    while running:
        dt = min(0.05, clock.tick(60) / 1000.0)
        for e in pygame.event.get():
            if e.type == pygame.QUIT:
                running = False
            elif e.type == pygame.MOUSEBUTTONDOWN:
                pluck(st)
            elif e.type == pygame.KEYDOWN:
                if e.key in (pygame.K_SPACE, pygame.K_RETURN):
                    pluck(st)
                elif e.key == pygame.K_r:
                    st = reset()
        st["t"] += dt
        t = st["t"]

        buf.blit(sky, (0, 0))
        # stars (twinkle like HTML: threshold .8 -> white)
        for s in st["stars"]:
            tw = 0.35 + 0.65 * abs(math.sin(t * 1.2 + s["p"]))
            if tw < 0.3:
                continue
            c = (255, 255, 255) if tw > 0.8 else STAR_DIM
            for dx in range(s["s"]):
                for dy in range(s["s"]):
                    put(buf, s["x"] + dx, s["y"] + dy, c)
        # moon + dither halo
        mx, my = W - 26, 34
        fill_circle(buf, mx, my, 8, MOON)
        for dx in range(-4, 5):
            put(buf, mx + dx, my + 2, MOON_SH)
        for dx in range(-2, 3):
            put(buf, mx + dx, my + 4, MOON_SH)
        for hx, hy in [(-10, -1), (9, 1), (-8, -7), (7, -6), (-9, 6), (8, 7)]:
            put(buf, mx + hx, my + hy, (120, 115, 90))
        # fireflies
        for f in st["flies"]:
            f["x"] += math.sin(t * 0.6 + f["p"]) * 0.12 * f["sp"]
            f["y"] += math.cos(t * 0.5 + f["p"]) * 0.10
            b = (math.sin(t * 4 * f["sp"] + f["p"]) + 1) / 2
            if b > 0.55:
                put(buf, f["x"], f["y"], FLY_CORE)
            if b > 0.82:
                x0, y0 = round(f["x"]), round(f["y"])
                put(buf, x0 - 1, y0, FLY_GLOW)
                put(buf, x0 + 1, y0, FLY_GLOW)
                put(buf, x0, y0 - 1, FLY_GLOW)
                put(buf, x0, y0 + 1, FLY_GLOW)

        # sad-finale tears: cold drops from the sky
        if st["over"] and not st["loves"] and len(st["tears"]) < 14 and random.random() < 0.06:
            st["tears"].append({"x": random.random() * W, "y": -4,
                                "vy": 0.7 + random.random() * 0.8,
                                "p": random.random() * 6.28})
        for tr in st["tears"][:]:
            tr["y"] += tr["vy"]
            tr["x"] += math.sin(t * 5 + tr["p"]) * 0.3
            if tr["y"] > GROUND_Y + 4:
                st["tears"].remove(tr)
                continue
            put(buf, tr["x"], tr["y"], (143, 179, 232))
            put(buf, tr["x"], tr["y"] + 1, (143, 179, 232))

        # grass
        buf.blit(grass, (0, GROUND_Y))
        for x in range(0, W, 2):
            h = 2 + ((x * 7) % 3)
            sway = round(math.sin(x * 0.08 - t * 3) * 1.5)
            for k in range(h + 1):
                put(buf, x + sway, GROUND_Y - h + k, BLADE)
        for x in range(W):
            put(buf, x, GROUND_Y, STEM_DK)

        sway_x = math.sin(t * 1.1) * 1.2
        base_x = FLOWER_X
        top_x = FLOWER_X + sway_x
        top_y, bot_y = FLOWER_Y, GROUND_Y + 8

        def stem_x(y):
            k = (y - top_y) / (bot_y - top_y)
            return top_x + (base_x - top_x) * k

        fx = top_x

        for Ld in st["landed"]:
            if Ld.get("vx"):
                Ld["x"] += Ld["vx"]
                Ld["vx"] *= 0.92
                Ld["rot"] += Ld["vx"] * 0.03
                if Ld["x"] < 4 or Ld["x"] > W - 4:
                    Ld["vx"] = 0
                if abs(Ld["vx"]) < 0.02:
                    Ld["vx"] = 0
            draw_petal(buf, Ld["x"], Ld["y"], Ld["rot"], Ld["len"] * 0.92, Ld["wid"] * 0.9)

        # stem + leaves (base planted, top leans)
        for y in range(top_y, bot_y):
            sx = stem_x(y)
            put(buf, sx - 1, y, STEM_DK)
            put(buf, sx, y, STEM_DK)
            put(buf, sx - 1, y, STEM_LT)
        draw_leaf(buf, stem_x(top_y + 36), top_y + 36, -1)
        draw_leaf(buf, stem_x(top_y + 54), top_y + 54, 1)

        for p in st["petals"]:
            px = fx + math.cos(p["a"]) * p["len"] * 0.66
            py = FLOWER_Y + math.sin(p["a"]) * p["len"] * 0.54
            draw_petal(buf, px, py, p["a"], p["len"] * 0.72, p["wid"])

        for f in st["falling"][:]:
            f["wob"] += 0.08
            f["vy"] = min(f["vy"] + 0.045, 1.6)
            f["vx"] *= 0.995
            f["x"] += f["vx"] + math.sin(f["wob"]) * f.get("wobAmp", 0.5)
            f["y"] += f["vy"]
            f["rot"] += f["vr"]
            if f["y"] >= GROUND_Y + 10:
                st["landed"].append({"x": max(6, min(W - 6, f["x"])),
                                     "y": GROUND_Y + 10 + random.random() * 22,
                                     "rot": (random.random() - 0.5) * 0.9,
                                     "len": f["len"], "wid": f["wid"],
                                     "vx": f["vx"] * 0.5})
                st["falling"].remove(f)
                continue
            draw_petal(buf, f["x"], f["y"], f["rot"], f["len"] * 0.72, f["wid"])

        # center
        fill_circle(buf, fx, FLOWER_Y, 11, CENTER_DK)
        fill_circle(buf, fx, FLOWER_Y, 9, CENTER)
        for dx in range(-5, 1):
            put(buf, fx + dx, FLOWER_Y - 5, CENTER_HI)
            put(buf, fx + dx, FLOWER_Y - 4, CENTER_HI)
        put(buf, fx + 1, FLOWER_Y - 1, CENTER_HI)
        put(buf, fx + 2, FLOWER_Y, CENTER_HI)
        for dx in range(-7, 7):
            put(buf, fx + dx, FLOWER_Y + 2, CENTER_SH)
        # sad finale: the heart of the flower goes dim
        if st["over"] and not st["loves"] and not st["petals"] and not st["falling"]:
            for dy in range(-9, 10):
                for dx in range(-9, 10):
                    if dx * dx + dy * dy <= 81 and (dx + dy) % 2 == 0:
                        put(buf, fx + dx, FLOWER_Y + dy, (60, 30, 50))

        for h in st["hearts"][:]:
            h["y"] += h["vy"]
            h["x"] += math.sin(t * 5 + h["p"]) * 0.4
            a = max(0.0, min(1.0, (h["y"] - 20) / 60))
            if a > 0.15:
                pixel_heart(buf, h["x"], h["y"])
            if h["y"] < 8:
                st["hearts"].remove(h)
        if st["over"] and st["loves"] and len(st["hearts"]) < 6 and random.random() < 0.1:
            st["hearts"].append({"x": FLOWER_X + (random.random() - 0.5) * 24,
                                 "y": FLOWER_Y, "vy": -0.6 - random.random() * 0.6,
                                 "p": random.random() * 6.28})

        if st["turn"]:
            txt = "LOVES ME" if st["loves"] else "LOVES ME NOT"
            draw_text(buf, txt, W / 2, 8, PINK if st["loves"] else BLUE,
                      PINK_DK if st["loves"] else BLUE_DK, px=2)

        # vignette (static, no flicker)
        buf.blit(vig, (0, 0))

        pygame.transform.scale(buf, (W * SCALE, H * SCALE), screen)
        pygame.display.flip()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
