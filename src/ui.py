import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT, TOOLBAR_VISIBLE,
    COL_UI_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT, COL_UI_SELECTED,
    COL_ENERGY_BAR, COL_ENERGY_LOW, COL_ENERGY_BG,
    PLAYER_MAX_ENERGY, WHITE, BLACK,
)
from src.i18n import t
from src.sprites import create_item_icon

_item_icon_cache = {}


def _get_item_icon(item_id):
    if item_id not in _item_icon_cache:
        _item_icon_cache[item_id] = create_item_icon(item_id, 16)
    return _item_icon_cache[item_id]


class HUD:
    def __init__(self):
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 11)
        self.messages = []
        self.craft_button_rect = None
        self.toolbar_rects = []
        self.tool_slot_rect = None

    def add_message(self, text, duration=2.0):
        self.messages.append([text, duration])

    def update(self, dt):
        self.messages = [[m, t - dt] for m, t in self.messages if t - dt > 0]

    def draw(self, surface, player, time_system, inventory, day, season, year,
             tool_manager=None):
        self._draw_top_bar(surface, time_system, day, season, year)
        self._draw_energy_bar(surface, player.energy)
        self._draw_toolbar(surface, inventory)
        if tool_manager:
            self._draw_tool_slot(surface, tool_manager)
        self._draw_craft_button(surface)
        self._draw_messages(surface)

    def _draw_top_bar(self, surface, time_system, day, season, year):
        bg = pygame.Surface((220, 34), pygame.SRCALPHA)
        bg.fill((*COL_UI_BG, 180))
        surface.blit(bg, (4, 4))

        season_key = f"season_{season}"
        info = f"{t('hud_day')} {day}  {t(season_key)}  {t('year')} {year}"
        text_surf = self.font.render(info, False, COL_UI_TEXT)
        surface.blit(text_surf, (8, 6))

        time_str = time_system.get_display_time()
        time_surf = self.font.render(time_str, False, COL_UI_HIGHLIGHT)
        surface.blit(time_surf, (8, 21))

    def _draw_energy_bar(self, surface, energy):
        bar_w = 70
        bar_h = 8
        x = INTERNAL_WIDTH - bar_w - 10
        y = 8

        bg = pygame.Surface((bar_w + 12, 26), pygame.SRCALPHA)
        bg.fill((*COL_UI_BG, 180))
        surface.blit(bg, (x - 6, y - 4))

        label = self.font_small.render(t("hud_energy"), False, COL_UI_TEXT)
        surface.blit(label, (x, y - 2))

        pygame.draw.rect(surface, COL_ENERGY_BG, (x, y + 12, bar_w, bar_h))

        ratio = max(0, energy / PLAYER_MAX_ENERGY)
        fill_w = int(bar_w * ratio)
        color = COL_ENERGY_BAR if ratio > 0.3 else COL_ENERGY_LOW
        if fill_w > 0:
            pygame.draw.rect(surface, color, (x, y + 12, fill_w, bar_h))

        pygame.draw.rect(surface, COL_UI_TEXT, (x, y + 12, bar_w, bar_h), 1)

    def _draw_toolbar(self, surface, inventory):
        slot_size = 24
        padding = 3
        total_w = TOOLBAR_VISIBLE * (slot_size + padding) - padding
        start_x = (INTERNAL_WIDTH - total_w) // 2
        y = INTERNAL_HEIGHT - slot_size - 8

        bg = pygame.Surface((total_w + 10, slot_size + 18), pygame.SRCALPHA)
        bg.fill((*COL_UI_BG, 180))
        surface.blit(bg, (start_x - 5, y - 5))

        vis_start, vis_end = inventory.get_visible_range()

        self.toolbar_rects = []
        for i in range(TOOLBAR_VISIBLE):
            abs_idx = vis_start + i
            sx = start_x + i * (slot_size + padding)
            rect = pygame.Rect(sx, y, slot_size, slot_size)
            self.toolbar_rects.append(rect)

            # Draw selection highlight (compare absolute index)
            if abs_idx == inventory.selected_slot:
                pygame.draw.rect(surface, COL_UI_SELECTED, (sx - 1, y - 1, slot_size + 2, slot_size + 2), 2)
            else:
                pygame.draw.rect(surface, (80, 80, 80), (sx, y, slot_size, slot_size), 1)

            slot = inventory.slots[abs_idx] if abs_idx < len(inventory.slots) else None
            if slot:
                icon = _get_item_icon(slot["item"])
                ix = sx + (slot_size - icon.get_width()) // 2
                iy = y + (slot_size - icon.get_height()) // 2 - 1
                surface.blit(icon, (ix, iy))

                if slot["qty"] > 1:
                    qty_surf = self.font_small.render(str(slot["qty"]), False, WHITE)
                    surface.blit(qty_surf, (sx + slot_size - qty_surf.get_width() - 1, y + slot_size - 12))

        # Page indicator (e.g. "1/2")
        page_text = f"{inventory.toolbar_page + 1}/2"
        page_surf = self.font_small.render(page_text, False, COL_UI_HIGHLIGHT)
        surface.blit(page_surf, (start_x + total_w // 2 - page_surf.get_width() // 2,
                                 y + slot_size + 2))

    def _draw_tool_slot(self, surface, tool_manager):
        slot_size = 28
        x = 8
        y = INTERNAL_HEIGHT - slot_size - 10

        # Background
        bg = pygame.Surface((slot_size + 8, slot_size + 20), pygame.SRCALPHA)
        bg.fill((*COL_UI_BG, 200))
        surface.blit(bg, (x - 4, y - 16))

        # Label
        label = self.font_small.render(t("hud_tool"), False, COL_UI_HIGHLIGHT)
        surface.blit(label, (x, y - 14))

        # Slot border — highlighted only when tool is active
        border_col = COL_UI_SELECTED if tool_manager.active else (80, 80, 80)
        pygame.draw.rect(surface, border_col, (x, y, slot_size, slot_size), 2)

        # Clickable rect
        self.tool_slot_rect = pygame.Rect(x, y, slot_size, slot_size)

        # Tool icon
        tool_id = tool_manager.current
        icon = _get_item_icon(tool_id)
        ix = x + (slot_size - icon.get_width()) // 2
        iy = y + (slot_size - icon.get_height()) // 2
        surface.blit(icon, (ix, iy))

        # Water indicator for water tools
        if tool_manager.is_water_tool():
            water = tool_manager.get_water()
            cap = tool_manager.get_capacity()
            water_text = f"{water}/{cap}"
            ws = self.font_small.render(water_text, False, (105, 175, 210))
            surface.blit(ws, (x, y + slot_size + 2))

    def _draw_craft_button(self, surface):
        bw, bh = 55, 16
        x = INTERNAL_WIDTH - bw - 8
        y = INTERNAL_HEIGHT - bh - 10

        bg = pygame.Surface((bw, bh), pygame.SRCALPHA)
        bg.fill((*COL_UI_BG, 200))
        surface.blit(bg, (x, y))
        pygame.draw.rect(surface, COL_UI_SELECTED, (x, y, bw, bh), 1)

        label = self.font_small.render(t("craft_button"), False, COL_UI_HIGHLIGHT)
        lx = x + (bw - label.get_width()) // 2
        ly = y + (bh - label.get_height()) // 2
        surface.blit(label, (lx, ly))
        self.craft_button_rect = pygame.Rect(x, y, bw, bh)

    def _draw_messages(self, surface):
        y = INTERNAL_HEIGHT // 2 - 30
        for msg, timer in self.messages:
            alpha = min(255, int(timer * 255))
            text_surf = self.font.render(msg, False, COL_UI_HIGHLIGHT)
            temp = pygame.Surface(text_surf.get_size(), pygame.SRCALPHA)
            temp.blit(text_surf, (0, 0))
            temp.set_alpha(alpha)
            x = (INTERNAL_WIDTH - text_surf.get_width()) // 2
            surface.blit(temp, (x, y))
            y -= 18


def draw_text(surface, text, x, y, font, color=COL_UI_TEXT, center=False):
    rendered = font.render(text, False, color)
    if center:
        rect = rendered.get_rect(center=(x, y))
    else:
        rect = rendered.get_rect(topleft=(x, y))
    surface.blit(rendered, rect)
    return rect


def draw_button(surface, text, x, y, font, selected=False, center=True):
    color = COL_UI_HIGHLIGHT if selected else COL_UI_TEXT
    if selected:
        prefix = "> "
        suffix = " <"
    else:
        prefix = "  "
        suffix = "  "
    full_text = prefix + text + suffix
    return draw_text(surface, full_text, x, y, font, color, center)
