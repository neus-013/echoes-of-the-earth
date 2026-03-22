import pygame
import random
from src.settings import (
    TILE_SIZE, MAP_WIDTH, MAP_HEIGHT,
    FARM_ORIGIN_X, FARM_ORIGIN_Y, FARM_WIDTH, FARM_HEIGHT,
    BLOCKING_TILES, WILD_TILES,
    TILE_GRASS, TILE_TREE, TILE_ROCK,
    TILE_BERRY, TILE_CAMPFIRE, TILE_BORDER, TILE_WATER,
    TILE_BED, TILE_TILLED, TILE_CHEST, TILE_DIRT,
    TILE_WILD_MORA, TILE_WILD_POTATO, TILE_WILD_WHEAT, TILE_WILD_PUMPKIN,
    WILD_TILE_TO_CROP, CROPS, CHEST_SLOTS,
    INTERNAL_WIDTH, INTERNAL_HEIGHT, RESOURCE_HP,
    BED_POSITIONS,
    TILE_WATERED,
)
from src.sprites import create_tile_sprites


class Camera:
    def __init__(self):
        self.x = 0.0
        self.y = 0.0
        self.map_pixel_w = MAP_WIDTH * TILE_SIZE
        self.map_pixel_h = MAP_HEIGHT * TILE_SIZE

    def follow(self, target_cx, target_cy):
        self.x = target_cx - INTERNAL_WIDTH / 2
        self.y = target_cy - INTERNAL_HEIGHT / 2
        max_x = self.map_pixel_w - INTERNAL_WIDTH
        max_y = self.map_pixel_h - INTERNAL_HEIGHT
        self.x = max(0, min(self.x, max_x))
        self.y = max(0, min(self.y, max_y))

    def world_to_screen(self, wx, wy):
        return wx - self.x, wy - self.y


