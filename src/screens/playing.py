import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, TILE_SIZE,
    COL_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, COL_UI_BG, COL_UI_SELECTED,
    PLAYER_MAX_ENERGY, FACING_DOWN,
    TILE_GRASS, TILE_TREE, TILE_ROCK, TILE_BERRY, TILE_TILLED, TILE_CHEST,
    TILE_WATER, TILE_BED, TILE_DIRT, TILE_WATERED, WILD_TILES,
    TOOL_STONE, TOOL_HOE, TOOL_WATER_BUCKET, TOOL_WATER_BARREL,
    TOOL_AXE, TOOL_HAMMER,
    ENERGY_COST_HIT, ENERGY_COST_PICK, ENERGY_COST_TILL_STONE, ENERGY_COST_TILL_HOE,
    ENERGY_COST_WATER, ENERGY_COST_PLANT, ENERGY_COST_HARVEST,
    ITEM_BERRIES, ITEM_CHEST, ITEM_WOOD, ITEM_STONE,
    SEED_TO_CROP, CROPS, CRAFTING_RECIPES, CHEST_SLOTS,
    PLAYER_START_X, PLAYER_START_Y, MAP_WIDTH, MAP_HEIGHT,
    WHITE, EDIBLE_ITEMS, ALL_SEED_ITEMS, TOOLBAR_VISIBLE,
    PG_FIRST_PLANT, NET_TICK_RATE, PLAYER_SPAWNS,
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

    # ── Inicialització ───────────────────────────────────────────

    def __init__(self, game):
        self.game = game
        self.world = World()
        self.time_system = TimeSystem()
        self.inventory = Inventory()
        self.tool_manager = ToolManager()
        self.farming = FarmingSystem(world=self.world)
        self.hud = HUD()
        self.player = None
        self.daily_items = {}
        self.daily_pg = 0
        self.planted_types = set()

        self.paused = False
        self.sleep_prompt = False
        self.pause_selected = 0
        self.font = pygame.font.SysFont("arial", 16)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.font_tiny = pygame.font.SysFont("arial", 11)

        self.interact_cooldown = 0.0
        self.hold_info = None

        self.crafting_open = False
        self.chest_open = False
        self.chest_pos = None

        self.pause_rects = []
        self.sleep_rects = []
        self.craft_rects = []
        self.chest_slot_rects = []
        self.chest_inv_rects = []

        # Seed selector overlay
        self.seed_select_open = False
        self.seed_select_pos = None
        self.seed_options = []
        self.seed_rects = []

        # Multiplayer
        self.is_multiplayer = False
        self.is_host = False
        self.local_player_id = 0
        self.server = None
        self.client = None
        self.players = {}
        self.inventories = {}
        self.tool_managers = {}
        self.planted_types_all = {}
        self.sleeping_players = set()
        self.waiting_for_sleep = False
        self.net_timer = 0.0
        self.disconnected_msg = ""
        self.user_ids = {}

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
        self.daily_items = {}
        self.daily_pg = 0
        self.interact_cooldown = 0.0
        self.hold_info = None
        self.crafting_open = False
        self.chest_open = False
        self.chest_pos = None
        self.seed_select_open = False
        self.seed_select_pos = None
        self.seed_options = []
        self.paused = False
        self.sleep_prompt = False

        if self.is_multiplayer:
            self._init_multiplayer(data)
        else:
            self._init_solo(data)

        # Farming
        self.farming = FarmingSystem(world=self.world)
        self.farming.from_save_data(data.get("farming_data"))
        self.planted_types = set(data.get("planted_types", []))

    def _init_solo(self, data):
        avatar = data.get("avatar", {"skin": 0, "hair_color": 0, "outfit": 0, "eyes": 0})
        cx = data.get("player_cx", PLAYER_START_X)
        cy = data.get("player_cy", PLAYER_START_Y)
        self.player = Player(cx, cy, avatar, name=data.get("player_name", ""))
        self.player.facing = data.get("player_facing", FACING_DOWN)
        self.player.energy = data.get("energy", PLAYER_MAX_ENERGY)
        self.inventory = Inventory()
        self.inventory.from_list(data.get("inventory", []))
        self.tool_manager = ToolManager()
        self.tool_manager.from_save_data(data.get("tools_data"))
        self.world = World()
        self.world.from_save_data(data.get("world_data"))

    def _init_multiplayer(self, data):
        self.server = data.get("server")
        self.client = data.get("client")
        num_players = data.get("num_players", 2)
        self.world = World(num_players=num_players)
        self.world.from_save_data(data.get("world_data"))
        self.players = {}
        self.inventories = {}
        self.tool_managers = {}
        self.planted_types_all = {}
        self.user_ids = {}

        for pdata in data.get("players", []):
            pid = pdata["id"]
            avatar = pdata.get("avatar", {"skin": 0, "hair_color": 0, "outfit": 0, "eyes": 0})
            p = Player(pdata.get("cx", PLAYER_START_X),
                       pdata.get("cy", PLAYER_START_Y),
                       avatar, name=pdata.get("name", ""))
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

        local_id = (self.local_player_id
                    if self.local_player_id in self.players
                    else next(iter(self.players), 0))
        self.player = self.players[local_id]
        self.inventory = self.inventories[local_id]
        self.tool_manager = self.tool_managers[local_id]

    # ── Gestió d'esdeveniments ───────────────────────────────────

    def handle_event(self, event):
        if self.waiting_for_sleep or self.disconnected_msg:
            return

        if self.seed_select_open:
            self._handle_seed_select_event(event)
            return

        if self.chest_open:
            self._handle_chest_event(event)
            return

        if self.crafting_open:
            self._handle_crafting_event(event)
            return

        if event.type == pygame.KEYDOWN:
            self._handle_keydown(event)

        elif event.type == pygame.MOUSEBUTTONDOWN:
            self._handle_mousedown(event)

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

    def _handle_keydown(self, event):
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

    def _handle_mousedown(self, event):
        mx, my = self._to_internal(event.pos)

        if event.button == 1:
            if self.sleep_prompt:
                for i, rect in enumerate(self.sleep_rects):
                    if rect and rect.collidepoint(mx, my):
                        if i == 0:
                            self._go_to_sleep(passed_out=False)
                        else:
                            self.sleep_prompt = False
                        return
                return

            if self.paused:
                for i, rect in enumerate(self.pause_rects):
                    if rect and rect.collidepoint(mx, my):
                        self.pause_selected = i
                        if i == 0:
                            self.paused = False
                        else:
                            self._exit_to_menu()
                        return
                return

            if self.hud.tool_slot_rect and self.hud.tool_slot_rect.collidepoint(mx, my):
                self.tool_manager.active = True
                self.inventory.selected_slot = -1
                return

            if self.hud.toolbar_rects:
                vis_start, _ = self.inventory.get_visible_range()
                for i, rect in enumerate(self.hud.toolbar_rects):
                    if rect and rect.collidepoint(mx, my):
                        abs_idx = vis_start + i
                        self.inventory.selected_slot = (
                            -1 if self.inventory.selected_slot == abs_idx else abs_idx
                        )
                        if self.inventory.selected_slot != -1:
                            self.tool_manager.active = False
                        return

            if self.hud.craft_button_rect and self.hud.craft_button_rect.collidepoint(mx, my):
                self.crafting_open = True
                return

            if self.interact_cooldown <= 0:
                self._handle_world_click(mx, my, event)

        elif event.button in (4, 5):
            direction = -1 if event.button == 4 else 1
            if self.tool_manager.active:
                self.tool_manager.cycle(direction)
            else:
                self.inventory.toggle_page()

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def _handle_world_click(self, mx, my, event=None):
        tx = int(mx // TILE_SIZE)
        ty = int(my // TILE_SIZE)
        self._do_tile_action(tx, ty, event)

    # ── Accions sobre tiles ──────────────────────────────────────

    def _do_tile_action(self, tx, ty, event=None):
        if tx < 0 or ty < 0 or tx >= MAP_WIDTH or ty >= MAP_HEIGHT:
            return

        tile = self.world.get_tile(tx, ty)

        # Context-free interactions
        if tile == TILE_BED:
            self.sleep_prompt = True
            return

        if tile == TILE_CHEST:
            self.chest_pos = (tx, ty)
            self.chest_open = True
            return

        # Wild crop interaction (no tool needed)
        if tile in WILD_TILES:
            self._try_harvest_wild(tx, ty)
            return

        # Tilled/watered: planting (inventory seed selected) or harvest if mature
        if tile in (TILE_TILLED, TILE_WATERED):
            # Harvest if crop is mature
            if self.farming.is_mature(tx, ty):
                self._try_harvest_crop(tx, ty)
                return
            # Plant if seed selected in inventory
            seeds = self.inventory.get_seeds()
            if seeds and self.inventory.selected_slot >= 0:
                selected = self.inventory.get_selected_item()
                if selected and selected["item"] in ALL_SEED_ITEMS:
                    self._try_plant(tx, ty, selected["item"])
                    return
            # Multiple seeds: open selector
            if len(seeds) > 1:
                self.seed_options = seeds
                self.seed_select_pos = (tx, ty)
                self.seed_select_open = True
                return
            elif len(seeds) == 1:
                self._try_plant(tx, ty, seeds[0])
                return
            return

        # Tool-specific actions
        if not self.tool_manager.active:
            return

        tool = self.tool_manager.current

        if tool in (TOOL_STONE, TOOL_AXE):
            self._action_hit_or_till(tool, tile, tx, ty)

        elif tool == TOOL_HOE:
            if tile == TILE_DIRT:
                self._action_till_hoe(tx, ty)

        elif tool in (TOOL_WATER_BUCKET, TOOL_WATER_BARREL):
            self._action_water(tile, tx, ty)

        elif tool == TOOL_HAMMER:
            if tile == TILE_ROCK:
                self._action_hit_rock(tool, tx, ty)

    def _action_hit_or_till(self, tool, tile, tx, ty):
        if tile == TILE_DIRT:
            if self.player.energy < ENERGY_COST_TILL_STONE:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            if self.world.till_soil(tx, ty):
                self.player.energy -= ENERGY_COST_TILL_STONE
                self.hud.add_message(t("msg_tilled"), 1.0)
            return

        if tile in (TILE_TREE, TILE_ROCK):
            if self.player.energy < ENERGY_COST_HIT:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            result = self.world.hit_resource(tx, ty, tool_id=tool)
            self.player.energy -= ENERGY_COST_HIT
            self.player.flash_timer = 0.1
            self._process_hit_result(result, tx, ty)

        if tile == TILE_BERRY:
            self._try_pick_berries(tx, ty)

    def _action_till_hoe(self, tx, ty):
        if self.player.energy < ENERGY_COST_TILL_HOE:
            self.hud.add_message(t("msg_no_energy"), 2.0)
            return
        if self.world.till_soil(tx, ty):
            self.player.energy -= ENERGY_COST_TILL_HOE
            self.hud.add_message(t("msg_tilled"), 1.0)
            self.hold_info = {"tx": tx, "ty": ty, "timer": 0.0, "type": "hoe", "done": False}

    def _action_water(self, tile, tx, ty):
        if tile == TILE_WATER:
            filled = self.tool_manager.fill_water()
            msg = t("msg_water_filled") if filled > 0 else t("msg_water_full")
            self.hud.add_message(msg, 1.5)
            return

        if tile == TILE_TILLED:
            if self.tool_manager.get_water() <= 0:
                self.hud.add_message(t("msg_water_empty"), 1.5)
                return
            if self.player.energy < ENERGY_COST_WATER:
                self.hud.add_message(t("msg_no_energy"), 2.0)
                return
            if self.world.water_soil(tx, ty):
                self.tool_manager.use_water()
                self.player.energy -= ENERGY_COST_WATER
                # Mark crop as watered in farming system
                plot = self.farming.get_crop(tx, ty)
                if plot:
                    plot["watered"] = True
                self.hud.add_message(t("msg_watered"), 1.0)
                self.hold_info = {"tx": tx, "ty": ty, "timer": 0.0, "type": "water", "done": False}

    def _action_hit_rock(self, tool, tx, ty):
        if self.player.energy < ENERGY_COST_HIT:
            self.hud.add_message(t("msg_no_energy"), 2.0)
            return
        result = self.world.hit_resource(tx, ty, tool_id=tool)
        self.player.energy -= ENERGY_COST_HIT
        self.player.flash_timer = 0.1
        self._process_hit_result(result, tx, ty)

    def _process_hit_result(self, result, tx, ty):
        if result:
            item_id, qty, _ = result
            if self.inventory.can_add(item_id):
                self.inventory.add_item(item_id, qty)
                self.hud.add_message(f"+{qty} {t(f'item_{item_id}')}", 1.5)
                self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty
            else:
                self.hud.add_message(t("msg_inventory_full"), 2.0)
        else:
            hp = self.world.get_resource_hp(tx, ty)
            self.hud.add_message(f"({hp})", 0.5)

    def _try_pick_berries(self, tx, ty):
        if self.player.energy < ENERGY_COST_PICK:
            self.hud.add_message(t("msg_no_energy"), 2.0)
            return
        result = self.world.hit_resource(tx, ty)
        if result:
            item_id, qty, _ = result
            if self.inventory.can_add(item_id):
                self.inventory.add_item(item_id, qty)
                self.player.energy -= ENERGY_COST_PICK
                self.hud.add_message(f"+{qty} {t(f'item_{item_id}')}", 1.5)
                self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty

    def _try_harvest_wild(self, tx, ty):
        result = self.world.harvest_wild(tx, ty)
        if result:
            seed_item, qty = result
            if self.inventory.can_add(seed_item):
                self.inventory.add_item(seed_item, qty)
                self.hud.add_message(f"+{qty} {t(f'item_{seed_item}')}", 1.5)
                self.daily_items[seed_item] = self.daily_items.get(seed_item, 0) + qty
            else:
                self.hud.add_message(t("msg_inventory_full"), 2.0)

    def _try_plant(self, tx, ty, seed_item):
        if self.player.energy < ENERGY_COST_PLANT:
            self.hud.add_message(t("msg_no_energy"), 2.0)
            return
        if self.inventory.count_item(seed_item) <= 0:
            self.hud.add_message(t("msg_need_seeds"), 2.0)
            return
        if self.farming.plant(tx, ty, seed_item):
            self.inventory.remove_item(seed_item, 1)
            self.player.energy -= ENERGY_COST_PLANT
            crop_id = SEED_TO_CROP.get(seed_item)
            crop_name = t(f"crop_{crop_id}") if crop_id else seed_item
            self.hud.add_message(f"{t('msg_planted')} {crop_name}", 1.5)
            # First-plant bonus
            if crop_id and crop_id not in self.planted_types:
                self.planted_types.add(crop_id)
                self.daily_pg += PG_FIRST_PLANT
        self.interact_cooldown = 0.3

    def _try_harvest_crop(self, tx, ty):
        if self.player.energy < ENERGY_COST_HARVEST:
            self.hud.add_message(t("msg_no_energy"), 2.0)
            return
        result = self.farming.harvest(tx, ty)
        if result:
            item_id, qty, quality, pg = result
            if self.inventory.can_add(item_id, quality):
                self.inventory.add_item(item_id, qty, quality)
                self.player.energy -= ENERGY_COST_HARVEST
                self.hud.add_message(f"{t('msg_harvested')} +{qty} {t(f'item_{item_id}')}", 1.5)
                self.daily_items[item_id] = self.daily_items.get(item_id, 0) + qty
                self.daily_pg += pg
            else:
                self.hud.add_message(t("msg_inventory_full"), 2.0)
        self.interact_cooldown = 0.3

    def _try_eat_selected(self):
        selected = self.inventory.get_selected_item()
        if not selected:
            return
        item_id = selected["item"]
        restore = EDIBLE_ITEMS.get(item_id)
        if restore is None:
            self.hud.add_message(t("msg_cant_eat"), 1.5)
            return
        self.player.eat_food(self.inventory, item_id, restore)

    # ── Seed selector overlay ────────────────────────────────────

    def _handle_seed_select_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.seed_select_open = False
            return
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.seed_rects):
                if rect and rect.collidepoint(mx, my):
                    tx, ty = self.seed_select_pos
                    self._try_plant(tx, ty, self.seed_options[i])
                    self.seed_select_open = False
                    return
            self.seed_select_open = False

    def _draw_seed_selector(self, surface):
        if not self.seed_options:
            return
        cx = INTERNAL_WIDTH // 2
        cy = INTERNAL_HEIGHT // 2
        item_h = 24
        box_w, box_h = 180, 30 + len(self.seed_options) * item_h
        pygame.draw.rect(surface, COL_UI_BG, (cx - box_w // 2, cy - box_h // 2, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_SELECTED, (cx - box_w // 2, cy - box_h // 2, box_w, box_h), 1)
        draw_text(surface, t("seed_select"), cx, cy - box_h // 2 + 6,
                  self.font_tiny, COL_UI_HIGHLIGHT, center=True)
        self.seed_rects = []
        for i, seed_id in enumerate(self.seed_options):
            ry = cy - box_h // 2 + 22 + i * item_h
            rect = pygame.Rect(cx - box_w // 2 + 4, ry, box_w - 8, item_h - 2)
            pygame.draw.rect(surface, (60, 50, 38), rect)
            self.seed_rects.append(rect)
            icon = _get_item_icon(seed_id)
            surface.blit(icon, (rect.x + 2, rect.y + 4))
            draw_text(surface, t(f"item_{seed_id}"), rect.x + 22, rect.y + 6,
                      self.font_tiny, COL_UI_TEXT)

    # ── Chest overlay ────────────────────────────────────────────

    def _handle_chest_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.chest_open = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return

        mx, my = self._to_internal(event.pos)
        chest = self.world.get_chest(*self.chest_pos)
        if not chest:
            self.chest_open = False
            return

        for i, rect in enumerate(self.chest_slot_rects):
            if rect and rect.collidepoint(mx, my):
                if chest[i]:
                    slot = chest[i]
                    if self.inventory.can_add(slot["item"], slot.get("quality", 0)):
                        self.inventory.add_item(slot["item"], slot["qty"], slot.get("quality", 0))
                        chest[i] = None
                    else:
                        self.hud.add_message(t("msg_inventory_full"), 1.5)
                return

        for i, rect in enumerate(self.chest_inv_rects):
            if rect and rect.collidepoint(mx, my):
                if i < len(self.inventory.slots) and self.inventory.slots[i]:
                    slot = self.inventory.slots[i]
                    empty = next((ci for ci, s in enumerate(chest) if s is None), None)
                    if empty is not None:
                        chest[empty] = slot.copy()
                        self.inventory.slots[i] = None
                    else:
                        self.hud.add_message(t("msg_chest_full"), 1.5)
                return

        self.chest_open = False

    def _draw_chest(self, surface):
        chest = self.world.get_chest(*self.chest_pos) if self.chest_pos else None
        if not chest:
            return

        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 100))
        surface.blit(overlay, (0, 0))

        slot_size, padding, cols = 22, 3, 5
        rows_chest = (CHEST_SLOTS + cols - 1) // cols
        pw = cols * (slot_size + padding) + padding + 20
        ph = 30 + (rows_chest + 2) * (slot_size + padding) + 30
        px = (INTERNAL_WIDTH - pw) // 2
        py = (INTERNAL_HEIGHT - ph) // 2

        pygame.draw.rect(surface, COL_UI_BG, (px, py, pw, ph))
        pygame.draw.rect(surface, COL_UI_SELECTED, (px, py, pw, ph), 1)
        draw_text(surface, t("chest_title"), px + pw // 2, py + 6,
                  self.font_tiny, COL_UI_HIGHLIGHT, center=True)

        self.chest_slot_rects = []
        base_x, base_y = px + 10, py + 20
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

        inv_y = base_y + rows_chest * (slot_size + padding) + 10
        draw_text(surface, t("inv_title"), px + pw // 2, inv_y,
                  self.font_tiny, COL_UI_TEXT, center=True)
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

    # ── Crafting overlay ─────────────────────────────────────────

    def _handle_crafting_event(self, event):
        if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
            self.crafting_open = False
            return
        if event.type != pygame.MOUSEBUTTONDOWN or event.button != 1:
            return
        mx, my = self._to_internal(event.pos)
        for i, rect in enumerate(self.craft_rects):
            if rect and rect.collidepoint(mx, my):
                recipe = CRAFTING_RECIPES[i]
                if can_craft(recipe, self.inventory):
                    if do_craft(recipe, self.inventory, self.tool_manager):
                        name = t(f"craft_{recipe['id'].replace('craft_', '')}")
                        self.hud.add_message(f"{t('msg_crafted')} {name}", 2.0)
                    self.crafting_open = False
                else:
                    self.hud.add_message(t("msg_cant_craft"), 2.0)
                return
        # Click outside closes
        self.crafting_open = False

    def _draw_crafting(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 110))
        surface.blit(overlay, (0, 0))

        item_h = 36
        box_w = 220
        box_h = 30 + len(CRAFTING_RECIPES) * item_h + 10
        bx = (INTERNAL_WIDTH - box_w) // 2
        by = (INTERNAL_HEIGHT - box_h) // 2

        pygame.draw.rect(surface, COL_UI_BG, (bx, by, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_SELECTED, (bx, by, box_w, box_h), 1)
        draw_text(surface, t("craft_title"), bx + box_w // 2, by + 8,
                  self.font_small, COL_UI_HIGHLIGHT, center=True)

        self.craft_rects = []
        for i, recipe in enumerate(CRAFTING_RECIPES):
            ry = by + 26 + i * item_h
            craftable = can_craft(recipe, self.inventory)
            col = COL_UI_HIGHLIGHT if craftable else (100, 100, 100)
            rect = pygame.Rect(bx + 6, ry, box_w - 12, item_h - 4)
            pygame.draw.rect(surface, (50, 40, 30), rect)
            pygame.draw.rect(surface, col, rect, 1)
            self.craft_rects.append(rect)

            name_key = recipe.get("name_key", recipe["id"])
            draw_text(surface, t(name_key), rect.x + 6, rect.y + 4,
                      self.font_tiny, col)

            # Ingredients summary
            parts = []
            for item_id, qty in recipe["ingredients"].items():
                have = self.inventory.count_item(item_id)
                parts.append(f"{t(f'item_{item_id}')} {have}/{qty}")
            draw_text(surface, "  ".join(parts), rect.x + 6, rect.y + 18,
                      self.font_tiny, (160, 150, 130))

    # ── Sleep / Pause / Menu ─────────────────────────────────────

    def _go_to_sleep(self, passed_out=False):
        if self.is_multiplayer and not passed_out:
            self.sleeping_players.add(self.local_player_id)
            self.sleep_prompt = False
            self.waiting_for_sleep = True
            if self.is_host:
                self._check_all_sleeping()
            elif self.client:
                self.client.send({"type": "sleep"})
            return
        self._do_day_transition(passed_out)

    def _do_day_transition(self, passed_out=False):
        data = self.game.data
        if self.is_multiplayer:
            players_save = []
            for pid in sorted(self.players.keys()):
                p = self.players[pid]
                inv = self.inventories.get(pid, Inventory())
                tm = self.tool_managers.get(pid, ToolManager())
                pt = self.planted_types_all.get(pid, set())
                players_save.append({
                    "id": pid, "name": p.name, "avatar": p.avatar.copy(),
                    "user_id": self.user_ids.get(pid, ""),
                    "cx": p.cx, "cy": p.cy, "facing": p.facing, "energy": p.energy,
                    "inventory": inv.to_list(), "tools_data": tm.to_save_data(),
                    "planted_types": list(pt),
                })
            data["players"] = players_save
        else:
            data["player_cx"] = self.player.cx
            data["player_cy"] = self.player.cy
            data["player_facing"] = self.player.facing
            data["energy"] = self.player.energy
            data["inventory"] = self.inventory.to_list()
            data["tools_data"] = self.tool_manager.to_save_data()
            data["planted_types"] = list(self.planted_types)

        data["world_data"] = self.world.to_save_data()
        self.farming.advance_day()
        data["farming_data"] = self.farming.to_save_data()

        from src.screens.day_summary import DaySummaryScreen
        self.game.change_screen(DaySummaryScreen,
                                daily_items=self.daily_items,
                                daily_pg=self.daily_pg,
                                passed_out=passed_out)

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

    # ── Update ───────────────────────────────────────────────────

    def update(self, dt):
        if self.disconnected_msg:
            return
        if self.paused or self.sleep_prompt or self.crafting_open or self.chest_open:
            return

        if self.waiting_for_sleep:
            self.hud.update(dt)
            if self.is_multiplayer:
                self._network_update(dt)
            return

        self.time_system.update(dt)
        if self.time_system.day_over:
            if self.is_multiplayer and not self.is_host:
                pass  # wait for host
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

        self._update_hold(dt)

        if self.is_multiplayer:
            for pid, p in self.players.items():
                if pid != self.local_player_id:
                    p.update(dt)
            self._network_update(dt)

    def _update_hold(self, dt):
        if not self.hold_info or self.hold_info["done"]:
            return
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

    def _hold_extra_hoe(self, start_tx, start_ty):
        """Till extra tiles in the facing direction when holding."""
        from src.settings import FACING_OFFSETS, HOLD_EXTRA_TILES
        ox, oy = FACING_OFFSETS[self.player.facing]
        for i in range(1, HOLD_EXTRA_TILES + 1):
            tx, ty = start_tx + ox * i, start_ty + oy * i
            if self.world.get_tile(tx, ty) == TILE_DIRT:
                if self.player.energy >= ENERGY_COST_TILL_HOE:
                    if self.world.till_soil(tx, ty):
                        self.player.energy -= ENERGY_COST_TILL_HOE

    def _hold_extra_water(self, start_tx, start_ty):
        """Water extra tiles in the facing direction when holding."""
        from src.settings import FACING_OFFSETS, HOLD_EXTRA_TILES
        ox, oy = FACING_OFFSETS[self.player.facing]
        for i in range(1, HOLD_EXTRA_TILES + 1):
            tx, ty = start_tx + ox * i, start_ty + oy * i
            if self.world.get_tile(tx, ty) == TILE_TILLED:
                if self.tool_manager.get_water() > 0 and self.player.energy >= ENERGY_COST_WATER:
                    if self.world.water_soil(tx, ty):
                        self.tool_manager.use_water()
                        self.player.energy -= ENERGY_COST_WATER
                        plot = self.farming.get_crop(tx, ty)
                        if plot:
                            plot["watered"] = True

    # ── Network ──────────────────────────────────────────────────

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
        for pid, msg in self.server.poll():
            mtype = msg.get("type")
            if mtype == "player_input":
                slot_id = self.server.player_info.get(pid, {}).get("slot_id")
                if slot_id in self.players:
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
                    name = self.players[slot_id].name if slot_id in self.players else "?"
                    self.hud.add_message(t("msg_player_sleeping").replace("{0}", name), 2.0)
                    self._check_all_sleeping()
            elif mtype == "disconnected":
                info = self.server.player_info.get(pid, {})
                self.hud.add_message(
                    t("msg_player_disconnected").replace("{0}", info.get("name", "?")), 3.0
                )

    def _host_broadcast_state(self):
        if not self.server:
            return
        state = {
            "type": "game_state",
            "time": self.time_system.current_time,
            "sleeping": list(self.sleeping_players),
            "world_changes": self.world.to_save_data(),
            "farming_data": self.farming.to_save_data(),
            "players": {
                str(pid): {
                    "cx": p.cx, "cy": p.cy,
                    "facing": p.facing, "moving": p.moving,
                    "energy": p.energy,
                }
                for pid, p in self.players.items()
            },
        }
        self.server.broadcast(state)

    def _client_network_poll(self):
        if not self.client:
            return
        for msg in self.client.poll():
            mtype = msg.get("type")
            if mtype == "game_state":
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
                return
            elif mtype == "day_over":
                self._do_day_transition(passed_out=True)
                return

        if not self.client.connected:
            self.disconnected_msg = t("msg_disconnected")

    def _client_send_input(self):
        if self.client:
            self.client.send({
                "type": "player_input",
                "cx": self.player.cx, "cy": self.player.cy,
                "facing": self.player.facing, "moving": self.player.moving,
                "energy": self.player.energy,
            })

    def _handle_remote_action(self, slot_id, msg):
        if msg.get("action") != "tile_action":
            return
        tx, ty = msg.get("tx", 0), msg.get("ty", 0)
        old_p, old_inv, old_tm, old_pt = (
            self.player, self.inventory, self.tool_manager, self.planted_types
        )
        self.player = self.players[slot_id]
        self.inventory = self.inventories[slot_id]
        self.tool_manager = self.tool_managers[slot_id]
        self.planted_types = self.planted_types_all.get(slot_id, set())
        self._do_tile_action(tx, ty)
        self.player, self.inventory = old_p, old_inv
        self.tool_manager, self.planted_types = old_tm, old_pt

    def _check_all_sleeping(self):
        if not self.is_multiplayer:
            return
        if self.sleeping_players >= set(self.players.keys()):
            if self.is_host and self.server:
                self.server.broadcast({"type": "all_sleep"})
            self._do_day_transition(passed_out=False)

    # ── Draw ─────────────────────────────────────────────────────

    def draw(self, surface):
        surface.fill(COL_BG)
        self.world.draw(surface, self.farming)

        if self.is_multiplayer:
            for pid, p in self.players.items():
                if pid != self.local_player_id:
                    p.draw(surface, self.world.camera)
        self.player.draw(surface, self.world.camera)

        overlay_color = self.time_system.get_overlay_color()
        if overlay_color:
            overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill(overlay_color)
            surface.blit(overlay, (0, 0))

        data = self.game.data
        self.hud.draw(
            surface, self.player, self.time_system, self.inventory,
            data.get("day", 1), data.get("season", 0), data.get("year", 1),
            tool_manager=self.tool_manager,
        )

        if self.waiting_for_sleep:
            self._draw_waiting_sleep(surface)
        if self.seed_select_open:
            self._draw_seed_selector(surface)
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
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        box_w, box_h = 260, 70
        pygame.draw.rect(surface, COL_BG, (cx - box_w // 2, cy - box_h // 2, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT, (cx - box_w // 2, cy - box_h // 2, box_w, box_h), 1)
        draw_text(surface, t("msg_waiting_sleep"), cx, cy - 12, self.font, COL_UI_HIGHLIGHT, center=True)
        total = len(self.players) if self.is_multiplayer else 1
        draw_text(surface, f"{len(self.sleeping_players)}/{total}", cx, cy + 12,
                  self.font_small, COL_UI_TEXT, center=True)

    def _draw_sleep_prompt(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 120))
        surface.blit(overlay, (0, 0))
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        box_w, box_h = 220, 90
        pygame.draw.rect(surface, COL_BG, (cx - box_w // 2, cy - box_h // 2, box_w, box_h))
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT, (cx - box_w // 2, cy - box_h // 2, box_w, box_h), 1)
        draw_text(surface, t("interact_sleep"), cx, cy - 22, self.font, COL_UI_HIGHLIGHT, center=True)
        self.sleep_rects = [
            draw_button(surface, t("interact_confirm"), cx, cy + 6, self.font_small, selected=True, center=True),
            draw_button(surface, t("interact_cancel"), cx, cy + 28, self.font_small, selected=False, center=True),
        ]

    def _draw_pause(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 150))
        surface.blit(overlay, (0, 0))
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        draw_text(surface, t("pause_title"), cx, cy - 40, self.font, COL_UI_HIGHLIGHT, center=True)
        self.pause_rects = [
            draw_button(surface, t("pause_continue"), cx, cy, self.font_small,
                        selected=(self.pause_selected == 0), center=True),
            draw_button(surface, t("pause_exit"), cx, cy + 28, self.font_small,
                        selected=(self.pause_selected == 1), center=True),
        ]

    def _draw_disconnected(self, surface):
        overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        surface.blit(overlay, (0, 0))
        cx, cy = INTERNAL_WIDTH // 2, INTERNAL_HEIGHT // 2
        draw_text(surface, self.disconnected_msg, cx, cy - 12, self.font, (200, 80, 80), center=True)
        draw_text(surface, t("pause_exit"), cx, cy + 16, self.font_small, COL_UI_HIGHLIGHT, center=True)