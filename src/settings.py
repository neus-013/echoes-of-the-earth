import pygame

# Display
GAME_TITLE = "Echoes of the Earth"
INTERNAL_WIDTH = 640
INTERNAL_HEIGHT = 360
TILE_SIZE = 32
FPS = 60

# Day duration in real seconds (Phase 0: 5 minutes)
DAY_DURATION_SECONDS = 300
DAY_START_HOUR = 6.0
DAY_END_HOUR = 26.0  # 2:00 AM = 26:00 for continuous math
HOURS_PER_DAY = DAY_END_HOUR - DAY_START_HOUR  # 20 in-game hours

# Player
PLAYER_SPEED = 120  # pixels per second
PLAYER_MAX_ENERGY = 100
ENERGY_COST_HIT = 5
ENERGY_COST_PICK = 2
ENERGY_BERRY_RESTORE = 15
RESOURCE_HP = 4  # hits to break tree/rock
PLAYER_HITBOX_W = 14
PLAYER_HITBOX_H = 10
PLAYER_SPRITE_W = 19
PLAYER_SPRITE_H = 40
PLAYER_WALK_FRAMES = 4
PLAYER_IDLE_FRAME = 2

# Inventory
INVENTORY_SLOTS = 10
TOOLBAR_VISIBLE = 5

# PG rewards (Phase 0)
PG_WOOD = 5
PG_STONE = 5
PG_BERRIES = 2

# Resource yields
YIELD_WOOD = 2
YIELD_STONE = 2
YIELD_BERRIES = 3

# ── Tile types ──────────────────────────────────────────────────
TILE_GRASS = 0
TILE_TREE = 1
TILE_ROCK = 2
TILE_BERRY = 3
TILE_CAMPFIRE = 4
TILE_BORDER = 5
TILE_WATER = 6
TILE_BED = 7
TILE_TILLED = 8
TILE_CHEST = 9
TILE_WILD_MORA = 10
TILE_WILD_POTATO = 11
TILE_WILD_WHEAT = 12
TILE_WILD_PUMPKIN = 13
TILE_DIRT = 14
TILE_WATERED = 15  # NEW: Watered tilled tile

BLOCKING_TILES = {
    TILE_TREE, TILE_ROCK, TILE_BERRY, TILE_CAMPFIRE,
    TILE_BORDER, TILE_WATER, TILE_BED, TILE_CHEST,
}

WILD_TILES = {TILE_WILD_MORA, TILE_WILD_POTATO, TILE_WILD_WHEAT, TILE_WILD_PUMPKIN}

# Facing directions
FACING_DOWN = "down"
FACING_UP = "up"
FACING_LEFT = "left"
FACING_RIGHT = "right"

FACING_OFFSETS = {
    FACING_DOWN: (0, 1),
    FACING_UP: (0, -1),
    FACING_LEFT: (-1, 0),
    FACING_RIGHT: (1, 0),
}

# ── Item IDs ────────────────────────────────────────────────────
ITEM_WOOD = "wood"
ITEM_STONE = "stone"
ITEM_BERRIES = "berries"

# Seeds
ITEM_SEED_MORA = "seed_mora"
ITEM_SEED_POTATO = "seed_potato"
ITEM_SEED_WHEAT = "seed_wheat"
ITEM_SEED_PUMPKIN = "seed_pumpkin"

# Harvested crops
ITEM_MORA = "mora"
ITEM_POTATO = "potato"
ITEM_WHEAT = "wheat"
ITEM_PUMPKIN = "pumpkin"

# Craftable items
ITEM_CHEST = "chest"

ALL_SEED_ITEMS = {ITEM_SEED_MORA, ITEM_SEED_POTATO, ITEM_SEED_WHEAT, ITEM_SEED_PUMPKIN}

# Edible items: item_id → energy restored
EDIBLE_ITEMS = {
    ITEM_BERRIES: 15,
    ITEM_MORA: 20,
    ITEM_POTATO: 25,
    ITEM_WHEAT: 10,
    ITEM_PUMPKIN: 30,
}