def generate_map(seed=2024, num_players=1):
    """Generate a 60x60 map procedurally."""
    rng = random.Random(seed)
    tilemap = [[TILE_GRASS] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    # 1) Border ring
    for ty in range(MAP_HEIGHT):
        for tx in range(MAP_WIDTH):
            if tx == 0 or ty == 0 or tx == MAP_WIDTH - 1 or ty == MAP_HEIGHT - 1:
                tilemap[ty][tx] = TILE_BORDER

    # 2) Dense forest outside the farm area
    fx0, fy0 = FARM_ORIGIN_X, FARM_ORIGIN_Y
    fx1, fy1 = fx0 + FARM_WIDTH, fy0 + FARM_HEIGHT
    for ty in range(1, MAP_HEIGHT - 1):
        for tx in range(1, MAP_WIDTH - 1):
            if fx0 <= tx < fx1 and fy0 <= ty < fy1:
                continue
            r = rng.random()
            if r < 0.22:
                tilemap[ty][tx] = TILE_TREE
            elif r < 0.30:
                tilemap[ty][tx] = TILE_ROCK
            elif r < 0.36:
                tilemap[ty][tx] = TILE_BERRY

    # 3) Wild crop plants in outer ring
    wild_tiles = [TILE_WILD_MORA, TILE_WILD_POTATO, TILE_WILD_WHEAT, TILE_WILD_PUMPKIN]
    for wt in wild_tiles:
        placed = 0
        attempts = 0
        while placed < 10 and attempts < 200:
            attempts += 1
            tx = rng.randint(2, MAP_WIDTH - 3)
            ty = rng.randint(2, MAP_HEIGHT - 3)
            if fx0 <= tx < fx1 and fy0 <= ty < fy1:
                continue
            if tilemap[ty][tx] == TILE_GRASS:
                tilemap[ty][tx] = wt
                placed += 1

    # 4) Lake cluster (SE corner of forest area)
    lake_cx = min(fx1 + 3, MAP_WIDTH - 5)
    lake_cy = min(fy1 + 3, MAP_HEIGHT - 5)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            if abs(dx) + abs(dy) <= 3:
                lx, ly = lake_cx + dx, lake_cy + dy
                if 1 <= lx < MAP_WIDTH - 1 and 1 <= ly < MAP_HEIGHT - 1:
                    tilemap[ly][lx] = TILE_WATER

    # 5) Dirt zone near the lake
    dirt_x0 = lake_cx - 13
    dirt_y0 = lake_cy - 4
    for dy in range(10):
        for dx in range(10):
            dx2, dy2 = dirt_x0 + dx, dirt_y0 + dy
            if 1 <= dx2 < MAP_WIDTH - 1 and 1 <= dy2 < MAP_HEIGHT - 1:
                tilemap[dy2][dx2] = TILE_DIRT

    # 6) Campfire + beds around it
    center_x = MAP_WIDTH // 2
    center_y = MAP_HEIGHT // 2
    tilemap[center_y][center_x] = TILE_CAMPFIRE

    for i in range(num_players):
        bx, by = BED_POSITIONS[i]
        tilemap[by][bx] = TILE_BED

    return tilemap


# Pre-computed flower probability table to avoid per-frame Random() construction
_FLOWER_TABLE = {}


def _build_flower_table():
    """Pre-compute which tiles have flowers and which variant."""
    for ty in range(MAP_HEIGHT):
        for tx in range(MAP_WIDTH):
            rng = random.Random(tx * 1000 + ty * 10000)
            if rng.random() < 0.18:
                _FLOWER_TABLE[(tx, ty)] = rng.randint(1, 5)


_build_flower_table()


class World:
    def __init__(self, map_seed=2024, num_players=1):
        self.num_players = num_players
        self.tilemap = generate_map(map_seed, num_players)
        self.base_map = [row[:] for row in self.tilemap]
        self.camera = Camera()
        self.tile_sprites = create_tile_sprites()
        self.resource_hp = {}
        self.harvested = set()
        self.chests = {}
        self._init_resources()

    def _init_resources(self):
        for ty in range(MAP_HEIGHT):
            for tx in range(MAP_WIDTH):
                tile = self.base_map[ty][tx]
                if tile in (TILE_TREE, TILE_ROCK):
                    self.resource_hp[(tx, ty)] = RESOURCE_HP

    def new_day(self):
        """Respawn trees/rocks/berries/wild crops for the new day."""
        self.tilemap = [row[:] for row in self.base_map]
        self.resource_hp.clear()
        self.harvested.clear()
        self._init_resources()

    def is_blocking(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= MAP_WIDTH or ty >= MAP_HEIGHT:
            return True
        return self.tilemap[ty][tx] in BLOCKING_TILES

    def get_tile(self, tx, ty):
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            return self.tilemap[ty][tx]
        return TILE_BORDER

    def get_original_tile(self, tx, ty):
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            return self.base_map[ty][tx]
        return TILE_BORDER

    def set_tile(self, tx, ty, tile_type):
        if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
            self.tilemap[ty][tx] = tile_type

    def is_farm_area(self, tx, ty):
        return (FARM_ORIGIN_X <= tx < FARM_ORIGIN_X + FARM_WIDTH and
                FARM_ORIGIN_Y <= ty < FARM_ORIGIN_Y + FARM_HEIGHT)

    def till_soil(self, tx, ty):
        """Convert dirt to tilled soil. Returns True if successful."""
        if self.tilemap[ty][tx] != TILE_DIRT:
            return False
        self.tilemap[ty][tx] = TILE_TILLED
        return True

    def water_soil(self, tx, ty):
        """Convert tilled soil to watered soil. Returns True if successful."""
        if self.tilemap[ty][tx] != TILE_TILLED:
            return False
        self.tilemap[ty][tx] = TILE_WATERED
        return True

    def place_chest(self, tx, ty):
        if self.tilemap[ty][tx] != TILE_GRASS:
            return False
        self.tilemap[ty][tx] = TILE_CHEST
        self.chests[(tx, ty)] = [None] * CHEST_SLOTS
        return True

    def get_chest(self, tx, ty):
        return self.chests.get((tx, ty))

    def harvest_wild(self, tx, ty):
        """Harvest a wild crop tile. Returns (seed_item, qty) or None."""
        tile = self.tilemap[ty][tx]
        if tile not in WILD_TILES or (tx, ty) in self.harvested:
            return None
        crop_id = WILD_TILE_TO_CROP.get(tile)
        if not crop_id:
            return None
        crop_info = CROPS[crop_id]
        self.harvested.add((tx, ty))
        if not crop_info["regrows"]:
            self.tilemap[ty][tx] = TILE_GRASS
            self.base_map[ty][tx] = TILE_GRASS
        return (crop_info["seed"], crop_info["seed_yield"])

    def hit_resource(self, tx, ty, tool_id=None):
        """Hit a resource. Returns (item_id, qty, depleted) or None."""
        from src.settings import (
            ITEM_WOOD, ITEM_STONE, ITEM_BERRIES,
            YIELD_WOOD, YIELD_STONE, YIELD_BERRIES,
        )
        from src.systems.tools import TOOL_INFO

        tile = self.tilemap[ty][tx]

        if tile == TILE_BERRY and (tx, ty) not in self.harvested:
            self.harvested.add((tx, ty))
            return (ITEM_BERRIES, YIELD_BERRIES, True)

        if tile in (TILE_TREE, TILE_ROCK):
            key = (tx, ty)
            if key not in self.resource_hp:
                return None
            info = TOOL_INFO.get(tool_id, {})
            if tile == TILE_TREE:
                max_hp = info.get("break_tree_hits", 5)
            else:
                max_hp = info.get("break_rock_hits", 5)

            if self.resource_hp[key] > max_hp:
                self.resource_hp[key] = max_hp
            self.resource_hp[key] -= 1

            if self.resource_hp[key] <= 0:
                self.harvested.add(key)
                del self.resource_hp[key]
                item = ITEM_WOOD if tile == TILE_TREE else ITEM_STONE
                qty = YIELD_WOOD if tile == TILE_TREE else YIELD_STONE
                self.tilemap[ty][tx] = TILE_GRASS
                return (item, qty, True)
            return None

        return None

    def get_resource_hp(self, tx, ty):
        return self.resource_hp.get((tx, ty), 0)

    def is_campfire(self, tx, ty):
        return self.get_tile(tx, ty) == TILE_CAMPFIRE

    def is_bed(self, tx, ty):
        return self.get_tile(tx, ty) == TILE_BED

    # ── Serialització ────────────────────────────────────────────

    def to_save_data(self):
        """Serialize persistent world state (tilled/watered tiles, chests, removed wilds)."""
        tilled = []
        watered = []
        removed_wilds = []

        for ty in range(MAP_HEIGHT):
            for tx in range(MAP_WIDTH):
                curr = self.tilemap[ty][tx]
                orig = self.base_map[ty][tx]
                if curr == TILE_TILLED:
                    tilled.append([tx, ty])
                elif curr == TILE_WATERED:
                    watered.append([tx, ty])
                if orig in WILD_TILES and curr == TILE_GRASS:
                    removed_wilds.append([tx, ty])

        chests_data = {}
        for (tx, ty), slots in self.chests.items():
            chests_data[f"{tx},{ty}"] = [s.copy() if s else None for s in slots]

        return {
            "tilled": tilled,
            "watered": watered,
            "chests": chests_data,
            "removed_wilds": removed_wilds,
        }

    def from_save_data(self, data):
        if not data:
            self.new_day()
            return

        self.tilemap = [row[:] for row in self.base_map]
        self.resource_hp.clear()
        self.harvested.clear()
        self._init_resources()

        for tx, ty in data.get("tilled", []):
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                self.tilemap[ty][tx] = TILE_TILLED

        for tx, ty in data.get("watered", []):
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                self.tilemap[ty][tx] = TILE_WATERED

        self.chests.clear()
        for key, slots in data.get("chests", {}).items():
            tx, ty = [int(v) for v in key.split(",")]
            self.chests[(tx, ty)] = [s.copy() if s else None for s in slots]
            self.tilemap[ty][tx] = TILE_CHEST

        for tx, ty in data.get("removed_wilds", []):
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                self.base_map[ty][tx] = TILE_GRASS
                self.tilemap[ty][tx] = TILE_GRASS

    # ── Render ───────────────────────────────────────────────────

    def draw(self, surface, farming_system=None):
        cam = self.camera
        start_tx = max(0, int(cam.x // TILE_SIZE))
        start_ty = max(0, int(cam.y // TILE_SIZE))
        end_tx = min(MAP_WIDTH, int((cam.x + INTERNAL_WIDTH) // TILE_SIZE) + 2)
        end_ty = min(MAP_HEIGHT, int((cam.y + INTERNAL_HEIGHT) // TILE_SIZE) + 2)

        sprites = self.tile_sprites

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                sx, sy = cam.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)
                tile = self.tilemap[ty][tx]
                original = self.base_map[ty][tx]

                # ── Watered soil (render before anything else) ──
                if tile == TILE_WATERED:
                    surface.blit(sprites[TILE_WATERED], (sx, sy))
                    # Draw crop on top if present
                    if farming_system:
                        crop = farming_system.get_crop(tx, ty)
                        if crop:
                            stage = farming_system.get_stage(tx, ty)
                            crop_key = f"crop_{crop['crop']}_{stage}"
                            if crop_key in sprites:
                                surface.blit(sprites[crop_key], (sx, sy))
                    continue

                # ── Ground base layer ──
                if tile == TILE_DIRT or original == TILE_DIRT:
                    surface.blit(sprites["dirt_0"], (sx, sy))
                else:
                    surface.blit(sprites["grass_0"], (sx, sy))
                    flower_idx = _FLOWER_TABLE.get((tx, ty))
                    if flower_idx:
                        flower_sprite = sprites.get(f"flower_{flower_idx}")
                        if flower_sprite:
                            fw = flower_sprite.get_width()
                            fh = flower_sprite.get_height()
                            surface.blit(flower_sprite,
                                         (sx + (TILE_SIZE - fw) // 2,
                                          sy + (TILE_SIZE - fh) // 2))

                # ── Objects ──
                if tile == TILE_TREE:
                    hp = self.resource_hp.get((tx, ty), 5)
                    key = "tree" if hp >= 4 else ("tree_1" if hp >= 2 else "tree_2")
                    tree_sprite = sprites[key]
                    tw, th = tree_sprite.get_size()
                    surface.blit(tree_sprite,
                                 (sx + (TILE_SIZE - tw) // 2, sy + TILE_SIZE - th))

                elif tile == TILE_ROCK:
                    hp = self.resource_hp.get((tx, ty), 5)
                    key = "rock" if hp >= 4 else ("rock_1" if hp >= 2 else "rock_2")
                    surface.blit(sprites[key], (sx, sy))

                elif tile == TILE_BERRY or original == TILE_BERRY:
                    key = "berry_empty" if (tx, ty) in self.harvested else "berry"
                    surface.blit(sprites[key], (sx, sy))

                elif tile == TILE_CAMPFIRE:
                    surface.blit(sprites["campfire"], (sx, sy))

                elif tile == TILE_BED:
                    surface.blit(sprites["bed"], (sx, sy))

                elif tile == TILE_WATER:
                    surface.blit(sprites["water_0"], (sx, sy))

                elif tile == TILE_BORDER:
                    surface.blit(sprites[f"border_{(tx * 11 + ty * 7) % 4}"], (sx, sy))

                elif tile == TILE_TILLED:
                    crop = farming_system.get_crop(tx, ty) if farming_system else None
                    if crop:
                        soil_key = "tilled_watered" if crop["watered"] else "tilled"
                        surface.blit(sprites[soil_key], (sx, sy))
                        stage = farming_system.get_stage(tx, ty)
                        crop_key = f"crop_{crop['crop']}_{stage}"
                        if crop_key in sprites:
                            surface.blit(sprites[crop_key], (sx, sy))
                    else:
                        surface.blit(sprites["tilled"], (sx, sy))

                elif tile == TILE_CHEST:
                    surface.blit(sprites["chest"], (sx, sy))

                elif tile in WILD_TILES:
                    crop_id = WILD_TILE_TO_CROP.get(tile)
                    if crop_id:
                        key = (f"wild_{crop_id}_empty"
                               if (tx, ty) in self.harvested
                               else f"wild_{crop_id}")
                        if key in sprites:
                            surface.blit(sprites[key], (sx, sy))
