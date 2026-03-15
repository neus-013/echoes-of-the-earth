import pygame
import time
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT,
    NET_PORT,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.network import Client, discover_host


class RejoinScreen:
    """Screen for non-host players to auto-reconnect to a multiplayer game.

    Uses the game_code stored in the save to discover the host via UDP,
    then connects and sends a rejoin message with the player's name.
    """

    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.status_msg = ""
        self.error_msg = ""
        self.searching = False
        self.back_rect = None

    def on_enter(self, **kwargs):
        self.error_msg = ""
        self.status_msg = t("rejoin_searching")
        self.searching = True
        self._try_connect()

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def _try_connect(self):
        data = self.game.data
        code = data.get("game_code", "")
        local_pid = data.get("local_player_id", 1)

        # Find this player's name from saved data
        player_name = ""
        for pdata in data.get("players", []):
            if pdata.get("id") == local_pid:
                player_name = pdata.get("name", "Jugador")
                break

        if not code:
            self.error_msg = t("rejoin_no_code")
            self.searching = False
            return

        host_ip, tcp_port = discover_host(code, timeout=8.0)
        if host_ip is None:
            self.error_msg = t("rejoin_host_not_found")
            self.searching = False
            return

        client = Client()
        if not client.connect(host_ip, tcp_port, timeout=5):
            self.error_msg = t("join_failed")
            self.searching = False
            return

        # Send join with the saved player name (roster will validate)
        avatar = {}
        for pdata in data.get("players", []):
            if pdata.get("id") == local_pid:
                avatar = pdata.get("avatar", {})
                break

        client.send({
            "type": "join",
            "name": player_name,
            "avatar": avatar,
        })

        # Wait for welcome
        deadline = time.time() + 3.0
        player_id = None
        lobby_players = []
        num_players = data.get("num_players", 4)
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
                    self.searching = False
                    return
            if player_id is not None:
                break
            time.sleep(0.05)

        if player_id is None:
            self.error_msg = t("join_failed")
            client.close()
            self.searching = False
            return

        # Success — update data and go to lobby as client
        data["is_host"] = False
        data["local_player_id"] = player_id
        data["client"] = client
        data["num_players"] = num_players
        data["lobby_players"] = lobby_players
        self.searching = False

        from src.screens.lobby import LobbyScreen
        self.game.change_screen(LobbyScreen)

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
            elif event.key == pygame.K_RETURN and self.error_msg:
                # Retry
                self.error_msg = ""
                self.status_msg = t("rejoin_searching")
                self.searching = True
                self._try_connect()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            if self.back_rect and self.back_rect.collidepoint(mx, my):
                self._go_back()

    def _go_back(self):
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        pass

    def draw(self, surface):
        surface.fill(COL_TITLE_BG)
        cx = INTERNAL_WIDTH // 2

        draw_text(surface, t("rejoin_title"), cx, 80,
                  self.font_title, COL_UI_HIGHLIGHT, center=True)

        y = 140
        if self.searching:
            draw_text(surface, self.status_msg, cx, y,
                      self.font, COL_UI_TEXT, center=True)
        elif self.error_msg:
            draw_text(surface, self.error_msg, cx, y,
                      self.font, (200, 80, 80), center=True)
            y += 30
            draw_text(surface, t("rejoin_retry_hint"), cx, y,
                      self.font_small, (170, 170, 170), center=True)

        y = 250
        self.back_rect = draw_button(surface, t("lobby_back"), cx, y,
                                     self.font, selected=True, center=True)