# ── Tool IDs ────────────────────────────────────────────────────

# Tool IDs
TOOL_STONE = "stone_tool"      # Pedra
TOOL_HOE = "hoe"               # Aixada
TOOL_WATER_BUCKET = "water_bucket"  # Cubell
TOOL_WATER_BARREL = "water_barrel"  # Bóta
TOOL_AXE = "axe"               # Destral
TOOL_HAMMER = "hammer"         # Martell

WATER_BARREL_CAPACITY = 10
WATER_BUCKET_CAPACITY = 20
HOLD_EXTRA_TILES = 2   # extra tiles when holding click (hoe / bucket)

# ── Energy costs (farming) ──────────────────────────────────────
ENERGY_COST_TILL_STONE = 3
ENERGY_COST_TILL_HOE = 1
ENERGY_COST_WATER = 1
ENERGY_COST_PLANT = 1
ENERGY_COST_HARVEST = 1

# ── Crop definitions ────────────────────────────────────────────
CROP_MORA = "mora"
CROP_POTATO = "potato"
CROP_WHEAT = "wheat"
CROP_PUMPKIN = "pumpkin"

CROPS = {
    CROP_MORA: {
        "name_key": "crop_mora",
        "seed": ITEM_SEED_MORA,
        "harvest_item": ITEM_MORA,
        "grow_days": 2,
        "regrows": True,
        "yield_qty": 2,
        "seed_yield": 1,
    },
    CROP_POTATO: {
        "name_key": "crop_potato",
        "seed": ITEM_SEED_POTATO,
        "harvest_item": ITEM_POTATO,
        "grow_days": 3,
        "regrows": False,
        "yield_qty": 2,
        "seed_yield": 2,
    },
    CROP_WHEAT: {
        "name_key": "crop_wheat",
        "seed": ITEM_SEED_WHEAT,
        "harvest_item": ITEM_WHEAT,
        "grow_days": 3,
        "regrows": True,
        "yield_qty": 3,
        "seed_yield": 2,
    },
    CROP_PUMPKIN: {
        "name_key": "crop_pumpkin",
        "seed": ITEM_SEED_PUMPKIN,
        "harvest_item": ITEM_PUMPKIN,
        "grow_days": 5,
        "regrows": False,
        "yield_qty": 1,
        "seed_yield": 1,
    },
}

SEED_TO_CROP = {
    ITEM_SEED_MORA: CROP_MORA,
    ITEM_SEED_POTATO: CROP_POTATO,
    ITEM_SEED_WHEAT: CROP_WHEAT,
    ITEM_SEED_PUMPKIN: CROP_PUMPKIN,
}

WILD_TILE_TO_CROP = {
    TILE_WILD_MORA: CROP_MORA,
    TILE_WILD_POTATO: CROP_POTATO,
    TILE_WILD_WHEAT: CROP_WHEAT,
    TILE_WILD_PUMPKIN: CROP_PUMPKIN,
}

# ── Farming PG ──────────────────────────────────────────────────
PG_FIRST_PLANT = 10     # first time planting each crop type
PG_HARVEST = {
    CROP_MORA: 3,
    CROP_POTATO: 4,
    CROP_WHEAT: 4,
    CROP_PUMPKIN: 6,
}

# ── Quality ─────────────────────────────────────────────────────
QUALITY_NORMAL = 0
QUALITY_GOOD = 1
HARVESTS_FOR_QUALITY = 10

