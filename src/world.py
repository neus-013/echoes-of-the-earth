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
    """Generate a 60×60 map procedurally."""
    rng = random.Random(seed)
    tilemap = [[TILE_GRASS] * MAP_WIDTH for _ in range(MAP_HEIGHT)]

    # 1) Border ring
    for ty in range(MAP_HEIGHT):
        for tx in range(MAP_WIDTH):
            if tx == 0 or ty == 0 or tx == MAP_WIDTH - 1 or ty == MAP_HEIGHT - 1:
                tilemap[ty][tx] = TILE_BORDER

    # 2) Dense forest in the border region (between border and farm)
    fx0, fy0 = FARM_ORIGIN_X, FARM_ORIGIN_Y
    fx1, fy1 = fx0 + FARM_WIDTH, fy0 + FARM_HEIGHT
    for ty in range(1, MAP_HEIGHT - 1):
        for tx in range(1, MAP_WIDTH - 1):
            if fx0 <= tx < fx1 and fy0 <= ty < fy1:
                continue  # farm area stays grass
            r = rng.random()
            if r < 0.22:
                tilemap[ty][tx] = TILE_TREE
            elif r < 0.30:
                tilemap[ty][tx] = TILE_ROCK
            elif r < 0.36:
                tilemap[ty][tx] = TILE_BERRY

    # 3) Wild crop plants in outer ring (8-12 of each)
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
    lake_cx, lake_cy = fx1 + 3, fy1 + 3
    lake_cx = min(lake_cx, MAP_WIDTH - 5)
    lake_cy = min(lake_cy, MAP_HEIGHT - 5)
    for dy in range(-3, 4):
        for dx in range(-3, 4):
            dist = abs(dx) + abs(dy)
            if dist <= 3:
                lx, ly = lake_cx + dx, lake_cy + dy
                if 1 <= lx < MAP_WIDTH - 1 and 1 <= ly < MAP_HEIGHT - 1:
                    tilemap[ly][lx] = TILE_WATER

    # 5) Dirt zone near the lake (10×10, just west of the lake)
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

    # Place beds: one per player, using BED_POSITIONS from settings
    for i in range(num_players):
        bx, by = BED_POSITIONS[i]
        tilemap[by][bx] = TILE_BED

    return tilemap


