from src.settings import (
    CROPS, SEED_TO_CROP, QUALITY_NORMAL, QUALITY_GOOD, HARVESTS_FOR_QUALITY,
    PG_HARVEST,
)


class FarmingSystem:
    """Manages planted crops and growth logic."""

    def __init__(self):
        # {(tx, ty): {"crop": crop_id, "day": int, "watered": bool}}
        self.plots = {}
        # Tracks how many times each crop type has been harvested (for quality)
        self.harvest_counts = {}

    def plant(self, tx, ty, seed_item):
        crop_id = SEED_TO_CROP.get(seed_item)
        if not crop_id:
            return False
        if (tx, ty) in self.plots:
            return False
        self.plots[(tx, ty)] = {"crop": crop_id, "day": 0, "watered": False}
        return True

    def water(self, tx, ty):
        plot = self.plots.get((tx, ty))
        if plot and not plot["watered"]:
            plot["watered"] = True
            return True
        return False

    def is_watered(self, tx, ty):
        plot = self.plots.get((tx, ty))
        return plot is not None and plot["watered"]

    def get_crop(self, tx, ty):
        return self.plots.get((tx, ty))

    def get_stage(self, tx, ty):
        """Return growth stage 0-3 (seed, sprout, growing, mature)."""
        plot = self.plots.get((tx, ty))
        if not plot:
            return -1
        crop_info = CROPS.get(plot["crop"])
        if not crop_info:
            return -1
        total_days = crop_info["grow_days"]
        day = plot["day"]
        if day >= total_days:
            return 3  # mature
        # Regrowable crop just harvested: show big plant without fruit
        if plot.get("regrowing"):
            return 2
        ratio = day / total_days
        if ratio < 0.33:
            return 0  # seed
        elif ratio < 0.66:
            return 1  # sprout
        else:
            return 2  # growing

    def is_mature(self, tx, ty):
        return self.get_stage(tx, ty) == 3

    def harvest(self, tx, ty):
        """Harvest a mature crop. Returns (item_id, qty, quality, pg) or None."""
        plot = self.plots.get((tx, ty))
        if not plot:
            return None
        crop_id = plot["crop"]
        crop_info = CROPS.get(crop_id)
        if not crop_info:
            return None
        if not self.is_mature(tx, ty):
            return None

        # Determine quality
        count = self.harvest_counts.get(crop_id, 0)
        quality = QUALITY_GOOD if count >= HARVESTS_FOR_QUALITY else QUALITY_NORMAL

        # Update harvest count
        self.harvest_counts[crop_id] = count + 1

        item_id = crop_info["harvest_item"]
        qty = crop_info["yield_qty"]
        pg = PG_HARVEST.get(crop_id, 0)

        if crop_info["regrows"]:
            # Reset to day 0, needs re-watering, show as big plant without fruit
            plot["day"] = 0
            plot["watered"] = False
            plot["regrowing"] = True
        else:
            # Remove crop entirely
            del self.plots[(tx, ty)]

        return (item_id, qty, quality, pg)

    def advance_day(self):
        """Called at the start of a new day. Watered crops grow, unwatered don't."""
        for pos, plot in list(self.plots.items()):
            if plot["watered"]:
                plot["day"] += 1
                # Clear regrowing flag once the crop starts growing again
                plot.pop("regrowing", None)
            # Reset watered status for next day
            plot["watered"] = False

    def to_save_data(self):
        plots_data = {}
        for (tx, ty), plot in self.plots.items():
            plots_data[f"{tx},{ty}"] = plot.copy()
        return {
            "plots": plots_data,
            "harvest_counts": dict(self.harvest_counts),
        }

    def from_save_data(self, data):
        if not data:
            return
        self.plots.clear()
        for key, plot in data.get("plots", {}).items():
            tx, ty = [int(v) for v in key.split(",")]
            self.plots[(tx, ty)] = plot.copy()
        self.harvest_counts = dict(data.get("harvest_counts", {}))
