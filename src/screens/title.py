import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, WHITE,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.sprites import create_title_illustration


class TitleScreen:
    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 28, bold=True)
        self.font_menu = pygame.font.SysFont("arial", 18)
        self.font_small = pygame.font.SysFont("arial", 14)
        self.options = ["new_game", "load_game", "join_game", "exit"]
        self.selected = 0
        self.button_rects = []
        self._bg = None

    def on_enter(self, **kwargs):
        self.selected = 0
        if self._bg is None:
            self._bg = create_title_illustration(INTERNAL_WIDTH, INTERNAL_HEIGHT)

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key in (pygame.K_w, pygame.K_UP):
                self.selected = (self.selected - 1) % len(self.options)
            elif event.key in (pygame.K_s, pygame.K_DOWN):
                self.selected = (self.selected + 1) % len(self.options)
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                self._select_option()
            elif event.key == pygame.K_ESCAPE:
                self.game.quit()
        elif event.type == pygame.MOUSEMOTION:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.button_rects):
                if rect and rect.collidepoint(mx, my):
                    self.selected = i
                    break
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.button_rects):
                if rect and rect.collidepoint(mx, my):
                    self.selected = i
                    self._select_option()
                    break

    def _select_option(self):
        opt = self.options[self.selected]
        if opt == "new_game":
            from src.screens.create_game import CreateGameScreen
            self.game.change_screen(CreateGameScreen)
        elif opt == "load_game":
            from src.screens.load_game import LoadGameScreen
            self.game.change_screen(LoadGameScreen)
        elif opt == "join_game":
            from src.screens.join_game import JoinGameScreen
            self.game.change_screen(JoinGameScreen)
        elif opt == "exit":
            self.game.quit()

    def update(self, dt):
        pass

    def draw(self, surface):
        # Illustrated background
        if self._bg:
            surface.blit(self._bg, (0, 0))
        else:
            surface.fill(COL_TITLE_BG)

        # Semi-transparent overlay for text readability (lower portion)
        overlay = pygame.Surface((INTERNAL_WIDTH, 140), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 80))
        surface.blit(overlay, (0, INTERNAL_HEIGHT - 140))

        # Title
        cx = INTERNAL_WIDTH // 2
        # Shadow
        draw_text(surface, t("game_title"), cx + 1, 76, self.font_title, (20, 15, 8), center=True)
        draw_text(surface, t("game_title"), cx, 75, self.font_title, (255, 240, 200), center=True)

        # Decorative line
        pygame.draw.line(surface, (255, 220, 140, 180), (cx - 70, 100), (cx + 70, 100), 1)

        # Menu options
        labels = {
            "new_game": t("menu_new_game"),
            "load_game": t("menu_load_game"),
            "join_game": t("menu_join_game"),
            "exit": t("menu_exit"),
        }

        self.button_rects = []
        y_start = INTERNAL_HEIGHT - 120
        for i, opt in enumerate(self.options):
            rect = draw_button(surface, labels[opt], cx, y_start + i * 32,
                       self.font_menu, selected=(i == self.selected))
            self.button_rects.append(rect)

        # Language indicator
        draw_text(surface, t("menu_language"), INTERNAL_WIDTH - 10, INTERNAL_HEIGHT - 18,
                 self.font_small, (150, 150, 150), center=False)