class World:
    def __init__(self, map_seed=2024, num_players=1):
        self.num_players = num_players
        self.tilemap = generate_map(map_seed, num_players)
        self.base_map = [row[:] for row in self.tilemap]
        self.camera = Camera()
        self.tile_sprites = create_tile_sprites()
        self.resource_hp = {}
        self.harvested = set()       # wild plants / berry bushes harvested
        self.chests = {}             # {(tx,ty): [list of CHEST_SLOTS slots]}
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
        # Re-apply persistent changes: tilled soil, chests, planted crops
        # (these are managed by farming_system and playing screen)

    def is_blocking(self, tx, ty):
        if tx < 0 or ty < 0 or tx >= MAP_WIDTH or ty >= MAP_HEIGHT:
            return True
        tile = self.tilemap[ty][tx]
        return tile in BLOCKING_TILES

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
        fx0, fy0 = FARM_ORIGIN_X, FARM_ORIGIN_Y
        return fx0 <= tx < fx0 + FARM_WIDTH and fy0 <= ty < fy0 + FARM_HEIGHT

    def till_soil(self, tx, ty):
        """Convert dirt to tilled soil. Returns True if successful."""
        tile = self.tilemap[ty][tx]
        if tile != TILE_DIRT:
            return False
        self.tilemap[ty][tx] = TILE_TILLED
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
        if tile not in WILD_TILES:
            return None
        if (tx, ty) in self.harvested:
            return None
        crop_id = WILD_TILE_TO_CROP.get(tile)
        if not crop_id:
            return None
        crop_info = CROPS[crop_id]
        self.harvested.add((tx, ty))
        # Non-regrowable wild crops disappear
        if not crop_info["regrows"]:
            self.tilemap[ty][tx] = TILE_GRASS
            self.base_map[ty][tx] = TILE_GRASS
        return (crop_info["seed"], crop_info["seed_yield"])

    def hit_resource(self, tx, ty):
        """Hit a resource at (tx, ty). Returns (item_id, qty, depleted) or None."""
        from src.settings import (
            ITEM_WOOD, ITEM_STONE, ITEM_BERRIES,
            YIELD_WOOD, YIELD_STONE, YIELD_BERRIES,
        )

        tile = self.tilemap[ty][tx]
        if tile == TILE_BERRY and (tx, ty) not in self.harvested:
            self.harvested.add((tx, ty))
            return (ITEM_BERRIES, YIELD_BERRIES, True)

        if tile in (TILE_TREE, TILE_ROCK):
            key = (tx, ty)
            if key not in self.resource_hp:
                return None
            self.resource_hp[key] -= 1
            if self.resource_hp[key] <= 0:
                self.harvested.add(key)
                del self.resource_hp[key]
                item = ITEM_WOOD if tile == TILE_TREE else ITEM_STONE
                qty = YIELD_WOOD if tile == TILE_TREE else YIELD_STONE
                self.tilemap[ty][tx] = TILE_GRASS
                return (item, qty, True)
            else:
                return None

        return None

    def get_resource_hp(self, tx, ty):
        return self.resource_hp.get((tx, ty), 0)

    def is_campfire(self, tx, ty):
        return self.get_tile(tx, ty) == TILE_CAMPFIRE

    def is_bed(self, tx, ty):
        return self.get_tile(tx, ty) == TILE_BED

    def draw(self, surface, farming_system=None):
        cam = self.camera
        start_tx = max(0, int(cam.x // TILE_SIZE))
        start_ty = max(0, int(cam.y // TILE_SIZE))
        end_tx = min(MAP_WIDTH, int((cam.x + INTERNAL_WIDTH) // TILE_SIZE) + 2)
        end_ty = min(MAP_HEIGHT, int((cam.y + INTERNAL_HEIGHT) // TILE_SIZE) + 2)

        for ty in range(start_ty, end_ty):
            for tx in range(start_tx, end_tx):
                sx, sy = cam.world_to_screen(tx * TILE_SIZE, ty * TILE_SIZE)

                tile = self.tilemap[ty][tx]
                original = self.base_map[ty][tx]

                # Ground base layer
                if tile == TILE_DIRT or original == TILE_DIRT:
                    dirt_key = f"dirt_{(tx * 5 + ty * 11) % 8}"
                    surface.blit(self.tile_sprites[dirt_key], (sx, sy))
                else:
                    grass_key = f"grass_{(tx * 7 + ty * 13) % 20}"
                    surface.blit(self.tile_sprites[grass_key], (sx, sy))

                if tile == TILE_TREE:
                    hp = self.resource_hp.get((tx, ty), RESOURCE_HP)
                    key = f"tree_{hp}" if hp < RESOURCE_HP else "tree"
                    surface.blit(self.tile_sprites[key], (sx, sy))
                elif tile == TILE_ROCK:
                    hp = self.resource_hp.get((tx, ty), RESOURCE_HP)
                    key = f"rock_{hp}" if hp < RESOURCE_HP else "rock"
                    surface.blit(self.tile_sprites[key], (sx, sy))
                elif tile == TILE_BERRY or original == TILE_BERRY:
                    if (tx, ty) in self.harvested:
                        surface.blit(self.tile_sprites["berry_empty"], (sx, sy))
                    else:
                        surface.blit(self.tile_sprites["berry"], (sx, sy))
                elif tile == TILE_CAMPFIRE:
                    surface.blit(self.tile_sprites["campfire"], (sx, sy))
                elif tile == TILE_BED:
                    surface.blit(self.tile_sprites["bed"], (sx, sy))
                elif tile == TILE_WATER:
                    vkey = f"water_{(tx * 3 + ty * 5) % 4}"
                    surface.blit(self.tile_sprites[vkey], (sx, sy))
                elif tile == TILE_BORDER:
                    vkey = f"border_{(tx * 11 + ty * 7) % 4}"
                    surface.blit(self.tile_sprites[vkey], (sx, sy))
                elif tile == TILE_TILLED:
                    # Check farming for watered / crop
                    crop = farming_system.get_crop(tx, ty) if farming_system else None
                    if crop:
                        watered = crop["watered"]
                        soil_key = "tilled_watered" if watered else "tilled"
                        surface.blit(self.tile_sprites[soil_key], (sx, sy))
                        stage = farming_system.get_stage(tx, ty)
                        crop_key = f"crop_{crop['crop']}_{stage}"
                        if crop_key in self.tile_sprites:
                            surface.blit(self.tile_sprites[crop_key], (sx, sy))
                    else:
                        surface.blit(self.tile_sprites["tilled"], (sx, sy))
                elif tile == TILE_CHEST:
                    surface.blit(self.tile_sprites["chest"], (sx, sy))
                elif tile in WILD_TILES:
                    crop_id = WILD_TILE_TO_CROP.get(tile)
                    if (tx, ty) in self.harvested:
                        key = f"wild_{crop_id}_empty"
                    else:
                        key = f"wild_{crop_id}"
                    if key in self.tile_sprites:
                        surface.blit(self.tile_sprites[key], (sx, sy))

    def to_save_data(self):
        # Save tilled tiles and chest positions/contents
        tilled = []
        for ty in range(MAP_HEIGHT):
            for tx in range(MAP_WIDTH):
                if self.tilemap[ty][tx] == TILE_TILLED:
                    tilled.append([tx, ty])

        chests_data = {}
        for (tx, ty), slots in self.chests.items():
            chests_data[f"{tx},{ty}"] = [s.copy() if s else None for s in slots]

        # Wild tiles that were permanently removed (non-regrowable wilds)
        removed_wilds = []
        for ty in range(MAP_HEIGHT):
            for tx in range(MAP_WIDTH):
                orig = self.base_map[ty][tx]
                curr = self.tilemap[ty][tx]
                if orig in WILD_TILES and curr != orig:
                    removed_wilds.append([tx, ty])

        return {
            "tilled": tilled,
            "chests": chests_data,
            "removed_wilds": removed_wilds,
            "harvested": [list(pos) for pos in self.harvested],
            "resource_hp": {f"{k[0]},{k[1]}": v for k, v in self.resource_hp.items()},
        }

    def from_save_data(self, data):
        if not data:
            self.new_day()
            return

        # Regenerate from base, then apply persistent state
        self.tilemap = [row[:] for row in self.base_map]
        self.resource_hp.clear()
        self.harvested.clear()
        self._init_resources()

        # Restore tilled tiles
        for tx, ty in data.get("tilled", []):
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                self.tilemap[ty][tx] = TILE_TILLED

        # Restore chests
        self.chests.clear()
        for key, slots in data.get("chests", {}).items():
            tx, ty = [int(v) for v in key.split(",")]
            self.chests[(tx, ty)] = [s.copy() if s else None for s in slots]
            self.tilemap[ty][tx] = TILE_CHEST

        # Restore permanently removed wild crops
        for tx, ty in data.get("removed_wilds", []):
            if 0 <= tx < MAP_WIDTH and 0 <= ty < MAP_HEIGHT:
                self.base_map[ty][tx] = TILE_GRASS
                self.tilemap[ty][tx] = TILE_GRASS
