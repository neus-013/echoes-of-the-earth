import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT,
    SKIN_SWATCH, HAIR_SWATCH, OUTFIT_SWATCH, EYE_SWATCH,
    NET_PORT,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.sprites import create_avatar_preview
from src.network import Client, discover_host
from src.systems.profile import get_user_id

_CUSTOM_CATS = [
    ("skin",       "create_skin",       SKIN_SWATCH),
    ("hair_color", "create_hair_color", HAIR_SWATCH),
    ("outfit",     "create_outfit",     OUTFIT_SWATCH),
    ("eyes",       "create_eyes",       EYE_SWATCH),
]


class JoinGameScreen:
    """Screen for a client to enter a game code, name, avatar, and connect."""

    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font_code = pygame.font.SysFont("arial", 20, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)

        self.game_code = ""
        self.player_name = ""
        self.skin_idx = 0
        self.hair_idx = 0
        self.outfit_idx = 0
        self.eyes_idx = 0
        self.cursor_blink = 0.0

        self.fields = ["game_code", "player_name", "skin", "hair_color", "outfit", "eyes",
                        "connect", "back"]
        self.selected_field = 0
        self.field_rects = {}
        self.swatch_rects = {}

        self.error_msg = ""
        self.connecting = False
        self._refresh_preview()

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
        self.game_code = ""
        self.player_name = ""
        self.skin_idx = 0
        self.hair_idx = 0
        self.outfit_idx = 0
        self.eyes_idx = 0
        self.selected_field = 0
        self.error_msg = ""
        self.connecting = False
        self._refresh_preview()

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def handle_event(self, event):
        if self.connecting:
            return

        field = self.fields[self.selected_field]

        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for cat_key, rects in self.swatch_rects.items():
                for i, rect in enumerate(rects):
                    if rect and rect.collidepoint(mx, my):
                        self._set_cat_idx(cat_key, i)
                        if cat_key in self.fields:
                            self.selected_field = self.fields.index(cat_key)
                        return
            for fname, rect in self.field_rects.items():
                if rect and rect.collidepoint(mx, my):
                    idx = self.fields.index(fname) if fname in self.fields else -1
                    if idx >= 0:
                        self.selected_field = idx
                        if fname == "connect":
                            self._try_connect()
                        elif fname == "back":
                            self._go_back()
                    break
            return

        if event.type == pygame.KEYDOWN:
            if field in ("game_code", "player_name"):
                if event.key == pygame.K_BACKSPACE:
                    if field == "game_code":
                        self.game_code = self.game_code[:-1]
                    else:
                        self.player_name = self.player_name[:-1]
                elif event.key in (pygame.K_RETURN, pygame.K_TAB, pygame.K_DOWN):
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key == pygame.K_UP:
                    self.selected_field = max(0, self.selected_field - 1)
                elif event.key == pygame.K_ESCAPE:
                    self._go_back()
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
                    self._go_back()
            else:
                if event.key in (pygame.K_DOWN, pygame.K_TAB):
                    self.selected_field = min(self.selected_field + 1, len(self.fields) - 1)
                elif event.key == pygame.K_UP:
                    self.selected_field = max(0, self.selected_field - 1)
                elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                    if field == "connect":
                        self._try_connect()
                    elif field == "back":
                        self._go_back()
                elif event.key == pygame.K_ESCAPE:
                    self._go_back()

        elif event.type == pygame.TEXTINPUT:
            if field == "game_code" and len(self.game_code) < 8:
                # Only allow alphanumeric, auto-uppercase
                ch = event.text.upper()
                self.game_code += "".join(c for c in ch if c.isalnum())
                self.game_code = self.game_code[:8]
            elif field == "player_name" and len(self.player_name) < 20:
                self.player_name += event.text

    def _try_connect(self):
        code = self.game_code.strip().upper()
        if not code:
            self.error_msg = t("join_no_code")
            return

        name = self.player_name.strip()
        if not name:
            name = "Jugador"

        avatar = {
            "skin": self.skin_idx,
            "hair_color": self.hair_idx,
            "outfit": self.outfit_idx,
            "eyes": self.eyes_idx,
        }

        self.connecting = True
        self.error_msg = ""

        # Discover host via UDP broadcast
        host_ip, tcp_port = discover_host(code, timeout=5.0)
        if host_ip is None:
            self.error_msg = t("join_code_not_found")
            self.connecting = False
            return

        # Connect via TCP
        client = Client()
        if not client.connect(host_ip, tcp_port, timeout=5):
            self.error_msg = t("join_failed")
            self.connecting = False
            return

        # Send join message
        client.send({
            "type": "join",
            "name": name,
            "avatar": avatar,
            "user_id": get_user_id(),
        })

        # Wait briefly for welcome response
        import time
        deadline = time.time() + 3.0
        player_id = None
        lobby_players = []
        num_players = 4
        while time.time() < deadline:
            msgs = client.poll()
            for msg in msgs:
                if msg.get("type") == "welcome":
                    player_id = msg["player_id"]
                    lobby_players = msg.get("lobby_players", [])
                    num_players = msg.get("num_players", 4)
                    break
                elif msg.get("type") == "reject":
                    self.error_msg = t("join_rejected")
                    client.close()
                    self.connecting = False
                    return
            if player_id is not None:
                break
            time.sleep(0.05)

        if player_id is None:
            self.error_msg = t("join_failed")
            client.close()
            self.connecting = False
            return

        # Success — go to lobby as client
        self.game.data = {
            "mode": "multi",
            "is_host": False,
            "local_player_id": player_id,
            "client": client,
            "num_players": num_players,
            "lobby_players": lobby_players,
            "game_code": code,
            "name": "",
        }
        self.connecting = False
        from src.screens.lobby import LobbyScreen
        self.game.change_screen(LobbyScreen)

    def _go_back(self):
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        self.cursor_blink += dt

    def draw(self, surface):
        surface.fill(COL_TITLE_BG)
        cx = INTERNAL_WIDTH // 2
        self.field_rects = {}
        self.swatch_rects = {}

        draw_text(surface, t("join_title"), cx, 14, self.font_title, COL_UI_HIGHLIGHT, center=True)

        # Avatar preview on left
        pw, ph = self.preview.get_size()
        preview_x = 40
        preview_y = 45
        pygame.draw.rect(surface, (60, 60, 60),
                         (preview_x - 2, preview_y - 2, pw + 4, ph + 4), 1)
        surface.blit(self.preview, (preview_x, preview_y))

        left_x = preview_x + pw + 20
        y = 45
        box_w = INTERNAL_WIDTH - left_x - 25
        box_h = 16

        # Game code field
        code_idx = self.fields.index("game_code")
        sel = self.selected_field == code_idx
        color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
        draw_text(surface, t("join_game_code"), left_x, y, self.font_small, color)
        y += 14
        code_box_h = 24
        code_rect = pygame.Rect(left_x, y, box_w, code_box_h)
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT if sel else (80, 80, 80), code_rect, 1)
        self.field_rects["game_code"] = code_rect
        display_code = self.game_code if self.game_code else (t("join_code_placeholder") if not sel else "")
        tcol = COL_UI_TEXT if self.game_code else (120, 120, 120)
        if display_code:
            draw_text(surface, display_code, left_x + 4, y + 4, self.font_code if self.game_code else self.font_small, tcol)
        if sel and int(self.cursor_blink * 3) % 2 == 0:
            font_for_cursor = self.font_code if self.game_code else self.font_small
            cx2 = left_x + 4 + font_for_cursor.size(self.game_code)[0]
            pygame.draw.line(surface, COL_UI_HIGHLIGHT, (cx2, y + 2), (cx2, y + code_box_h - 2))
        y += code_box_h + 8

        # Player name field
        pn_idx = self.fields.index("player_name")
        sel = self.selected_field == pn_idx
        color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
        draw_text(surface, t("join_player_name"), left_x, y, self.font_small, color)
        y += 14
        pn_rect = pygame.Rect(left_x, y, box_w, box_h)
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT if sel else (80, 80, 80), pn_rect, 1)
        self.field_rects["player_name"] = pn_rect
        display = self.player_name if self.player_name else ("Jugador" if not sel else "")
        tcol = COL_UI_TEXT if self.player_name else (120, 120, 120)
        if display:
            draw_text(surface, display, left_x + 3, y + 2, self.font_small, tcol)
        if sel and int(self.cursor_blink * 3) % 2 == 0:
            cx2 = left_x + 3 + self.font_small.size(self.player_name)[0]
            pygame.draw.line(surface, COL_UI_HIGHLIGHT, (cx2, y + 2), (cx2, y + box_h - 2))
        y += 20

        # Colour swatches
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
            y += swatch_size + 7

        y += 4

        # Error message
        if self.error_msg:
            draw_text(surface, self.error_msg, cx, y, self.font_small, (200, 80, 80), center=True)
            y += 18

        # Connecting message
        if self.connecting:
            draw_text(surface, t("join_searching"), cx, y, self.font_small,
                      (180, 180, 120), center=True)
            y += 18

        # Buttons
        btn_cx = left_x + (INTERNAL_WIDTH - left_x - 25) // 2
        r1 = draw_button(surface, t("join_connect"), btn_cx - 50, y,
                         self.font, selected=(self.selected_field == self.fields.index("connect")),
                         center=False)
        self.field_rects["connect"] = r1
        r2 = draw_button(surface, t("join_back"), btn_cx + 50, y,
                         self.font, selected=(self.selected_field == self.fields.index("back")),
                         center=False)
        self.field_rects["back"] = r2