# ── Crafting recipes ────────────────────────────────────────────
CRAFTING_RECIPES = [
    {
        "id": "craft_hoe",
        "result": TOOL_HOE,
        "result_type": "tool",
        "ingredients": {ITEM_WOOD: 5, ITEM_STONE: 3},
        "name_key": "craft_hoe",
    },
    {
        "id": "craft_water_bucket",
        "result": TOOL_WATER_BUCKET,
        "result_type": "tool",
        "ingredients": {ITEM_WOOD: 4, ITEM_STONE: 2},
        "name_key": "craft_water_bucket",
    },
    {
        "id": "craft_axe",
        "result": TOOL_AXE,
        "result_type": "tool",
        "ingredients": {ITEM_WOOD: 8, ITEM_STONE: 4},
        "name_key": "craft_axe",
    },
    {
        "id": "craft_hammer",
        "result": TOOL_HAMMER,
        "result_type": "tool",
        "ingredients": {ITEM_WOOD: 4, ITEM_STONE: 8},
        "name_key": "craft_hammer",
    },
    {
        "id": "craft_chest",
        "result": ITEM_CHEST,
        "result_type": "item",
        "ingredients": {ITEM_WOOD: 10, ITEM_STONE: 2},
        "name_key": "craft_chest",
    },
]

# ── Chest ───────────────────────────────────────────────────────
CHEST_SLOTS = 20

# ── Map (60×60, generated procedurally in world.py) ────────────
MAP_WIDTH = 60
MAP_HEIGHT = 60
FARM_ORIGIN_X = 10
FARM_ORIGIN_Y = 10
FARM_WIDTH = 40
FARM_HEIGHT = 40

PLAYER_START_X = 30 * TILE_SIZE + TILE_SIZE // 2
PLAYER_START_Y = 31 * TILE_SIZE + TILE_SIZE // 2

# Colors – Roots of Pacha warm earthy palette
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
COL_BG = (22, 18, 14)
COL_GRASS_1 = (126, 166, 60)
COL_GRASS_2 = (114, 150, 52)
COL_GRASS_3 = (100, 138, 48)
COL_GRASS_DARK = (78, 110, 40)
COL_GRASS_GOLD = (158, 178, 68)
COL_EARTH = (120, 88, 56)
COL_EARTH_DARK = (90, 65, 42)
COL_TREE_TRUNK = (110, 76, 44)
COL_TREE_TRUNK_HI = (138, 98, 58)
COL_TREE_TRUNK_LO = (78, 52, 30)
COL_TREE_CANOPY = (62, 130, 48)
COL_TREE_CANOPY_HI = (90, 156, 62)
COL_TREE_CANOPY_LO = (42, 100, 34)
COL_TREE_CANOPY_DEEP = (30, 80, 26)
COL_ROCK = (158, 148, 128)
COL_ROCK_HI = (180, 170, 150)
COL_ROCK_SHADOW = (110, 102, 88)
COL_ROCK_WARM = (145, 128, 105)
COL_BERRY_BUSH = (68, 120, 50)
COL_BERRY_BUSH_HI = (88, 145, 64)
COL_BERRY = (195, 52, 55)
COL_BERRY_HI = (225, 85, 80)
COL_CAMPFIRE_LOG = (90, 58, 32)
COL_CAMPFIRE_FIRE = (255, 168, 48)
COL_CAMPFIRE_FIRE2 = (255, 120, 32)
COL_CAMPFIRE_GLOW = (255, 200, 100)
COL_WATER_1 = (68, 138, 185)
COL_WATER_2 = (55, 118, 165)
COL_WATER_HI = (105, 175, 210)
COL_WATER_DEEP = (40, 95, 140)
COL_BORDER = (28, 52, 22)
COL_BORDER_HI = (38, 68, 30)
COL_UI_BG = (42, 32, 24)
COL_UI_TEXT = (245, 238, 220)
COL_UI_HIGHLIGHT = (255, 215, 90)
COL_UI_SELECTED = (210, 168, 60)
COL_ENERGY_BAR = (120, 195, 85)
COL_ENERGY_LOW = (200, 80, 65)
COL_ENERGY_BG = (55, 42, 32)
COL_TITLE_BG = (18, 28, 16)
COL_MENU_BG = (32, 48, 28)
COL_TITLE_SKY_TOP = (42, 68, 95)
COL_TITLE_SKY_MID = (85, 115, 130)
COL_TITLE_SKY_BOT = (145, 155, 120)
COL_TITLE_GROUND = (78, 110, 40)
COL_TILLED = (140, 100, 62)
COL_TILLED_DARK = (100, 72, 44)
COL_WATERED = (95, 72, 48)

