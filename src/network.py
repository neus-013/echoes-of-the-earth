"""
Multiplayer networking module for Echoes of the Earth.

Uses TCP sockets with length-prefixed JSON messages.
Server runs on the host; clients connect to join.
Includes UDP discovery so clients can find a host by game code.
"""

import socket
import select
import struct
import json
import threading
import random
import string
import time


DEFAULT_PORT = 7777
DISCOVERY_PORT = 7778
HEADER_SIZE = 4  # 4-byte big-endian message length

# Characters that are easy to read and not confusable
_CODE_CHARS = "ABCDEFGHJKMNPQRSTUVWXYZ23456789"


def generate_game_code(length=5):
    """Generate a short, human-friendly game code."""
    return "".join(random.choices(_CODE_CHARS, k=length))


# ── Message helpers ─────────────────────────────────────────────

def _send_msg(sock, message):
    """Send a length-prefixed JSON message."""
    data = json.dumps(message, ensure_ascii=False).encode("utf-8")
    header = struct.pack("!I", len(data))
    try:
        sock.sendall(header + data)
        return True
    except (OSError, BrokenPipeError, ConnectionResetError):
        return False


def _read_messages(sock, buffer):
    """Read available data from sock, parse complete messages.

    Returns (messages_list, updated_buffer, alive).
    """
    try:
        data = sock.recv(8192)
    except BlockingIOError:
        return [], buffer, True
    except (OSError, ConnectionResetError):
        return [], buffer, False

    if not data:
        return [], buffer, False  # connection closed

    buffer += data
    messages = []

    while len(buffer) >= HEADER_SIZE:
        msg_len = struct.unpack("!I", buffer[:HEADER_SIZE])[0]
        if msg_len > 1_000_000:  # sanity limit: 1 MB
            return messages, b"", False
        if len(buffer) < HEADER_SIZE + msg_len:
            break  # incomplete message
        payload = buffer[HEADER_SIZE : HEADER_SIZE + msg_len]
        buffer = buffer[HEADER_SIZE + msg_len :]
        try:
            msg = json.loads(payload.decode("utf-8"))
            messages.append(msg)
        except (json.JSONDecodeError, UnicodeDecodeError):
            pass  # skip malformed

    return messages, buffer, True


def get_local_ip():
    """Best-effort LAN IP detection."""
    try:
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        s.connect(("8.8.8.8", 80))
        ip = s.getsockname()[0]
        s.close()
        return ip
    except Exception:
        try:
            return socket.gethostbyname(socket.gethostname())
        except Exception:
            return "127.0.0.1"


# ── UDP Discovery ───────────────────────────────────────────────

class DiscoveryBeacon:
    """UDP beacon that lets clients find this host by game code.

    The host runs this alongside the TCP server. Clients broadcast
    a query with three pipe separated fields "ALBADA_DISCOVER|<code>|?", and the beacon
    replies with "ALBADA_DISCOVER|<code>|<tcp_ip>:<tcp_port>".
    """

    def __init__(self, game_code, tcp_port=DEFAULT_PORT):
        self.game_code = game_code
        self.tcp_port = tcp_port
        self.local_ip = get_local_ip()
        self._sock = None
        self._thread = None
        self._running = False

    def start(self, port=DISCOVERY_PORT):
        self._sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self._sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
        self._sock.bind(("0.0.0.0", port))
        self._sock.settimeout(0.5)
        self._running = True
        self._thread = threading.Thread(target=self._listen, daemon=True)
        self._thread.start()

    def _listen(self):
        while self._running:
            try:
                data, addr = self._sock.recvfrom(256)
            except socket.timeout:
                continue
            except OSError:
                break
            try:
                text = data.decode("utf-8").strip()
            except UnicodeDecodeError:
                continue
            # Expected: "ALBADA_DISCOVER|<code>|?"
            parts = text.split("|")
            if len(parts) == 3 and parts[0] == "ALBADA_DISCOVER" and parts[2] == "?":
                if parts[1].upper() == self.game_code.upper():
                    reply = "ALBADA_DISCOVER|%s|%s:%d" % (
                        self.game_code, self.local_ip, self.tcp_port
                    )
                    try:
                        self._sock.sendto(reply.encode("utf-8"), addr)
                    except OSError:
                        pass

    def stop(self):
        self._running = False
        if self._sock:
            try:
                self._sock.close()
            except OSError:
                pass
        if self._thread:
            self._thread.join(timeout=2)
        self._sock = None
        self._thread = None


