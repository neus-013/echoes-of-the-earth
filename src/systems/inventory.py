from src.settings import INVENTORY_SLOTS, TOOLBAR_VISIBLE


class Inventory:
    def __init__(self):
        self.slots = [None] * INVENTORY_SLOTS  # Each: {"item": id, "qty": n, "quality": 0} or None
        self.selected_slot = -1  # -1 = no selection (absolute index 0..9)
        self.toolbar_page = 0   # 0 = slots 0-4, 1 = slots 5-9

    def toggle_page(self):
        self.toolbar_page = 1 - self.toolbar_page

    def get_visible_range(self):
        """Return (start, end) indices for the currently visible toolbar page."""
        start = self.toolbar_page * TOOLBAR_VISIBLE
        return start, start + TOOLBAR_VISIBLE

    def get_selected_item(self):
        """Return the item dict in the selected slot, or None."""
        if 0 <= self.selected_slot < len(self.slots):
            return self.slots[self.selected_slot]
        return None

    def add_item(self, item_id, qty=1, quality=0):
        # Try to stack with existing slot (same item AND quality)
        for slot in self.slots:
            if slot and slot["item"] == item_id and slot.get("quality", 0) == quality:
                slot["qty"] += qty
                return True
        # Find first empty slot
        for i, slot in enumerate(self.slots):
            if slot is None:
                self.slots[i] = {"item": item_id, "qty": qty, "quality": quality}
                return True
        return False  # Inventory full

    def remove_item(self, item_id, qty=1):
        for i, slot in enumerate(self.slots):
            if slot and slot["item"] == item_id:
                slot["qty"] -= qty
                if slot["qty"] <= 0:
                    self.slots[i] = None
                return True
        return False

    def count_item(self, item_id):
        total = 0
        for slot in self.slots:
            if slot and slot["item"] == item_id:
                total += slot["qty"]
        return total

    def is_full(self):
        return all(slot is not None for slot in self.slots)

    def can_add(self, item_id, quality=0):
        for slot in self.slots:
            if slot and slot["item"] == item_id and slot.get("quality", 0) == quality:
                return True
        return not self.is_full()

    def get_seeds(self):
        """Return list of seed item IDs the player has."""
        from src.settings import ALL_SEED_ITEMS
        seeds = []
        for slot in self.slots:
            if slot and slot["item"] in ALL_SEED_ITEMS and slot["item"] not in seeds:
                seeds.append(slot["item"])
        return seeds

    def to_list(self):
        return [s.copy() if s else None for s in self.slots]

    def from_list(self, data):
        self.slots = [None] * INVENTORY_SLOTS
        if data:
            for i, s in enumerate(data):
                if i < INVENTORY_SLOTS and s:
                    self.slots[i] = s.copy()
