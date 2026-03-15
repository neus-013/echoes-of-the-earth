from src.settings import (
    DAY_START_HOUR, DAY_END_HOUR, HOURS_PER_DAY, DAY_DURATION_SECONDS,
)


class TimeSystem:
    def __init__(self):
        self.current_time = DAY_START_HOUR  # in-game hours (6.0 = 06:00)
        self.day_over = False
        self.hours_per_second = HOURS_PER_DAY / DAY_DURATION_SECONDS

    def reset_day(self):
        self.current_time = DAY_START_HOUR
        self.day_over = False

    def update(self, dt):
        if self.day_over:
            return
        self.current_time += self.hours_per_second * dt
        if self.current_time >= DAY_END_HOUR:
            self.current_time = DAY_END_HOUR
            self.day_over = True

    def get_display_time(self):
        hour = int(self.current_time) % 24
        minute = int((self.current_time % 1) * 60)
        return f"{hour:02d}:{minute:02d}"

    def get_period(self):
        t = self.current_time
        if t < 8:
            return "dawn"
        elif t < 12:
            return "morning"
        elif t < 14:
            return "midday"
        elif t < 19:
            return "afternoon"
        elif t < 21:
            return "evening"
        else:
            return "night"

    def get_overlay_color(self):
        """Returns (r, g, b, a) for the time-of-day overlay, or None."""
        t = self.current_time
        if 6 <= t < 8:  # Dawn
            progress = (t - 6) / 2
            alpha = int(70 * (1 - progress))
            return (80, 80, 160, alpha)
        elif 8 <= t < 12:  # Morning - clear
            return None
        elif 12 <= t < 14:  # Midday - warm
            return (255, 230, 180, 12)
        elif 14 <= t < 19:  # Afternoon - golden
            progress = (t - 14) / 5
            alpha = int(15 + 25 * progress)
            return (255, 200, 100, alpha)
        elif 19 <= t < 21:  # Evening - orange
            progress = (t - 19) / 2
            alpha = int(40 + 70 * progress)
            return (200, 100, 50, alpha)
        else:  # Night
            return (15, 15, 50, 140)
