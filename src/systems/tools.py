from src.settings import (
    TOOL_STONE, TOOL_HOE, TOOL_WATER_BUCKET,
    WATER_BUCKET_CAPACITY,
)


TOOL_INFO = {
    TOOL_STONE: {"name_key": "tool_stone", "water": False},
    TOOL_HOE: {"name_key": "tool_hoe", "water": False},
    TOOL_WATER_BUCKET: {"name_key": "tool_water_bucket", "water": True, "capacity": WATER_BUCKET_CAPACITY},
}


class ToolManager:
    def __init__(self):
        self.tools = [TOOL_STONE, TOOL_WATER_BUCKET]
        self.selected = 0
        self.active = True   # True = tool in use; False = inventory selection active
        self.water = {TOOL_WATER_BUCKET: WATER_BUCKET_CAPACITY}

    @property
    def current(self):
        return self.tools[self.selected]

    def cycle(self, direction=1):
        if not self.tools:
            return
        self.selected = (self.selected + direction) % len(self.tools)
        self.active = True

    def add_tool(self, tool_id):
        if tool_id not in self.tools:
            self.tools.append(tool_id)
            # Initialise water for water-capable tools
            info = TOOL_INFO.get(tool_id)
            if info and info.get("water"):
                self.water.setdefault(tool_id, 0)

    def has_tool(self, tool_id):
        return tool_id in self.tools

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
        if info and info.get("water"):
            return info["capacity"]
        return 0

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
            old = self.water.get(tid, 0)
            self.water[tid] = cap
            return cap - old
        return 0

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

        # Migration: replace old water_barrel with water_bucket
        if "water_barrel" in self.tools:
            idx = self.tools.index("water_barrel")
            if TOOL_WATER_BUCKET not in self.tools:
                self.tools[idx] = TOOL_WATER_BUCKET
                old_w = saved_water.get("water_barrel", 0)
                saved_water[TOOL_WATER_BUCKET] = min(old_w, WATER_BUCKET_CAPACITY)
            else:
                self.tools.pop(idx)
            saved_water.pop("water_barrel", None)

        # Rebuild water dict
        self.water = {}
        for tid in self.tools:
            info = TOOL_INFO.get(tid)
            if info and info.get("water"):
                self.water[tid] = saved_water.get(tid, 0)
        if self.selected >= len(self.tools):
            self.selected = 0
