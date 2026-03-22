from src.settings import (
    TOOL_STONE, TOOL_HOE, TOOL_WATER_BUCKET, TOOL_WATER_BARREL,
    TOOL_AXE, TOOL_HAMMER,
    WATER_BUCKET_CAPACITY, WATER_BARREL_CAPACITY,
)

TOOL_INFO = {
    TOOL_STONE:        {"name_key": "tool_stone",        "water": False, "break_tree_hits": 5, "break_rock_hits": 5, "till": 1},
    TOOL_HOE:          {"name_key": "tool_hoe",          "water": False, "till": 3},
    TOOL_WATER_BARREL: {"name_key": "tool_water_barrel", "water": True,  "capacity": WATER_BARREL_CAPACITY, "water_tiles": 1},
    TOOL_WATER_BUCKET: {"name_key": "tool_water_bucket", "water": True,  "capacity": WATER_BUCKET_CAPACITY, "water_tiles": 3},
    TOOL_AXE:          {"name_key": "tool_axe",          "water": False, "break_tree_hits": 3},
    TOOL_HAMMER:       {"name_key": "tool_hammer",       "water": False, "break_rock_hits": 3},
}


class ToolManager:
    def __init__(self):
        self.tools = [TOOL_STONE, TOOL_WATER_BARREL]
        self.selected = 0
        self.active = True
        self.water = {TOOL_WATER_BARREL: WATER_BARREL_CAPACITY}

    # ── Propietats ───────────────────────────────────────────────

    @property
    def current(self):
        return self.tools[self.selected]

    # ── Navegació ────────────────────────────────────────────────

    def cycle(self, direction=1):
        if self.tools:
            self.selected = (self.selected + direction) % len(self.tools)
            self.active = True

    # ── Gestió d'eines ───────────────────────────────────────────

    def add_tool(self, tool_id):
        if tool_id not in self.tools:
            self.tools.append(tool_id)
            info = TOOL_INFO.get(tool_id)
            if info and info.get("water"):
                self.water.setdefault(tool_id, 0)

    def has_tool(self, tool_id):
        return tool_id in self.tools

    # ── Aigua ────────────────────────────────────────────────────

    def is_water_tool(self, tool_id=None):
        tid = tool_id or self.current
        info = TOOL_INFO.get(tid)
        return info is not None and info.get("water", False)

    def get_water(self, tool_id=None):
        tid = tool_id or self.current
        return self.water.get(tid, 0)

    def get_capacity(self, tool_id=None):
        tid = tool_id or self.current
        info = TOOL_INFO.get(tid)
        return info["capacity"] if info and info.get("water") else 0

    def use_water(self, amount=1, tool_id=None):
        tid = tool_id or self.current
        if self.water.get(tid, 0) >= amount:
            self.water[tid] -= amount
            return True
        return False

    def fill_water(self, tool_id=None):
        tid = tool_id or self.current
        cap = self.get_capacity(tid)
        if cap > 0:
            filled = cap - self.water.get(tid, 0)
            self.water[tid] = cap
            return filled
        return 0

    # ── Serialització ────────────────────────────────────────────

    def to_save_data(self):
        return {
            "tools": list(self.tools),
            "selected": self.selected,
            "water": dict(self.water),
        }

    def from_save_data(self, data):
        if not data:
            return
        self.tools = data.get("tools", [TOOL_STONE])
        self.selected = data.get("selected", 0)
        saved_water = data.get("water", {})

        # Migració: substituir water_barrel antic per la constant correcta
        if TOOL_WATER_BARREL in self.tools and isinstance(self.tools[0], str):
            pass  # ja és string, correcte

        # Migració de saves antics que usaven strings literals
        _migrations = {"water_barrel": TOOL_WATER_BARREL, "stone": TOOL_STONE,
                       "hoe": TOOL_HOE, "axe": TOOL_AXE, "hammer": TOOL_HAMMER,
                       "water_bucket": TOOL_WATER_BUCKET}
        self.tools = [_migrations.get(t, t) for t in self.tools]

        # Migració: si hi havia water_barrel com a string literal en el water dict
        for old, new in _migrations.items():
            if old in saved_water and new not in saved_water:
                saved_water[new] = saved_water.pop(old)

        # Eliminar duplicats mantenint ordre
        seen = []
        for t in self.tools:
            if t not in seen:
                seen.append(t)
        self.tools = seen

        # Reconstruir dict d'aigua
        self.water = {}
        for tid in self.tools:
            info = TOOL_INFO.get(tid)
            if info and info.get("water"):
                self.water[tid] = min(
                    saved_water.get(tid, 0),
                    info["capacity"]
                )

        if self.selected >= len(self.tools):
            self.selected = 0