def discover_host(game_code, timeout=5.0, discovery_port=DISCOVERY_PORT):
    """Broadcast a query to find the host with the given game code.

    Returns (host_ip, tcp_port) on success, or (None, None) on failure.
    """
    sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_BROADCAST, 1)
    sock.settimeout(1.0)

    query = ("ALBADA_DISCOVER|%s|?" % game_code.upper()).encode("utf-8")
    deadline = time.time() + timeout

    try:
        while time.time() < deadline:
            # Send to broadcast
            try:
                sock.sendto(query, ("<broadcast>", discovery_port))
            except OSError:
                pass
            # Also try common subnet broadcast (255.255.255.255 may be blocked)
            try:
                sock.sendto(query, ("255.255.255.255", discovery_port))
            except OSError:
                pass

            # Listen for reply
            read_deadline = min(time.time() + 1.0, deadline)
            while time.time() < read_deadline:
                remaining = read_deadline - time.time()
                if remaining <= 0:
                    break
                sock.settimeout(max(0.1, remaining))
                try:
                    data, addr = sock.recvfrom(256)
                except socket.timeout:
                    break
                except OSError:
                    break
                try:
                    text = data.decode("utf-8").strip()
                except UnicodeDecodeError:
                    continue
                parts = text.split("|")
                if (len(parts) == 3 and parts[0] == "ALBADA_DISCOVER"
                        and parts[1].upper() == game_code.upper() and parts[2] != "?"):
                    # parts[2] = "ip:port"
                    hp = parts[2].rsplit(":", 1)
                    if len(hp) == 2:
                        try:
                            return hp[0], int(hp[1])
                        except ValueError:
                            pass
    finally:
        sock.close()

    return None, None


# ── Server ──────────────────────────────────────────────────────

class Server:
    """Authoritative game server running on the host machine."""

    def __init__(self, num_players):
        self.num_players = num_players
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        self.clients = {}       # player_id -> socket
        self.buffers = {}       # player_id -> bytes
        self.player_info = {}   # player_id -> {"name": str, "avatar": dict}
        self.next_id = 1        # 0 is reserved for host
        self.running = False
        self._accept_thread = None

    def start(self, port=DEFAULT_PORT):
        self.sock.bind(("0.0.0.0", port))
        self.sock.listen(self.num_players)
        self.sock.setblocking(False)
        self.running = True

    def poll(self):
        """Non-blocking poll. Returns list of (player_id, message) tuples."""
        results = []

        # Accept new connections
        try:
            while True:
                conn, addr = self.sock.accept()
                conn.setblocking(False)
                pid = self.next_id
                self.next_id += 1
                self.clients[pid] = conn
                self.buffers[pid] = b""
        except BlockingIOError:
            pass
        except OSError:
            pass

        # Read from connected clients
        dead = []
        for pid, sock in list(self.clients.items()):
            try:
                readable, _, _ = select.select([sock], [], [], 0)
            except (OSError, ValueError):
                dead.append(pid)
                continue

            if readable:
                msgs, self.buffers[pid], alive = _read_messages(sock, self.buffers[pid])
                if not alive:
                    dead.append(pid)
                    continue
                for m in msgs:
                    results.append((pid, m))

        # Handle disconnections
        for pid in dead:
            self._disconnect(pid)
            results.append((pid, {"type": "disconnected"}))

        return results

    def broadcast(self, message, exclude=None):
        """Send message to all connected clients."""
        dead = []
        for pid, sock in list(self.clients.items()):
            if pid == exclude:
                continue
            if not _send_msg(sock, message):
                dead.append(pid)
        for pid in dead:
            self._disconnect(pid)

    def send_to(self, player_id, message):
        """Send message to a specific client."""
        if player_id in self.clients:
            if not _send_msg(self.clients[player_id], message):
                self._disconnect(player_id)

    def _disconnect(self, player_id):
        if player_id in self.clients:
            try:
                self.clients[player_id].close()
            except OSError:
                pass
            del self.clients[player_id]
            if player_id in self.buffers:
                del self.buffers[player_id]

    @property
    def connected_count(self):
        """Number of remote clients connected (not counting host)."""
        return len(self.clients)

    def is_full(self):
        """All expected remote players have connected."""
        return self.connected_count >= self.num_players - 1

    def stop(self):
        self.running = False
        for sock in list(self.clients.values()):
            try:
                sock.close()
            except OSError:
                pass
        self.clients.clear()
        self.buffers.clear()
        try:
            self.sock.close()
        except OSError:
            pass


# ── Client ──────────────────────────────────────────────────────

class Client:
    """Game client that connects to a host server."""

    def __init__(self):
        self.sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        self.connected = False
        self.buffer = b""
        self.player_id = None

    def connect(self, host, port=DEFAULT_PORT, timeout=5):
        """Connect to server. Returns True on success."""
        self.sock.settimeout(timeout)
        try:
            self.sock.connect((host, port))
            self.sock.setblocking(False)
            self.connected = True
            return True
        except (OSError, socket.timeout):
            return False

    def send(self, message):
        """Send a message to the server."""
        if self.connected:
            if not _send_msg(self.sock, message):
                self.connected = False

    def poll(self):
        """Non-blocking poll. Returns list of messages from server."""
        if not self.connected:
            return []
        try:
            readable, _, _ = select.select([self.sock], [], [], 0)
        except (OSError, ValueError):
            self.connected = False
            return []

        if not readable:
            return []

        msgs, self.buffer, alive = _read_messages(self.sock, self.buffer)
        if not alive:
            self.connected = False
        return msgs

    def close(self):
        self.connected = False
        try:
            self.sock.close()
        except OSError:
            pass
