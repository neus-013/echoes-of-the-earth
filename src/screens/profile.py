import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.systems.profile import save_profile


class ProfileScreen:
    """First-launch screen: asks the user for their name to create a profile."""

    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.name = ""
        self.cursor_blink = 0.0
        self.confirm_rect = None

    def on_enter(self, **kwargs):
        self.name = ""
        self.cursor_blink = 0.0

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_BACKSPACE:
                self.name = self.name[:-1]
            elif event.key == pygame.K_RETURN:
                self._confirm()
        elif event.type == pygame.TEXTINPUT:
            if len(self.name) < 20:
                self.name += event.text
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            if self.confirm_rect and self.confirm_rect.collidepoint(mx, my):
                self._confirm()

    def _confirm(self):
        name = self.name.strip()
        if not name:
            name = "Jugador"
        profile = save_profile(name)
        self.game.profile = profile
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        self.cursor_blink += dt

    def draw(self, surface):
        surface.fill(COL_TITLE_BG)
        cx = INTERNAL_WIDTH // 2

        draw_text(surface, t("profile_title"), cx, 80,
                  self.font_title, COL_UI_HIGHLIGHT, center=True)

        draw_text(surface, t("profile_enter_name"), cx, 130,
                  self.font, COL_UI_TEXT, center=True)

        # Input box
        box_w, box_h = 200, 22
        box_x = cx - box_w // 2
        box_y = 155
        sel = True
        pygame.draw.rect(surface, COL_UI_HIGHLIGHT if sel else (80, 80, 80),
                         (box_x, box_y, box_w, box_h), 1)
        if self.name:
            draw_text(surface, self.name, box_x + 4, box_y + 4, self.font, COL_UI_TEXT)
        if int(self.cursor_blink * 3) % 2 == 0:
            cx2 = box_x + 4 + self.font.size(self.name)[0]
            pygame.draw.line(surface, COL_UI_HIGHLIGHT, (cx2, box_y + 3), (cx2, box_y + box_h - 3))

        # Confirm button
        self.confirm_rect = draw_button(surface, t("profile_confirm"), cx, 200,
                                        self.font, selected=True, center=True)
