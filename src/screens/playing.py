import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, TILE_SIZE,
    COL_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, COL_UI_BG, COL_UI_SELECTED,
    PLAYER_MAX_ENERGY, FACING_DOWN, FACING_UP, FACING_LEFT, FACING_RIGHT,
    TILE_GRASS, TILE_TREE, TILE_ROCK, TILE_BERRY, TILE_TILLED, TILE_CHEST,
    TILE_WATER, TILE_BED, TILE_DIRT, WILD_TILES,
    TOOL_STONE, TOOL_HOE, TOOL_WATER_BUCKET,
    ENERGY_COST_HIT, ENERGY_COST_PICK, ENERGY_COST_TILL_STONE, ENERGY_COST_TILL_HOE,
    ENERGY_COST_WATER, ENERGY_COST_PLANT, ENERGY_COST_HARVEST,
    HOLD_EXTRA_TILES, FACING_OFFSETS, ITEM_BERRIES, ITEM_CHEST, ITEM_WOOD, ITEM_STONE,
    SEED_TO_CROP, CROPS, CRAFTING_RECIPES, CHEST_SLOTS,
    PLAYER_START_X, PLAYER_START_Y, MAP_WIDTH, MAP_HEIGHT,
    WHITE, EDIBLE_ITEMS, ALL_SEED_ITEMS, TOOLBAR_VISIBLE,
    PG_FIRST_PLANT, NET_TICK_RATE,
)
from src.i18n import t
from src.ui import HUD, draw_text, draw_button, _get_item_icon
from src.world import World
from src.player import Player
from src.systems.time_system import TimeSystem
from src.systems.inventory import Inventory
from src.systems.tools import ToolManager
from src.systems.farming import FarmingSystem
from src.systems.crafting import can_craft, do_craft


