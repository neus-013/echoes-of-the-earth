from src.settings import (
    TOOL_STONE, TOOL_HOE, TOOL_WATER_BUCKET, TOOL_WATER_BARREL,
    TOOL_AXE, TOOL_HAMMER,
    WATER_BUCKET_CAPACITY, WATER_BARREL_CAPACITY,
)

# ── Definició de capacitats per eina ────────────────────────────────
#
#  break_tree_hits  : cops per tallar un arbre (None = no pot)
#  break_rock_hits  : cops per trencar una roca (None = no pot)
#  can_till         : pot llaurar terra?
#  water            : és una eina d'aigua?
#  capacity         : litres d'aigua màxims
#  water_tiles      : tiles que rega amb click llarg
#                     (1 = només el clicat, 3 = clicat + 1 a cada costat)
#
TOOL_INFO = {
    TOOL_STONE: {
        "name_key":        "tool_stone",
        "break_tree_hits": 5,
        "break_rock_hits": 5,
        "can_till":        True,
        "water":           False,
    },
    TOOL_HOE: {
        "name_key":        "tool_hoe",
        "break_tree_hits": None,
        "break_rock_hits": None,
        "can_till":        True,
        "water":           False,
    },
    TOOL_AXE: {
        "name_key":        "tool_axe",
        "break_tree_hits": 3,
        "break_rock_hits": None,
        "can_till":        False,
        "water":           False,
    },
    TOOL_HAMMER: {
        "name_key":        "tool_hammer",
        "break_tree_hits": None,
        "break_rock_hits": 3,
        "can_till":        False,
        "water":           False,
    },
    TOOL_WATER_BARREL: {
        "name_key":        "tool_water_barrel",
        "break_tree_hits": None,
        "break_rock_hits": None,
        "can_till":        False,
        "water":           True,
        "capacity":        WATER_BARREL_CAPACITY,
        "water_tiles":     1,
    },
    TOOL_WATER_BUCKET: {
        "name_key":        "tool_water_bucket",
        "break_tree_hits": None,
        "break_rock_hits": None,
        "can_till":        False,
        "water":           True,
        "capacity":        WATER_BUCKET_CAPACITY,
        "water_tiles":     3,
    },
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

    # ── Consultes de capacitat ───────────────────────────────────

    def can_break_tree(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("break_tree_hits") is not None

    def can_break_rock(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("break_rock_hits") is not None

    def can_till(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("can_till", False)

    def is_water_tool(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("water", False)

    def get_water_tiles(self, tool_id=None):
        """Quants tiles rega aquesta eina amb click llarg."""
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("water_tiles", 1)

    def get_tree_hits(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("break_tree_hits", 5)

    def get_rock_hits(self, tool_id=None):
        tid = tool_id or self.current
        return TOOL_INFO.get(tid, {}).get("break_rock_hits", 5)

    # ── Gestió d'eines ───────────────────────────────────────────

    def add_tool(self, tool_id):
        """Afegeix una eina. Si és la galleda, substitueix la bóta."""
        if tool_id == TOOL_WATER_BUCKET and TOOL_WATER_BARREL in self.tools:
            # Transferim l'aigua proporcionalment i substituïm al mateix índex
            barrel_water = self.water.pop(TOOL_WATER_BARREL, 0)
            idx = self.tools.index(TOOL_WATER_BARREL)
            self.tools[idx] = TOOL_WATER_BUCKET
            ratio = barrel_water / max(WATER_BARREL_CAPACITY, 1)
            self.water[TOOL_WATER_BUCKET] = int(ratio * WATER_BUCKET_CAPACITY)
        elif tool_id not in self.tools:
            self.tools.append(tool_id)
            info = TOOL_INFO.get(tool_id)
            if info and info.get("water"):
                self.water.setdefault(tool_id, 0)

    def has_tool(self, tool_id):
        return tool_id in self.tools

    def remove_tool(self, tool_id):
        if tool_id in self.tools:
            idx = self.tools.index(tool_id)
            self.tools.pop(idx)
            self.water.pop(tool_id, None)
            if self.selected >= len(self.tools):
                self.selected = max(0, len(self.tools) - 1)

    # ── Aigua ────────────────────────────────────────────────────

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
            "tools":    list(self.tools),
            "selected": self.selected,
            "water":    dict(self.water),
        }

    def from_save_data(self, data):
        if not data:
            return

        self.tools = data.get("tools", [TOOL_STONE])
        self.selected = data.get("selected", 0)
        saved_water = dict(data.get("water", {}))

        # Migració de saves antics amb strings literals
        _migrations = {
            "stone":        TOOL_STONE,
            "hoe":          TOOL_HOE,
            "axe":          TOOL_AXE,
            "hammer":       TOOL_HAMMER,
            "water_barrel": TOOL_WATER_BARREL,
            "water_bucket": TOOL_WATER_BUCKET,
        }
        self.tools = [_migrations.get(tid, tid) for tid in self.tools]
        for old, new in _migrations.items():
            if old in saved_water and new not in saved_water:
                saved_water[new] = saved_water.pop(old)

        # Eliminar duplicats mantenint ordre
        seen = []
        for tid in self.tools:
            if tid not in seen:
                seen.append(tid)
        self.tools = seen

        # Reconstruir dict d'aigua
        self.water = {}
        for tid in self.tools:
            info = TOOL_INFO.get(tid)
            if info and info.get("water"):
                self.water[tid] = min(
                    saved_water.get(tid, 0),
                    info["capacity"],
                )

        if self.selected >= len(self.tools):
            self.selected = 0