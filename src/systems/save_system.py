import json
import os
from datetime import datetime


def _saves_dir(user_id=None):
    base = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    if user_id:
        d = os.path.join(base, "data", "saves", user_id)
    else:
        d = os.path.join(base, "data", "saves")
    os.makedirs(d, exist_ok=True)
    return d


def _save_path(save_name, user_id=None):
    safe_name = "".join(c if c.isalnum() or c in " _-" else "_" for c in save_name)
    safe_name = safe_name.strip().replace(" ", "_")
    if not safe_name:
        safe_name = "partida"
    return os.path.join(_saves_dir(user_id), f"{safe_name}.json")


_EXCLUDE_KEYS = {"server", "client", "roster_names", "lobby_players"}


def save_game(data, user_id=None):
    # Filter out non-serializable runtime keys
    clean = {k: v for k, v in data.items() if k not in _EXCLUDE_KEYS}
    # Also clean per-player data
    if "players" in clean and isinstance(clean["players"], list):
        cleaned_players = []
        for p in clean["players"]:
            cleaned_players.append({k: v for k, v in p.items() if k != "net_pid"})
        clean["players"] = cleaned_players
    clean["timestamp"] = datetime.now().isoformat()
    path = _save_path(clean["name"], user_id)
    with open(path, "w", encoding="utf-8") as f:
        json.dump(clean, f, ensure_ascii=False, indent=2)


def load_game(save_name, user_id=None):
    path = _save_path(save_name, user_id)
    if not os.path.exists(path):
        return None
    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)


def list_saves(user_id=None):
    saves = []
    d = _saves_dir(user_id)
    for fname in os.listdir(d):
        if fname.endswith(".json"):
            path = os.path.join(d, fname)
            with open(path, "r", encoding="utf-8") as f:
                data = json.load(f)
            saves.append({
                "name": data.get("name", fname),
                "day": data.get("day", 1),
                "season": data.get("season", 0),
                "year": data.get("year", 1),
                "timestamp": data.get("timestamp", ""),
                "filename": fname,
                "mode": data.get("mode", "solo"),
                "num_players": data.get("num_players", 1),
            })
    saves.sort(key=lambda s: s["timestamp"], reverse=True)
    return saves


def delete_save(save_name, user_id=None):
    path = _save_path(save_name, user_id)
    if os.path.exists(path):
        os.remove(path)
