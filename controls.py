"""
Android touch control system for Shepu's Snake Game.

Three control modes:
  - swipe  : Swipe gestures anywhere on the play area
  - corner : Virtual joystick in bottom-left or bottom-right corner
  - split  : 80/20 split screen with dedicated joystick panel
"""

import math
import random
import pygame
import config
from utils import resource_path


CONTROL_SWIPE = "swipe"
CONTROL_CORNER = "corner"
CONTROL_SPLIT = "split"

CONTROL_LABELS = {
    CONTROL_SWIPE: "SWIPE",
    CONTROL_CORNER: "CORNER JOYSTICK",
    CONTROL_SPLIT: "SPLIT SCREEN",
}

CONTROL_ORDER = [CONTROL_SWIPE, CONTROL_CORNER, CONTROL_SPLIT]

SPLIT_GAME_RATIO = 0.80
CORNER_RADIUS = 72
CORNER_KNOB_RADIUS = 28
CORNER_DEADZONE = 14
SWIPE_MIN_DISTANCE = 36


class PlayArea:
    """Defines where the snake game is rendered and where entities may spawn."""

    def __init__(self, screen_w, screen_h, control_mode=CONTROL_SWIPE, corner_side="right"):
        self.screen_w = screen_w
        self.screen_h = screen_h
        self.control_mode = control_mode
        self.corner_side = corner_side
        self._recompute()

    def _recompute(self):
        if self.control_mode == CONTROL_SPLIT:
            self.play_w = int(self.screen_w * SPLIT_GAME_RATIO)
            self.play_h = self.screen_h
            self.offset_x = 0
            self.offset_y = 0
            self.panel_x = self.play_w
            self.panel_w = self.screen_w - self.play_w
            self.panel_h = self.screen_h
        else:
            self.play_w = self.screen_w
            self.play_h = self.screen_h
            self.offset_x = 0
            self.offset_y = 0
            self.panel_x = 0
            self.panel_w = 0
            self.panel_h = 0

        self.joystick_center = self._joystick_center()
        self.joystick_radius = CORNER_RADIUS if self.control_mode == CONTROL_CORNER else min(90, self.panel_w // 2 - 12, self.panel_h // 2 - 24)

    def _joystick_center(self):
        margin = CORNER_RADIUS + 24
        if self.control_mode == CONTROL_SPLIT:
            return (self.panel_x + self.panel_w // 2, self.screen_h // 2)
        y = self.screen_h - margin
        if self.corner_side == "left":
            return (margin, y)
        return (self.screen_w - margin, y)

    def update(self, screen_w, screen_h, control_mode=None, corner_side=None):
        self.screen_w = screen_w
        self.screen_h = screen_h
        if control_mode is not None:
            self.control_mode = control_mode
        if corner_side is not None:
            self.corner_side = corner_side
        self._recompute()

    def game_rect(self):
        return pygame.Rect(self.offset_x, self.offset_y, self.play_w, self.play_h)

    def exclusion_rects(self):
        """Rects where food/power-ups must not spawn."""
        rects = []
        if self.control_mode == CONTROL_CORNER:
            cx, cy = self.joystick_center
            pad = CORNER_RADIUS + config.STEP * 2
            rects.append(pygame.Rect(cx - pad, cy - pad, pad * 2, pad * 2))
        elif self.control_mode == CONTROL_SPLIT:
            rects.append(pygame.Rect(self.panel_x, 0, self.panel_w, self.panel_h))
        return rects

    def is_in_play_area(self, x, y):
        return self.game_rect().collidepoint(x, y)

    def is_in_control_zone(self, x, y):
        if self.control_mode == CONTROL_CORNER:
            cx, cy = self.joystick_center
            return math.hypot(x - cx, y - cy) <= CORNER_RADIUS + 20
        if self.control_mode == CONTROL_SPLIT:
            return x >= self.panel_x
        return False

    def apply_to_config(self):
        config.PLAY_WIDTH = self.play_w
        config.PLAY_HEIGHT = self.play_h
        config.PLAY_OFFSET_X = self.offset_x
        config.PLAY_OFFSET_Y = self.offset_y


def get_spawn_exclusion_rects():
    """Extra blocked rects for entity spawning (level HUD + joystick zones)."""
    rects = [pygame.Rect(0, 0, 220, 120)]
    if hasattr(config, "_PLAY_AREA") and config._PLAY_AREA:
        rects.extend(config._PLAY_AREA.exclusion_rects())
    return rects


def is_spawn_blocked(pos, snake_body, extra_blocked=None):
    s = config.STEP
    cell = pygame.Rect(pos[0], pos[1], s, s)
    if pos in snake_body:
        return True
    if extra_blocked:
        for item in extra_blocked:
            if isinstance(item, list) and item == pos:
                return True
            if hasattr(item, "pos") and item.pos == pos:
                return True
    play_w = getattr(config, "PLAY_WIDTH", config.WIDTH)
    play_h = getattr(config, "PLAY_HEIGHT", config.HEIGHT)
    ox = getattr(config, "PLAY_OFFSET_X", 0)
    oy = getattr(config, "PLAY_OFFSET_Y", 0)
    if not pygame.Rect(ox, oy, play_w, play_h).contains(cell):
        return True
    for rect in get_spawn_exclusion_rects():
        if rect.colliderect(cell):
            return True
    return False


def find_spawn_position(snake_body, extra_blocked=None, max_tries=500):
    w = getattr(config, "PLAY_WIDTH", config.WIDTH)
    h = getattr(config, "PLAY_HEIGHT", config.HEIGHT)
    ox = getattr(config, "PLAY_OFFSET_X", 0)
    oy = getattr(config, "PLAY_OFFSET_Y", 0)
    s = config.STEP
    for _ in range(max_tries):
        pos = [
            ox + random_grid(w, s),
            oy + random_grid(h, s),
        ]
        if not is_spawn_blocked(pos, snake_body, extra_blocked):
            return pos
    return [ox + w // 2, oy + h // 2]


def random_grid(length, step):
    cells = max(1, length // step)
    return random.randrange(0, cells) * step


class ControlManager:
    def __init__(self, game_data):
        self.mode = game_data.get("control_mode", CONTROL_SWIPE)
        self.corner_side = game_data.get("joystick_side", "right")
        self.play_area = PlayArea(config.WIDTH, config.HEIGHT, self.mode, self.corner_side)
        self.play_area.apply_to_config()
        config._PLAY_AREA = self.play_area

        self._swipe_start = None
        self._swipe_active = False
        self._joystick_touch_id = None
        self._knob_offset = (0, 0)
        self._pending_direction = None
        self._swipe_image = None
        self._load_swipe_image()

    def _load_swipe_image(self):
        try:
            img = pygame.image.load(resource_path("assets/images/swipe.png")).convert_alpha()
            max_w = int(config.WIDTH * 0.55)
            ratio = max_w / img.get_width()
            size = (max_w, int(img.get_height() * ratio))
            self._swipe_image = pygame.transform.smoothscale(img, size)
        except Exception:
            self._swipe_image = None

    def set_mode(self, mode, corner_side=None):
        self.mode = mode
        if corner_side:
            self.corner_side = corner_side
        self.play_area.update(config.WIDTH, config.HEIGHT, self.mode, self.corner_side)
        self.play_area.apply_to_config()
        self.reset_touch_state()

    def cycle_mode(self):
        idx = CONTROL_ORDER.index(self.mode) if self.mode in CONTROL_ORDER else 0
        self.set_mode(CONTROL_ORDER[(idx + 1) % len(CONTROL_ORDER)])

    def reset_touch_state(self):
        self._swipe_start = None
        self._swipe_active = False
        self._joystick_touch_id = None
        self._knob_offset = (0, 0)
        self._pending_direction = None

    def resize(self, width, height):
        self.play_area.update(width, height)
        self.play_area.apply_to_config()
        self._load_swipe_image()

    def consume_direction(self):
        direction = self._pending_direction
        self._pending_direction = None
        return direction

    def _queue_direction(self, direction):
        self._pending_direction = direction

    def _direction_from_delta(self, dx, dy):
        if abs(dx) < 1 and abs(dy) < 1:
            return None
        if abs(dx) > abs(dy):
            return "RIGHT" if dx > 0 else "LEFT"
        return "DOWN" if dy > 0 else "UP"

    def _joystick_direction(self, dx, dy):
        dist = math.hypot(dx, dy)
        if dist < CORNER_DEADZONE:
            return None
        return self._direction_from_delta(dx, dy)

    def _event_position(self, event):
        if hasattr(event, "pos"):
            return event.pos
        if hasattr(event, "x") and hasattr(event, "y"):
            return (
                int(event.x * config.WIDTH),
                int(event.y * config.HEIGHT),
            )
        return None

    def _event_touch_id(self, event):
        if hasattr(event, "finger_id"):
            return event.finger_id
        if hasattr(event, "touch_id"):
            return event.touch_id
        return 0

    def handle_event(self, event, game_state):
        if game_state not in ("PLAYING", "SWIPE_TUTORIAL"):
            return False

        if self.mode == CONTROL_SWIPE and game_state == "SWIPE_TUTORIAL":
            return False

        pos = self._event_position(event)
        if pos is None:
            return False

        if event.type in (pygame.FINGERDOWN, pygame.MOUSEBUTTONDOWN):
            if event.type == pygame.MOUSEBUTTONDOWN and getattr(event, "button", 1) != 1:
                return False
            if self.mode == CONTROL_SWIPE:
                if self.play_area.is_in_play_area(*pos):
                    self._swipe_start = pos
                    self._swipe_active = True
                    return True
            elif self.mode in (CONTROL_CORNER, CONTROL_SPLIT):
                if self.play_area.is_in_control_zone(*pos) or (
                    self.mode == CONTROL_CORNER and self.play_area.is_in_control_zone(*pos)
                ):
                    self._joystick_touch_id = self._event_touch_id(event)
                    self._update_knob(pos)
                    return True
                if self.mode == CONTROL_SPLIT and pos[0] >= self.play_area.panel_x:
                    self._joystick_touch_id = self._event_touch_id(event)
                    self._update_knob(pos)
                    return True
                if self.mode == CONTROL_CORNER and self._near_joystick(*pos):
                    self._joystick_touch_id = self._event_touch_id(event)
                    self._update_knob(pos)
                    return True

        elif event.type in (pygame.FINGERMOTION, pygame.MOUSEMOTION):
            if self.mode == CONTROL_SWIPE and self._swipe_active and self._swipe_start:
                dx = pos[0] - self._swipe_start[0]
                dy = pos[1] - self._swipe_start[1]
                if math.hypot(dx, dy) >= SWIPE_MIN_DISTANCE:
                    direction = self._direction_from_delta(dx, dy)
                    if direction:
                        self._queue_direction(direction)
                        self._swipe_start = pos
                return True
            if self._joystick_touch_id is not None:
                if event.type == pygame.MOUSEMOTION or self._event_touch_id(event) == self._joystick_touch_id:
                    self._update_knob(pos)
                    return True

        elif event.type in (pygame.FINGERUP, pygame.MOUSEBUTTONUP):
            if self.mode == CONTROL_SWIPE and self._swipe_active and self._swipe_start:
                dx = pos[0] - self._swipe_start[0]
                dy = pos[1] - self._swipe_start[1]
                if math.hypot(dx, dy) >= SWIPE_MIN_DISTANCE:
                    direction = self._direction_from_delta(dx, dy)
                    if direction:
                        self._queue_direction(direction)
                self._swipe_start = None
                self._swipe_active = False
                return True
            if self._joystick_touch_id is not None:
                if event.type == pygame.MOUSEBUTTONUP or self._event_touch_id(event) == self._joystick_touch_id:
                    self._knob_offset = (0, 0)
                    self._joystick_touch_id = None
                    return True

        return False

    def _near_joystick(self, x, y):
        cx, cy = self.play_area.joystick_center
        return math.hypot(x - cx, y - cy) <= self.play_area.joystick_radius + 36

    def _update_knob(self, pos):
        cx, cy = self.play_area.joystick_center
        dx = pos[0] - cx
        dy = pos[1] - cy
        dist = math.hypot(dx, dy)
        max_dist = self.play_area.joystick_radius
        if dist > max_dist:
            scale = max_dist / dist
            dx *= scale
            dy *= scale
        self._knob_offset = (dx, dy)
        direction = self._joystick_direction(dx, dy)
        if direction:
            self._queue_direction(direction)

    def draw(self, screen, game_state, swipe_tutorial_alpha=255):
        if game_state == "SWIPE_TUTORIAL" and self.mode == CONTROL_SWIPE:
            self._draw_swipe_tutorial(screen, swipe_tutorial_alpha)
            return

        if game_state != "PLAYING":
            return

        if self.mode == CONTROL_CORNER:
            self._draw_corner_joystick(screen)
        elif self.mode == CONTROL_SPLIT:
            self._draw_split_panel(screen)
            self._draw_corner_joystick(screen, in_panel=True)

    def _draw_swipe_tutorial(self, screen, alpha):
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 160))
        screen.blit(overlay, (0, 0))

        if self._swipe_image:
            img = self._swipe_image.copy()
            img.set_alpha(alpha)
            rect = img.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 30))
            screen.blit(img, rect)
        else:
            font = pygame.font.SysFont("arial", 28, bold=True)
            txt = font.render("SWIPE TO MOVE", True, (255, 255, 255))
            screen.blit(txt, txt.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 - 40)))

        font_small = pygame.font.SysFont("arial", 20)
        hint = font_small.render("সোয়াইপ করে সাপ নিয়ন্ত্রণ করুন", True, (200, 220, 255))
        screen.blit(hint, hint.get_rect(center=(config.WIDTH // 2, config.HEIGHT // 2 + 80)))

    def _draw_split_panel(self, screen):
        panel = pygame.Rect(self.play_area.panel_x, 0, self.play_area.panel_w, self.play_area.panel_h)
        pygame.draw.rect(screen, (12, 14, 28), panel)
        pygame.draw.line(screen, (0, 180, 220), (panel.left, 0), (panel.left, panel.height), 2)
        font = pygame.font.SysFont("arial", 16, bold=True)
        label = font.render("JOYSTICK", True, (120, 200, 255))
        screen.blit(label, label.get_rect(center=(panel.centerx, 28)))

    def _draw_corner_joystick(self, screen, in_panel=False):
        cx, cy = self.play_area.joystick_center
        r = self.play_area.joystick_radius
        base_color = (30, 40, 70, 170)
        border_color = (0, 200, 255)

        base = pygame.Surface((r * 2 + 8, r * 2 + 8), pygame.SRCALPHA)
        pygame.draw.circle(base, base_color, (r + 4, r + 4), r)
        pygame.draw.circle(base, border_color, (r + 4, r + 4), r, 2)
        screen.blit(base, (cx - r - 4, cy - r - 4))

        kx = cx + self._knob_offset[0]
        ky = cy + self._knob_offset[1]
        knob = pygame.Surface((CORNER_KNOB_RADIUS * 2, CORNER_KNOB_RADIUS * 2), pygame.SRCALPHA)
        pygame.draw.circle(knob, (0, 255, 200, 210), (CORNER_KNOB_RADIUS, CORNER_KNOB_RADIUS), CORNER_KNOB_RADIUS)
        screen.blit(knob, (kx - CORNER_KNOB_RADIUS, ky - CORNER_KNOB_RADIUS))
