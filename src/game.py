import pygame
from src.settings import INTERNAL_WIDTH, INTERNAL_HEIGHT, FPS, GAME_TITLE, BLACK
from src.i18n import load_language
from src.systems.profile import load_profile


class Game:
    def __init__(self):
        pygame.init()
        pygame.font.init()

        # Load translations
        load_language("ca")

        # Display setup – borderless windowed fullscreen to avoid disrupting
        # other windows' sizes / positions (unlike exclusive pygame.FULLSCREEN).
        screen_info = pygame.display.Info()
        self.screen_w = screen_info.current_w
        self.screen_h = screen_info.current_h
        self.screen = pygame.display.set_mode(
            (self.screen_w, self.screen_h), pygame.NOFRAME
        )
        pygame.display.set_caption(GAME_TITLE)

        # Game surface at internal resolution
        self.game_surface = pygame.Surface((INTERNAL_WIDTH, INTERNAL_HEIGHT))

        # Compute integer scale and offsets for centering
        self.scale = min(self.screen_w // INTERNAL_WIDTH, self.screen_h // INTERNAL_HEIGHT)
        if self.scale < 1:
            self.scale = 1
        self.scaled_w = INTERNAL_WIDTH * self.scale
        self.scaled_h = INTERNAL_HEIGHT * self.scale
        self.offset_x = (self.screen_w - self.scaled_w) // 2
        self.offset_y = (self.screen_h - self.scaled_h) // 2

        self.clock = pygame.time.Clock()
        self.running = True
        self.current_screen = None
        self.data = {}  # shared game state between screens

        # Load user profile
        self.profile = load_profile()

        # Start with profile screen if no profile, otherwise title screen
        if self.profile is None:
            from src.screens.profile import ProfileScreen
            self.change_screen(ProfileScreen)
        else:
            from src.screens.title import TitleScreen
            self.change_screen(TitleScreen)

    def change_screen(self, screen_class, **kwargs):
        self.current_screen = screen_class(self)
        self.current_screen.on_enter(**kwargs)

    def screen_to_internal(self, screen_x, screen_y):
        """Convert screen (pixel) coordinates to internal game coordinates."""
        return (
            (screen_x - self.offset_x) / self.scale,
            (screen_y - self.offset_y) / self.scale,
        )

    def quit(self):
        self.running = False

    def run(self):
        while self.running:
            dt = self.clock.tick(FPS) / 1000.0
            dt = min(dt, 0.05)  # Cap delta time to prevent physics issues

            # Events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
                elif event.type == pygame.KEYDOWN and event.key == pygame.K_F11:
                    # Toggle fullscreen (emergency exit to windowed)
                    pygame.display.toggle_fullscreen()
                else:
                    if self.current_screen:
                        self.current_screen.handle_event(event)

            # Update
            if self.current_screen:
                self.current_screen.update(dt)

            # Draw
            self.game_surface.fill(BLACK)
            if self.current_screen:
                self.current_screen.draw(self.game_surface)

            # Scale and display
            self.screen.fill(BLACK)
            scaled = pygame.transform.scale(self.game_surface, (self.scaled_w, self.scaled_h))
            self.screen.blit(scaled, (self.offset_x, self.offset_y))
            pygame.display.flip()

        pygame.quit()
