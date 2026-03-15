import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, COL_UI_BG,
    PG_WOOD, PG_STONE, PG_BERRIES, PG_HARVEST,
    ITEM_WOOD, ITEM_STONE, ITEM_BERRIES,
    ITEM_MORA, ITEM_POTATO, ITEM_WHEAT, ITEM_PUMPKIN,
    ITEM_SEED_MORA, ITEM_SEED_POTATO, ITEM_SEED_WHEAT, ITEM_SEED_PUMPKIN,
    ITEM_CHEST,
    CROP_MORA, CROP_POTATO, CROP_WHEAT, CROP_PUMPKIN,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.systems.save_system import save_game
from src.systems.profile import get_user_id

# Map item_id → PG per unit
PG_VALUES = {
    ITEM_WOOD: PG_WOOD,
    ITEM_STONE: PG_STONE,
    ITEM_BERRIES: PG_BERRIES,
    ITEM_MORA: PG_HARVEST[CROP_MORA],
    ITEM_POTATO: PG_HARVEST[CROP_POTATO],
    ITEM_WHEAT: PG_HARVEST[CROP_WHEAT],
    ITEM_PUMPKIN: PG_HARVEST[CROP_PUMPKIN],
}


class DaySummaryScreen:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.daily_items = {}
        self.pg_earned = 0
        self.saved = False
        self.passed_out = False
        self.continue_rect = None

        # Multiplayer sync state
        self.waiting_for_others = False
        self.ready_players = set()

    def on_enter(self, daily_items=None, daily_pg=0, passed_out=False, **kwargs):
        self.daily_items = daily_items or {}
        self.passed_out = passed_out
        self.saved = False
        self.waiting_for_others = False
        self.ready_players = set()

        # PG from items
        item_pg = 0
        for item_id, qty in self.daily_items.items():
            item_pg += PG_VALUES.get(item_id, 0) * qty

        # Add farming PG passed from playing screen (first-plant bonuses, harvest PG)
        self.pg_earned = item_pg + daily_pg

        # Update game data
        data = self.game.data
        data["pg_total"] = data.get("pg_total", 0) + self.pg_earned

        # Auto-save
        self._save()

    @property
    def _is_multi(self):
        return self.game.data.get("mode") == "multi"

    @property
    def _is_host(self):
        return self.game.data.get("is_host", True)

    def _save(self):
        data = self.game.data
        save_game(data, user_id=get_user_id())
        self.saved = True

    def handle_event(self, event):
        if self.waiting_for_others:
            return
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._continue()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self.game.screen_to_internal(event.pos[0], event.pos[1])
            if self.continue_rect and self.continue_rect.collidepoint(mx, my):
                self._continue()

    def _continue(self):
        data = self.game.data

        if self._is_multi:
            # Signal readiness and wait
            local_pid = data.get("local_player_id", 0)
            self.ready_players.add(local_pid)
            self.waiting_for_others = True

            if self._is_host:
                server = data.get("server")
                if server:
                    server.broadcast({"type": "host_day_ready"})
                self._check_all_ready()
            else:
                client = data.get("client")
                if client:
                    client.send({"type": "day_ready"})
            return

        self._advance_day()

    def _check_all_ready(self):
        data = self.game.data
        num_players = data.get("num_players", 1)
        if len(self.ready_players) >= num_players:
            if self._is_host:
                server = data.get("server")
                if server:
                    server.broadcast({"type": "all_day_ready"})
            self._advance_day()

    def _advance_day(self):
        data = self.game.data
        data["day"] = data.get("day", 1) + 1

        # Season advancement: 30 days per season (simplified for Phase 0)
        if data["day"] > 30:
            data["day"] = 1
            data["season"] = data.get("season", 0) + 1
            if data["season"] > 3:
                data["season"] = 0
                data["year"] = data.get("year", 1) + 1

        from src.settings import PLAYER_MAX_ENERGY, PLAYER_START_X, PLAYER_START_Y, PLAYER_SPAWNS

        if data.get("mode") == "multi":
            # Restore energy and positions for all players
            for pdata in data.get("players", []):
                pdata["energy"] = PLAYER_MAX_ENERGY
                pid = pdata.get("id", 0)
                if pid < len(PLAYER_SPAWNS):
                    pdata["cx"] = PLAYER_SPAWNS[pid][0]
                    pdata["cy"] = PLAYER_SPAWNS[pid][1]
        else:
            data["energy"] = PLAYER_MAX_ENERGY
            data["player_cx"] = PLAYER_START_X
            data["player_cy"] = PLAYER_START_Y

        from src.screens.playing import PlayingScreen
        self.game.change_screen(PlayingScreen)

    def update(self, dt):
        if not self._is_multi or not self.waiting_for_others:
            return

        data = self.game.data
        if self._is_host:
            server = data.get("server")
            if server:
                messages = server.poll()
                for pid, msg in messages:
                    if msg.get("type") == "day_ready":
                        slot_id = server.player_info.get(pid, {}).get("slot_id")
                        if slot_id is not None:
                            self.ready_players.add(slot_id)
                            self._check_all_ready()
        else:
            client = data.get("client")
            if client:
                messages = client.poll()
                for msg in messages:
                    if msg.get("type") == "all_day_ready":
                        self._advance_day()
                        return

    def draw(self, surface):
        surface.fill(COL_BG)
        cx = INTERNAL_WIDTH // 2

        # Passed out message
        y = 35
        if self.passed_out:
            draw_text(surface, t("msg_passed_out"), cx, y, self.font, (200, 80, 80), center=True)
            y += 28

        # Title
        data = self.game.data
        title = f"{t('summary_title')} {data.get('day', 1)}"
        draw_text(surface, title, cx, y, self.font_title, COL_UI_HIGHLIGHT, center=True)
        y += 36

        # Items collected
        draw_text(surface, t("summary_collected"), cx, y, self.font, COL_UI_TEXT, center=True)
        y += 22

        if self.daily_items:
            for item_id, qty in self.daily_items.items():
                name = t(f"item_{item_id}")
                pg = PG_VALUES.get(item_id, 0) * qty
                line = f"{name}: x{qty}  (+{pg} PG)"
                draw_text(surface, line, cx, y, self.font_small, COL_UI_TEXT, center=True)
                y += 18
        else:
            draw_text(surface, "---", cx, y, self.font_small, (120, 120, 120), center=True)
            y += 18

        y += 14

        # PG summary
        draw_text(surface, f"{t('summary_pg_earned')} {self.pg_earned}",
                 cx, y, self.font, COL_UI_HIGHLIGHT, center=True)
        y += 22
        draw_text(surface, f"{t('summary_pg_total')} {data.get('pg_total', 0)}",
                 cx, y, self.font, COL_UI_TEXT, center=True)
        y += 30

        # Save status
        if self.saved:
            draw_text(surface, t("summary_saved"), cx, y, self.font_small,
                     (100, 200, 100), center=True)
        y += 24

        # Continue button
        self.continue_rect = draw_button(surface, t("summary_continue"), cx, y,
                                         self.font, selected=True, center=True)

        # Waiting overlay
        if self.waiting_for_others:
            overlay = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT), pygame.SRCALPHA)
            overlay.fill((0, 0, 0, 140))
            surface.blit(overlay, (0, 0))

            draw_text(surface, t("msg_waiting_players"), cx, INTERNAL_HEIGHT // 2 - 10,
                      self.font, COL_UI_HIGHLIGHT, center=True)

            num_players = self.game.data.get("num_players", 1)
            status = f"{len(self.ready_players)}/{num_players}"
            draw_text(surface, status, cx, INTERNAL_HEIGHT // 2 + 14,
                      self.font_small, COL_UI_TEXT, center=True)
