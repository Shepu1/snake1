import pygame
import random
import math
import config
from controls import find_spawn_position


def _play_bounds():
    w = getattr(config, "PLAY_WIDTH", config.WIDTH)
    h = getattr(config, "PLAY_HEIGHT", config.HEIGHT)
    ox = getattr(config, "PLAY_OFFSET_X", 0)
    oy = getattr(config, "PLAY_OFFSET_Y", 0)
    return w, h, ox, oy

class Snake:
    def __init__(self):
        self.input_queue = []
        self.reset()

    def reset(self):
        w, h, ox, oy = _play_bounds()
        s = config.STEP
        cx = ox + w // 2
        cy = oy + h // 2
        self.pos = [cx, cy]
        self.body = [
            [cx, cy],
            [cx - s, cy],
            [cx - (2 * s), cy],
        ]
        self.prev_body = [list(p) for p in self.body]
        self.direction = 'RIGHT'
        self.input_queue = []

    def handle_input(self, key):
        last = self.input_queue[-1] if self.input_queue else self.direction
        OPPOSITES = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        KEY_MAP = {
            pygame.K_UP:    'UP',
            pygame.K_DOWN:  'DOWN',
            pygame.K_LEFT:  'LEFT',
            pygame.K_RIGHT: 'RIGHT',
            pygame.K_w:     'UP',
            pygame.K_s:     'DOWN',
            pygame.K_a:     'LEFT',
            pygame.K_d:     'RIGHT',
        }
        new_dir = KEY_MAP.get(key)
        self.queue_direction(new_dir, OPPOSITES, last)

    def queue_direction(self, new_dir, opposites=None, last=None):
        if not new_dir:
            return
        if opposites is None:
            opposites = {'UP': 'DOWN', 'DOWN': 'UP', 'LEFT': 'RIGHT', 'RIGHT': 'LEFT'}
        if last is None:
            last = self.input_queue[-1] if self.input_queue else self.direction
        if new_dir != opposites.get(last) and new_dir != last:
            if len(self.input_queue) < 2:
                self.input_queue.append(new_dir)

    def move(self, grow=False):
        self.prev_body = [list(p) for p in self.body]
        if self.input_queue:
            self.direction = self.input_queue.pop(0)
        s = config.STEP
        if self.direction == 'UP':
            self.pos[1] -= s
        elif self.direction == 'DOWN':
            self.pos[1] += s
        elif self.direction == 'LEFT':
            self.pos[0] -= s
        elif self.direction == 'RIGHT':
            self.pos[0] += s
        self.body.insert(0, list(self.pos))
        if not grow:
            self.body.pop()

    def check_collision(self, mode="Classic", ghost_mode=False):
        if ghost_mode: return False
        w, h, ox, oy = _play_bounds()
        s = config.STEP
        if mode != "No Wall":
            if (self.pos[0] < ox or self.pos[0] > ox + w - s or
                    self.pos[1] < oy or self.pos[1] > oy + h - s):
                return True
        else:
            if self.pos[0] < ox: self.pos[0] = ox + w - s
            elif self.pos[0] > ox + w - s: self.pos[0] = ox
            elif self.pos[1] < oy: self.pos[1] = oy + h - s
            elif self.pos[1] > oy + h - s: self.pos[1] = oy
            self.body[0] = list(self.pos)
        for block in self.body[1:]:
            if self.pos == block:
                return True
        return False

    def draw(self, screen, assets, skin="classic", offset=(0,0), interp=1.0, style="Robotic"):
        ox, oy = offset
        s = config.STEP
        render_size = int(s * 1.15)
        offset_val = (render_size - s) // 2
        
        if style == "Robotic": interp = 1.0

        head_key = f"head_{skin}" if skin != "classic" else "head"
        body_key = f"body_{skin}" if skin != "classic" else "body"
        tail_key = f"tail_{skin}" if skin != "classic" else "tail"

        def get_interp_pos(idx):
            curr = self.body[idx]
            if style == "Robotic": return curr
            prev = self.prev_body[idx] if idx < len(self.prev_body) else curr
            if abs(curr[0] - prev[0]) > s * 2 or abs(curr[1] - prev[1]) > s * 2:
                return curr
            return [prev[0] + (curr[0] - prev[0]) * interp, prev[1] + (curr[1] - prev[1]) * interp]

        def get_angle(idx):
            curr = self.body[idx]
            prev_seg = self.body[idx-1] if idx > 0 else None
            
            if style == "Robotic":
                if idx == 0:
                    if self.direction == 'UP': return 90
                    elif self.direction == 'DOWN': return -90
                    elif self.direction == 'LEFT': return 180
                    return 0
                if prev_seg:
                    # Point AWAY from previous segment
                    dx, dy = curr[0] - prev_seg[0], curr[1] - prev_seg[1]
                    if dx > 0: return 0
                    if dx < 0: return 180
                    if dy > 0: return -90
                    if dy < 0: return 90
                return 0

            # Realistic Style (Smooth Angle)
            target_angle = 0
            if prev_seg:
                dx, dy = curr[0] - prev_seg[0], curr[1] - prev_seg[1]
                if abs(dx) > s * 2 or abs(dy) > s * 2: 
                    # Use current direction for wrap-around
                    if self.direction == 'UP': target_angle = 90
                    elif self.direction == 'DOWN': target_angle = -90
                    elif self.direction == 'LEFT': target_angle = 180
                    else: target_angle = 0
                else: target_angle = math.degrees(math.atan2(-dy, dx))
            elif self.direction == 'UP': target_angle = 90
            elif self.direction == 'DOWN': target_angle = -90
            elif self.direction == 'LEFT': target_angle = 180
            elif self.direction == 'RIGHT': target_angle = 0
            return target_angle

        for i in range(len(self.body) - 1, -1, -1):
            pos = get_interp_pos(i)
            angle = get_angle(i)
            
            if style == "Realistic":
                shadow_surf = pygame.Surface((render_size, render_size), pygame.SRCALPHA)
                pygame.draw.circle(shadow_surf, (0, 0, 0, 40), (render_size//2, render_size//2), render_size//2)
                screen.blit(shadow_surf, (pos[0] + ox - offset_val + 4, pos[1] + oy - offset_val + 4))

            if i == 0:
                img = assets.images.get(head_key, assets.images['head'])
            elif i == len(self.body) - 1:
                img = assets.images.get(tail_key, assets.images['tail'])
            else:
                img = assets.images.get(body_key, assets.images['body'])
            
            render_img = pygame.transform.smoothscale(img, (render_size, render_size))
            render_img = pygame.transform.rotate(render_img, angle)
            rect = render_img.get_rect(center=(pos[0] + s//2 + ox, pos[1] + s//2 + oy))
            screen.blit(render_img, rect)

class Food:
    def __init__(self, ftype="normal"):
        self.type = ftype
        self.pos = [0, 0]
        self.active = False
        self.spawn_time = 0

    def spawn(self, snake_body):
        self.pos = find_spawn_position(snake_body)
        self.active = True
        self.spawn_time = pygame.time.get_ticks()

class ShepuFood:
    """Mid-tier food: spawns more than special_food, gives 15 points.
    Randomly uses one of 3 shepu food images."""
    VARIANTS = ['shepuf1', 'shepuf2', 'shepuf3']

    def __init__(self):
        self.pos = [0, 0]
        self.active = False
        self.spawn_time = 0
        self.variant = random.choice(self.VARIANTS)

    def spawn(self, snake_body, obstacles=None):
        blocked = list(snake_body)
        if obstacles:
            blocked += [o.pos for o in obstacles]
        self.pos = find_spawn_position(snake_body, blocked)
        self.active = True
        self.spawn_time = pygame.time.get_ticks()
        self.variant = random.choice(self.VARIANTS)

    def draw(self, screen, assets, offset=(0, 0)):
        if not self.active: return
        ox, oy = offset
        if assets and self.variant in assets.images:
            screen.blit(assets.images[self.variant], (self.pos[0] + ox, self.pos[1] + oy))



class Obstacle:
    def __init__(self, pos, moving=False):
        self.pos = list(pos)
        self.moving = moving
        if moving:
            self.vx = random.choice([-2, 2])
            self.vy = random.choice([-2, 2])
        else:
            self.vx = 0
            self.vy = 0

    def update(self):
        if not self.moving: return
        self.pos[0] += self.vx
        self.pos[1] += self.vy
        w, h, ox, oy = _play_bounds()
        s = config.STEP
        if self.pos[0] < ox or self.pos[0] > ox + w - s: self.vx *= -1
        if self.pos[1] < oy or self.pos[1] > oy + h - s: self.vy *= -1

    def draw(self, screen, assets, offset=(0,0)):
        ox, oy = offset
        screen.blit(assets.images['obstacle'], (self.pos[0] + ox, self.pos[1] + oy))

class PowerUp:
    def __init__(self, ptype="ghost"):
        self.type = ptype
        self.pos = [0, 0]
        self.active_on_field = False
        self.spawn_time = 0
        self.pulse = 0
        self.pulse_dir = 1

    def spawn(self, snake_body, obstacles):
        blocked = list(snake_body)
        if obstacles:
            blocked += [o.pos for o in obstacles]
        self.pos = find_spawn_position(snake_body, blocked)
        self.active_on_field = True
        self.spawn_time = pygame.time.get_ticks()

    def draw(self, screen, assets=None, offset=(0,0)):
        ox, oy = offset
        self.pulse += 0.2 * self.pulse_dir
        if self.pulse > 5 or self.pulse < 0: self.pulse_dir *= -1
        s = config.STEP
        cx = self.pos[0] + s // 2 + ox
        cy = self.pos[1] + s // 2 + oy

        # Determine image and glow color from assets
        img_key = None
        color = (255, 255, 255)
        if assets:
            if self.type == "ghost":
                img_key = 'pu_ghost';  color = (160, 32, 240)
            elif self.type == "slowmo":
                img_key = 'pu_slowmo'; color = (0, 255, 255)
            elif self.type == "double":
                img_key = 'pu_double'; color = (255, 215, 0)

        if img_key and img_key in assets.images:
            img = assets.images[img_key]
            # Pulsing scale: grow and shrink smoothly
            scale_factor = 1.0 + (self.pulse / 30.0)
            iw = int(img.get_width() * scale_factor)
            ih = int(img.get_height() * scale_factor)
            scaled = pygame.transform.smoothscale(img, (iw, ih))
            # Glow ring behind image
            glow_r = iw // 2 + 4
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (*color, 60), (glow_r, glow_r), glow_r)
            screen.blit(glow_surf, (cx - glow_r, cy - glow_r))
            rect = scaled.get_rect(center=(cx, cy))
            screen.blit(scaled, rect)
        else:
            # Fallback: plain circles
            pygame.draw.circle(screen, color, (cx, cy), s // 2 + int(self.pulse), 2)
            pygame.draw.circle(screen, color, (cx, cy), s // 3)

class Boss:
    def __init__(self):
        self.reset(1)

    def reset(self, level):
        w, h, ox, oy = _play_bounds()
        self.pos = [ox + w - 100, oy + h - 100]
        self.pulse = 0
        self.pulse_dir = 1
        self.health = 3 + level
        self.speed = 1.0 + (level * 0.15)
        self.active = False
        self._sine_time = 0.0
        self._sine_amp = 60.0
        self._sine_freq = 1.8

    def update(self, dt, snake_pos):
        if not self.active: return
        try:
            self._sine_time += 0.001 * dt
            dx = snake_pos[0] - self.pos[0]
            dy = snake_pos[1] - self.pos[1]
            dist = math.hypot(dx, dy)
            if dist > 1:
                nx, ny = dx / dist, dy / dist
                perp_x, perp_y = -ny, nx
                sine_offset = math.sin(self._sine_time * self._sine_freq) * self._sine_amp
                self.pos[0] += (nx * self.speed + perp_x * sine_offset * 0.04) * (dt/16)
                self.pos[1] += (ny * self.speed + perp_y * sine_offset * 0.04) * (dt/16)
            w, h, ox, oy = _play_bounds()
            self.pos[0] = max(ox, min(ox + w, self.pos[0]))
            self.pos[1] = max(oy, min(oy + h, self.pos[1]))
            self.pulse += 0.5 * self.pulse_dir
            if self.pulse > 15 or self.pulse < 0: self.pulse_dir *= -1
        except Exception:
            pass

    def draw(self, screen, assets=None, offset=(0,0)):
        if not self.active: return
        ox, oy = offset
        s = config.STEP
        radius = s * 2 + int(self.pulse)
        cx = int(self.pos[0] + ox)
        cy = int(self.pos[1] + oy)

        if assets and 'boss_img' in assets.images:
            img = assets.images['boss_img']
            # Pulsing scale on boss image
            scale_factor = 1.0 + (self.pulse / 80.0)
            iw = int(img.get_width() * scale_factor)
            ih = int(img.get_height() * scale_factor)
            scaled = pygame.transform.smoothscale(img, (iw, ih))
            # Red glow behind boss
            glow_r = iw // 2 + 8
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (255, 0, 0, 80), (glow_r, glow_r), glow_r)
            screen.blit(glow_surf, (cx - glow_r, cy - glow_r))
            rect = scaled.get_rect(center=(cx, cy))
            screen.blit(scaled, rect)
        else:
            # Fallback: concentric red circles
            for i in range(3):
                alpha = 150 - (i * 40)
                surf = pygame.Surface((radius * 2, radius * 2), pygame.SRCALPHA)
                pygame.draw.circle(surf, (255, 0, 0, alpha), (radius, radius), radius - (i * 10))
                screen.blit(surf, (cx - radius, cy - radius))
            pygame.draw.circle(screen, (255, 50, 50), (cx, cy), s)

        # Health bar (always visible)
        bar_w = 60
        bar_x = int(self.pos[0] - bar_w // 2 + ox)
        bar_y = int(self.pos[1] - radius - 14 + oy)
        hp_frac = max(0, min(1, self.health / 5))
        pygame.draw.rect(screen, (60, 0, 0), (bar_x, bar_y, bar_w, 8), border_radius=4)
        pygame.draw.rect(screen, (255, 50, 50), (bar_x, bar_y, int(bar_w * hp_frac), 8), border_radius=4)

class MatrixFood:
    def __init__(self):
        self.pos = [0, 0]
        self.active = False
        self.spawn_time = 0
        self.pulse = 0
        self.pulse_dir = 1

    def spawn(self, snake_body, entities):
        blocked = list(snake_body)
        if entities:
            for ent in entities:
                if isinstance(ent, list):
                    blocked.append(ent)
                elif hasattr(ent, "pos"):
                    blocked.append(ent.pos)
        self.pos = find_spawn_position(snake_body, blocked)
        self.active = True
        self.spawn_time = pygame.time.get_ticks()

    def draw(self, screen, assets=None, offset=(0,0)):
        if not self.active: return
        ox, oy = offset
        self.pulse += 0.3 * self.pulse_dir
        if self.pulse > 8 or self.pulse < 0: self.pulse_dir *= -1
        s = config.STEP
        cx = self.pos[0] + s // 2 + ox
        cy = self.pos[1] + s // 2 + oy

        if assets and 'pu_hack' in assets.images:
            img = assets.images['pu_hack']
            scale_factor = 1.0 + (self.pulse / 40.0)
            iw = int(img.get_width() * scale_factor)
            ih = int(img.get_height() * scale_factor)
            scaled = pygame.transform.smoothscale(img, (iw, ih))
            # Green matrix glow
            glow_r = iw // 2 + 5
            glow_surf = pygame.Surface((glow_r * 2, glow_r * 2), pygame.SRCALPHA)
            pygame.draw.circle(glow_surf, (0, 255, 70, 70), (glow_r, glow_r), glow_r)
            screen.blit(glow_surf, (cx - glow_r, cy - glow_r))
            rect = scaled.get_rect(center=(cx, cy))
            screen.blit(scaled, rect)
        else:
            pygame.draw.circle(screen, (0, 255, 0), (cx, cy), s // 2 + int(self.pulse), 2)
            pygame.draw.circle(screen, (0, 100, 0), (cx, cy), s // 3)