# ── Base colors in the original sprite PNGs (for palette-swap) ──
SPRITE_BASE_SKIN = [(217, 160, 126), (138, 100, 76)]
SPRITE_BASE_HAIR = [(175, 131, 111), (115, 81, 74), (74, 52, 51), (44, 26, 29)]
SPRITE_BASE_OUTFIT = [(57, 124, 63), (35, 95, 43), (20, 63, 28)]
SPRITE_BASE_EYES = [(153, 175, 55), (84, 111, 34)]

# Replacement palettes (same length as their base)
SKIN_PALETTES = [
    [(217, 160, 126), (138, 100, 76)],           # Original
    [(240, 210, 178), (170, 135, 105)],           # Rosada
    [(185, 135, 95), (120, 82, 55)],              # Morena
    [(120, 80, 50), (75, 50, 30)],                # Fosca
]

HAIR_PALETTES = [
    [(175, 131, 111), (115, 81, 74), (74, 52, 51), (44, 26, 29)],  # Marró (original)
    [(70, 65, 65), (50, 45, 45), (32, 30, 30), (18, 15, 15)],      # Negre
    [(225, 200, 140), (195, 165, 105), (155, 125, 70), (115, 88, 45)],  # Ros
    [(210, 120, 70), (175, 85, 45), (130, 55, 25), (90, 35, 15)],  # Pèl-roig
    [(230, 225, 220), (190, 185, 180), (150, 145, 140), (110, 105, 100)],  # Blanc/gris
]

OUTFIT_PALETTES = [
    [(57, 124, 63), (35, 95, 43), (20, 63, 28)],            # Verd (original)
    [(65, 95, 155), (42, 68, 118), (24, 44, 80)],           # Blau
    [(155, 62, 58), (118, 42, 40), (80, 24, 24)],           # Vermell
    [(145, 115, 72), (110, 82, 50), (72, 55, 32)],          # Marró
    [(125, 72, 145), (92, 50, 110), (60, 30, 75)],          # Lila
]

EYE_PALETTES = [
    [(153, 175, 55), (84, 111, 34)],     # Verd (original)
    [(85, 135, 195), (48, 88, 145)],     # Blau
    [(135, 95, 52), (88, 60, 32)],       # Marró
    [(185, 155, 52), (135, 105, 32)],    # Ambre
]

# Preview swatch color (brightest shade) for each palette
SKIN_SWATCH = [p[0] for p in SKIN_PALETTES]
HAIR_SWATCH = [p[0] for p in HAIR_PALETTES]
OUTFIT_SWATCH = [p[0] for p in OUTFIT_PALETTES]
EYE_SWATCH = [p[0] for p in EYE_PALETTES]

# ── Multiplayer ─────────────────────────────────────────────────
MAX_PLAYERS = 4
NET_PORT = 7777
DISCOVERY_PORT = 7778  # UDP port for game code discovery
NET_TICK_RATE = 20  # state updates per second from server

# Bed positions around the campfire (relative to MAP center)
# campfire is at (center_x, center_y); beds surround it
_CX = MAP_WIDTH // 2
_CY = MAP_HEIGHT // 2
BED_POSITIONS = [
    (_CX + 1, _CY),      # East
    (_CX - 1, _CY),      # West
    (_CX, _CY + 1),      # South
    (_CX, _CY - 1),      # North
]
# Player spawn positions (adjacent to their bed, one tile further from campfire)
PLAYER_SPAWNS = [
    ((_CX + 2) * TILE_SIZE + TILE_SIZE // 2, _CY * TILE_SIZE + TILE_SIZE // 2),
    ((_CX - 2) * TILE_SIZE + TILE_SIZE // 2, _CY * TILE_SIZE + TILE_SIZE // 2),
    (_CX * TILE_SIZE + TILE_SIZE // 2, (_CY + 2) * TILE_SIZE + TILE_SIZE // 2),
    (_CX * TILE_SIZE + TILE_SIZE // 2, (_CY - 2) * TILE_SIZE + TILE_SIZE // 2),
]