class PlayingScreen:
    def __init__(self, game):
        self.game = game
        self.world = World()
        self.time_system = TimeSystem()
        self.inventory = Inventory()
        self.tool_manager = ToolManager()
        self.farming = FarmingSystem()
        self.hud = HUD()
        self.player = None
        self.daily_items = {}
        self.daily_pg = 0
        self.planted_types = set()   # crop types planted at least once (for first-plant PG)

        # Sub-states
        self.paused = False
        self.sleep_prompt = False
        self.pause_selected = 0
        self.font = pygame.font.SysFont("arial", 16)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.font_tiny = pygame.font.SysFont("arial", 11)

        # Interaction cooldown
        self.interact_cooldown = 0.0

        # Hold state (for bucket watering / hoe tilling adjacent tiles)
        self.hold_info = None   # {"tx": int, "ty": int, "timer": float, "type": str, "done": bool}

        # Overlay states
        self.crafting_open = False
        self.chest_open = False
        self.chest_pos = None

        # Button rects
        self.pause_rects = []
        self.sleep_rects = []
        self.craft_rects = []
        self.chest_slot_rects = []
        self.chest_inv_rects = []

        # ── Multiplayer state ──
        self.is_multiplayer = False
        self.is_host = False
        self.local_player_id = 0
        self.server = None   # Server (host only)
        self.client = None   # Client (client only)
        self.players = {}    # pid -> Player object
        self.inventories = {}    # pid -> Inventory
        self.tool_managers = {}  # pid -> ToolManager
        self.planted_types_all = {}  # pid -> set
        self.sleeping_players = set()  # pids currently sleeping
        self.waiting_for_sleep = False  # True when local player is waiting for others to sleep
        self.net_timer = 0.0
        self.disconnected_msg = ""
        self.user_ids = {}  # pid -> user_id (for saving)

    def on_enter(self, **kwargs):
        data = self.game.data
        mode = data.get("mode", "solo")
        self.is_multiplayer = (mode == "multi")
        self.is_host = data.get("is_host", True)
        self.local_player_id = data.get("local_player_id", 0)
        self.sleeping_players = set()
        self.waiting_for_sleep = False
        self.disconnected_msg = ""
        self.net_timer = 0.0

        if self.is_multiplayer:
            self.server = data.get("server")
            self.client = data.get("client")
            num_players = data.get("num_players", 2)
            self.world = World(num_players=num_players)
            self.world.from_save_data(data.get("world_data"))

            # Create all player objects + per-player inventories/tools
            self.players = {}
            self.inventories = {}
            self.tool_managers = {}
            self.planted_types_all = {}
            self.user_ids = {}

            for pdata in data.get("players", []):
                pid = pdata["id"]
                avatar = pdata.get("avatar", {"skin": 0, "hair_color": 0, "outfit": 0, "eyes": 0})
                cx = pdata.get("cx", PLAYER_START_X)
                cy = pdata.get("cy", PLAYER_START_Y)
                p = Player(cx, cy, avatar, name=pdata.get("name", ""))
                p.facing = pdata.get("facing", FACING_DOWN)
                p.energy = pdata.get("energy", PLAYER_MAX_ENERGY)
                self.players[pid] = p
                self.user_ids[pid] = pdata.get("user_id", "")

                inv = Inventory()
                inv.from_list(pdata.get("inventory", []))
                self.inventories[pid] = inv

                tm = ToolManager()
                tm.from_save_data(pdata.get("tools_data"))
                self.tool_managers[pid] = tm

                self.planted_types_all[pid] = set(pdata.get("planted_types", []))

            # Point self.player/inventory/tool_manager to local player
            self.player = self.players.get(self.local_player_id)
            self.inventory = self.inventories.get(self.local_player_id, Inventory())
            self.tool_manager = self.tool_managers.get(self.local_player_id, ToolManager())
            self.planted_types = self.planted_types_all.get(self.local_player_id, set())
        else:
            # Solo mode — original logic
            avatar = data.get("avatar", {"skin": 0, "hair_color": 0, "outfit": 0, "eyes": 0})
            cx = data.get("player_cx", PLAYER_START_X)
            cy = data.get("player_cy", PLAYER_START_Y)
            self.player = Player(cx, cy, avatar)
            self.player.facing = data.get("player_facing", FACING_DOWN)
            self.player.energy = data.get("energy", PLAYER_MAX_ENERGY)
            self.inventory.from_list(data.get("inventory", []))
            self.tool_manager.from_save_data(data.get("tools_data"))
            self.world.from_save_data(data.get("world_data"))
            self.players = {}
            self.server = None
            self.client = None

        self.farming.from_save_data(data.get("farming_data"))
        if not self.is_multiplayer:
            self.planted_types = set(data.get("planted_types", []))

        # Re-apply tilled tiles for plots that have crops
        for (tx, ty) in self.farming.plots:
            if self.world.get_tile(tx, ty) != TILE_TILLED:
                self.world.set_tile(tx, ty, TILE_TILLED)

        self.time_system.reset_day()
        self.daily_items = {}
        self.daily_pg = 0
        self.paused = False
        self.sleep_prompt = False
        self.crafting_open = False
        self.chest_open = False
        self.hold_info = None

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    # ── EVENT HANDLING ──────────────────────────────────────────────
    def handle_event(self, event):
        # Disconnected overlay: any key/click exits to menu
        if self.disconnected_msg:
            if event.type in (pygame.KEYDOWN, pygame.MOUSEBUTTONDOWN):
                self._exit_to_menu()
            return

        # Block all input while waiting for others to sleep
        if self.waiting_for_sleep:
            return

        # Route to active overlay first
        if self.chest_open:
            self._handle_chest_event(event)
            return
        if self.crafting_open:
            self._handle_crafting_event(event)
            return

        if event.type == pygame.KEYDOWN:
            if self.sleep_prompt:
                if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    self._go_to_sleep(passed_out=False)
                elif event.key == pygame.K_ESCAPE:
                    self.sleep_prompt = False
                return

            if self.paused:
                if event.key in (pygame.K_UP, pygame.K_w):
                    self.pause_selected = (self.pause_selected - 1) % 2
                elif event.key in (pygame.K_DOWN, pygame.K_s):
                    self.pause_selected = (self.pause_selected + 1) % 2
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if self.pause_selected == 0:
                        self.paused = False
                    else:
                        self._exit_to_menu()
                elif event.key == pygame.K_ESCAPE:
                    self.paused = False
                return

            # Normal gameplay input
            if event.key == pygame.K_ESCAPE:
                self.paused = True
                self.pause_selected = 0
            elif event.key == pygame.K_TAB:
                if self.tool_manager.active:
                    self.tool_manager.cycle()
                else:
                    self.inventory.toggle_page()
            elif event.key == pygame.K_q:
                self._try_eat_selected()

        elif event.type == pygame.MOUSEBUTTONDOWN:
            mx, my = self._to_internal(event.pos)

            if event.button == 1:  # Left click
                if self.sleep_prompt:
                    for i, rect in enumerate(self.sleep_rects):
                        if rect and rect.collidepoint(mx, my):
                            if i == 0:
                                self._go_to_sleep(passed_out=False)
                            else:
                                self.sleep_prompt = False
                            break
                    return

                if self.paused:
                    for i, rect in enumerate(self.pause_rects):
                        if rect and rect.collidepoint(mx, my):
                            self.pause_selected = i
                            if i == 0:
                                self.paused = False
                            else:
                                self._exit_to_menu()
                            break
                    return

                # Check tool slot click
                if self.hud.tool_slot_rect and self.hud.tool_slot_rect.collidepoint(mx, my):
                    self.tool_manager.active = True
                    self.inventory.selected_slot = -1
                    return

                # Check toolbar slot clicks
                if self.hud.toolbar_rects:
                    vis_start, _ = self.inventory.get_visible_range()
                    for i, rect in enumerate(self.hud.toolbar_rects):
                        if rect and rect.collidepoint(mx, my):
                            abs_idx = vis_start + i
                            if self.inventory.selected_slot == abs_idx:
                                self.inventory.selected_slot = -1  # deselect
                            else:
                                self.inventory.selected_slot = abs_idx
                                self.tool_manager.active = False
                            return

                # Check craft button
                if self.hud.craft_button_rect and self.hud.craft_button_rect.collidepoint(mx, my):
                    self.crafting_open = True
                    return

                # Gameplay left-click
                if self.interact_cooldown <= 0:
                    self._handle_world_click(mx, my)

            elif event.button in (4, 5):  # Scroll wheel
                direction = -1 if event.button == 4 else 1
                if self.tool_manager.active:
                    self.tool_manager.cycle(direction)
                else:
                    self.inventory.toggle_page()

        elif event.type == pygame.MOUSEBUTTONUP:
            if event.button == 1:
                self.hold_info = None

        elif event.type == pygame.MOUSEMOTION:
            if self.paused:
                mx, my = self._to_internal(event.pos)
                for i, rect in enumerate(self.pause_rects):
                    if rect and rect.collidepoint(mx, my):
                        self.pause_selected = i
                        break

    # ── WORLD CLICK ─────────────────────────────────────────────────
    def _handle_world_click(self, mx, my):
        cam = self.world.camera
        wx = mx + cam.x
        wy = my + cam.y
        tx = int(wx // TILE_SIZE)
        ty = int(wy // TILE_SIZE)

        px, py = self.player.tile_x, self.player.tile_y
        dx = tx - px
        dy = ty - py

        # Must be adjacent (including diagonals) or the player's own tile
        if abs(dx) > 1 or abs(dy) > 1:
            return

        # Face toward clicked tile (skip if clicking own tile)
        if dx != 0 or dy != 0:
            if abs(dx) >= abs(dy):
                self.player.facing = FACING_RIGHT if dx > 0 else FACING_LEFT
            else:
                self.player.facing = FACING_DOWN if dy > 0 else FACING_UP

        self._do_tile_action(tx, ty)
        self.interact_cooldown = 0.25

        # In multiplayer, send action to server for sync
        if self.is_multiplayer and not self.is_host and self.client:
            self.client.send({
                "type": "action", "action": "tile_action",
                "tx": tx, "ty": ty,
            })

    def _do_tile_action(self, tx, ty):
        """Main interaction dispatch based on current tool + target tile."""
        if tx < 0 or ty < 0 or tx >= MAP_WIDTH or ty >= MAP_HEIGHT:
            return

        tile = self.world.get_tile(tx, ty)

        # ── Context-free interactions (work regardless of tool/inventory) ──
        if tile == TILE_BED:
            self.sleep_prompt = True
            return

        if tile == TILE_CHEST:
            self.chest_pos = (tx, ty)
            self.chest_open = True
            return

        # ── Tool-specific actions (only when tool is active) ──
        if self.tool_manager.active:
            tool = self.tool_manager.current

            if tool == TOOL_STONE:
                # Till dirt
                if tile == TILE_DIRT:
                    if self.player.energy < ENERGY_COST_TILL_STONE:
                        self.hud.add_message(t("msg_no_energy"), 2.0)
                        return
                    if self.world.till_soil(tx, ty):
                        self.player.energy -= ENERGY_COST_TILL_STONE
                        self.hud.add_message(t("msg_tilled"), 1.0)
                        return

                # Hit tree / rock
                if tile in (TILE_TREE, TILE_ROCK):
                    if self.player.energy < ENERGY_COST_HIT:
                        self.hud.add_message(t("msg_no_energy"), 2.0)
                        return
                    result = self.world.hit_resource(tx, ty)
                    self.player.energy -= ENERGY_COST_HIT
                    self.player.flash_timer = 0.1
                    if result:
                        item_id, qty, _ = result
                        if self.inventory.can_add(item_id):
                            self.inventory.add_item(item_id, qty)
                            item_name = t(f"item_{item_id}")
                            self.hud.add_message(f"+{qty} {item_name}", 1.5)
                            self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty
                        else:
                            self.hud.add_message(t("msg_inventory_full"), 2.0)
                    else:
                        hp = self.world.get_resource_hp(tx, ty)
                        self.hud.add_message(f"({hp})", 0.5)
                    return

            if tool == TOOL_HOE:
                # Hoe ONLY tills — no hitting trees/rocks
                if tile == TILE_DIRT:
                    if self.player.energy < ENERGY_COST_TILL_HOE:
                        self.hud.add_message(t("msg_no_energy"), 2.0)
                        return
                    if self.world.till_soil(tx, ty):
                        self.player.energy -= ENERGY_COST_TILL_HOE
                        self.hud.add_message(t("msg_tilled"), 1.0)
                        # Start hold timer for tilling extra tiles in facing direction
                        self.hold_info = {"tx": tx, "ty": ty, "timer": 0.0, "type": "hoe", "done": False}
                        return

            if tool == TOOL_WATER_BUCKET:
                # Fill at water tile
                if tile == TILE_WATER:
                    filled = self.tool_manager.fill_water()
                    if filled > 0:
                        self.hud.add_message(t("msg_water_filled"), 1.5)
                    else:
                        self.hud.add_message(t("msg_water_full"), 1.0)
                    return

                # Water any tilled soil (with or without crop)
                if tile == TILE_TILLED:
                    if self.tool_manager.get_water() <= 0:
                        self.hud.add_message(t("msg_water_empty"), 1.5)
                        return
                    if self.player.energy < ENERGY_COST_WATER:
                        self.hud.add_message(t("msg_no_energy"), 2.0)
                        return
                    self.farming.water(tx, ty)
                    self.tool_manager.use_water()
                    self.player.energy -= ENERGY_COST_WATER
                    self.hud.add_message(t("msg_watered"), 1.0)
                    # Start hold timer for direction-based adjacent watering
                    self.hold_info = {"tx": tx, "ty": ty, "timer": 0.0, "type": "water", "done": False}
                    return

                # Click any other tile with bucket → waste 1 water
                if self.tool_manager.get_water() > 0:
                    self.tool_manager.use_water()
                    self.hud.add_message(t("msg_water_wasted"), 1.0)
                else:
                    self.hud.add_message(t("msg_water_empty"), 1.5)
                return

        # ── Generic interactions (work regardless of tool/inventory) ──
        # Harvest mature crop
        if tile == TILE_TILLED and self.farming.is_mature(tx, ty):
            if self.player.energy < ENERGY_COST_HARVEST:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            result = self.farming.harvest(tx, ty)
            if result:
                item_id, qty, quality, pg = result
                if not self.inventory.can_add(item_id, quality):
                    self.hud.add_message(t("msg_inventory_full"), 2.0)
                    return
                self.inventory.add_item(item_id, qty, quality)
                self.player.energy -= ENERGY_COST_HARVEST
                item_name = t(f"item_{item_id}")
                q_text = f" ({t('quality_good')})" if quality > 0 else ""
                self.hud.add_message(f"+{qty} {item_name}{q_text}", 1.5)
                self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty
                self.daily_pg += pg
                if (tx, ty) not in self.farming.plots:
                    pass  # stays TILE_TILLED
            return

        # Plant seed on empty tilled soil (from selected inventory slot)
        if tile == TILE_TILLED and not self.farming.get_crop(tx, ty):
            selected = self.inventory.get_selected_item()
            if selected and selected["item"] in ALL_SEED_ITEMS:
                if self.player.energy < ENERGY_COST_PLANT:
                    self.hud.add_message(t("msg_no_energy"), 2.0)
                    return
                self._plant_seed(tx, ty, selected["item"])
                # Clear selection if slot is now empty
                if self.inventory.get_selected_item() is None:
                    self.inventory.selected_slot = -1
            else:
                self.hud.add_message(t("msg_need_seeds"), 1.5)
            return

        # Berry bush
        if tile == TILE_BERRY and (tx, ty) not in self.world.harvested:
            if self.player.energy < ENERGY_COST_PICK:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            result = self.world.hit_resource(tx, ty)
            if result:
                item_id, qty, _ = result
                if self.inventory.can_add(item_id):
                    self.inventory.add_item(item_id, qty)
                    self.player.energy -= ENERGY_COST_PICK
                    item_name = t(f"item_{item_id}")
                    self.hud.add_message(f"+{qty} {item_name}", 1.5)
                    self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty
                else:
                    self.hud.add_message(t("msg_inventory_full"), 2.0)
            return

        # Wild crop harvest
        if tile in WILD_TILES and (tx, ty) not in self.world.harvested:
            if self.player.energy < ENERGY_COST_PICK:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            result = self.world.harvest_wild(tx, ty)
            if result:
                seed_item, qty = result
                if self.inventory.can_add(seed_item):
                    self.inventory.add_item(seed_item, qty)
                    self.player.energy -= ENERGY_COST_PICK
                    item_name = t(f"item_{seed_item}")
                    self.hud.add_message(f"+{qty} {item_name}", 1.5)
                    self.daily_items[seed_item] = self.daily_items.get(seed_item, 0) + qty
                else:
                    self.hud.add_message(t("msg_inventory_full"), 2.0)
            return

        # Place chest
        if tile == TILE_GRASS and self.inventory.count_item(ITEM_CHEST) > 0:
            if self.world.place_chest(tx, ty):
                self.inventory.remove_item(ITEM_CHEST, 1)
                self.hud.add_message(t("msg_chest_placed"), 1.5)
            return

    def _plant_seed(self, tx, ty, seed_item):
        crop_id = SEED_TO_CROP.get(seed_item)
        if not crop_id:
            return
        if self.farming.plant(tx, ty, seed_item):
            self.inventory.remove_item(seed_item, 1)
            self.player.energy -= ENERGY_COST_PLANT
            crop_name = t(CROPS[crop_id]["name_key"])
            self.hud.add_message(f"{t('msg_planted')} {crop_name}", 1.5)
            # First-plant PG bonus
            if crop_id not in self.planted_types:
                self.planted_types.add(crop_id)
                self.daily_pg += PG_FIRST_PLANT
                self.hud.add_message(f"+{PG_FIRST_PLANT} PG!", 2.0)

    def _try_eat_selected(self):
        """Try to eat the item in the selected inventory slot."""
        selected = self.inventory.get_selected_item()
        if not selected:
            return
        item_id = selected["item"]
        restore = EDIBLE_ITEMS.get(item_id)
        if restore is None:
            self.hud.add_message(t("msg_cant_eat"), 1.0)
            return
        if self.player.eat_food(self.inventory, item_id, restore):
            item_name = t(f"item_{item_id}")
            self.hud.add_message(f"+{item_name} → {t('hud_energy')}", 1.5)
            # Clear selection if slot is now empty
            if self.inventory.get_selected_item() is None:
                self.inventory.selected_slot = -1

    def _hold_extra_hoe(self, tx, ty):
        """Till up to HOLD_EXTRA_TILES tiles ahead in facing direction."""
        fdx, fdy = FACING_OFFSETS[self.player.facing]
        tilled = 0
        for step in range(1, HOLD_EXTRA_TILES + 1):
            ntx, nty = tx + fdx * step, ty + fdy * step
            if (self.world.get_tile(ntx, nty) == TILE_DIRT
                    and self.player.energy >= ENERGY_COST_TILL_HOE):
                if self.world.till_soil(ntx, nty):
                    self.player.energy -= ENERGY_COST_TILL_HOE
                    tilled += 1
        if tilled > 0:
            self.hud.add_message(t("msg_tilled"), 1.0)

    def _hold_extra_water(self, tx, ty):
        """Water up to HOLD_EXTRA_TILES adjacent tiles perpendicular to facing direction."""
        facing = self.player.facing
        # Up/Down → water horizontally (left, right)
        # Left/Right → water vertically (up, down)
        if facing in (FACING_UP, FACING_DOWN):
            offsets = [(-1, 0), (1, 0)]
        else:
            offsets = [(0, -1), (0, 1)]
        watered = 0
        for odx, ody in offsets:
            if watered >= HOLD_EXTRA_TILES:
                break
            ntx, nty = tx + odx, ty + ody
            if (self.world.get_tile(ntx, nty) == TILE_TILLED
                    and self.tool_manager.get_water() > 0):
                self.farming.water(ntx, nty)
                self.tool_manager.use_water()
                watered += 1
        if watered > 0:
            self.hud.add_message(t("msg_watered"), 1.0)

    # ── CRAFTING OVERLAY ────────────────────────────────────────────
    def _handle_crafting_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.crafting_open = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.craft_rects):
                if rect and rect.collidepoint(mx, my):
                    recipe = CRAFTING_RECIPES[i]
                    if can_craft(recipe, self.inventory):
                        if do_craft(recipe, self.inventory, self.tool_manager):
                            name = t(recipe["name_key"])
                            self.hud.add_message(f"{t('msg_crafted')} {name}", 2.0)
                    else:
                        self.hud.add_message(t("msg_cant_craft"), 1.5)
                    return
            # Click outside panel = close
            self.crafting_open = False

    def _draw_crafting(self, surface):
        pw, ph = 220, 30 + len(CRAFTING_RECIPES) * 48
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2

        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        pygame.draw.rect(surface, COL_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(surface, COL_UI_SELECTED, (px, py, pw, ph), 1)

        draw_text(surface, t("craft_title"), px + pw // 2, py + 8, self.font_small,
                  COL_UI_HIGHLIGHT, center=True)

        self.craft_rects = []
        for i, recipe in enumerate(CRAFTING_RECIPES):
            ry = py + 26 + i * 48
            rect = pygame.Rect(px + 6, ry, pw - 12, 44)
            self.craft_rects.append(rect)

            # Tool already owned check
            already_owned = (
                recipe["result_type"] == "tool"
                and self.tool_manager.has_tool(recipe["result"])
            )
            craftable = can_craft(recipe, self.inventory) and not already_owned
            bg_col = (55, 45, 32) if craftable else (40, 32, 24)
            pygame.draw.rect(surface, bg_col, rect)
            border_col = COL_UI_HIGHLIGHT if craftable else (80, 70, 60)
            pygame.draw.rect(surface, border_col, rect, 1)

            # Recipe name
            name = t(recipe["name_key"])
            draw_text(surface, name, px + 12, ry + 4, self.font_tiny, COL_UI_TEXT)

            # Ingredients
            ing_texts = []
            for item_id, needed in recipe["ingredients"].items():
                have = self.inventory.count_item(item_id)
                iname = t(f"item_{item_id}")
                col = (120, 200, 100) if have >= needed else (200, 80, 65)
                ing_texts.append((f"{iname}: {have}/{needed}", col))

            ix = px + 12
            for txt, col in ing_texts:
                ts = self.font_tiny.render(txt, False, col)
                surface.blit(ts, (ix, ry + 18))
                ix += ts.get_width() + 10

            # Craft button label
            if craftable:
                draw_text(surface, t("craft_do"), px + pw - 50, ry + 30, self.font_tiny,
                          COL_UI_HIGHLIGHT)

    # ── CHEST OVERLAY ───────────────────────────────────────────────
    def _handle_chest_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.chest_open = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)

            chest = self.world.get_chest(self.chest_pos[0], self.chest_pos[1])
            if not chest:
                self.chest_open = False
                return

            # Click on chest slot → move to inventory
            for i, rect in enumerate(self.chest_slot_rects):
                if rect and rect.collidepoint(mx, my):
                    if chest[i]:
                        slot = chest[i]
                        q = slot.get("quality", 0)
                        if self.inventory.can_add(slot["item"], q):
                            self.inventory.add_item(slot["item"], slot["qty"], q)
                            chest[i] = None
                        else:
                            self.hud.add_message(t("msg_inventory_full"), 1.5)
                    return

            # Click on inventory slot → move to chest
            for i, rect in enumerate(self.chest_inv_rects):
                if rect and rect.collidepoint(mx, my):
                    if i < len(self.inventory.slots) and self.inventory.slots[i]:
                        slot = self.inventory.slots[i]
                        # Find empty chest slot
                        for ci in range(len(chest)):
                            if chest[ci] is None:
                                chest[ci] = slot.copy()
                                self.inventory.slots[i] = None
                                break
                        else:
                            self.hud.add_message(t("msg_chest_full"), 1.5)
                    return

            # Click outside = close
            self.chest_open = False

    def _draw_chest(self, surface):
        chest = self.world.get_chest(self.chest_pos[0], self.chest_pos[1]) if self.chest_pos else None
        if not chest:
            return

        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        slot_size = 22
        padding = 3
        cols = 5
        rows_chest = (CHEST_SLOTS + cols - 1) // cols
        rows_inv = 2

        pw = cols * (slot_size + padding) + padding + 20
        ph = 30 + (rows_chest + rows_inv) * (slot_size + padding) + 30
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2

        pygame.draw.rect(surface, COL_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(surface, COL_UI_SELECTED, (px, py, pw, ph), 1)

        # Chest label
        draw_text(surface, t("chest_title"), px + pw // 2, py + 6, self.font_tiny,
                  COL_UI_HIGHLIGHT, center=True)

        self.chest_slot_rects = []
        base_x = px + 10
        base_y = py + 20

        for i in range(CHEST_SLOTS):
            row, col = divmod(i, cols)
            sx = base_x + col * (slot_size + padding)
            sy = base_y + row * (slot_size + padding)
            rect = pygame.Rect(sx, sy, slot_size, slot_size)
            self.chest_slot_rects.append(rect)
            pygame.draw.rect(surface, (60, 50, 38), rect)
            pygame.draw.rect(surface, (90, 80, 60), rect, 1)
            if chest[i]:
                icon = _get_item_icon(chest[i]["item"])
                surface.blit(icon, (sx + 3, sy + 3))
                if chest[i]["qty"] > 1:
                    qs = self.font_tiny.render(str(chest[i]["qty"]), False, WHITE)
                    surface.blit(qs, (sx + slot_size - qs.get_width() - 1, sy + slot_size - 10))

        # Inventory label
        inv_y = base_y + rows_chest * (slot_size + padding) + 10
        draw_text(surface, t("inv_title"), px + pw // 2, inv_y, self.font_tiny,
                  COL_UI_TEXT, center=True)
        inv_y += 14

        self.chest_inv_rects = []
        for i in range(len(self.inventory.slots)):
            row, col = divmod(i, cols)
            sx = base_x + col * (slot_size + padding)
            sy = inv_y + row * (slot_size + padding)
            rect = pygame.Rect(sx, sy, slot_size, slot_size)
            self.chest_inv_rects.append(rect)
            pygame.draw.rect(surface, (50, 42, 32), rect)
            pygame.draw.rect(surface, (80, 70, 55), rect, 1)
            slot = self.inventory.slots[i]
            if slot:
                icon = _get_item_icon(slot["item"])
                surface.blit(icon, (sx + 3, sy + 3))
                if slot["qty"] > 1:
                    qs = self.font_tiny.render(str(slot["qty"]), False, WHITE)
                    surface.blit(qs, (sx + slot_size - qs.get_width() - 1, sy + slot_size - 10))

    # ── SLEEP / PAUSE / MENU ────────────────────────────────────────
    def _go_to_sleep(self, passed_out=False):
        if self.is_multiplayer and not passed_out:
            # Voluntary sleep — signal and wait
            self.sleeping_players.add(self.local_player_id)
            self.sleep_prompt = False
            self.waiting_for_sleep = True
            if self.is_host:
                self._check_all_sleeping()
            else:
                if self.client:
                    self.client.send({"type": "sleep"})
            return

        # Actually transition to day summary (called when all sleep or day over)
        self._do_day_transition(passed_out)

    def _do_day_transition(self, passed_out=False):
        data = self.game.data

        if self.is_multiplayer:
            # Save all players' data
            players_save = []
            for pid in sorted(self.players.keys()):
                p = self.players[pid]
                inv = self.inventories.get(pid, Inventory())
                tm = self.tool_managers.get(pid, ToolManager())
                pt = self.planted_types_all.get(pid, set())
                pdata = {
                    "id": pid,
                    "name": p.name,
                    "avatar": p.avatar.copy(),
                    "user_id": self.user_ids.get(pid, ""),
                    "cx": p.cx, "cy": p.cy,
                    "facing": p.facing,
                    "energy": p.energy,
                    "inventory": inv.to_list(),
                    "tools_data": tm.to_save_data(),
                    "planted_types": list(pt),
                }
                players_save.append(pdata)

            data["players"] = players_save
            data["world_data"] = self.world.to_save_data()
            self.farming.advance_day()
            data["farming_data"] = self.farming.to_save_data()
        else:
            # Solo mode
            data["player_cx"] = self.player.cx
            data["player_cy"] = self.player.cy
            data["player_facing"] = self.player.facing
            data["energy"] = self.player.energy
            data["inventory"] = self.inventory.to_list()
            data["tools_data"] = self.tool_manager.to_save_data()
            data["world_data"] = self.world.to_save_data()
            data["planted_types"] = list(self.planted_types)
            self.farming.advance_day()
            data["farming_data"] = self.farming.to_save_data()

        from src.screens.day_summary import DaySummaryScreen
        self.game.change_screen(DaySummaryScreen, daily_items=self.daily_items,
                                daily_pg=self.daily_pg, passed_out=passed_out)

    def _exit_to_menu(self):
        self._cleanup_network()
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def _cleanup_network(self):
        if self.server:
            self.server.stop()
            self.server = None
            self.game.data.pop("server", None)
        if self.client:
            self.client.close()
            self.client = None
            self.game.data.pop("client", None)

    # ── UPDATE ──────────────────────────────────────────────────────
    def update(self, dt):
        if self.disconnected_msg:
            return
        if self.paused or self.sleep_prompt or self.crafting_open or self.chest_open:
            return

        # When waiting for others to sleep, only do network + HUD updates
        if self.waiting_for_sleep:
            self.hud.update(dt)
            if self.is_multiplayer:
                self._network_update(dt)
            return

        self.time_system.update(dt)
        if self.time_system.day_over:
            if self.is_multiplayer and not self.is_host:
                pass  # wait for host to signal day_over
            elif self.is_multiplayer and self.is_host:
                if self.server:
                    self.server.broadcast({"type": "day_over"})
                self._do_day_transition(passed_out=True)
                return
            else:
                self._go_to_sleep(passed_out=True)
                return

        keys = pygame.key.get_pressed()
        self.player.handle_input(keys, dt, self.world)
        self.player.update(dt)
        self.world.camera.follow(self.player.cx, self.player.cy)
        self.hud.update(dt)

        if self.interact_cooldown > 0:
            self.interact_cooldown -= dt

        # Hold logic: hoe tills extra / bucket waters extra
        if self.hold_info and not self.hold_info["done"]:
            if pygame.mouse.get_pressed()[0]:
                self.hold_info["timer"] += dt
                if self.hold_info["timer"] >= 0.3:
                    hx, hy = self.hold_info["tx"], self.hold_info["ty"]
                    if self.hold_info["type"] == "water":
                        self._hold_extra_water(hx, hy)
                    elif self.hold_info["type"] == "hoe":
                        self._hold_extra_hoe(hx, hy)
                    self.hold_info["done"] = True
            else:
                self.hold_info = None

        # Update remote players' animations
        if self.is_multiplayer:
            for pid, p in self.players.items():
                if pid != self.local_player_id:
                    p.update(dt)

        # Network polling
        if self.is_multiplayer:
            self._network_update(dt)

    # ── NETWORK ──────────────────────────────────────────────────────
    def _network_update(self, dt):
        self.net_timer += dt
        tick_interval = 1.0 / NET_TICK_RATE
        if self.is_host:
            self._host_network_poll()
            if self.net_timer >= tick_interval:
                self.net_timer -= tick_interval
                self._host_broadcast_state()
        else:
            self._client_network_poll()
            if self.net_timer >= tick_interval:
                self.net_timer -= tick_interval
                self._client_send_input()

    def _host_network_poll(self):
        if not self.server:
            return
        messages = self.server.poll()
        for pid, msg in messages:
            mtype = msg.get("type")
            if mtype == "player_input":
                slot_id = self.server.player_info.get(pid, {}).get("slot_id")
                if slot_id is not None and slot_id in self.players:
                    p = self.players[slot_id]
                    p.apply_remote_state(
                        msg.get("cx", p.cx), msg.get("cy", p.cy),
                        msg.get("facing", p.facing), msg.get("moving", False),
                        msg.get("energy"),
                    )
            elif mtype == "action":
                slot_id = self.server.player_info.get(pid, {}).get("slot_id")
                if slot_id is not None:
                    self._handle_remote_action(slot_id, msg)
            elif mtype == "sleep":
                slot_id = self.server.player_info.get(pid, {}).get("slot_id")
                if slot_id is not None:
                    self.sleeping_players.add(slot_id)
                    self.hud.add_message(
                        t("msg_player_sleeping").replace("{0}", self.players[slot_id].name), 2.0
                    )
                    self._check_all_sleeping()
            elif mtype == "disconnected":
                self.disconnected_msg = t("msg_disconnected")
                info = self.server.player_info.get(pid)
                name = info["name"] if info else "?"
                self.hud.add_message(t("msg_player_disconnected").replace("{0}", name), 3.0)

    def _host_broadcast_state(self):
        if not self.server:
            return
        state = {
            "type": "game_state",
            "time": self.time_system.current_time,
            "sleeping": list(self.sleeping_players),
            "world_changes": self.world.to_save_data(),
            "farming_data": self.farming.to_save_data(),
            "players": {},
        }
        for pid, p in self.players.items():
            state["players"][str(pid)] = {
                "cx": p.cx, "cy": p.cy,
                "facing": p.facing, "moving": p.moving,
                "energy": p.energy,
            }
        self.server.broadcast(state)

    def _client_network_poll(self):
        if not self.client:
            return
        messages = self.client.poll()
        for msg in messages:
            mtype = msg.get("type")
            if mtype == "game_state":
                # Update remote players
                for pid_str, pstate in msg.get("players", {}).items():
                    pid = int(pid_str)
                    if pid != self.local_player_id and pid in self.players:
                        self.players[pid].apply_remote_state(
                            pstate["cx"], pstate["cy"],
                            pstate["facing"], pstate["moving"],
                            pstate.get("energy"),
                        )
                self.sleeping_players = set(msg.get("sleeping", []))
            elif mtype == "all_sleep":
                self._do_day_transition(passed_out=False)
            elif mtype == "day_over":
                self._do_day_transition(passed_out=True)

        if not self.client.connected:
            self.disconnected_msg = t("msg_disconnected")

    def _client_send_input(self):
        if not self.client:
            return
        self.client.send({
            "type": "player_input",
            "cx": self.player.cx,
            "cy": self.player.cy,
            "facing": self.player.facing,
            "moving": self.player.moving,
            "energy": self.player.energy,
        })

    def _handle_remote_action(self, slot_id, msg):
        """Host processes an action request from a remote player.
        We temporarily swap self.player/inventory/tool_manager to the remote player's,
        execute the action, then restore."""
        action = msg.get("action")
        if action == "tile_action":
            tx, ty = msg.get("tx", 0), msg.get("ty", 0)
            # Swap context
            old_p, old_inv, old_tm, old_pt = (
                self.player, self.inventory, self.tool_manager, self.planted_types
            )
            self.player = self.players[slot_id]
            self.inventory = self.inventories[slot_id]
            self.tool_manager = self.tool_managers[slot_id]
            self.planted_types = self.planted_types_all.get(slot_id, set())

            self._do_tile_action(tx, ty)

            # Restore context
            self.player = old_p
            self.inventory = old_inv
            self.tool_manager = old_tm
            self.planted_types = old_pt

    def _check_all_sleeping(self):
        """Check if all players are sleeping; if so, advance the day."""
        if not self.is_multiplayer:
            return
        all_pids = set(self.players.keys())
        if self.sleeping_players >= all_pids:
            if self.is_host and self.server:
                self.server.broadcast({"type": "all_sleep"})
            self._do_day_transition(passed_out=False)

    # ── DRAW ────────────────────────────────────────────────────────
    def draw(self, surface):
        surface.fill(COL_BG)

        self.world.draw(surface, self.farming)

        # Draw all players (remote first, then local on top)
        if self.is_multiplayer:
            for pid, p in self.players.items():
                if pid != self.local_player_id:
                    p.draw(surface, self.world.camera)
        self.player.draw(surface, self.world.camera)

        # Day/night overlay
        overlay_color = self.time_system.get_overlay_color()
        if overlay_color:
            overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill(overlay_color)
            surface.blit(overlay, (0, 0))

        # HUD
        data = self.game.data
        self.hud.draw(
            surface, self.player, self.time_system, self.inventory,
            data.get("day", 1), data.get("season", 0), data.get("year", 1),
            tool_manager=self.tool_manager,
        )

        # Overlays
        if self.waiting_for_sleep:
            self._draw_waiting_sleep(surface)
        if self.chest_open:
            self._draw_chest(surface)
        if self.crafting_open:
            self._draw_crafting(surface)
        if self.sleep_prompt:
            self._draw_sleep_prompt(surface)
        if self.paused:
            self._draw_pause(surface)
        if self.disconnected_msg:
            self._draw_disconnected(surface)

    def _draw_waiting_sleep(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        surface.blit(overlay, (0, 0))

        cx = INTERNAL_WIDTH // 2
        cy = INTERNAL_HEIGHT // 2

        box_w, box_h = 260, 70
        pygame.draw.rect(surface, COL_BG, (cx - box_w // 2, cy - box_h // 2, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT, (cx - box_w // 2, cy - box_h // 2, box_w, box_h), 1)

        draw_text(surface, t("msg_waiting_sleep"), cx, cy - 12, self.font, COL_UI_HIGHLIGHT, center=True)

        sleeping_count = len(self.sleeping_players)
        total_count = len(self.players) if self.is_multiplayer else 1
        status = f"{sleeping_count}/{total_count}"
        draw_text(surface, status, cx, cy + 12, self.font_small, COL_UI_TEXT, center=True)

    def _draw_sleep_prompt(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))

        cx = INTERNAL_WIDTH // 2
        cy = INTERNAL_HEIGHT // 2

        box_w, box_h = 220, 90
        pygame.draw.rect(surface, COL_BG, (cx - box_w // 2, cy - box_h // 2, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT, (cx - box_w // 2, cy - box_h // 2, box_w, box_h), 1)

        draw_text(surface, t("interact_sleep"), cx, cy - 22, self.font, COL_UI_HIGHLIGHT, center=True)

        self.sleep_rects = []
        r1 = draw_button(surface, t("interact_confirm"), cx, cy + 6, self.font_small, selected=True, center=True)
        self.sleep_rects.append(r1)
        r2 = draw_button(surface, t("interact_cancel"), cx, cy + 28, self.font_small, selected=False, center=True)
        self.sleep_rects.append(r2)

    def _draw_pause(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))

        cx = INTERNAL_WIDTH // 2
        cy = INTERNAL_HEIGHT // 2

        draw_text(surface, t("pause_title"), cx, cy - 40, self.font, COL_UI_HIGHLIGHT, center=True)

        self.pause_rects = []
        r1 = draw_button(surface, t("pause_continue"), cx, cy, self.font_small,
                         selected=(self.pause_selected == 0), center=True)
        self.pause_rects.append(r1)
        r2 = draw_button(surface, t("pause_exit"), cx, cy + 28, self.font_small,
                         selected=(self.pause_selected == 1), center=True)
        self.pause_rects.append(r2)

    def _draw_disconnected(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        cx = INTERNAL_WIDTH // 2
        cy = INTERNAL_HEIGHT // 2
        draw_text(surface, self.disconnected_msg, cx, cy - 12, self.font, (200, 80, 80), center=True)
        draw_text(surface, t("pause_exit"), cx, cy + 16, self.font_small, COL_UI_HIGHLIGHT, center=True)
