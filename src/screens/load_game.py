import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.systems.save_system import list_saves, load_game, delete_save
from src.systems.profile import get_user_id


class LoadGameScreen:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.saves = []
        self.selected = 0
        self.item_rects = []

    def on_enter(self, **kwargs):
        self._refresh_saves()

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def _get_user_id(self):
        profile = self.game.profile
        return profile["user_id"] if profile else None

    def _refresh_saves(self):
        self.saves = list_saves(user_id=self._get_user_id())
        if self.selected >= len(self.saves) + 1:
            self.selected = max(0, len(self.saves))

    def handle_event(self, event):
        total = len(self.saves) + 1  # saves + back button
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_UP, pygame.K_w):
                self.selected = (self.selected - 1) % total
            elif event.key in (pygame.K_DOWN, pygame.K_s):
                self.selected = (self.selected + 1) % total
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.selected < len(self.saves):
                    self._load_selected()
                else:
                    self._go_back()
            elif event.key == pygame.K_DELETE:
                if self.selected < len(self.saves):
                    self._delete_selected()
            elif event.key == pygame.K_ESCAPE:
                self._go_back()
        elif event.type == pygame.MOUSEMOTION:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.item_rects):
                if rect and rect.collidepoint(mx, my):
                    self.selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.item_rects):
                if rect and rect.collidepoint(mx, my):
                    self.selected = i
                    if i < len(self.saves):
                        self._load_selected()
                    else:
                        self._go_back()
                    break

    def _load_selected(self):
        save_info = self.saves[self.selected]
        uid = self._get_user_id()
        data = load_game(save_info["name"], user_id=uid)
        if data:
            self.game.data = data
            if data.get("mode") == "multi":
                # Find this user's player slot by user_id
                local_pid = 0
                for pdata in data.get("players", []):
                    if pdata.get("user_id") == uid:
                        local_pid = pdata["id"]
                        break
                data["local_player_id"] = local_pid
                if local_pid == 0:
                    # Host: re-create lobby to wait for players
                    data["is_host"] = True
                    data["roster_names"] = [p["name"] for p in data.get("players", [])]
                    from src.screens.lobby import LobbyScreen
                    self.game.change_screen(LobbyScreen)
                else:
                    # Non-host: go to waiting screen, auto-discover host
                    data["is_host"] = False
                    from src.screens.rejoin import RejoinScreen
                    self.game.change_screen(RejoinScreen)
            else:
                from src.screens.playing import PlayingScreen
                self.game.change_screen(PlayingScreen)

    def _delete_selected(self):
        save_info = self.saves[self.selected]
        delete_save(save_info["name"], user_id=self._get_user_id())
        self._refresh_saves()

    def _go_back(self):
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(COL_TITLE_BG)

        cx = INTERNAL_WIDTH // 2
        self.item_rects = []

        draw_text(surface, t("load_title"), cx, 28, self.font_title, COL_UI_HIGHLIGHT, center=True)

        if not self.saves:
            draw_text(surface, t("load_empty"), cx, 120, self.font, (150, 150, 150), center=True)
            r = draw_button(surface, t("load_back"), cx, 180, self.font,
                       selected=True, center=True)
            self.item_rects.append(r)
            return

        y = 70
        for i, save in enumerate(self.saves):
            sel = (i == self.selected)
            color = COL_UI_HIGHLIGHT if sel else COL_UI_TEXT
            prefix = "> " if sel else "  "

            name = save["name"]
            season_key = f"season_{save['season']}"
            mode_tag = ""
            if save.get("mode") == "multi":
                mode_tag = f" [{save.get('num_players', 2)}P]"
            info = f"{t('hud_day')} {save['day']} - {t(season_key)} - {t('year')} {save['year']}{mode_tag}"

            r = draw_text(surface, f"{prefix}{name}", 40, y, self.font, color)
            draw_text(surface, info, 60, y + 16, self.font_small, (170, 170, 170))

            if sel:
                draw_text(surface, t("load_delete"), INTERNAL_WIDTH - 110, y + 6,
                         self.font_small, (180, 100, 100))

            # Make the rect cover the full row for clicking
            row_rect = pygame.Rect(30, y - 2, INTERNAL_WIDTH - 60, 34)
            self.item_rects.append(row_rect)

            y += 38

        # Back button
        r = draw_button(surface, t("load_back"), cx, y + 14, self.font,
                   selected=(self.selected >= len(self.saves)), center=True)
        self.item_rects.append(r)
