import pygame
import random
import config

class Button:
    def __init__(self, x, y, width, height, text, font, color=config.BLUE, hover_color=config.CYAN):
        self.rect = pygame.Rect(x - width // 2, y - height // 2, width, height)
        self.text = text
        self.font = font
        self.color = color
        self.hover_color = hover_color
        self.is_hovered = False
        self.scale = 1.0
        self.target_scale = 1.0

    def draw(self, screen, mouse_pos):
        self.is_hovered = self.rect.collidepoint(mouse_pos)
        if self.is_hovered:
            self.target_scale = 1.08
            current_color = self.hover_color
        else:
            self.target_scale = 1.0
            current_color = self.color
        
        self.scale += (self.target_scale - self.scale) * 0.2
        sw = int(self.rect.width * self.scale)
        sh = int(self.rect.height * self.scale)
        s_rect = pygame.Rect(0, 0, sw, sh)
        s_rect.center = self.rect.center
        
        if self.is_hovered:
            glow_rect = s_rect.inflate(10, 10)
            glow_surf = pygame.Surface((glow_rect.width, glow_rect.height), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (*current_color, 50), (0, 0, glow_rect.width, glow_rect.height), border_radius=15)
            screen.blit(glow_surf, glow_rect)

        pygame.draw.rect(screen, (20, 20, 30), s_rect, border_radius=12)
        pygame.draw.rect(screen, current_color, s_rect, 2, border_radius=12)
        
        text_surf = self.font.render(self.text, True, config.WHITE if not self.is_hovered else current_color)
        text_rect = text_surf.get_rect(center=self.rect.center)
        screen.blit(text_surf, text_rect)

    def is_clicked(self, event, mouse_pos):
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            return self.rect.collidepoint(mouse_pos)
        return False

class Particle:
    def __init__(self, x, y, color):
        self.x = x
        self.y = y
        self.color = color
        self.vx = random.uniform(-4, 4)
        self.vy = random.uniform(-4, 4)
        self.life = 255 
        self.size = random.randint(2, 5)

    def update(self):
        self.x += self.vx
        self.y += self.vy
        self.life -= 12
        return self.life > 0

    def draw(self, screen, offset=(0,0)):
        if self.life <= 0: return
        ox, oy = offset
        pygame.draw.circle(screen, (*self.color, self.life), (int(self.x + ox), int(self.y + oy)), int(self.size))

class UIManager:
    def __init__(self):
        try:
            from utils import resource_path
            self.font_large = pygame.font.Font(resource_path("assets/fonts/shepu1.ttf"), 85)
            self.font_mid = pygame.font.Font(resource_path("assets/fonts/shepu2.ttf"), 42)
            self.font_small = pygame.font.Font(resource_path("assets/fonts/shepu2.ttf"), 26)
            self.font_tiny = pygame.font.Font(resource_path("assets/fonts/shepu2.ttf"), 18)
            self.font_button = pygame.font.Font(resource_path("assets/fonts/shepu2.ttf"), 30)
            self.font_hud = pygame.font.Font(resource_path("assets/fonts/shepu2.ttf"), 24)
            
            self.font_num_large = pygame.font.SysFont("Verdana", 80, bold=True)
            self.font_num_mid = pygame.font.SysFont("Verdana", 40, bold=True)
            self.font_num_small = pygame.font.SysFont("Verdana", 24, bold=True)
            self.font_num_tiny = pygame.font.SysFont("Verdana", 18, bold=True)
            
        except Exception:
            self.font_large = pygame.font.SysFont("Verdana", 80, bold=True)
            self.font_mid = pygame.font.SysFont("Verdana", 40, bold=True)
            self.font_small = pygame.font.SysFont("Verdana", 24, bold=True)
            self.font_tiny = pygame.font.SysFont("Verdana", 18, bold=True)
            self.font_button = self.font_small
            self.font_hud = self.font_tiny
            self.font_num_large = self.font_large
            self.font_num_mid = self.font_mid
            self.font_num_small = self.font_small
            self.font_num_tiny = self.font_tiny
        
        self.particles = []
        self.shake_amount = 0
        self.shake_timer = 0

    def draw_text(self, screen, text, font, color, x, y, center=True, shadow=True, align="left"):
        if shadow:
            s_surf = font.render(text, True, (10, 10, 20))
            s_rect = s_surf.get_rect()
            if center: s_rect.center = (x + 2, y + 2)
            elif align == "right": s_rect.topright = (x + 2, y + 2)
            else: s_rect.topleft = (x + 2, y + 2)
            screen.blit(s_surf, s_rect)
            
        surf = font.render(text, True, color)
        rect = surf.get_rect()
        if center: rect.center = (x, y)
        elif align == "right": rect.topright = (x, y)
        else: rect.topleft = (x, y)
        screen.blit(surf, rect)

    def draw_level_info(self, screen, level, score, next_level_score):
        hud_rect = pygame.Rect(15, 15, 200, 80)
        pygame.draw.rect(screen, (10, 10, 20, 180), hud_rect, border_radius=10)
        pygame.draw.rect(screen, config.BLUE, hud_rect, 1, border_radius=10)
        self.draw_text(screen, f"LEVEL {level}", self.font_num_small, config.CYAN, 30, 35, center=False)
        bar_w = 170
        if next_level_score == 'MAX': prog = 1.0
        else:
            prev = config.LEVEL_UP_SCORES.get(level, 0)
            prog = min(1.0, (score - prev) / (next_level_score - prev))
        pygame.draw.rect(screen, (40, 40, 50), (30, 70, bar_w, 6), border_radius=3)
        pygame.draw.rect(screen, config.CYAN, (30, 70, bar_w * prog, 6), border_radius=3)
        xp_text = f"{score} XP" if next_level_score == 'MAX' else f"{score} / {next_level_score} XP"
        self.draw_text(screen, xp_text, self.font_num_tiny, config.LIGHT_GRAY, 30, 85, center=False)

    def draw_overlay(self, screen, alpha=180):
        overlay = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        overlay.fill((5, 5, 10, alpha))
        screen.blit(overlay, (0, 0))

    def create_particles(self, x, y, color):
        for _ in range(config.PARTICLE_COUNT):
            self.particles.append(Particle(x, y, color))

    def update_effects(self, dt):
        self.particles = [p for p in self.particles if p.update()]
        if self.shake_timer > 0:
            self.shake_timer -= dt
            if self.shake_timer <= 0:
                self.shake_amount = 0

    def trigger_shake(self, intensity=config.SHAKE_INTENSITY, duration=config.SHAKE_DURATION):
        self.shake_amount = intensity
        self.shake_timer = duration

    def get_shake_offset(self):
        if self.shake_timer > 0:
            return (random.randint(-self.shake_amount, self.shake_amount),
                    random.randint(-self.shake_amount, self.shake_amount))
        return (0, 0)

    def draw_particles(self, screen, offset=(0,0)):
        for p in self.particles:
            p.draw(screen, offset)
