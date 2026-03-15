import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, COL_UI_SELECTED,
    PLAYER_START_X, PLAYER_START_Y, FACING_DOWN,
    SKIN_SWATCH, HAIR_SWATCH, OUTFIT_SWATCH, EYE_SWATCH,
    MAX_PLAYERS, PLAYER_SPAWNS,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.sprites import create_avatar_preview
from src.systems.profile import get_user_id

# Customizable categories: key, i18n label, swatch list
_CUSTOM_CATS = [
    ("skin",       "create_skin",       SKIN_SWATCH),
    ("hair_color", "create_hair_color", HAIR_SWATCH),
    ("outfit",     "create_outfit",     OUTFIT_SWATCH),
    ("eyes",       "create_eyes",       EYE_SWATCH),
]


class CreateGameScreen:
    """Two-phase screen: 1) choose solo/multi, 2) configure game + avatar."""

    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)

        # Phase: "mode" or "config"
        self.phase = "mode"

        # Mode selection
        self.mode = "solo"  # "solo" or "multi"
        self.num_players = 2
        self.mode_selected = 0  # 0=solo, 1=multi, 2=back
        self.mode_rects = []
        self.np_rects = []  # num_players selector rects

        # Config phase
        self.game_name = ""
        self.player_name = ""
        self.skin_idx = 0
        self.hair_idx = 0
        self.outfit_idx = 0
        self.eyes_idx = 0
        self.cursor_blink = 0.0

        # Config fields for keyboard nav
        self.fields = []
        self.selected_field = 0
        self._rebuild_fields()
        self._refresh_preview()
        self.field_rects = {}
        self.swatch_rects = {}

    def _rebuild_fields(self):
        if self.mode == "solo":
            self.fields = ["game_name", "skin", "hair_color", "outfit", "eyes", "start", "back"]
        else:
            self.fields = ["game_name", "player_name", "skin", "hair_color", "outfit", "eyes", "start", "back"]

    def _refresh_preview(self):
        self.preview = create_avatar_preview(
            self.skin_idx, self.hair_idx, self.outfit_idx, self.eyes_idx, size=64
        )

    def _get_cat_idx(self, key):
        if key == "skin":       return self.skin_idx
        if key == "hair_color": return self.hair_idx
        if key == "outfit":     return self.outfit_idx
        if key == "eyes":       return self.eyes_idx
        return 0

    def _set_cat_idx(self, key, val):
        if key == "skin":       self.skin_idx = val
        elif key == "hair_color": self.hair_idx = val
        elif key == "outfit":     self.outfit_idx = val
        elif key == "eyes":       self.eyes_idx = val
        self._refresh_preview()

    def _cycle_cat(self, key, direction):
        swatches = None
        for k, _, sw in _CUSTOM_CATS:
            if k == key:
                swatches = sw
                break
        if not swatches:
            return
        cur = self._get_cat_idx(key)
        self._set_cat_idx(key, (cur + direction) % len(swatches))

    def on_enter(self, **kwargs):
        self.phase = "mode"
        self.mode_selected = 0
        self.mode = "solo"
        self.num_players = 2
        self.game_name = ""
        self.player_name = ""
        self.skin_idx = 0
        self.hair_idx = 0
        self.outfit_idx = 0
        self.eyes_idx = 0
        self.selected_field = 0
        self._rebuild_fields()
        self._refresh_preview()

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    # ── EVENT HANDLING ──────────────────────────────────────────
    def handle_event(self, event):
        if self.phase == "mode":
            self._handle_mode_event(event)
        else:
            self._handle_config_event(event)

    def _handle_mode_event(self, event):
        # Mode choices: solo, multi-2, multi-3, multi-4, back
        total = 2 + (MAX_PLAYERS - 1) + 1  # solo + multi(2..4) + back = 6
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.mode_selected = (self.mode_selected - 1) % total
            elif event.key in (pygame.K_DOWN, pygame.K_s, pygame.K_TAB):
                self.mode_selected = (self.mode_selected + 1) % total
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_mode()
            elif event.key == pygame.K_ESCAPE:
                self._go_back()
        elif event.type == pygame.MOUSEMOTION:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.mode_rects):
                if rect and rect.collidepoint(mx, my):
                    self.mode_selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.mode_rects):
                if rect and rect.collidepoint(mx, my):
                    self.mode_selected = i
                    self._select_mode()
                    break

    def _select_mode(self):
        idx = self.mode_selected
        if idx == 0:
            self.mode = "solo"
            self.num_players = 1
            self._rebuild_fields()
            self.selected_field = 0
            self.phase = "config"
        elif 1 <= idx <= MAX_PLAYERS - 1:
            self.mode = "multi"
            self.num_players = idx + 1  # idx=1 → 2 players, idx=2 → 3, idx=3 → 4
            self._rebuild_fields()
            self.selected_field = 0
            self.phase = "config"
        else:
            self._go_back()

    def _handle_config_event(self, event):
        field = self.fields[self.selected_field]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            # Check swatch clicks
            for cat_key, rects in self.swatch_rects.items():
                for i, rect in enumerate(rects):
                    if rect and rect.collidepoint(mx, my):
                        self._set_cat_idx(cat_key, i)
                        if cat_key in self.fields:
                            self.selected_field = self.fields.index(cat_key)
                        return
            # Check other field clicks
            for fname, rect in self.field_rects.items():
                if rect and rect.collidepoint(mx, my):
                    idx = self.fields.index(fname) if fname in self.fields else -1
                    if idx >= 0:
                        self.selected_field = idx
                        if fname == "start":
                            self._start_game()
                        elif fname == "back":
                            self.phase = "mode"
                    break
            return

        if event.type == pygame.KEYDOWN:
            if field in ("game_name", "player_name"):
                if event.key == pygame.K_BACKSPACE:
                    if field == "game_name":
                        self.game_name = self.game_name[:-1]
                    else:
                        self.player_name = self.player_name[:-1]
                elif event.key == pygame.K_RETURN:
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key in (pygame.K_TAB, pygame.K_DOWN):
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key == pygame.K_UP:
                    self.selected_field = max(0, self.selected_field - 1)
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "mode"
            elif field in ("skin", "hair_color", "outfit", "eyes"):
                if event.key in (pygame.K_LEFT, pygame.K_a):
                    self._cycle_cat(field, -1)
                elif event.key in (pygame.K_RIGHT, pygame.K_d):
                    self._cycle_cat(field, 1)
                elif event.key in (pygame.K_DOWN, pygame.K_TAB):
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key == pygame.K_UP:
                    self.selected_field = max(0, self.selected_field - 1)
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "mode"
            else:
                if event.key in (pygame.K_DOWN, pygame.K_TAB):
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key == pygame.K_UP:
                    self.selected_field = max(0, self.selected_field - 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if field == "start":
                        self._start_game()
                    elif field == "back":
                        self.phase = "mode"
                elif event.key == pygame.K_ESCAPE:
                    self.phase = "mode"

        elif event.type == pygame.TEXTINPUT:
            if field == "game_name" and len(self.game_name) < 20:
                self.game_name += event.text
            elif field == "player_name" and len(self.player_name) < 20:
                self.player_name += event.text

    def _start_game(self):
        game_name = self.game_name.strip()
        if not game_name:
            game_name = t("create_name_placeholder")

        avatar = {
            "skin": self.skin_idx,
            "hair_color": self.hair_idx,
            "outfit": self.outfit_idx,
            "eyes": self.eyes_idx,
        }

        if self.mode == "solo":
            # Solo game — same format as before
            game_data = {
                "name": game_name,
                "mode": "solo",
                "avatar": avatar,
                "player_cx": PLAYER_START_X,
                "player_cy": PLAYER_START_Y,
                "player_facing": FACING_DOWN,
                "energy": 100,
                "inventory": [],
                "day": 1,
                "season": 0,
                "year": 1,
                "pg_total": 0,
            }
            self.game.data = game_data
            from src.screens.playing import PlayingScreen
            self.game.change_screen(PlayingScreen)
        else:
            # Multiplayer — host creates game, goes to lobby
            player_name = self.player_name.strip()
            if not player_name:
                player_name = "Jugador 1"

            host_player = {
                "id": 0,
                "name": player_name,
                "avatar": avatar,
                "user_id": get_user_id(),
                "cx": PLAYER_SPAWNS[0][0],
                "cy": PLAYER_SPAWNS[0][1],
                "facing": FACING_DOWN,
                "energy": 100,
                "inventory": [],
                "tools_data": None,
                "planted_types": [],
            }

            game_data = {
                "name": game_name,
                "mode": "multi",
                "num_players": self.num_players,
                "players": [host_player],
                "day": 1,
                "season": 0,
                "year": 1,
                "pg_total": 0,
                "is_host": True,
                "local_player_id": 0,
            }
            self.game.data = game_data
            from src.screens.lobby import LobbyScreen
            self.game.change_screen(LobbyScreen)

    def _go_back(self):
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        self.cursor_blink += dt

    # ── DRAW ────────────────────────────────────────────────────
    def draw(self, surface):
        if self.phase == "mode":
            self._draw_mode(surface)
        else:
            self._draw_config(surface)

    def _draw_mode(self, surface):
        surface.fill(COL_TITLE_BG)
        cx = INTERNAL_WIDTH // 2
        self.mode_rects = []

        draw_text(surface, t("create_mode_title"), cx, 40, self.font_title, COL_UI_HIGHLIGHT, center=True)

        y = 90
        # Solo button
        r = draw_button(surface, t("create_mode_solo"), cx, y,
                        self.font, selected=(self.mode_selected == 0), center=True)
        self.mode_rects.append(r)
        y += 32

        # Multi buttons: 2, 3, 4 players
        for n in range(2, MAX_PLAYERS + 1):
            idx = n - 1  # idx 1..3
            label = f"{t('create_mode_multi')} ({n} {t('create_num_players').rstrip(':')})"
            label = f"{t('create_mode_multi')} - {n} jug."
            r = draw_button(surface, label, cx, y,
                            self.font, selected=(self.mode_selected == idx), center=True)
            self.mode_rects.append(r)
            y += 32

        # Back button
        y += 10
        r = draw_button(surface, t("create_back"), cx, y,
                        self.font, selected=(self.mode_selected == MAX_PLAYERS), center=True)
        self.mode_rects.append(r)

    def _draw_config(self, surface):
        surface.fill(COL_TITLE_BG)

        cx = INTERNAL_WIDTH // 2
        self.field_rects = {}
        self.swatch_rects = {}

        # Title
        if self.mode == "solo":
            title = t("create_title")
        else:
            title = f"{t('create_title')} ({t('create_mode_multi')} {self.num_players})"
        draw_text(surface, title, cx, 18, self.font_title, COL_UI_HIGHLIGHT, center=True)

        # Avatar preview on the left
        pw, ph = self.preview.get_size()
        preview_x = 50
        preview_y = 55
        pygame.draw.rect(surface, (60, 60, 60),
                         (preview_x - 2, preview_y - 2, pw + 4, ph + 4), 1)
        surface.blit(self.preview, (preview_x, preview_y))

        # --- Fields on the right ---
        left_x = preview_x + pw + 24
        y = 55
        box_w = INTERNAL_WIDTH - left_x - 30

        # Game name field
        game_name_idx = self.fields.index("game_name")
        sel = self.selected_field == game_name_idx
        color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
        draw_text(surface, t("create_name"), left_x, y, self.font_small, color)
        y += 14
        box_h = 16
        box_color = COL_UI_HIGHLIGHT if sel else (80, 80, 80)
        name_rect = pygame.Rect(left_x, y, box_w, box_h)
        pygame.draw.rect(surface, box_color, name_rect, 1)
        self.field_rects["game_name"] = name_rect

        display_text = self.game_name if self.game_name else (
            t("create_name_placeholder") if not sel else ""
        )
        text_color = COL_UI_TEXT if self.game_name else (120, 120, 120)
        if display_text:
            draw_text(surface, display_text, left_x + 3, y + 2, self.font_small, text_color)
        if sel and int(self.cursor_blink * 3) % 2 == 0:
            cur_x = left_x + 3 + self.font_small.size(self.game_name)[0]
            pygame.draw.line(surface, COL_UI_HIGHLIGHT, (cur_x, y + 2), (cur_x, y + box_h - 2))

        y += 22

        # Player name field (multiplayer only)
        if self.mode == "multi":
            pn_idx = self.fields.index("player_name")
            sel = self.selected_field == pn_idx
            color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
            draw_text(surface, t("create_player_name"), left_x, y, self.font_small, color)
            y += 14
            pn_rect = pygame.Rect(left_x, y, box_w, box_h)
            box_color = COL_UI_HIGHLIGHT if sel else (80, 80, 80)
            pygame.draw.rect(surface, box_color, pn_rect, 1)
            self.field_rects["player_name"] = pn_rect

            display_text = self.player_name if self.player_name else (
                "Jugador 1" if not sel else ""
            )
            text_color = COL_UI_TEXT if self.player_name else (120, 120, 120)
            if display_text:
                draw_text(surface, display_text, left_x + 3, y + 2, self.font_small, text_color)
            if sel and int(self.cursor_blink * 3) % 2 == 0:
                cur_x = left_x + 3 + self.font_small.size(self.player_name)[0]
                pygame.draw.line(surface, COL_UI_HIGHLIGHT, (cur_x, y + 2), (cur_x, y + box_h - 2))
            y += 22

        # Colour customisation rows
        swatch_size = 14
        swatch_gap = 4
        for cat_key, label_key, swatches in _CUSTOM_CATS:
            field_idx = self.fields.index(cat_key)
            sel = self.selected_field == field_idx
            color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
            draw_text(surface, t(label_key), left_x, y + 1, self.font_small, color)
            sw_x = left_x + 60
            rects = []
            cur_idx = self._get_cat_idx(cat_key)
            for i, swatch_col in enumerate(swatches):
                rect = pygame.Rect(sw_x, y, swatch_size, swatch_size)
                pygame.draw.rect(surface, swatch_col, rect)
                if i == cur_idx:
                    pygame.draw.rect(surface, COL_UI_HIGHLIGHT, rect.inflate(4, 4), 2)
                elif sel:
                    pygame.draw.rect(surface, (80, 80, 80), rect, 1)
                rects.append(rect)
                sw_x += swatch_size + swatch_gap
            self.swatch_rects[cat_key] = rects
            self.field_rects[cat_key] = pygame.Rect(left_x, y, sw_x - left_x, swatch_size)
            y += swatch_size + 8

        y += 6

        # Buttons
        btn_cx = left_x + (INTERNAL_WIDTH - left_x - 30) // 2
        start_label = t("create_start") if self.mode == "solo" else t("lobby_start")
        r1 = draw_button(surface, start_label, btn_cx - 50, y,
                         self.font, selected=(self.selected_field == self.fields.index("start")),
                         center=False)
        self.field_rects["start"] = r1
        r2 = draw_button(surface, t("create_back"), btn_cx + 50, y,
                         self.font, selected=(self.selected_field == self.fields.index("back")),
                         center=False)
        self.field_rects["back"] = r2
