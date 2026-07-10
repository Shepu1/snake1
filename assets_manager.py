import pygame
import os
import sys
import random
import config
from utils import resource_path

class AssetManager:
    def __init__(self):
        self.images = {}
        self.sounds = {}
        self.music_volume = 0.5
        self.sound_volume = 0.5
        self.current_music_index = 0
        self.selected_bg = random.choice(["bk.png", "bk1.png"])

    def load_assets(self):
        s = config.STEP
        w, h = config.WIDTH, config.HEIGHT

        def load_and_smooth(path, size):
            img = pygame.image.load(resource_path(path)).convert_alpha()
            return pygame.transform.smoothscale(img, size)

        self.images['head'] = load_and_smooth("assets/images/snake_head.png", (s, s))
        self.images['body'] = load_and_smooth("assets/images/snake_body.png", (s, s))
        self.images['tail'] = load_and_smooth("assets/images/snake_tail.png", (s, s))
        self.images['food'] = load_and_smooth("assets/images/food.png", (s, s))
        self.images['special_food'] = load_and_smooth("assets/images/s food.png", (s, s))
        self.images['cut_food'] = load_and_smooth("assets/images/cut.png", (s, s))
        self.images['obstacle'] = load_and_smooth("assets/images/obstacle.png", (s, s))

        # Shepu power-up & special entity images
        pu_size = (int(s * 1.4), int(s * 1.4))
        self.images['pu_slowmo'] = load_and_smooth("assets/images/shepuslow.png", pu_size)
        self.images['pu_double'] = load_and_smooth("assets/images/shepuduble.png", pu_size)
        self.images['pu_ghost']  = load_and_smooth("assets/images/shepuinv.png",  pu_size)
        self.images['pu_hack']   = load_and_smooth("assets/images/shepuhack.png", pu_size)
        boss_size = (int(s * 3.5), int(s * 3.5))
        self.images['boss_img']  = load_and_smooth("assets/images/shepuboss.png", boss_size)

        # Shepu food variants (shepuf1, shepuf2, shepuf3)
        sf_size = (int(s * 1.2), int(s * 1.2))
        self.images['shepuf1'] = load_and_smooth("assets/images/shepuf1.png", sf_size)
        self.images['shepuf2'] = load_and_smooth("assets/images/shepuf2.png", sf_size)
        self.images['shepuf3'] = load_and_smooth("assets/images/shepuf3.png", sf_size)

        self.bg_files = ["bk.png", "bk1.png", "bk2.jpg", "bk3.jpg"]
        current_bg = self.bg_files[getattr(self, 'bg_index', 0)]
        bg_img = pygame.image.load(resource_path(f"assets/images/{current_bg}")).convert()
        
        # Professional "Cover" Scaling
        img_rect = bg_img.get_rect()
        img_ratio = img_rect.width / img_rect.height
        screen_ratio = w / h
        
        if screen_ratio > img_ratio:
            new_w = w
            new_h = int(w / img_ratio)
        else:
            new_h = h
            new_w = int(h * img_ratio)
            
        scaled_bg = pygame.transform.smoothscale(bg_img, (new_w, new_h))
        self.images['background'] = pygame.Surface((w, h))
        self.images['background'].blit(scaled_bg, ((w - new_w) // 2, (h - new_h) // 2))

        self.images['head_dragon'] = load_and_smooth("assets/images/snake_head_dragon.png", (s, s))
        self.images['body_dragon'] = load_and_smooth("assets/images/snake_body_dragon.png", (s, s))
        self.images['tail_dragon'] = load_and_smooth("assets/images/snake_tail_dragon.png", (s, s))
        
        self.images['head_robot'] = load_and_smooth("assets/images/snake_head_robot.png", (s, s))
        self.images['body_robot'] = load_and_smooth("assets/images/snake_body_robot.png", (s, s))
        self.images['tail_robot'] = self.images['body_robot']

        if not self.sounds:
            self.sounds['eat'] = pygame.mixer.Sound(resource_path("assets/sounds/gop.wav"))
            self.sounds['special_eat'] = pygame.mixer.Sound(resource_path("assets/sounds/s food.mp3"))
            self.sounds['cut'] = pygame.mixer.Sound(resource_path("assets/sounds/cut.mp3"))
            self.sounds['game_over'] = pygame.mixer.Sound(resource_path("assets/sounds/gameover.wav"))
            try:
                self.sounds['click'] = pygame.mixer.Sound(resource_path("assets/sounds/click.wav"))
            except Exception:
                self.sounds['click'] = None
            
            self.music_files = [
                resource_path(f"assets/sounds/bkm{'' if i==0 else i}.mp3") for i in range(10)
            ]
        
        self.set_music_volume(self.music_volume)
        self.set_sound_volume(self.sound_volume)

    def play_music(self, index=None):
        if index is not None:
            self.current_music_index = index
        if 0 <= self.current_music_index < len(self.music_files):
            pygame.mixer.music.load(self.music_files[self.current_music_index])
            pygame.mixer.music.play(-1)

    def stop_music(self):
        pygame.mixer.music.stop()

    def set_music_volume(self, volume):
        self.music_volume = volume
        pygame.mixer.music.set_volume(volume)

    def set_sound_volume(self, volume):
        self.sound_volume = volume
        for sound in self.sounds.values():
            sound.set_volume(volume)
