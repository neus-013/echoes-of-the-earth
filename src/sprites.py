import json
import pygame
import math
import random
import os
from src.settings import (
    TILE_SIZE,
    SPRITE_BASE_SKIN, SPRITE_BASE_HAIR, SPRITE_BASE_OUTFIT, SPRITE_BASE_EYES,
    SKIN_PALETTES, HAIR_PALETTES, OUTFIT_PALETTES, EYE_PALETTES,
    COL_GRASS_1, COL_GRASS_2, COL_GRASS_3, COL_GRASS_DARK, COL_GRASS_GOLD,
    COL_EARTH, COL_EARTH_DARK,
    COL_TREE_TRUNK, COL_TREE_TRUNK_HI, COL_TREE_TRUNK_LO,
    COL_TREE_CANOPY, COL_TREE_CANOPY_HI, COL_TREE_CANOPY_LO, COL_TREE_CANOPY_DEEP,
    COL_ROCK, COL_ROCK_HI, COL_ROCK_SHADOW, COL_ROCK_WARM,
    COL_BERRY_BUSH, COL_BERRY_BUSH_HI, COL_BERRY, COL_BERRY_HI,
    COL_CAMPFIRE_LOG, COL_CAMPFIRE_FIRE, COL_CAMPFIRE_FIRE2, COL_CAMPFIRE_GLOW,
    COL_WATER_1, COL_WATER_2, COL_WATER_HI, COL_WATER_DEEP,
    COL_BORDER, COL_BORDER_HI, BLACK,
    PLAYER_SPRITE_W, PLAYER_SPRITE_H, PLAYER_WALK_FRAMES,
    COL_TILLED, COL_TILLED_DARK, COL_WATERED,
    CROP_MORA, CROP_POTATO, CROP_WHEAT, CROP_PUMPKIN,
)

T = TILE_SIZE  # 32
_tile_cache = {}


# ── helpers ────────────────────────────────────────────────────────
def _clamp(v, lo=0, hi=255):
    return max(lo, min(hi, int(v)))


def _shade(col, amt):
    return (_clamp(col[0] + amt), _clamp(col[1] + amt), _clamp(col[2] + amt))


