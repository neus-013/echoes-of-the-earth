import pygame
from src.settings import (
    TILE_SIZE, PLAYER_SPEED, PLAYER_MAX_ENERGY,
    PLAYER_HITBOX_W, PLAYER_HITBOX_H,
    PLAYER_SPRITE_W, PLAYER_SPRITE_H,
    PLAYER_WALK_FRAMES, PLAYER_IDLE_FRAME,
    FACING_DOWN, FACING_UP, FACING_LEFT, FACING_RIGHT,
    FACING_OFFSETS,
    MAP_WIDTH, MAP_HEIGHT,
)
from src.sprites import create_player_sprites


class Player:
    def __init__(self, cx, cy, avatar, name=""):
        self.cx = float(cx)
        self.cy = float(cy)
        self.facing = FACING_DOWN
        self.energy = PLAYER_MAX_ENERGY
        self.avatar = avatar
        self.name = name

        # Animation
        self.anim_frame = PLAYER_IDLE_FRAME
        self.anim_timer = 0.0
        self.anim_speed = 0.15
        self.moving = False

        # Sprites
        self.sprites = create_player_sprites(
            avatar.get("skin", 0),
            avatar.get("hair_color", 0),
            avatar.get("outfit", 0),
            avatar.get("eyes", 0),
        )

        # Hit flash
        self.flash_timer = 0.0

    @property
    def hitbox(self):
        return pygame.Rect(
            self.cx - PLAYER_HITBOX_W / 2,
            self.cy - PLAYER_HITBOX_H / 2,
            PLAYER_HITBOX_W,
            PLAYER_HITBOX_H,
        )

    @property
    def tile_x(self):
        return int(self.cx // TILE_SIZE)

    @property
    def tile_y(self):
        return int(self.cy // TILE_SIZE)

    def get_facing_tile(self):
        ox, oy = FACING_OFFSETS[self.facing]
        return self.tile_x + ox, self.tile_y + oy

    def handle_input(self, keys, dt, world):
        dx, dy = 0, 0
        if keys[pygame.K_w] or keys[pygame.K_UP]:
            dy -= 1
            self.facing = FACING_UP
        if keys[pygame.K_s] or keys[pygame.K_DOWN]:
            dy += 1
            self.facing = FACING_DOWN
        if keys[pygame.K_a] or keys[pygame.K_LEFT]:
            dx -= 1
            self.facing = FACING_LEFT
        if keys[pygame.K_d] or keys[pygame.K_RIGHT]:
            dx += 1
            self.facing = FACING_RIGHT

        self.moving = dx != 0 or dy != 0

        if self.moving:
            if dx != 0 and dy != 0:
                factor = 0.7071
                dx *= factor
                dy *= factor

            speed = PLAYER_SPEED
            if self.energy <= 0:
                speed *= 0.5

            move_x = dx * speed * dt
            move_y = dy * speed * dt

            new_cx = self.cx + move_x
            if not self._collides(new_cx, self.cy, world):
                self.cx = new_cx

            new_cy = self.cy + move_y
            if not self._collides(self.cx, new_cy, world):
                self.cy = new_cy

    def _collides(self, cx, cy, world):
        hx = cx - PLAYER_HITBOX_W / 2
        hy = cy - PLAYER_HITBOX_H / 2
        corners = [
            (hx, hy),
            (hx + PLAYER_HITBOX_W - 1, hy),
            (hx, hy + PLAYER_HITBOX_H - 1),
            (hx + PLAYER_HITBOX_W - 1, hy + PLAYER_HITBOX_H - 1),
        ]
        for px, py in corners:
            tx = int(px // TILE_SIZE)
            ty = int(py // TILE_SIZE)
            if world.is_blocking(tx, ty):
                return True
        return False

    def eat_food(self, inventory, item_id, restore_amount):
        """Eat a food item from inventory and restore energy."""
        if inventory.count_item(item_id) > 0:
            inventory.remove_item(item_id, 1)
            self.energy = min(PLAYER_MAX_ENERGY, self.energy + restore_amount)
            return True
        return False

    def update(self, dt):
        if self.moving:
            self.anim_timer += dt
            if self.anim_timer >= self.anim_speed:
                self.anim_timer = 0
                self.anim_frame = (self.anim_frame + 1) % PLAYER_WALK_FRAMES
        else:
            self.anim_frame = PLAYER_IDLE_FRAME
            self.anim_timer = 0

        if self.flash_timer > 0:
            self.flash_timer -= dt

    def draw(self, surface, camera):
        sprite = self.sprites[self.facing][self.anim_frame]
        sx, sy = camera.world_to_screen(self.cx, self.cy)
        draw_x = sx - PLAYER_SPRITE_W / 2
        draw_y = sy - PLAYER_SPRITE_H + PLAYER_HITBOX_H / 2
        surface.blit(sprite, (draw_x, draw_y))

    def to_save_data(self):
        return {
            "cx": self.cx,
            "cy": self.cy,
            "facing": self.facing,
            "energy": self.energy,
            "avatar": self.avatar.copy(),
            "name": self.name,
        }

    def apply_remote_state(self, cx, cy, facing, moving, energy=None):
        """Update this player from remote/server data."""
        old_cx, old_cy = self.cx, self.cy
        self.cx = float(cx)
        self.cy = float(cy)
        self.facing = facing
        self.moving = moving
        if energy is not None:
            self.energy = energy

    def from_save_data(self, data):
        self.cx = data["cx"]
        self.cy = data["cy"]
        self.facing = data.get("facing", FACING_DOWN)
        self.energy = data.get("energy", PLAYER_MAX_ENERGY)
