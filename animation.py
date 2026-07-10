import pygame
import math
import random
import config

class CinematicIntro:
    def __init__(self, width, height, font_large, font_small):
        self.width = width
        self.height = height
        self.font_large = font_large
        self.font_small = font_small
        
        self.timer = 0
        self.done = False
        
        self.vignette = pygame.Surface((width, height), pygame.SRCALPHA)
        self._create_vignette()
        
        self.scan_line_y = 0
        self.logo_alpha = 0
        
        self.particles = []
        for _ in range(25):
            self.particles.append({'x': random.randint(0, width), 'y': random.randint(0, height), 'v': random.uniform(0.02, 0.05), 's': random.randint(1, 3)})
        
    def _create_vignette(self):
        for r in range(self.width // 2, self.width):
            alpha = int(((r - self.width // 2) / (self.width // 2)) * 120)
            pygame.draw.circle(self.vignette, (0, 0, 0, alpha), (self.width // 2, self.height // 2), r, 2)

    def update(self, dt):
        self.timer += dt
        if self.timer > 4500: 
            self.done = True

    def draw(self, screen):
        curr_w, curr_h = screen.get_size()
        if curr_w != self.width or curr_h != self.height:
            self.width, self.height = curr_w, curr_h
            self.vignette = pygame.Surface((self.width, self.height), pygame.SRCALPHA)
            self._create_vignette()

        screen.fill((12, 12, 18))
        mid_x, mid_y = self.width // 2, self.height // 2
        t = self.timer
        
        for p in self.particles:
            p['y'] -= p['v'] * 16 
            if p['y'] < 0: p['y'] = self.height
            pygame.draw.circle(screen, (0, 255, 255, 100), (int(p['x']), int(p['y'])), p['s'])

        if t < 1200:
            scan_y = (t / 1200) * self.height
            pygame.draw.line(screen, (0, 180, 255), (0, scan_y), (self.width, scan_y), 1)
            glow_surf = pygame.Surface((self.width, 30), pygame.SRCALPHA)
            pygame.draw.rect(glow_surf, (0, 150, 255, 20), (0, 0, self.width, 30))
            screen.blit(glow_surf, (0, scan_y - 15))

        if 1200 < t < 4500:
            brand_t = min(1.0, (t - 1200) / 1000)
            self.logo_alpha = int(brand_t * 255)
            
            brand_text = "S H E P U"
            brand_font = pygame.font.SysFont("Verdana", 24, bold=True)
            
            brand_surf = brand_font.render(brand_text, True, (220, 220, 240))
            brand_surf.set_alpha(self.logo_alpha)
            rect = brand_surf.get_rect(center=(mid_x, mid_y - 80))
            screen.blit(brand_surf, rect)
            
            line_w = int(brand_t * 120)
            pygame.draw.line(screen, (60, 60, 80), (mid_x - line_w, mid_y - 50), (mid_x + line_w, mid_y - 50), 1)

        if t > 2200:
            title_t = min(1.0, (t - 2200) / 1000)
            title_alpha = int(title_t * 255)
            
            frame_w, frame_h = 420, 90
            frame_rect = pygame.Rect(mid_x - frame_w // 2, mid_y - frame_h // 2, frame_w, frame_h)
            
            c_len = 15
            pygame.draw.lines(screen, config.CYAN, False, [(frame_rect.left, frame_rect.top + c_len), (frame_rect.left, frame_rect.top), (frame_rect.left + c_len, frame_rect.top)], 2)
            pygame.draw.lines(screen, config.CYAN, False, [(frame_rect.right - c_len, frame_rect.bottom), (frame_rect.right, frame_rect.bottom), (frame_rect.right, frame_rect.bottom - c_len)], 2)

            glow_s = self.font_large.render("SNAKE PRO", True, (0, 255, 255))
            glow_s.set_alpha(int(title_alpha * 0.3))
            for off in [(2,2), (-2, -2), (2, -2), (-2, 2)]:
                screen.blit(glow_s, glow_s.get_rect(center=(mid_x + off[0], mid_y + off[1])))

            title_surf = self.font_large.render("SNAKE PRO", True, config.WHITE)
            title_surf.set_alpha(title_alpha)
            screen.blit(title_surf, title_surf.get_rect(center=(mid_x, mid_y)))
            
            if t > 3000:
                sub_alpha = min(255, int(((t - 3000) / 1000) * 255))
                sub_surf = self.font_small.render("PROFESSIONAL EDITION", True, (160, 160, 180))
                sub_surf.set_alpha(sub_alpha)
                screen.blit(sub_surf, sub_surf.get_rect(center=(mid_x, mid_y + 100)))

        screen.blit(self.vignette, (0, 0))
        
        if 2180 < t < 2220:
            screen.fill((20, 20, 40), special_flags=pygame.BLEND_RGB_ADD)