def _warm_shade(col, amt):
    """Shift towards warm tones when brightening."""
    return (_clamp(col[0] + amt + abs(amt) // 6),
            _clamp(col[1] + amt),
            _clamp(col[2] + amt - abs(amt) // 8))


def _px(surf, x, y, col):
    if 0 <= x < surf.get_width() and 0 <= y < surf.get_height():
        surf.set_at((int(x), int(y)), col)


def _lerp_color(c1, c2, t_val):
    return (
        _clamp(c1[0] + (c2[0] - c1[0]) * t_val),
        _clamp(c1[1] + (c2[1] - c1[1]) * t_val),
        _clamp(c1[2] + (c2[2] - c1[2]) * t_val),
    )


def _soft_circle(surf, cx, cy, r, col, rng, jitter=1):
    """Draw a circle with slightly irregular edges for organic feel."""
    for a_step in range(int(r * 6)):
        a = a_step * math.pi * 2 / (r * 6)
        rr = r + rng.uniform(-jitter, jitter * 0.5)
        px_x = cx + rr * math.cos(a)
        px_y = cy + rr * math.sin(a)
        _px(surf, int(px_x), int(px_y), col)
    pygame.draw.circle(surf, col, (int(cx), int(cy)), max(1, int(r) - 1))


_ASSETS_TILES = os.path.join(os.path.dirname(os.path.dirname(__file__)), "assets", "tiles")


def _load_tile_sheet(png_name, json_name, scale_to_tile=True):
    """Load an Aseprite-exported sprite sheet and return list of Surfaces. Optionally scale to TILE_SIZE."""
    png_path = os.path.join(_ASSETS_TILES, png_name)
    json_path = os.path.join(_ASSETS_TILES, json_name)
    sheet = pygame.image.load(png_path).convert_alpha()
    with open(json_path, "r", encoding="utf-8") as f:
        meta = json.load(f)
    frames = []
    for frame_data in meta["frames"].values():
        r = frame_data["frame"]
        surf = sheet.subsurface(pygame.Rect(r["x"], r["y"], r["w"], r["h"])).copy()
        if scale_to_tile and (surf.get_width() != T or surf.get_height() != T):
            surf = pygame.transform.scale(surf, (T, T))
        frames.append(surf)
    return frames


# ── grass ──────────────────────────────────────────────────────────
def _draw_grass(seed):
    s = pygame.Surface((T, T))
    rng = random.Random(seed)

    # Base with warm variation per tile
    r_off = rng.randint(-8, 8)
    base = (_clamp(COL_GRASS_1[0] + r_off), _clamp(COL_GRASS_1[1] + r_off + 2),
            _clamp(COL_GRASS_1[2] + r_off - 2))
    s.fill(base)

    # Subtle earth patches underneath (organic ground texture)
    for _ in range(3):
        ex = rng.randint(0, T - 1)
        ey = rng.randint(0, T - 1)
        er = rng.randint(2, 5)
        earth = _lerp_color(base, COL_EARTH, 0.15)
        pygame.draw.circle(s, _shade(earth, rng.randint(-5, 5)), (ex, ey), er)

    # Colour variation patches (lighter and darker greens)
    for _ in range(4):
        px_x = rng.randint(2, T - 3)
        px_y = rng.randint(2, T - 3)
        pr = rng.randint(3, 7)
        variant = rng.choice([COL_GRASS_2, COL_GRASS_3, COL_GRASS_GOLD, base])
        pygame.draw.circle(s, _shade(variant, rng.randint(-6, 6)), (px_x, px_y), pr)

    # Detailed grass blades of varying height
    for _ in range(18):
        gx = rng.randint(0, T - 1)
        gy = rng.randint(2, T - 1)
        h = rng.randint(2, 6)
        lean = rng.randint(-2, 2)
        shade = rng.randint(-20, 15)
        col = _shade(rng.choice([COL_GRASS_1, COL_GRASS_2, COL_GRASS_GOLD]), shade)
        for step in range(h):
            bx = gx + int(lean * step / max(h, 1))
            by = gy - step
            _px(s, bx, by, col)
            if step == h - 1:
                _px(s, bx + (1 if lean >= 0 else -1), by, _shade(col, 10))

    # Tiny flowers (varied, more detail)
    if rng.random() < 0.3:
        fx, fy = rng.randint(4, T - 5), rng.randint(4, T - 5)
        flower_palettes = [
            [(255, 235, 70), (255, 210, 40)],   # Groc
            [(255, 175, 195), (220, 140, 165)],  # Rosa
            [(195, 175, 255), (165, 148, 220)],  # Lila
            [(255, 255, 240), (230, 230, 210)],  # Blanc
            [(255, 145, 60), (225, 115, 40)],    # Taronja
        ]
        fc, fc2 = rng.choice(flower_palettes)
        # Stem
        _px(s, fx, fy + 1, _shade(COL_GRASS_DARK, -5))
        _px(s, fx, fy + 2, COL_GRASS_DARK)
        # Petals (cross pattern)
        _px(s, fx, fy, fc)
        _px(s, fx - 1, fy, fc2)
        _px(s, fx + 1, fy, fc2)
        _px(s, fx, fy - 1, fc2)
        # Center
        _px(s, fx, fy, (255, 220, 60))

    # Additional flower
    if rng.random() < 0.15:
        fx2, fy2 = rng.randint(3, T - 4), rng.randint(3, T - 4)
        _px(s, fx2, fy2 + 1, COL_GRASS_DARK)
        fc3 = rng.choice([(255, 200, 80), (200, 140, 200), (255, 160, 120)])
        _px(s, fx2, fy2, fc3)
        _px(s, fx2 + 1, fy2, _shade(fc3, -15))

    # Tiny pebbles
    if rng.random() < 0.12:
        px_x, py = rng.randint(2, T - 3), rng.randint(T - 8, T - 2)
        pcol = _lerp_color(COL_ROCK_WARM, base, 0.4)
        _px(s, px_x, py, pcol)
        _px(s, px_x + 1, py, _shade(pcol, 8))

    return s


# ── dirt ───────────────────────────────────────────────────────────
def _draw_dirt(seed):
    s = pygame.Surface((T, T))
    rng = random.Random(seed)

    # Base earthy brown with variation
    r_off = rng.randint(-8, 8)
    base = (_clamp(COL_EARTH[0] + r_off),
            _clamp(COL_EARTH[1] + r_off - 2),
            _clamp(COL_EARTH[2] + r_off - 4))
    s.fill(base)

    # Darker earth patches (texture)
    for _ in range(5):
        ex = rng.randint(0, T - 1)
        ey = rng.randint(0, T - 1)
        er = rng.randint(3, 6)
        dark = _lerp_color(base, COL_EARTH_DARK, 0.4)
        pygame.draw.circle(s, _shade(dark, rng.randint(-6, 6)), (ex, ey), er)

    # Lighter sandy patches
    for _ in range(3):
        px_x = rng.randint(2, T - 3)
        px_y = rng.randint(2, T - 3)
        pr = rng.randint(2, 5)
        light = _shade(base, rng.randint(8, 18))
        pygame.draw.circle(s, light, (px_x, px_y), pr)

    # Small pebbles
    for _ in range(4):
        px_x = rng.randint(1, T - 2)
        py = rng.randint(1, T - 2)
        pcol = _lerp_color(COL_ROCK_WARM, base, 0.5)
        _px(s, px_x, py, _shade(pcol, rng.randint(-8, 8)))

    # Tiny cracks / soil lines
    for _ in range(3):
        cx = rng.randint(4, T - 5)
        cy = rng.randint(4, T - 5)
        cl = rng.randint(3, 6)
        ccol = _shade(COL_EARTH_DARK, rng.randint(-10, 0))
        for step in range(cl):
            _px(s, cx + step, cy + rng.randint(-1, 1), ccol)

    return s


# ── tree ───────────────────────────────────────────────────────────
def _draw_tree(damaged_level=0):
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    rng = random.Random(42 + damaged_level)

    trunk = COL_TREE_TRUNK
    trunk_hi = COL_TREE_TRUNK_HI
    trunk_lo = COL_TREE_TRUNK_LO

    # Ground shadow (warm tinted)
    shadow_col = (58, 80, 35, 80)
    pygame.draw.ellipse(s, shadow_col, (4, 26, 24, 6))

    # ── Roots (visible, organic) ──
    for rx, ry, rw in [(10, 27, 4), (20, 27, 3), (8, 28, 3), (22, 28, 2)]:
        pygame.draw.line(s, trunk_lo, (rx, ry), (rx + rng.randint(-2, 2), ry + rw), 1)
        _px(s, rx, ry, trunk)

    # ── Trunk (tapered, textured with bark detail) ──
    tx, tw_top, tw_bot = 12, 5, 8
    ty_top, ty_bot = 14, 28
    for row in range(ty_top, ty_bot):
        progress = (row - ty_top) / (ty_bot - ty_top)
        w = int(tw_top + (tw_bot - tw_top) * progress)
        x0 = 16 - w // 2
        for col_x in range(w):
            # Bark colour gradient: lighter on left (light source), darker right
            t_val = col_x / max(w - 1, 1)
            col = _lerp_color(trunk_hi, trunk_lo, t_val)
            # Vertical bark noise
            noise = rng.randint(-6, 6)
            _px(s, x0 + col_x, row, _shade(col, noise))

    # Bark horizontal lines
    for by in range(ty_top + 2, ty_bot - 1, 2):
        for bx in range(13, 19):
            if rng.random() < 0.4:
                _px(s, bx, by, _shade(trunk_lo, -10))

    # Knot detail
    _px(s, 15, 20, _shade(trunk_lo, -15))
    _px(s, 16, 20, _shade(trunk_lo, -20))
    _px(s, 15, 21, _shade(trunk_lo, -10))

    # ── Canopy (layered, organic Roots of Pacha style) ──
    # Deep shadow layer first
    for ccx, ccy, r in [(16, 11, 11), (11, 10, 7), (21, 10, 6)]:
        _soft_circle(s, ccx, ccy + 1, r, COL_TREE_CANOPY_DEEP, rng, 1.5)

    # Main foliage mass
    canopy_layers = [
        (16, 12, 11, COL_TREE_CANOPY),
        (11, 10, 8, COL_TREE_CANOPY_HI),
        (21, 10, 7, COL_TREE_CANOPY),
        (16, 8, 7, COL_TREE_CANOPY_HI),
        (13, 6, 5, _warm_shade(COL_TREE_CANOPY_HI, 10)),
        (19, 7, 5, COL_TREE_CANOPY),
    ]
    for ccx, ccy, r, col in canopy_layers:
        _soft_circle(s, ccx, ccy, r, col, rng, 1.2)

    # Light dappling – brighter spots on top-left (sun direction)
    for _ in range(15):
        lx = rng.randint(6, 24)
        ly = rng.randint(2, 16)
        dist = math.sqrt((lx - 16) ** 2 + (ly - 10) ** 2)
        if dist < 10:
            bright = _warm_shade(COL_TREE_CANOPY_HI, rng.randint(10, 30))
            _px(s, lx, ly, bright)
            if rng.random() < 0.5:
                _px(s, lx + 1, ly, bright)

    # Leaf edge detail – organic bumps around canopy perimeter
    for _ in range(30):
        a = rng.uniform(0, math.pi * 2)
        r = rng.uniform(9, 12)
        lx = int(16 + r * math.cos(a))
        ly = int(10 + r * math.sin(a) * 0.85)
        col = rng.choice([COL_TREE_CANOPY_HI, COL_TREE_CANOPY, COL_TREE_CANOPY_LO])
        _px(s, lx, ly, col)
        if rng.random() < 0.4:
            _px(s, lx + rng.choice([-1, 1]), ly, _shade(col, -8))

    # Inner shadow below canopy on trunk
    for sx in range(12, 20):
        _px(s, sx, ty_top, _shade(trunk, -35))
        _px(s, sx, ty_top + 1, _shade(trunk, -20))

    # Highlight arc on upper-left canopy (sunlight)
    for i in range(5):
        _px(s, 8 + i, 3 + (i % 2), _warm_shade(COL_TREE_CANOPY_HI, 30))
        _px(s, 9 + i, 4, _warm_shade(COL_TREE_CANOPY_HI, 20))

    # Very top leaf wisps
    for dx, dy in [(-1, 0), (0, -1), (1, 0)]:
        _px(s, 14 + dx, 1 + dy, COL_TREE_CANOPY_HI)

    # ── Damage effects ──
    if damaged_level > 0:
        crack_col = (65, 42, 22)
        if damaged_level >= 1:
            pygame.draw.line(s, crack_col, (14, 16), (16, 20), 1)
            _px(s, 15, 18, _shade(crack_col, -10))
        if damaged_level >= 2:
            pygame.draw.line(s, crack_col, (17, 14), (19, 19), 1)
            _px(s, 18, 17, (95, 75, 45))
        if damaged_level >= 3:
            pygame.draw.line(s, crack_col, (13, 12), (15, 17), 1)
            for lx, ly in [(7, 20), (24, 22), (5, 24), (26, 25)]:
                _px(s, lx, ly, rng.choice([COL_TREE_CANOPY_HI, COL_TREE_CANOPY]))
                _px(s, lx + 1, ly + 1, COL_TREE_CANOPY_LO)

    return s


# ── rock ───────────────────────────────────────────────────────────
def _draw_rock(damaged_level=0):
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    rng = random.Random(77 + damaged_level)

    # Ground shadow
    pygame.draw.ellipse(s, (80, 75, 58, 60), (3, 22, 26, 8))

    # Main body with detailed polygon
    body_pts = [(7, 23), (4, 16), (6, 11), (12, 8), (20, 7), (26, 10), (28, 16), (27, 23)]
    pygame.draw.polygon(s, COL_ROCK_WARM, body_pts)

    # Highlight face (left side – light source)
    hi_pts = [(8, 21), (6, 14), (10, 10), (18, 9), (20, 14), (18, 21)]
    pygame.draw.polygon(s, COL_ROCK, hi_pts)

    # Top highlight (very bright, rounded feel)
    top_pts = [(10, 11), (14, 8), (22, 9), (20, 12), (12, 12)]
    pygame.draw.polygon(s, COL_ROCK_HI, top_pts)

    # Specular highlight
    _px(s, 13, 10, _shade(COL_ROCK_HI, 25))
    _px(s, 14, 10, _shade(COL_ROCK_HI, 30))
    _px(s, 14, 9, _shade(COL_ROCK_HI, 20))

    # Edge outline (subtle, darker)
    pygame.draw.polygon(s, COL_ROCK_SHADOW, body_pts, 1)

    # Right side shadow gradient
    for row in range(10, 22):
        for offset in range(3):
            sx = 27 - offset
            _px(s, sx, row, _lerp_color(COL_ROCK_SHADOW, COL_ROCK_WARM, offset / 3))

    # Mineral speckles (varied, warm)
    for _ in range(10):
        mx = rng.randint(7, 26)
        my = rng.randint(9, 22)
        spec_col = rng.choice([
            _shade(COL_ROCK, rng.randint(-12, 20)),
            _shade(COL_ROCK_WARM, rng.randint(-8, 15)),
            (165, 155, 130),
        ])
        _px(s, mx, my, spec_col)

    # Moss accents (warm green, organic)
    moss_col = (82, 120, 52)
    moss_hi = (98, 138, 62)
    for mx, my in [(6, 20), (7, 21), (5, 21), (8, 22), (6, 22)]:
        _px(s, mx, my, rng.choice([moss_col, moss_hi]))
    if rng.random() < 0.5:
        for mx, my in [(24, 21), (25, 22)]:
            _px(s, mx, my, moss_col)

    # Tiny lichen patches
    for _ in range(3):
        lx = rng.randint(8, 24)
        ly = rng.randint(10, 18)
        lichen = (145, 148, 105)
        _px(s, lx, ly, lichen)
        _px(s, lx + 1, ly, _shade(lichen, -8))

    # Damage cracks
    if damaged_level > 0:
        crack = _shade(COL_ROCK_SHADOW, -30)
        if damaged_level >= 1:
            pygame.draw.line(s, crack, (14, 12), (18, 17), 1)
            _px(s, 16, 14, _shade(crack, -8))
        if damaged_level >= 2:
            pygame.draw.line(s, crack, (10, 16), (14, 20), 1)
            _px(s, 12, 18, (60, 50, 38))
        if damaged_level >= 3:
            pygame.draw.line(s, crack, (19, 10), (23, 16), 1)
            _px(s, 22, 22, _shade(COL_ROCK, -25))
            _px(s, 10, 23, _shade(COL_ROCK, -25))
            _px(s, 23, 23, _shade(COL_ROCK, -30))

    return s


# ── berry bush ─────────────────────────────────────────────────────
def _draw_berry_bush(has_berries=True):
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    rng = random.Random(33)
    bush = COL_BERRY_BUSH
    bush_hi = COL_BERRY_BUSH_HI
    bush_lo = _shade(bush, -22)

    # Ground shadow
    pygame.draw.ellipse(s, (50, 72, 32, 55), (3, 23, 26, 7))

    # Tiny stems visible at base
    for sx in [12, 16, 20]:
        pygame.draw.line(s, _shade(COL_EARTH, 10), (sx, 26), (sx + rng.randint(-1, 1), 22), 1)

    # Bush body – layered ellipses for depth
    pygame.draw.ellipse(s, bush_lo, (2, 9, 28, 20))
    pygame.draw.ellipse(s, bush, (4, 10, 24, 17))
    pygame.draw.ellipse(s, bush_hi, (6, 11, 20, 13))

    # Top highlight (sunlit)
    pygame.draw.ellipse(s, _warm_shade(bush_hi, 12), (8, 9, 14, 8))

    # Individual leaf clusters (organic bumps at edges)
    leaf_positions = [
        (5, 14), (8, 9), (14, 7), (20, 8), (25, 12),
        (26, 17), (23, 22), (9, 22), (4, 18),
    ]
    for lx, ly in leaf_positions:
        r = rng.randint(2, 4)
        col = rng.choice([bush, bush_hi, bush_lo])
        pygame.draw.circle(s, col, (lx, ly), r)

    # Leaf detail pixels
    for _ in range(20):
        lx = rng.randint(5, 27)
        ly = rng.randint(9, 24)
        dist = math.sqrt((lx - 16) ** 2 + ((ly - 16) * 1.3) ** 2)
        if dist < 12:
            col = _warm_shade(bush_hi, rng.randint(5, 25)) if ly < 15 else _shade(bush_lo, rng.randint(-5, 5))
            _px(s, lx, ly, col)
            if rng.random() < 0.3:
                _px(s, lx + 1, ly, _shade(col, -5))

    # Shadow on lower half
    for sx_x in range(6, 26):
        for sy in range(20, 25):
            dist = math.sqrt((sx_x - 16) ** 2 + ((sy - 16) * 1.3) ** 2)
            if dist < 11:
                _px(s, sx_x, sy, _shade(bush_lo, -5))

    if has_berries:
        berry_positions = [
            (10, 13), (18, 12), (14, 17), (22, 15), (8, 16),
            (12, 10), (21, 19), (16, 14), (7, 19), (24, 13),
            (15, 20), (19, 17),
        ]
        for bx, by in berry_positions:
            dist = math.sqrt((bx - 16) ** 2 + ((by - 16) * 1.3) ** 2)
            if dist < 11:
                pygame.draw.circle(s, COL_BERRY, (bx, by), 2)
                _px(s, bx - 1, by - 1, COL_BERRY_HI)
                _px(s, bx + 1, by + 1, _shade(COL_BERRY, -30))
                _px(s, bx, by - 2, bush)

    return s


# ── campfire ───────────────────────────────────────────────────────
def _draw_campfire():
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    rng = random.Random(55)

    # Warm ground glow (layered)
    pygame.draw.circle(s, (60, 40, 15, 30), (16, 20), 15)
    pygame.draw.circle(s, (70, 45, 18, 45), (16, 20), 11)

    # Ash circle base
    pygame.draw.circle(s, (85, 78, 65), (16, 21), 10)
    pygame.draw.circle(s, (75, 68, 55), (16, 21), 8)

    # Stone ring (detailed, varied stones)
    stone_positions = []
    for i in range(10):
        a = i * math.pi / 5 + 0.15
        sx = 16 + 11 * math.cos(a)
        sy = 21 + 7 * math.sin(a)
        stone_positions.append((int(sx), int(sy)))

    for sx, sy in stone_positions:
        stone_col = _shade((128, 125, 115), rng.randint(-12, 12))
        stone_hi = _shade(stone_col, 18)
        pygame.draw.circle(s, stone_col, (sx, sy), rng.randint(2, 3))
        _px(s, sx - 1, sy - 1, stone_hi)

    # Logs – crossed, with bark texture
    log = COL_CAMPFIRE_LOG
    log_hi = _shade(log, 28)
    log_lo = _shade(log, -18)
    pygame.draw.line(s, log, (8, 23), (24, 18), 3)
    pygame.draw.line(s, log_hi, (8, 22), (24, 17), 1)
    pygame.draw.line(s, log_lo, (8, 24), (24, 19), 1)
    pygame.draw.line(s, log, (9, 17), (23, 23), 3)
    pygame.draw.line(s, log_hi, (9, 16), (23, 22), 1)
    pygame.draw.line(s, log_lo, (9, 18), (23, 24), 1)

    # Charcoal/ember bed
    for _ in range(8):
        ex = rng.randint(12, 20)
        ey = rng.randint(18, 22)
        ember = rng.choice([(180, 60, 20), (200, 80, 25), (160, 45, 15)])
        _px(s, ex, ey, ember)

    # Flame (layered, warm)
    pygame.draw.polygon(s, COL_CAMPFIRE_FIRE, [(16, 5), (10, 19), (22, 19)])
    pygame.draw.polygon(s, COL_CAMPFIRE_FIRE2, [(16, 8), (11, 18), (21, 18)])
    pygame.draw.polygon(s, COL_CAMPFIRE_GLOW, [(16, 10), (13, 17), (19, 17)])
    pygame.draw.polygon(s, (255, 248, 220), [(16, 12), (14, 16), (18, 16)])

    # Flame wisps at edges
    for fx, fy in [(12, 8), (20, 9), (14, 6), (18, 7)]:
        _px(s, fx, fy, COL_CAMPFIRE_FIRE)
        _px(s, fx + rng.choice([-1, 1]), fy - 1, _shade(COL_CAMPFIRE_FIRE, 20))

    # Sparks rising
    for sx, sy in [(11, 5), (21, 4), (14, 3), (19, 2), (16, 1)]:
        spark_col = rng.choice([(255, 210, 90), (255, 180, 60), (255, 240, 140)])
        _px(s, sx, sy, spark_col)

    # Embers at base glow
    for ex, ey in [(14, 19), (17, 20), (15, 18), (18, 19)]:
        _px(s, ex, ey, (255, 130, 40))

    return s


# ── bed ────────────────────────────────────────────────────────────
def _draw_bed():
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    rng = random.Random(99)

    # Ground shadow
    pygame.draw.ellipse(s, (38, 55, 25, 55), (2, 22, 28, 8))

    # Wooden frame (prehistoric style – rounded logs)
    frame_col = (95, 65, 38)
    frame_hi = _shade(frame_col, 22)
    frame_lo = _shade(frame_col, -18)

    # Side logs
    pygame.draw.line(s, frame_col, (3, 11), (3, 28), 2)
    pygame.draw.line(s, frame_hi, (3, 11), (3, 28), 1)
    pygame.draw.line(s, frame_col, (28, 11), (28, 28), 2)
    pygame.draw.line(s, frame_lo, (29, 11), (29, 28), 1)
    pygame.draw.line(s, frame_col, (3, 28), (28, 28), 2)
    pygame.draw.line(s, frame_hi, (3, 27), (28, 27), 1)
    pygame.draw.line(s, frame_col, (3, 11), (28, 11), 2)

    # Hide/fur base
    hide = (168, 128, 78)
    hide_hi = _warm_shade(hide, 22)
    hide_lo = _shade(hide, -22)
    pygame.draw.rect(s, hide, (4, 12, 24, 16))

    # Fur texture lines
    for fy in range(13, 27):
        for fx in range(5, 27):
            noise = rng.randint(-8, 8)
            if abs(noise) > 5:
                _px(s, fx, fy, _shade(hide, noise))

    # Fur edge tufts
    for fx in range(5, 27, 2):
        _px(s, fx, 12, _shade(hide_hi, rng.randint(-5, 10)))
        _px(s, fx, 27, _shade(hide_lo, rng.randint(-5, 5)))

    # Blanket (animal skin pattern)
    blanket = (145, 105, 62)
    blanket_hi = _warm_shade(blanket, 18)
    pygame.draw.rect(s, blanket, (5, 18, 22, 8))
    for _ in range(6):
        bx = rng.randint(6, 25)
        by = rng.randint(19, 25)
        _px(s, bx, by, _shade(blanket, rng.randint(-15, 15)))
        _px(s, bx + 1, by, _shade(blanket, rng.randint(-10, 10)))
    pygame.draw.line(s, _shade(blanket, -15), (5, 18), (27, 18), 1)
    pygame.draw.line(s, blanket_hi, (5, 19), (27, 19), 1)

    # Pillow (rolled hide, detailed)
    pillow = (185, 152, 100)
    pillow_hi = _warm_shade(pillow, 20)
    pillow_lo = _shade(pillow, -20)
    pygame.draw.ellipse(s, pillow, (5, 10, 14, 8))
    pygame.draw.ellipse(s, pillow_hi, (6, 11, 10, 5))
    _px(s, 8, 11, _shade(pillow_hi, 15))
    pygame.draw.ellipse(s, pillow_lo, (5, 10, 14, 8), 1)

    return s


# ── water ──────────────────────────────────────────────────────────
def _draw_water(seed):
    s = pygame.Surface((T, T))
    rng = random.Random(seed)

    r_off = rng.randint(-5, 5)
    base = (_clamp(COL_WATER_1[0] + r_off), _clamp(COL_WATER_1[1] + r_off),
            _clamp(COL_WATER_1[2] + r_off))
    s.fill(base)

    # Depth variation (darker patches)
    for _ in range(5):
        dx = rng.randint(0, T - 4)
        dy = rng.randint(0, T - 4)
        dr = rng.randint(3, 7)
        deep = _lerp_color(base, COL_WATER_DEEP, rng.uniform(0.2, 0.5))
        pygame.draw.circle(s, deep, (dx, dy), dr)

    # Wave highlights (curved, soft)
    for i in range(5):
        wy = 3 + i * 6 + rng.randint(-1, 1)
        wave_phase = rng.uniform(0, math.pi)
        for wx in range(0, T):
            offset = int(1.5 * math.sin(wx * 0.25 + wave_phase + i * 0.5))
            y = wy + offset
            _px(s, wx, y, _lerp_color(base, COL_WATER_HI, 0.5 + 0.3 * math.sin(wx * 0.3)))
            _px(s, wx, y + 1, _lerp_color(base, COL_WATER_DEEP, 0.2))

    # Sparkle reflections
    for _ in range(4):
        sx = rng.randint(2, T - 3)
        sy = rng.randint(2, T - 3)
        _px(s, sx, sy, _shade(COL_WATER_HI, 30))
        if rng.random() < 0.5:
            _px(s, sx + 1, sy, _shade(COL_WATER_HI, 20))

    # Subtle warm tint at edges
    for ex in range(T):
        _px(s, ex, 0, _lerp_color(base, (120, 155, 160), 0.15))
        _px(s, ex, T - 1, _lerp_color(base, COL_WATER_DEEP, 0.1))

    return s


# ── border (dense ancient forest) ─────────────────────────────────
def _draw_border(seed):
    s = pygame.Surface((T, T))
    s.fill(COL_BORDER)
    rng = random.Random(seed)

    # Dense undergrowth base
    for _ in range(4):
        ux = rng.randint(0, T)
        uy = rng.randint(T // 2, T)
        ur = rng.randint(4, 8)
        pygame.draw.circle(s, _shade(COL_BORDER, rng.randint(-8, 5)), (ux, uy), ur)

    # Tree canopy layers
    for _ in range(6):
        c_x = rng.randint(0, T)
        c_y = rng.randint(-2, T // 2 + 4)
        r = rng.randint(6, 11)
        col = _shade(COL_BORDER_HI, rng.randint(-12, 8))
        pygame.draw.circle(s, col, (c_x, c_y), r)

    # Trunk hints
    for _ in range(3):
        t_x = rng.randint(3, T - 4)
        ty_start = rng.randint(8, 16)
        for ty in range(ty_start, min(ty_start + rng.randint(6, 14), T)):
            _px(s, t_x, ty, _shade(COL_BORDER, -18))
            _px(s, t_x + 1, ty, _shade(COL_BORDER, -12))

    # Highlight leaf specks
    for _ in range(14):
        hx = rng.randint(0, T - 1)
        hy = rng.randint(0, T - 1)
        _px(s, hx, hy, _shade(COL_BORDER_HI, rng.randint(5, 22)))

    # Occasional deep shadow
    for _ in range(5):
        sx = rng.randint(0, T - 1)
        sy = rng.randint(0, T - 1)
        _px(s, sx, sy, _shade(COL_BORDER, -15))

    return s


# ═══════════════════════════════════════════════════════════════════
def create_tile_sprites():
    global _tile_cache
    if _tile_cache:
        return _tile_cache

    tiles = {}

    # Grass variants (from sprite sheet)
    grass_frames = _load_tile_sheet("herba.png", "herba.json")
    for i, frame in enumerate(grass_frames):
        tiles[f"grass_{i}"] = frame

    # Dirt variants (from sprite sheet)
    dirt_frames = _load_tile_sheet("terra.png", "terra.json")
    for i, frame in enumerate(dirt_frames):
        tiles[f"dirt_{i}"] = frame

    # Tree sprites (new PNG/JSON assets)
    tree_frames = _load_tile_sheet("arbre.png", "arbre.json", scale_to_tile=False)
    tiles["tree"] = tree_frames[0]  # sencer
    tiles["tree_1"] = tree_frames[1]  # danyat
    tiles["tree_2"] = tree_frames[2]  # soca
    # If you have a fourth frame for stump, add: tiles["tree_empty"] = tree_frames[3]

    # Rock sprites (new PNG/JSON assets)
    rock_frames = _load_tile_sheet("pedra.png", "pedra.json")
    tiles["rock"] = rock_frames[0]  # sencer
    tiles["rock_1"] = rock_frames[1]  # danyat
    tiles["rock_2"] = rock_frames[2]  # runa
    # If you have a fourth frame for rubble, add: tiles["rock_empty"] = rock_frames[3]

    # Berry bush
    tiles["berry"] = _draw_berry_bush(True)
    tiles["berry_empty"] = _draw_berry_bush(False)

    # Campfire
    tiles["campfire"] = _draw_campfire()

    # Bed
    tiles["bed"] = _draw_bed()

    # Water (from sprite sheet)
    water_frames = _load_tile_sheet("aigua.png", "aigua.json")
    for i, frame in enumerate(water_frames):
        tiles[f"water_{i}"] = frame

    # Border variants
    for i in range(4):
        tiles[f"border_{i}"] = _draw_border(i * 17 + 3)

    # ── Tilled soil (from sprite sheet) ──
    tilled_frames = _load_tile_sheet("terra-llaurada.png", "terra-llaurada.json")
    tiles["tilled"] = tilled_frames[0]
    # 'terra-mullada': utilitza el PNG personalitzat
    terra_mullada_frames = _load_tile_sheet("terra-mullada.png", "terra-llaurada.json")
    # Flower sprites (from sprite sheet)
    flower_frames = _load_tile_sheet("flowers.png", "flowers.json")
    for i, frame in enumerate(flower_frames):
        tiles[f"flower_{i+1}"] = frame
    tiles["terra-mullada"] = terra_mullada_frames[0]
    from src.settings import TILE_WATERED
    tiles[TILE_WATERED] = terra_mullada_frames[0]  # Associate TILE_WATERED with terra-mullada.png

    # 'tilled_watered': igual que terra-mullada (plots regats)
    tilled_watered = tilled_frames[0].copy()
    for x in range(T):
        for y in range(T):
            c = tilled_watered.get_at((x, y))
            if c.a > 0:
                if (x + y) % 2 == 0:
                    r, g, b = 255, 120, 200  # Rosa
                else:
                    r, g, b = 180, 90, 255   # Lila
                tilled_watered.set_at((x, y), pygame.Color(r, g, b, c.a))
    tiles["tilled_watered"] = tilled_watered

    # ── Chest ──
    tiles["chest"] = _draw_chest()

    # ── Wild crop tiles (look like mature stage) ──
    for crop_id in (CROP_MORA, CROP_POTATO, CROP_WHEAT, CROP_PUMPKIN):
        tiles[f"wild_{crop_id}"] = _draw_crop(crop_id, 3)
        # Regrowable wilds show big plant without fruit; others show bare ground
        from src.settings import CROPS as _CROPS
        if _CROPS[crop_id]["regrows"]:
            tiles[f"wild_{crop_id}_empty"] = _draw_crop(crop_id, 2)
        else:
            tiles[f"wild_{crop_id}_empty"] = _draw_tilled(False)

    # ── Planted crop stages ──
    for crop_id in (CROP_MORA, CROP_POTATO, CROP_WHEAT, CROP_PUMPKIN):
        for stage in range(4):
            tiles[f"crop_{crop_id}_{stage}"] = _draw_crop(crop_id, stage)

    _tile_cache = tiles
    return tiles


# ── TILLED SOIL ────────────────────────────────────────────────
def _draw_tilled(watered):
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    base = COL_WATERED if watered else COL_TILLED
    dark = (75, 55, 38) if watered else COL_TILLED_DARK
    s.fill(base)
    rng = random.Random(55 if watered else 44)
    # Furrow lines
    for row in range(4, T - 2, 6):
        for col in range(2, T - 2, 4):
            if rng.random() < 0.7:
                _px(s, col, row, dark)
                _px(s, col + 1, row, dark)
    # Small dirt clumps
    for _ in range(4):
        x = rng.randint(3, T - 5)
        y = rng.randint(3, T - 5)
        _px(s, x, y, _shade(base, -12))
    return s


# ── CHEST ──────────────────────────────────────────────────────
def _draw_chest():
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    # Shadow
    pygame.draw.ellipse(s, (40, 30, 20, 60), (6, 24, 20, 6))
    # Body
    body_col = (140, 95, 50)
    pygame.draw.rect(s, body_col, (8, 14, 16, 12))
    # Lid
    lid_col = (160, 112, 60)
    pygame.draw.rect(s, lid_col, (7, 11, 18, 5))
    # Highlight
    pygame.draw.rect(s, (180, 130, 75), (8, 12, 16, 2))
    # Lock/clasp
    pygame.draw.rect(s, (200, 180, 80), (14, 17, 4, 3))
    _px(s, 15, 18, (220, 200, 100))
    # Dark trim
    pygame.draw.rect(s, (90, 60, 32), (8, 14, 16, 12), 1)
    return s


# ── CROP SPRITE ────────────────────────────────────────────────
_CROP_COLORS = {
    CROP_MORA: {"stem": (55, 100, 40), "fruit": (195, 52, 55), "fruit_hi": (225, 85, 80)},
    CROP_POTATO: {"stem": (65, 110, 45), "fruit": (185, 155, 90), "fruit_hi": (210, 180, 115)},
    CROP_WHEAT: {"stem": (145, 165, 60), "fruit": (210, 190, 80), "fruit_hi": (235, 215, 110)},
    CROP_PUMPKIN: {"stem": (55, 110, 40), "fruit": (220, 140, 40), "fruit_hi": (245, 170, 65)},
}


def _draw_crop(crop_id, stage):
    """Draw a crop at given growth stage (0=seed, 1=sprout, 2=growing, 3=mature)."""
    s = pygame.Surface((T, T), pygame.SRCALPHA)
    cols = _CROP_COLORS.get(crop_id, _CROP_COLORS[CROP_MORA])
    stem = cols["stem"]
    fruit = cols["fruit"]
    fruit_hi = cols["fruit_hi"]
    cx, base_y = T // 2, T - 6

    if stage == 0:  # seed – tiny mound
        pygame.draw.ellipse(s, COL_TILLED_DARK, (cx - 3, base_y - 1, 6, 3))
        _px(s, cx, base_y - 2, (100, 80, 50))
    elif stage == 1:  # sprout – small green shoot
        pygame.draw.line(s, stem, (cx, base_y), (cx, base_y - 6), 1)
        _px(s, cx - 1, base_y - 6, (80, 145, 55))
        _px(s, cx + 1, base_y - 6, (80, 145, 55))
        _px(s, cx, base_y - 7, (90, 155, 60))
    elif stage == 2:  # growing – taller plant
        pygame.draw.line(s, stem, (cx, base_y), (cx, base_y - 12), 2)
        for lx, ly in [(-3, -8), (3, -10), (-2, -12)]:
            pygame.draw.line(s, stem, (cx, base_y + ly), (cx + lx, base_y + ly - 2), 1)
        _px(s, cx, base_y - 13, _shade(stem, 20))
    else:  # mature – full plant with visible fruit
        pygame.draw.line(s, stem, (cx, base_y), (cx, base_y - 16), 2)
        for lx, ly in [(-4, -8), (4, -10), (-3, -13), (3, -15)]:
            pygame.draw.line(s, stem, (cx, base_y + ly), (cx + lx, base_y + ly - 3), 1)
        # Fruits
        for fx, fy in [(cx - 3, base_y - 10), (cx + 3, base_y - 13)]:
            pygame.draw.circle(s, fruit, (fx, fy), 3)
            _px(s, fx - 1, fy - 1, fruit_hi)
        if crop_id == CROP_PUMPKIN:
            pygame.draw.ellipse(s, fruit, (cx - 4, base_y - 5, 8, 6))
            _px(s, cx - 2, base_y - 4, fruit_hi)
    return s


# ═══════════════════════════════════════════════════════════════════
# PLAYER SPRITES  (loaded from Aseprite PNGs)
# ═══════════════════════════════════════════════════════════════════

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), '..', 'assets', 'player')
_player_cache = {}  # keyed by (skin, hair, outfit, eyes)
_raw_sheets = {}    # cache raw loaded spritesheets


def _load_raw_sheet(filename):
    """Load a raw spritesheet (cached)."""
    if filename not in _raw_sheets:
        path = os.path.join(_ASSETS_DIR, filename)
        _raw_sheets[filename] = pygame.image.load(path).convert_alpha()
    return _raw_sheets[filename]


def _build_color_map(skin_idx, hair_idx, outfit_idx, eyes_idx):
    """Build a dict mapping original RGB → replacement RGB."""
    cmap = {}
    skin_pal = SKIN_PALETTES[skin_idx % len(SKIN_PALETTES)]
    hair_pal = HAIR_PALETTES[hair_idx % len(HAIR_PALETTES)]
    outfit_pal = OUTFIT_PALETTES[outfit_idx % len(OUTFIT_PALETTES)]
    eye_pal = EYE_PALETTES[eyes_idx % len(EYE_PALETTES)]
    for base, repl in zip(SPRITE_BASE_SKIN, skin_pal):
        cmap[base] = repl
    for base, repl in zip(SPRITE_BASE_HAIR, hair_pal):
        cmap[base] = repl
    for base, repl in zip(SPRITE_BASE_OUTFIT, outfit_pal):
        cmap[base] = repl
    for base, repl in zip(SPRITE_BASE_EYES, eye_pal):
        cmap[base] = repl
    return cmap


def _recolor_surface(surf, cmap):
    """Return a copy of surf with pixel colors replaced per cmap."""
    out = surf.copy()
    w, h = out.get_size()
    for y in range(h):
        for x in range(w):
            r, g, b, a = out.get_at((x, y))
            if a == 0:
                continue
            key = (r, g, b)
            if key in cmap:
                nr, ng, nb = cmap[key]
                out.set_at((x, y), (nr, ng, nb, a))
    return out


def _load_spritesheet(filename, cmap):
    """Load a walk spritesheet, split into frames, and apply palette swap."""
    sheet = _load_raw_sheet(filename)
    frames = []
    for i in range(PLAYER_WALK_FRAMES):
        frame = pygame.Surface((PLAYER_SPRITE_W, PLAYER_SPRITE_H), pygame.SRCALPHA)
        frame.blit(sheet, (0, 0), (i * PLAYER_SPRITE_W, 0, PLAYER_SPRITE_W, PLAYER_SPRITE_H))
        if cmap:
            frame = _recolor_surface(frame, cmap)
        frames.append(frame)
    return frames


def create_player_sprites(skin_idx=0, hair_idx=0, outfit_idx=0, eyes_idx=0):
    """Load player sprites with palette-swapped colors.

    Returns dict: {facing: [frame0, frame1, frame2, frame3]}
    """
    key = (skin_idx, hair_idx, outfit_idx, eyes_idx)
    if key in _player_cache:
        return _player_cache[key]

    cmap = _build_color_map(skin_idx, hair_idx, outfit_idx, eyes_idx)
    # Skip recoloring if all indices are 0 (original palette)
    use_cmap = cmap if key != (0, 0, 0, 0) else None

    sprites = {}
    sprites["down"] = _load_spritesheet("player_walk_down.png", use_cmap)
    sprites["up"] = _load_spritesheet("player_walk_up.png", use_cmap)
    sprites["right"] = _load_spritesheet("player_walk_right.png", use_cmap)
    sprites["left"] = [pygame.transform.flip(f, True, False) for f in sprites["right"]]

    _player_cache[key] = sprites
    return sprites


def create_avatar_preview(skin_idx=0, hair_idx=0, outfit_idx=0, eyes_idx=0, size=96):
    """Return a scaled-up idle frame for the character creation preview."""
    sprites = create_player_sprites(skin_idx, hair_idx, outfit_idx, eyes_idx)
    idle_frame = sprites["down"][2]  # Frame 2 = idle
    scale = max(1, size // PLAYER_SPRITE_W)
    return pygame.transform.scale(idle_frame, (PLAYER_SPRITE_W * scale, PLAYER_SPRITE_H * scale))


# ═══════════════════════════════════════════════════════════════════
# ITEM ICONS  (16x16)
# ═══════════════════════════════════════════════════════════════════

def create_item_icon(item_id, size=16):
    s = pygame.Surface((size, size), pygame.SRCALPHA)
    if item_id == "wood":
        pygame.draw.rect(s, COL_TREE_TRUNK, (3, 3, 5, size - 5))
        pygame.draw.rect(s, COL_TREE_TRUNK_HI, (4, 4, 2, size - 7))
        pygame.draw.rect(s, COL_TREE_TRUNK_LO, (7, 4, 1, size - 7))
        for by in range(5, size - 3, 3):
            _px(s, 5, by, COL_TREE_TRUNK_LO)
        pygame.draw.ellipse(s, _shade(COL_TREE_TRUNK, 22), (3, 2, 5, 3))
        pygame.draw.circle(s, (72, 135, 48), (10, 4), 3)
        _px(s, 11, 3, (88, 152, 58))
    elif item_id == "stone":
        pygame.draw.ellipse(s, COL_ROCK_WARM, (1, 3, size - 2, size - 5))
        pygame.draw.ellipse(s, COL_ROCK, (3, 4, size - 6, size - 8))
        pygame.draw.ellipse(s, COL_ROCK_HI, (4, 4, 6, 4))
        _px(s, 5, 5, _shade(COL_ROCK_HI, 22))
        _px(s, 8, 8, COL_ROCK_SHADOW)
        _px(s, 10, 6, _shade(COL_ROCK_WARM, -8))
    elif item_id == "berries":
        for bx, by in [(5, 6), (9, 5), (7, 9), (11, 8)]:
            pygame.draw.circle(s, COL_BERRY, (bx, by), 3)
            _px(s, bx - 1, by - 1, COL_BERRY_HI)
            _px(s, bx + 1, by + 1, _shade(COL_BERRY, -25))
        _px(s, 7, 3, (72, 135, 48))
        _px(s, 8, 3, (72, 135, 48))
        _px(s, 8, 4, (62, 120, 42))

    # ── Seeds ──
    elif item_id.startswith("seed_"):
        _draw_seed_icon(s, item_id, size)

    # ── Crop harvests ──
    elif item_id == "mora":
        for bx, by in [(5, 7), (9, 5), (7, 10)]:
            pygame.draw.circle(s, (195, 52, 55), (bx, by), 3)
            _px(s, bx - 1, by - 1, (225, 85, 80))
    elif item_id == "potato":
        pygame.draw.ellipse(s, (185, 155, 90), (2, 4, 12, 9))
        pygame.draw.ellipse(s, (210, 180, 115), (4, 5, 6, 4))
    elif item_id == "wheat":
        pygame.draw.rect(s, (210, 190, 80), (6, 2, 4, 10))
        pygame.draw.rect(s, (235, 215, 110), (7, 2, 2, 4))
        pygame.draw.line(s, (145, 165, 60), (8, 12), (8, size - 2), 1)
    elif item_id == "pumpkin":
        pygame.draw.ellipse(s, (220, 140, 40), (2, 3, 12, 10))
        _px(s, 7, 3, (245, 170, 65))
        _px(s, 8, 2, (55, 110, 40))

    # ── Chest item ──
    elif item_id == "chest":
        pygame.draw.rect(s, (140, 95, 50), (2, 5, 12, 8))
        pygame.draw.rect(s, (160, 112, 60), (1, 3, 14, 4))
        pygame.draw.rect(s, (200, 180, 80), (6, 7, 3, 2))

    # ── Tool icons ──
    elif item_id == "stone_tool":
        pygame.draw.ellipse(s, COL_ROCK, (3, 2, 10, 8))
        pygame.draw.ellipse(s, COL_ROCK_HI, (5, 3, 5, 4))
        pygame.draw.rect(s, COL_TREE_TRUNK, (7, 9, 2, 5))
    elif item_id == "hoe":
        pygame.draw.rect(s, COL_TREE_TRUNK, (7, 3, 2, 10))
        pygame.draw.rect(s, COL_ROCK, (3, 2, 8, 3))
        pygame.draw.rect(s, COL_ROCK_HI, (4, 2, 5, 2))
    elif item_id == "water_bucket":
        pygame.draw.rect(s, (100, 75, 50), (3, 4, 10, 9))
        pygame.draw.rect(s, COL_WATER_1, (4, 5, 8, 7))
        pygame.draw.rect(s, COL_WATER_HI, (5, 6, 4, 3))
        pygame.draw.arc(s, (90, 60, 35), (4, 1, 8, 6), 0.3, 2.8, 1)

    return s


def _draw_seed_icon(s, item_id, size):
    """Draw a small seed icon colored by crop type."""
    seed_colors = {
        "seed_mora": ((140, 50, 50), (170, 75, 75)),
        "seed_potato": ((140, 120, 70), (170, 145, 95)),
        "seed_wheat": ((170, 155, 55), (200, 185, 85)),
        "seed_pumpkin": ((160, 110, 35), (195, 140, 60)),
    }
    base, hi = seed_colors.get(item_id, ((120, 100, 70), (150, 130, 100)))
    for sx, sy in [(5, 5), (9, 7), (6, 10), (10, 4)]:
        pygame.draw.ellipse(s, base, (sx - 1, sy - 1, 3, 4))
        _px(s, sx, sy - 1, hi)


# ═══════════════════════════════════════════════════════════════════
# TITLE SCREEN ART – Sacred Tree of Energies
# ═══════════════════════════════════════════════════════════════════

def draw_title_tree(surface, cx, base_y, tree_h):
    """Draw a large, detailed sacred tree for the title screen.
    cx = center x, base_y = ground level, tree_h = total height."""
    rng = random.Random(2024)

    trunk_col = (95, 68, 38)
    trunk_hi = (128, 92, 55)
    trunk_lo = (65, 45, 25)
    bark_dark = (55, 38, 20)

    canopy_base = (52, 115, 42)
    canopy_hi = (78, 148, 55)
    canopy_lo = (35, 88, 28)
    canopy_deep = (25, 68, 20)
    canopy_gold = (118, 158, 52)

    # ── Visible root system ──
    root_y = base_y
    roots = [
        (-40, 8), (-32, 12), (-22, 6), (-15, 10),
        (15, 8), (22, 10), (32, 6), (40, 12),
    ]
    for rx_off, r_depth in roots:
        rx = cx + rx_off
        for step in range(r_depth + 4):
            progress = step / (r_depth + 3)
            thickness = max(1, int(3 * (1 - progress)))
            col = _lerp_color(trunk_col, trunk_lo, progress)
            x_drift = int(rx_off * 0.3 * progress)
            pygame.draw.circle(surface, col, (rx + x_drift, root_y + step), thickness)
        _px(surface, rx, root_y, trunk_hi)

    # ── Trunk (wide, tapered, detailed bark) ──
    trunk_top = base_y - tree_h + int(tree_h * 0.45)
    trunk_bottom = base_y
    trunk_w_bot = 28
    trunk_w_top = 10

    for row in range(trunk_top, trunk_bottom):
        progress = (row - trunk_top) / max(trunk_bottom - trunk_top - 1, 1)
        tw = int(trunk_w_top + (trunk_w_bot - trunk_w_top) * progress)
        x0 = cx - tw // 2
        for col_x in range(tw):
            t_val = col_x / max(tw - 1, 1)
            if t_val < 0.2:
                col = trunk_lo
            elif t_val < 0.5:
                col = _lerp_color(trunk_hi, trunk_col, (t_val - 0.2) / 0.3)
            elif t_val < 0.7:
                col = trunk_col
            else:
                col = _lerp_color(trunk_col, trunk_lo, (t_val - 0.7) / 0.3)
            noise = rng.randint(-5, 5)
            _px(surface, x0 + col_x, row, _shade(col, noise))

    # Bark horizontal lines (texture)
    for by in range(trunk_top + 3, trunk_bottom - 2, 3):
        progress = (by - trunk_top) / max(trunk_bottom - trunk_top - 1, 1)
        tw = int(trunk_w_top + (trunk_w_bot - trunk_w_top) * progress)
        x0 = cx - tw // 2
        for bx in range(x0 + 2, x0 + tw - 2):
            if rng.random() < 0.35:
                _px(surface, bx, by, bark_dark)

    # Knots and burl details
    for kx_off, ky_off in [(-5, int(tree_h * 0.3)), (3, int(tree_h * 0.5)), (-2, int(tree_h * 0.65))]:
        kx = cx + kx_off
        ky = base_y - tree_h + int(tree_h * 0.45) + ky_off
        pygame.draw.circle(surface, bark_dark, (kx, ky), 2)
        _px(surface, kx - 1, ky - 1, trunk_hi)

    # ── Branches ──
    branch_data = [
        (-35, -tree_h + int(tree_h * 0.5), 18),
        (38, -tree_h + int(tree_h * 0.48), 20),
        (-50, -tree_h + int(tree_h * 0.55), 14),
        (48, -tree_h + int(tree_h * 0.52), 16),
        (-28, -tree_h + int(tree_h * 0.6), 12),
        (30, -tree_h + int(tree_h * 0.58), 14),
    ]
    for bx_off, by_off, b_len in branch_data:
        bx_start = cx + int(bx_off * 0.2)
        by_start = base_y + by_off
        bx_end = cx + bx_off
        by_end = by_start - b_len + rng.randint(-3, 3)
        for step in range(12):
            t_val = step / 11
            px_x = int(bx_start + (bx_end - bx_start) * t_val)
            py = int(by_start + (by_end - by_start) * t_val)
            thickness = max(1, int(4 * (1 - t_val * 0.7)))
            col = _lerp_color(trunk_col, trunk_lo, t_val * 0.5)
            pygame.draw.circle(surface, col, (px_x, py), thickness)

    # ── Canopy (massive, layered) ──
    canopy_cy = base_y - tree_h + int(tree_h * 0.3)

    # Deep shadow layer
    for scx, scy, sr in [(cx, canopy_cy + 5, 52), (cx - 25, canopy_cy + 8, 35),
                          (cx + 28, canopy_cy + 10, 32)]:
        pygame.draw.circle(surface, canopy_deep, (scx, scy), sr)

    # Main canopy mass
    canopy_circles = [
        (cx, canopy_cy, 48, canopy_base),
        (cx - 30, canopy_cy - 5, 32, canopy_hi),
        (cx + 32, canopy_cy - 3, 30, canopy_base),
        (cx - 15, canopy_cy - 15, 28, canopy_hi),
        (cx + 18, canopy_cy - 12, 26, canopy_gold),
        (cx, canopy_cy - 20, 25, canopy_hi),
        (cx - 40, canopy_cy + 5, 22, canopy_lo),
        (cx + 42, canopy_cy + 3, 20, canopy_lo),
        (cx - 10, canopy_cy - 28, 18, canopy_gold),
        (cx + 12, canopy_cy - 25, 16, canopy_hi),
        (cx, canopy_cy - 32, 12, _warm_shade(canopy_hi, 10)),
    ]
    for ccx, ccy, cr, col in canopy_circles:
        pygame.draw.circle(surface, col, (ccx, ccy), cr)

    # Light dappling
    for _ in range(80):
        lx = cx + rng.randint(-48, 48)
        ly = canopy_cy + rng.randint(-35, 15)
        dist = math.sqrt((lx - cx) ** 2 + (ly - canopy_cy) ** 2)
        if dist < 48:
            bright = _warm_shade(canopy_hi, rng.randint(8, 28))
            _px(surface, lx, ly, bright)
            if rng.random() < 0.4:
                _px(surface, lx + 1, ly, _shade(bright, -5))

    # Canopy edge leaf detail
    for _ in range(60):
        a = rng.uniform(0, math.pi * 2)
        r = rng.uniform(42, 52)
        lx = int(cx + r * math.cos(a))
        ly = int(canopy_cy + r * math.sin(a) * 0.7)
        col = rng.choice([canopy_hi, canopy_base, canopy_lo, canopy_gold])
        _px(surface, lx, ly, col)
        if rng.random() < 0.5:
            _px(surface, lx + rng.choice([-1, 1]), ly + rng.choice([-1, 0]),
                _shade(col, rng.randint(-10, 10)))

    # Sunlight arc upper-left
    for i in range(10):
        for j in range(2):
            _px(surface, cx - 35 + i * 2, canopy_cy - 30 + i + j,
                _warm_shade(canopy_gold, 20 - i))

    # ── Energy glow spots (representing the game's energies) ──
    energy_colors = [
        (255, 220, 80, 120),   # Gold – Spiritual energy
        (140, 220, 255, 100),  # Blue – Water/wisdom
        (255, 160, 100, 100),  # Orange – Fire/strength
        (180, 255, 140, 100),  # Green – Nature/growth
        (230, 180, 255, 100),  # Purple – Mystery/magic
    ]
    energy_positions = [
        (cx - 20, canopy_cy - 10),
        (cx + 22, canopy_cy - 8),
        (cx - 8, canopy_cy - 25),
        (cx + 10, canopy_cy + 5),
        (cx, canopy_cy - 15),
    ]
    for (ex, ey), ecol in zip(energy_positions, energy_colors):
        glow_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        glow_col = (ecol[0], ecol[1], ecol[2], ecol[3])
        pygame.draw.circle(glow_surf, glow_col, (8, 8), 6)
        pygame.draw.circle(glow_surf, (ecol[0], ecol[1], ecol[2], min(255, ecol[3] + 60)), (8, 8), 3)
        surface.blit(glow_surf, (ex - 8, ey - 8))
        _px(surface, ex, ey, (ecol[0], ecol[1], ecol[2]))
        _px(surface, ex + 1, ey, (min(255, ecol[0] + 30), min(255, ecol[1] + 30), min(255, ecol[2] + 30)))

    # ── Falling leaves ──
    for _ in range(8):
        lx = cx + rng.randint(-55, 55)
        ly = rng.randint(canopy_cy + 10, base_y - 5)
        col = rng.choice([canopy_hi, canopy_gold, (158, 138, 58)])
        _px(surface, lx, ly, col)
        _px(surface, lx + 1, ly + 1, _shade(col, -12))


def draw_title_ground(surface, ground_y):
    """Draw the ground/grass section for title screen."""
    w = surface.get_width()
    h = surface.get_height()
    rng = random.Random(1234)

    for row in range(ground_y, h):
        progress = (row - ground_y) / max(h - ground_y - 1, 1)
        col = _lerp_color(COL_GRASS_1, COL_GRASS_DARK, progress * 0.6)
        noise = rng.randint(-4, 4)
        pygame.draw.line(surface, _shade(col, noise), (0, row), (w, row))

    # Grass blade detail at top edge
    for gx in range(0, w, 2):
        h_blade = rng.randint(2, 7)
        lean = rng.randint(-1, 1)
        col = rng.choice([COL_GRASS_1, COL_GRASS_2, COL_GRASS_GOLD])
        shade = rng.randint(-10, 10)
        for step in range(h_blade):
            _px(surface, gx + int(lean * step / max(h_blade, 1)), ground_y - step,
                _shade(col, shade - step * 2))

    # Flowers in grass
    for _ in range(12):
        fx = rng.randint(10, w - 10)
        fy = rng.randint(ground_y + 2, ground_y + 15)
        fc = rng.choice([(255, 235, 70), (255, 180, 195), (255, 145, 60), (200, 180, 255)])
        _px(surface, fx, fy, fc)
        _px(surface, fx + 1, fy, _shade(fc, -15))
        _px(surface, fx, fy - 1, _shade(fc, -20))
        _px(surface, fx, fy + 1, COL_GRASS_DARK)


def draw_title_sky(surface, ground_y):
    """Draw atmospheric sky gradient for title screen."""
    w = surface.get_width()
    from src.settings import COL_TITLE_SKY_TOP, COL_TITLE_SKY_MID, COL_TITLE_SKY_BOT

    for row in range(ground_y):
        progress = row / max(ground_y - 1, 1)
        if progress < 0.5:
            col = _lerp_color(COL_TITLE_SKY_TOP, COL_TITLE_SKY_MID, progress * 2)
        else:
            col = _lerp_color(COL_TITLE_SKY_MID, COL_TITLE_SKY_BOT, (progress - 0.5) * 2)
        pygame.draw.line(surface, col, (0, row), (w, row))

    # Subtle clouds
    rng = random.Random(777)
    for _ in range(5):
        cloud_x = rng.randint(20, w - 20)
        cloud_y = rng.randint(15, ground_y // 2)
        cloud_w = rng.randint(20, 50)
        cloud_h = rng.randint(6, 12)
        cloud_col = _lerp_color(COL_TITLE_SKY_MID, (200, 200, 195), 0.2)
        cloud_surf = pygame.Surface((cloud_w, cloud_h), pygame.SRCALPHA)
        pygame.draw.ellipse(cloud_surf, (*cloud_col, 30), (0, 0, cloud_w, cloud_h))
        surface.blit(cloud_surf, (cloud_x - cloud_w // 2, cloud_y - cloud_h // 2))

    # Stars / distant lights
    for _ in range(15):
        sx = rng.randint(0, w)
        sy = rng.randint(0, ground_y // 3)
        brightness = rng.randint(140, 220)
        _px(surface, sx, sy, (brightness, brightness, brightness - 10))


def create_title_illustration(width, height):
    """Create the complete title screen background illustration."""
    surf = pygame.Surface((width, height))
    ground_y = int(height * 0.72)

    draw_title_sky(surf, ground_y)
    draw_title_ground(surf, ground_y)

    tree_h = int(height * 0.6)
    draw_title_tree(surf, width // 2, ground_y, tree_h)

    return surf
