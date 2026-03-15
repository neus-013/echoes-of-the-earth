import pygame
from src.settings import (
    INTERNAL_WIDTH, INTERNAL_HEIGHT,
    COL_TITLE_BG, COL_UI_TEXT, COL_UI_HIGHLIGHT,
    PLAYER_SPAWNS, FACING_DOWN, NET_PORT, DISCOVERY_PORT,
)
from src.i18n import t
from src.ui import draw_text, draw_button
from src.network import Server, get_local_ip, generate_game_code, DiscoveryBeacon


class LobbyScreen:
    """Waiting room before a multiplayer game starts.

    For the host: starts a server, waits for all clients to connect,
    then launches PlayingScreen.
    For a client: waits for the host to start the game.
    """

    def __init__(self, game):
        self.game = game
        self.font_title = pygame.font.SysFont("arial", 22, bold=True)
        self.font_code = pygame.font.SysFont("arial", 28, bold=True)
        self.font = pygame.font.SysFont("arial", 14)
        self.font_small = pygame.font.SysFont("arial", 12)
        self.font_tiny = pygame.font.SysFont("arial", 11)

        self.is_host = True
        self.server = None
        self.beacon = None
        self.game_code = ""
        self.num_players = 2

        # Player slots: list of {id, name, avatar} — slot 0 is always the host
        self.player_slots = []

        self.button_rects = []
        self.error_msg = ""

    def on_enter(self, **kwargs):
        data = self.game.data
        self.is_host = data.get("is_host", True)
        self.num_players = data.get("num_players", 2)

        if self.is_host:
            self.player_slots = list(data.get("players", []))
            # Reuse existing game code or generate a new one
            self.game_code = data.get("game_code") or generate_game_code()
            data["game_code"] = self.game_code
            # Start TCP server
            self.server = Server(self.num_players)
            try:
                self.server.start(NET_PORT)
                self.error_msg = ""
            except OSError as e:
                self.error_msg = str(e)
                self.server = None
            # Start UDP discovery beacon
            if self.server:
                self.beacon = DiscoveryBeacon(self.game_code, tcp_port=NET_PORT)
                try:
                    self.beacon.start(DISCOVERY_PORT)
                except OSError:
                    self.beacon = None  # non-critical
            # Store server reference in game.data so PlayingScreen can access it
            data["server"] = self.server
        else:
            # Client mode — player_slots will be populated from server messages
            self.player_slots = data.get("lobby_players", [])
            self.game_code = data.get("game_code", "")

    def _to_internal(self, pos):
        return self.game.screen_to_internal(pos[0], pos[1])

    def handle_event(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_ESCAPE:
                self._go_back()
            elif event.key in (pygame.K_RETURN, pygame.K_SPACE):
                if self.is_host and self._all_connected():
                    self._start_game()
        elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            mx, my = self._to_internal(event.pos)
            for i, rect in enumerate(self.button_rects):
                if rect and rect.collidepoint(mx, my):
                    if i == 0 and self.is_host and self._all_connected():
                        self._start_game()
                    elif i == 1 or (i == 0 and not self._all_connected()):
                        self._go_back()

    def _all_connected(self):
        return len(self.player_slots) >= self.num_players

    def _start_game(self):
        if not self.is_host:
            return

        # Stop discovery beacon — no longer needed
        if self.beacon:
            self.beacon.stop()
            self.beacon = None

        data = self.game.data
        data["players"] = self.player_slots

        # Tell all clients the game is starting
        if self.server:
            self.server.broadcast({
                "type": "game_start",
                "game_data": {
                    "name": data["name"],
                    "mode": "multi",
                    "num_players": self.num_players,
                    "players": self.player_slots,
                    "day": data.get("day", 1),
                    "season": data.get("season", 0),
                    "year": data.get("year", 1),
                    "pg_total": data.get("pg_total", 0),
                    "game_code": self.game_code,
                },
            })

        from src.screens.playing import PlayingScreen
        self.game.change_screen(PlayingScreen)

    def _go_back(self):
        if self.beacon:
            self.beacon.stop()
            self.beacon = None
        if self.server:
            self.server.stop()
            self.server = None
        self.game.data.pop("server", None)
        self.game.data.pop("game_code", None)
        # If we're a client, close the connection
        client = self.game.data.get("client")
        if client:
            client.close()
            self.game.data.pop("client", None)
        from src.screens.title import TitleScreen
        self.game.change_screen(TitleScreen)

    def update(self, dt):
        if self.is_host and self.server:
            self._host_poll()
        elif not self.is_host:
            self._client_poll()

    def _host_poll(self):
        """Process incoming connections and join messages on the host."""
        messages = self.server.poll()
        for pid, msg in messages:
            if msg.get("type") == "join":
                # Validate: check we haven't exceeded player count
                if len(self.player_slots) >= self.num_players:
                    self.server.send_to(pid, {"type": "reject", "reason": "full"})
                    continue

                # Check if this is a load game with a roster
                roster = self.game.data.get("roster_names")
                if roster:
                    name = msg.get("name", "")
                    if name not in roster:
                        self.server.send_to(pid, {"type": "reject", "reason": "not_in_roster"})
                        continue
                    # Check not already connected
                    taken = {p["name"] for p in self.player_slots}
                    if name in taken:
                        self.server.send_to(pid, {"type": "reject", "reason": "name_taken"})
                        continue

                slot_id = len(self.player_slots)
                player_data = {
                    "id": slot_id,
                    "name": msg.get("name", f"Jugador {slot_id+1}"),
                    "avatar": msg.get("avatar", {}),
                    "user_id": msg.get("user_id", ""),
                    "cx": PLAYER_SPAWNS[slot_id][0],
                    "cy": PLAYER_SPAWNS[slot_id][1],
                    "facing": FACING_DOWN,
                    "energy": 100,
                    "inventory": [],
                    "tools_data": None,
                    "planted_types": [],
                    "net_pid": pid,  # network player id for routing
                }
                self.player_slots.append(player_data)
                self.server.player_info[pid] = {
                    "slot_id": slot_id,
                    "name": player_data["name"],
                }

                # Confirm to the joining client
                self.server.send_to(pid, {
                    "type": "welcome",
                    "player_id": slot_id,
                    "num_players": self.num_players,
                    "lobby_players": self.player_slots,
                })

                # Broadcast updated lobby to all clients
                self.server.broadcast({
                    "type": "lobby_update",
                    "lobby_players": self.player_slots,
                })

            elif msg.get("type") == "disconnected":
                # Remove player
                info = self.server.player_info.get(pid)
                if info:
                    sid = info["slot_id"]
                    self.player_slots = [p for p in self.player_slots if p["id"] != sid]
                    # Re-broadcast lobby
                    self.server.broadcast({
                        "type": "lobby_update",
                        "lobby_players": self.player_slots,
                    })

    def _client_poll(self):
        """Process messages from server on the client side."""
        client = self.game.data.get("client")
        if not client:
            return

        messages = client.poll()
        for msg in messages:
            if msg.get("type") == "lobby_update":
                self.player_slots = msg.get("lobby_players", [])
            elif msg.get("type") == "game_start":
                # Server says go!
                gd = msg.get("game_data", {})
                self.game.data.update(gd)
                self.game.data["is_host"] = False
                from src.screens.playing import PlayingScreen
                self.game.change_screen(PlayingScreen)
            elif msg.get("type") == "reject":
                self.error_msg = t("join_rejected")

        if not client.connected:
            self.error_msg = t("msg_disconnected")

    def draw(self, surface):
        surface.fill(COL_TITLE_BG)
        cx = INTERNAL_WIDTH // 2
        self.button_rects = []

        draw_text(surface, t("lobby_title"), cx, 28, self.font_title, COL_UI_HIGHLIGHT, center=True)

        y = 65

        # Show game code prominently
        if self.is_host and self.game_code:
            draw_text(surface, t("lobby_game_code"), cx, y, self.font, COL_UI_TEXT, center=True)
            y += 20
            draw_text(surface, self.game_code, cx, y, self.font_code, (120, 230, 120), center=True)
            y += 36
        elif not self.is_host and self.game_code:
            draw_text(surface, "%s %s" % (t("lobby_game_code"), self.game_code),
                      cx, y, self.font, COL_UI_TEXT, center=True)
            y += 24

        # Error
        if self.error_msg:
            draw_text(surface, self.error_msg, cx, y, self.font_small, (200, 80, 80), center=True)
            y += 20

        # Player slots
        draw_text(surface, t("lobby_players"), cx, y, self.font, COL_UI_TEXT, center=True)
        y += 22

        for i in range(self.num_players):
            if i < len(self.player_slots):
                p = self.player_slots[i]
                label = f"  {i+1}. {p['name']}"
                color = COL_UI_HIGHLIGHT
            else:
                label = f"  {i+1}. {t('lobby_empty_slot')}"
                color = (120, 120, 120)
            draw_text(surface, label, cx, y, self.font_small, color, center=True)
            y += 20

        y += 16

        # Status
        if self._all_connected():
            draw_text(surface, t("lobby_ready"), cx, y, self.font, (100, 200, 100), center=True)
        else:
            draw_text(surface, t("lobby_waiting"), cx, y, self.font, (180, 180, 120), center=True)
        y += 28

        # Buttons
        if self.is_host and self._all_connected():
            r = draw_button(surface, t("lobby_start"), cx, y, self.font,
                            selected=True, center=True)
            self.button_rects.append(r)
            y += 30

        r = draw_button(surface, t("lobby_back"), cx, y, self.font,
                        selected=not (self.is_host and self._all_connected()), center=True)
        self.button_rects.append(r)
