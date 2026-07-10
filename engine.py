import pygame
import time
import random
import math
import config
from utils import DataManager, is_android
from assets_manager import AssetManager
from entities import Snake, Food, PowerUp, Boss, MatrixFood, ShepuFood
from ui import Button, UIManager
from animation import CinematicIntro
from controls import (
    ControlManager, CONTROL_SWIPE, CONTROL_CORNER, CONTROL_SPLIT,
    CONTROL_LABELS, find_spawn_position,
)

class GameEngine:
    def __init__(self, screen):
        self.screen = screen
        self.clock = pygame.time.Clock()
        self.running = True
        
        self.ui = UIManager()
        self.data_manager = DataManager()
        self.game_data = self.data_manager.load_data()
        
        config.FPS = self.game_data.get('fps', 10)
        config.STEP = self.game_data.get('step', 30)
        self.game_mode = self.game_data.get('game_mode', 'Classic')
        
        self.assets = AssetManager()
        self.assets.music_volume = self.game_data.get('music_volume', 0.5)
        self.assets.sound_volume = self.game_data.get('sound_volume', 0.5)
        self.assets.current_music_index = random.randint(0, 9)
        self.assets.bg_index = random.randint(0, 3)
        
        self.assets.load_assets()
        self.assets.play_music()

        self.control_manager = ControlManager(self.game_data)
        self.swipe_tutorial_timer = 0
        self.use_touch_controls = is_android()

        # First launch: ask name; otherwise go to SPLASH
        if not self.game_data.get('player_name', ''):
            self.state = "NAME_INPUT"
        else:
            self.state = "SPLASH"
        self.splash = CinematicIntro(config.WIDTH, config.HEIGHT, self.ui.font_large, self.ui.font_small)
        self.fullscreen = False
        self.name_input_text = ""  # buffer for name entry
        
        self.snake = Snake()
        self.food = Food("normal")
        self.special_food = Food("special")
        self.cut_food = Food("cut")
        self.power_up = PowerUp()
        self.boss = Boss()
        self.matrix_food = MatrixFood()
        self.shepu_food = ShepuFood()
        self.obstacles = []
        
        self.matrix_active = False
        self.matrix_timer = 0
        self.matrix_chars = []
        
        self.current_score = 0
        self.start_time = 0
        self.next_cut_food_score = config.CUT_FOOD_INTERVAL
        self.level_up_message = ""
        self.level_up_message_time = 0
        self.game_over_timer = 0
        self.new_high_score = False 
        self.pause_start_time = 0
        
        self.active_power_up = None
        self.power_up_timer = 0
        self.move_timer = 0
        
        self.night_mode_active = False
        self.night_timer = 0
        self.night_event_delay = config.NIGHT_MODE_INTERVAL * 1000
        self.night_alpha = 0
        self.darkness = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
        
        self.moving_event_active = False
        self.moving_event_timer = 0
        self.moving_event_delay = config.MOVING_OBSTACLE_INTERVAL * 1000
        
        self.boss_battle_active = False
        
        self.create_buttons()
        self.settings_buttons["bg_effect"].text = f"BG TINT: {'ON' if self.game_data.get('bg_effect', True) else 'OFF'}"
        self._refresh_control_settings_labels()
        pygame.mouse.set_visible(not is_android())
        self.cursor_angle = 0
        self.cursor_surf = self.pre_render_cursor()
        
        self.move_timer = 0
        self.target_fps = 60

    def _play_click(self):
        """Play the menu click sound if available."""
        snd = self.assets.sounds.get('click')
        if snd:
            snd.set_volume(min(1.0, self.assets.sound_volume * 1.2))
            snd.play()

    def _refresh_control_settings_labels(self):
        mode = self.game_data.get("control_mode", CONTROL_SWIPE)
        label = CONTROL_LABELS.get(mode, mode.upper())
        self.settings_buttons["control_mode"].text = f"CONTROL: {label}"
        side = self.game_data.get("joystick_side", "right").upper()
        self.settings_buttons["joystick_side"].text = f"JOY SIDE: {side}"

    def _start_play_session(self):
        self.reset_game()
        self.control_manager.set_mode(
            self.game_data.get("control_mode", CONTROL_SWIPE),
            self.game_data.get("joystick_side", "right"),
        )
        if self.game_data.get("control_mode", CONTROL_SWIPE) == CONTROL_SWIPE:
            self.state = "SWIPE_TUTORIAL"
            self.swipe_tutorial_timer = 2000
        else:
            self.state = "PLAYING"

    def _select_control_mode(self, mode):
        self.game_data["control_mode"] = mode
        self.game_data["control_setup_done"] = True
        self.data_manager.save_data(self.game_data)
        self.control_manager.set_mode(mode, self.game_data.get("joystick_side", "right"))
        self._start_play_session()

    def create_buttons(self):
        mid_x = config.WIDTH // 2
        bw, bh = 240, 50
        y_start = 190
        space = 53
        self.menu_buttons = {
            "play":       Button(mid_x, y_start,          bw, bh, "START GAME",  self.ui.font_small),
            "mode":       Button(mid_x, y_start + space,  bw, bh, "GAME MODE",   self.ui.font_small),
            "skins":      Button(mid_x, y_start + 2*space,bw, bh, "SKIN SHOP",   self.ui.font_small),
            "high_score": Button(mid_x, y_start + 3*space,bw, bh, "LEADERBOARD", self.ui.font_small),
            "settings":   Button(mid_x, y_start + 4*space,bw, bh, "SETTINGS",    self.ui.font_small),
            "support":    Button(mid_x, y_start + 5*space,bw, bh, "SUPPORT US <3",self.ui.font_small),
            "exit":       Button(mid_x, y_start + 6*space,bw, bh, "EXIT",         self.ui.font_small)
        }
        lx, rx = mid_x - 150, mid_x + 150
        self.settings_buttons = {
            "speed_plus": Button(lx + 60, 150, 40, 40, "+", self.ui.font_mid),
            "speed_minus": Button(lx - 60, 150, 40, 40, "-", self.ui.font_mid),
            "size_plus": Button(lx + 60, 230, 40, 40, "+", self.ui.font_mid),
            "size_minus": Button(lx - 60, 230, 40, 40, "-", self.ui.font_mid),
            "bg_effect": Button(lx, 310, 180, 40, "BG TINT: ON", self.ui.font_small),
            "bg_change": Button(lx, 390, 180, 40, f"BG: {self.game_data.get('bg_index', 0) + 1}", self.ui.font_num_small),
            
            "music_plus": Button(rx + 60, 150, 40, 40, "+", self.ui.font_mid),
            "music_minus": Button(rx - 60, 150, 40, 40, "-", self.ui.font_mid),
            "sound_plus": Button(rx + 60, 230, 40, 40, "+", self.ui.font_mid),
            "sound_minus": Button(rx - 60, 230, 40, 40, "-", self.ui.font_mid),
            "music_prev": Button(rx - 70, 310, 40, 40, "<", self.ui.font_mid),
            "music_track": Button(rx, 310, 80, 40, f"{self.assets.current_music_index + 1}", self.ui.font_num_small),
            "music_next": Button(rx + 70, 310, 40, 40, ">", self.ui.font_mid),
            "move_style": Button(rx, 390, 180, 40, f"STYLE: {self.game_data.get('movement_style', 'Robotic').upper()}", self.ui.font_small),
            "control_mode": Button(lx, 450, 180, 40, "CONTROL: SWIPE", self.ui.font_small),
            "joystick_side": Button(rx, 450, 180, 40, "JOY SIDE: RIGHT", self.ui.font_small),
            "back": Button(mid_x, 560, 140, 45, "BACK", self.ui.font_small)
        }
        self.control_select_buttons = {
            CONTROL_SWIPE: Button(mid_x, 210, 280, 52, "SWIPE CONTROL", self.ui.font_small),
            CONTROL_CORNER: Button(mid_x, 280, 280, 52, "CORNER JOYSTICK", self.ui.font_small),
            CONTROL_SPLIT: Button(mid_x, 350, 280, 52, "SPLIT SCREEN JOYSTICK", self.ui.font_small),
            "back": Button(mid_x, 450, 140, 45, "BACK", self.ui.font_small),
        }
        self.mode_buttons = {
            "Classic": Button(mid_x, 220, 240, 50, "CLASSIC", self.ui.font_small),
            "Time Attack": Button(mid_x, 280, 240, 50, "TIME ATTACK", self.ui.font_small),
            "No Wall": Button(mid_x, 340, 240, 50, "NO WALLS", self.ui.font_small),
            "back": Button(mid_x, 440, 140, 45, "BACK", self.ui.font_small)
        }
        self.skin_buttons = {
            "classic": Button(mid_x, 220, 240, 50, "CLASSIC", self.ui.font_small),
            "dragon": Button(mid_x, 280, 240, 50, "DRAGON", self.ui.font_small),
            "robot": Button(mid_x, 340, 240, 50, "ROBOT", self.ui.font_small),
            "back": Button(mid_x, 440, 140, 45, "BACK", self.ui.font_small)
        }
        self.pause_buttons = {
            "resume":  Button(mid_x, 220, 240, 50, "RESUME",    self.ui.font_small),
            "restart": Button(mid_x, 280, 240, 50, "RESTART",   self.ui.font_small),
            "menu":    Button(mid_x, 340, 240, 50, "MAIN MENU", self.ui.font_small)
        }
        self.support_buttons = {
            "back": Button(mid_x, 530, 160, 45, "BACK", self.ui.font_small)
        }

    def toggle_fullscreen(self):
        self.fullscreen = not self.fullscreen
        if self.fullscreen:
            info = pygame.display.Info()
            config.WIDTH, config.HEIGHT = info.current_w, info.current_h
            self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.FULLSCREEN)
        else:
            config.WIDTH, config.HEIGHT = 800, 600 
            self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
        
        self.assets.load_assets()
        self.create_buttons()
        self.control_manager.resize(config.WIDTH, config.HEIGHT)
        self.darkness = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)

    def reset_game(self):
        self.snake.reset()
        self.spawn_obstacles()
        self.food.spawn(self.snake.body + [o.pos for o in self.obstacles])
        self.special_food.active = False
        self.cut_food.active = False
        self.power_up.active_on_field = False
        self.active_power_up = None
        self.power_up_timer = 0
        self.power_up_max_timer = config.POWER_UP_DURATION * 1000 
        self.current_score = 0
        self.start_time = time.time()
        self.next_cut_food_score = config.CUT_FOOD_INTERVAL
        self.move_timer = 0
        self.night_mode_active = False
        self.night_timer = 0
        self.night_event_delay = config.NIGHT_MODE_INTERVAL * 1000
        self.night_alpha = 0
        self.moving_event_active = False
        self.moving_event_timer = 0
        self.moving_event_delay = config.MOVING_OBSTACLE_INTERVAL * 1000
        self.boss_battle_active = False
        self.matrix_active = False
        self.matrix_timer = 0
        self.matrix_chars = []
        self.matrix_food.active = False
        self.shepu_food.active = False
        self.boss.active = False
        self.new_high_score = False
        
        self.assets.play_music()

    def spawn_obstacles(self):
        from entities import Obstacle
        self.obstacles = []
        if self.game_mode == "No Wall":
            return
            
        num_obstacles = max(0, (self.game_data['level'] - 1) * config.OBSTACLE_COUNT_PER_LEVEL)
        
        for i in range(num_obstacles):
            pos = find_spawn_position(self.snake.body, [o.pos for o in self.obstacles])
            if pos not in [o.pos for o in self.obstacles]:
                self.obstacles.append(Obstacle(pos, moving=False))

    def handle_events(self):
        mouse_pos = pygame.mouse.get_pos()
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
                self.data_manager.save_data(self.game_data)
            
            if event.type == pygame.VIDEORESIZE:
                if not self.fullscreen:
                    config.WIDTH, config.HEIGHT = event.w, event.h
                    self.screen = pygame.display.set_mode((config.WIDTH, config.HEIGHT), pygame.RESIZABLE)
                    self.assets.load_assets()
                    self.create_buttons()
                    self.control_manager.resize(config.WIDTH, config.HEIGHT)
                    self.darkness = pygame.Surface((config.WIDTH, config.HEIGHT), pygame.SRCALPHA)
            
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_F11: self.toggle_fullscreen()

            if self.state == "MENU":
                for k, btn in self.menu_buttons.items():
                    if btn.is_clicked(event, mouse_pos):
                        self._play_click()
                        if k == "play":
                            if not self.game_data.get("control_setup_done", False):
                                self.state = "CONTROL_SELECT"
                            else:
                                self._start_play_session()
                        elif k == "mode": self.state = "MODE"
                        elif k == "skins": self.state = "SKINS"
                        elif k == "high_score": self.state = "HIGH_SCORE"
                        elif k == "settings": self.state = "SETTINGS"
                        elif k == "support": self.state = "SUPPORT"
                        elif k == "exit": self.running = False

            elif self.state == "MODE":
                for mode, btn in self.mode_buttons.items():
                    if btn.is_clicked(event, mouse_pos):
                        self._play_click()
                        if mode == "back": self.state = "MENU"
                        else: 
                            self.game_mode = mode
                            self.game_data['game_mode'] = mode
                            self.data_manager.save_data(self.game_data)
            
            elif self.state == "SKINS":
                for skin, btn in self.skin_buttons.items():
                    if btn.is_clicked(event, mouse_pos):
                        self._play_click()
                        if skin == "back": self.state = "MENU"
                        else:
                            req = config.SKIN_UNLOCKS.get(skin, 0)
                            if self.game_data["lifetime_score"] >= req: 
                                self.game_data["current_skin"] = skin
                                self.data_manager.save_data(self.game_data)
                            else: self.ui.trigger_shake(5, 100)

            elif self.state == "SETTINGS":
                if self.settings_buttons["speed_plus"].is_clicked(event, mouse_pos): 
                    config.FPS = min(20, config.FPS + 1)
                    self.game_data['fps'] = config.FPS
                elif self.settings_buttons["speed_minus"].is_clicked(event, mouse_pos): 
                    config.FPS = max(1, config.FPS - 1)
                    self.game_data['fps'] = config.FPS
                elif self.settings_buttons["size_plus"].is_clicked(event, mouse_pos):
                    config.STEP = min(60, config.STEP + 5)
                    self.game_data['step'] = config.STEP
                    config.VISION_RADIUS = config.STEP * 6.5
                    self.assets.load_assets()
                elif self.settings_buttons["size_minus"].is_clicked(event, mouse_pos):
                    config.STEP = max(10, config.STEP - 5)
                    self.game_data['step'] = config.STEP
                    config.VISION_RADIUS = config.STEP * 6.5
                    self.assets.load_assets()
                elif self.settings_buttons["music_plus"].is_clicked(event, mouse_pos):
                    self.assets.music_volume = min(1.0, self.assets.music_volume + 0.1)
                    self.assets.set_music_volume(self.assets.music_volume)
                    self.game_data['music_volume'] = self.assets.music_volume
                elif self.settings_buttons["music_minus"].is_clicked(event, mouse_pos):
                    self.assets.music_volume = max(0.0, self.assets.music_volume - 0.1)
                    self.assets.set_music_volume(self.assets.music_volume)
                    self.game_data['music_volume'] = self.assets.music_volume
                elif self.settings_buttons["sound_plus"].is_clicked(event, mouse_pos):
                    self.assets.sound_volume = min(1.0, self.assets.sound_volume + 0.1)
                    self.assets.set_sound_volume(self.assets.sound_volume)
                    self.game_data['sound_volume'] = self.assets.sound_volume
                elif self.settings_buttons["sound_minus"].is_clicked(event, mouse_pos):
                    self.assets.sound_volume = max(0.0, self.assets.sound_volume - 0.1)
                    self.assets.set_sound_volume(self.assets.sound_volume)
                    self.game_data['sound_volume'] = self.assets.sound_volume
                elif self.settings_buttons["bg_effect"].is_clicked(event, mouse_pos):
                    self.game_data['bg_effect'] = not self.game_data['bg_effect']
                    self.settings_buttons["bg_effect"].text = f"BG TINT: {'ON' if self.game_data['bg_effect'] else 'OFF'}"
                elif self.settings_buttons["bg_change"].is_clicked(event, mouse_pos):
                    self.assets.bg_index = (self.assets.bg_index + 1) % 4
                    self.assets.load_assets()
                    self.settings_buttons["bg_change"].text = f"BG: {self.assets.bg_index + 1}"
                elif self.settings_buttons["move_style"].is_clicked(event, mouse_pos):
                    curr = self.game_data.get('movement_style', 'Robotic')
                    new_style = "Realistic" if curr == "Robotic" else "Robotic"
                    self.game_data['movement_style'] = new_style
                    self.settings_buttons["move_style"].text = f"STYLE: {new_style.upper()}"
                elif self.settings_buttons["control_mode"].is_clicked(event, mouse_pos):
                    self.control_manager.cycle_mode()
                    self.game_data["control_mode"] = self.control_manager.mode
                    self._refresh_control_settings_labels()
                    self.data_manager.save_data(self.game_data)
                elif self.settings_buttons["joystick_side"].is_clicked(event, mouse_pos):
                    side = "left" if self.game_data.get("joystick_side", "right") == "right" else "right"
                    self.game_data["joystick_side"] = side
                    self.control_manager.set_mode(self.control_manager.mode, side)
                    self._refresh_control_settings_labels()
                    self.data_manager.save_data(self.game_data)
                elif self.settings_buttons["music_next"].is_clicked(event, mouse_pos):
                    self.assets.current_music_index = (self.assets.current_music_index + 1) % 10
                    self.assets.play_music()
                    self.settings_buttons["music_track"].text = f"{self.assets.current_music_index + 1}"
                elif self.settings_buttons["music_prev"].is_clicked(event, mouse_pos):
                    self.assets.current_music_index = (self.assets.current_music_index - 1) % 10
                    self.assets.play_music()
                    self.settings_buttons["music_track"].text = f"{self.assets.current_music_index + 1}"
                elif self.settings_buttons["music_track"].is_clicked(event, mouse_pos):
                    self.assets.current_music_index = (self.assets.current_music_index + 1) % 10
                    self.assets.play_music()
                    self.settings_buttons["music_track"].text = f"{self.assets.current_music_index + 1}"
                elif self.settings_buttons["back"].is_clicked(event, mouse_pos): 
                    self.data_manager.save_data(self.game_data)
                    self.state = "MENU"

            elif self.state == "HIGH_SCORE":
                if event.type == pygame.KEYDOWN or (event.type == pygame.MOUSEBUTTONDOWN and event.button == 1):
                    self._play_click()
                    self.state = "MENU"

            elif self.state == "CONTROL_SELECT":
                for key, btn in self.control_select_buttons.items():
                    if btn.is_clicked(event, mouse_pos):
                        self._play_click()
                        if key == "back":
                            self.state = "MENU"
                        else:
                            self._select_control_mode(key)

            elif self.state in ("PLAYING", "SWIPE_TUTORIAL", "PAUSED"):
                if self.state in ("PLAYING", "SWIPE_TUTORIAL"):
                    self.control_manager.handle_event(event, self.state)
                if event.type == pygame.KEYDOWN and self.state == "PLAYING":
                    if event.key == pygame.K_ESCAPE or event.key == pygame.K_p:
                        self.state = "PAUSED"
                        self.pause_start_time = time.time()
                    else:
                        self.snake.handle_input(event.key)
                if self.state == "PAUSED":
                    for k, btn in self.pause_buttons.items():
                        if btn.is_clicked(event, mouse_pos):
                            self._play_click()
                            if k == "resume":
                                self.state = "PLAYING"
                                self.start_time += (time.time() - self.pause_start_time)
                            elif k == "restart":
                                self.reset_game()
                                self.state = "PLAYING"
                            elif k == "menu":
                                self.state = "MENU"

            elif self.state == "NAME_INPUT":
                if event.type == pygame.KEYDOWN:
                    if event.key == pygame.K_RETURN and self.name_input_text.strip():
                        self.game_data['player_name'] = self.name_input_text.strip()[:20]
                        self.data_manager.save_data(self.game_data)
                        self.state = "SPLASH"
                    elif event.key == pygame.K_BACKSPACE:
                        self.name_input_text = self.name_input_text[:-1]
                    elif len(self.name_input_text) < 20:
                        if event.unicode and event.unicode.isprintable():
                            self.name_input_text += event.unicode

            elif self.state == "SUPPORT":
                for k, btn in self.support_buttons.items():
                    if btn.is_clicked(event, mouse_pos):
                        self._play_click()
                        if k == "back": self.state = "MENU"
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    self.state = "MENU"

    def update(self):
        dt = self.clock.tick(self.target_fps)
        self.ui.update_effects(dt)
        
        if self.state in ("NAME_INPUT", "SUPPORT", "CONTROL_SELECT"): return
        if self.state == "SWIPE_TUTORIAL":
            self.swipe_tutorial_timer -= dt
            direction = self.control_manager.consume_direction()
            if direction:
                self.snake.queue_direction(direction)
            if self.swipe_tutorial_timer <= 0:
                self.state = "PLAYING"
            return
        if self.state == "SPLASH":
            self.splash.update(dt)
            if self.splash.done: self.state = "MENU"
            return
        if self.state == "GAME_OVER":
            self.game_over_timer -= dt
            if self.game_over_timer <= 0: self.state = "MENU"
            return
        if self.state != "PLAYING": return

        direction = self.control_manager.consume_direction()
        if direction:
            self.snake.queue_direction(direction)

        if self.matrix_active:
            self.matrix_timer -= dt
            if self.matrix_timer <= 0: self.matrix_active = False
        if self.matrix_food.active:
            if pygame.time.get_ticks() - self.matrix_food.spawn_time > config.MATRIX_FOOD_LIFETIME * 1000:
                self.matrix_food.active = False

        if self.active_power_up:
            self.power_up_timer -= dt
            if self.power_up_timer <= 0: self.active_power_up = None

        if self.boss.active and hasattr(self.snake, 'pos'): 
            self.boss.update(dt, self.snake.pos)
        for o in self.obstacles: o.update()

        speed_mult = 0.5 if self.active_power_up == "slowmo" else 1.0
        move_delay = (1000 // config.FPS) / speed_mult
        self.move_timer += dt
        
        if self.move_timer >= move_delay:
            self.move_timer -= move_delay
            self.move_snake()
            self.check_level_up()

        if self.game_data['level'] >= config.NIGHT_MODE_START_LEVEL and not self.boss_battle_active:
            if not self.night_mode_active:
                self.night_event_delay -= dt
                if self.night_event_delay <= 0:
                    self.night_mode_active = True
                    self.night_timer = config.NIGHT_MODE_DURATION * 1000
            else:
                self.night_timer -= dt
                if self.night_timer <= 0:
                    self.night_mode_active = False
                    self.night_event_delay = config.NIGHT_MODE_INTERVAL * 1000
        
        if self.night_mode_active: self.night_alpha = min(245, self.night_alpha + 5)
        else: self.night_alpha = max(0, self.night_alpha - 5)

        if self.game_data['level'] >= config.MOVING_OBSTACLE_START_LEVEL and not self.boss_battle_active:
            if not self.moving_event_active:
                self.moving_event_delay -= dt
                if self.moving_event_delay <= 0:
                    self.moving_event_active = True
                    self.moving_event_timer = config.MOVING_OBSTACLE_DURATION * 1000
                    for o in self.obstacles: 
                        o.moving = True
                        o.vx = random.choice([-2, 2]); o.vy = random.choice([-2, 2])
            else:
                self.moving_event_timer -= dt
                if self.moving_event_timer <= 0:
                    self.moving_event_active = False
                    self.moving_event_delay = config.MOVING_OBSTACLE_INTERVAL * 1000
                    for o in self.obstacles: o.moving = False

        if self.boss_battle_active and hasattr(self.snake, 'pos'):
            br = pygame.Rect(self.boss.pos[0] - config.STEP, self.boss.pos[1] - config.STEP, config.STEP * 2, config.STEP * 2)
            sr = pygame.Rect(self.snake.pos[0], self.snake.pos[1], config.STEP, config.STEP)
            if sr.colliderect(br) and self.active_power_up != "ghost": self.game_over(); return

        if self.active_power_up:
            self.power_up_timer -= dt
        if self.game_mode == "Time Attack":
            if config.TIME_ATTACK_DURATION - (time.time() - self.start_time) <= 0: self.game_over(); return

    def move_snake(self):
        grow = False
        snake_rect = pygame.Rect(self.snake.pos[0], self.snake.pos[1], config.STEP, config.STEP)
        
        if snake_rect.colliderect(pygame.Rect(self.food.pos[0], self.food.pos[1], config.STEP, config.STEP)):
            self.assets.sounds['eat'].play()
            gain = 10
            if self.active_power_up == "double": gain *= 2
            self.current_score += gain; self.game_data['lifetime_score'] += gain
            self.ui.create_particles(self.food.pos[0] + config.STEP//2, self.food.pos[1] + config.STEP//2, config.WHITE)
            self.food.spawn(self.snake.body + [o.pos for o in self.obstacles])
            grow = True; self.check_level_up()
            sp_chance = 0.5 if self.boss_battle_active else config.SPECIAL_FOOD_SPAWN_CHANCE
            if not self.special_food.active and random.random() < sp_chance: self.special_food.spawn(self.snake.body + [o.pos for o in self.obstacles])
            # Shepu food spawn — more likely than special, less than normal
            if not self.shepu_food.active and random.random() < config.SHEPU_FOOD_SPAWN_CHANCE:
                self.shepu_food.spawn(self.snake.body, self.obstacles)
            if not self.power_up.active_on_field and not self.active_power_up and random.random() < config.POWER_UP_SPAWN_CHANCE:
                self.power_up.type = random.choice(config.POWER_UP_TYPES); self.power_up.spawn(self.snake.body, self.obstacles)
        
        if self.special_food.active:
            if snake_rect.colliderect(pygame.Rect(self.special_food.pos[0], self.special_food.pos[1], config.STEP, config.STEP)):
                self.assets.sounds['special_eat'].play()
                gain = 20
                if self.active_power_up == "double": gain *= 2
                self.current_score += gain; self.game_data['lifetime_score'] += gain
                self.ui.create_particles(self.special_food.pos[0] + config.STEP//2, self.special_food.pos[1] + config.STEP//2, config.GREEN)
                self.ui.trigger_shake(8, 300); self.special_food.active = False
                if self.boss_battle_active:
                    self.boss.health -= 1
                    if self.boss.health <= 0: self.defeat_boss()
                else: self.check_level_up()
            elif (pygame.time.get_ticks() - self.special_food.spawn_time) > config.SPECIAL_FOOD_DURATION * 1000: self.special_food.active = False

        # Shepu food collision & timeout
        if self.shepu_food.active:
            if snake_rect.colliderect(pygame.Rect(self.shepu_food.pos[0], self.shepu_food.pos[1], config.STEP, config.STEP)):
                self.assets.sounds['eat'].play()
                gain = config.SHEPU_FOOD_POINTS
                if self.active_power_up == "double": gain *= 2
                self.current_score += gain; self.game_data['lifetime_score'] += gain
                self.ui.create_particles(self.shepu_food.pos[0] + config.STEP//2, self.shepu_food.pos[1] + config.STEP//2, config.GOLD)
                self.ui.trigger_shake(5, 200); self.shepu_food.active = False
                self.check_level_up()
            elif (pygame.time.get_ticks() - self.shepu_food.spawn_time) > config.SHEPU_FOOD_DURATION * 1000:
                self.shepu_food.active = False
        
        if self.power_up.active_on_field:
            if snake_rect.colliderect(pygame.Rect(self.power_up.pos[0], self.power_up.pos[1], config.STEP, config.STEP)):
                self.active_power_up = self.power_up.type
                self.power_up_timer = config.POWER_UP_DURATION * 1000
                self.power_up_max_timer = self.power_up_timer
                self.power_up.active_on_field = False
                self.ui.trigger_shake(5, 150)
                self.ui.create_particles(self.power_up.pos[0] + config.STEP//2, self.power_up.pos[1] + config.STEP//2, config.CYAN)
            elif (pygame.time.get_ticks() - self.power_up.spawn_time) > 10000: self.power_up.active_on_field = False

        if self.current_score >= self.next_cut_food_score and not self.cut_food.active: self.cut_food.spawn(self.snake.body + [o.pos for o in self.obstacles])
        if self.cut_food.active:
            if snake_rect.colliderect(pygame.Rect(self.cut_food.pos[0], self.cut_food.pos[1], config.STEP, config.STEP)):
                self.assets.sounds['cut'].play(); self.ui.create_particles(self.cut_food.pos[0] + config.STEP//2, self.cut_food.pos[1] + config.STEP//2, config.BLUE)
                self.cut_food.active = False; self.next_cut_food_score += config.CUT_FOOD_INTERVAL
                if len(self.snake.body) > 2: del self.snake.body[-2:]
            elif (pygame.time.get_ticks() - self.cut_food.spawn_time) > config.CUT_FOOD_DURATION * 1000: self.cut_food.active = False; self.next_cut_food_score += config.CUT_FOOD_INTERVAL
        
            if not self.matrix_food.active and not self.matrix_active and random.random() < config.MATRIX_FOOD_SPAWN_CHANCE:
                # Pass all active entities to prevent overlap
                self.matrix_food.spawn(self.snake.body, self.obstacles + [self.food.pos, self.special_food.pos])

        if self.matrix_food.active:
            if snake_rect.colliderect(pygame.Rect(self.matrix_food.pos[0], self.matrix_food.pos[1], config.STEP, config.STEP)):
                self.matrix_active = True
                self.matrix_timer = config.MATRIX_EFFECT_DURATION * 1000
                self.matrix_food.active = False
                self.assets.sounds['special_eat'].play()
                self.ui.trigger_shake(12, 400)
                self.matrix_chars = []
                for _ in range(100):
                    self.matrix_chars.append({'x': random.randint(0, config.WIDTH), 'y': random.randint(0, config.HEIGHT), 'char': random.choice(['0', '1', '@']), 'speed': random.randint(2, 7)})

        self.snake.move(grow)
        ghost = (self.active_power_up == "ghost")
        snake_rect = pygame.Rect(self.snake.pos[0], self.snake.pos[1], config.STEP, config.STEP)
        if self.snake.check_collision(self.game_mode, ghost): self.game_over(); return
        if not ghost:
            for o in self.obstacles:
                if snake_rect.colliderect(pygame.Rect(o.pos[0], o.pos[1], config.STEP, config.STEP)):
                    self.game_over(); return

    def check_level_up(self):
        lvl = self.game_data['level']
        if (lvl + 1) in config.LEVEL_UP_SCORES and self.game_data['lifetime_score'] >= config.LEVEL_UP_SCORES[lvl + 1]:
            self.game_data['level'] += 1
            if self.game_data['level'] % config.BOSS_LEVEL_INTERVAL == 0: self.start_boss_battle()
            else:
                self.level_up_message = f"LEVEL {self.game_data['level']} UNLOCKED!"
                self.level_up_message_time = time.time(); self.data_manager.save_data(self.game_data); self.spawn_obstacles()

    def start_boss_battle(self):
        self.boss_battle_active = True; self.boss.reset(self.game_data['level']); self.boss.active = True
        self.obstacles = []; self.level_up_message = f"BOSS FIGHT LV{self.game_data['level']}!"
        self.level_up_message_time = time.time(); self.ui.trigger_shake(20, 1000)

    def defeat_boss(self):
        self.boss_battle_active = False; self.boss.active = False; self.current_score += 100; self.game_data['lifetime_score'] += 100
        self.level_up_message = "BOSS DEFEATED! +100 XP"; self.level_up_message_time = time.time()
        self.data_manager.save_data(self.game_data); self.spawn_obstacles(); self.ui.trigger_shake(15, 500)

    def game_over(self):
        self.state = "GAME_OVER"; self.game_over_timer = 3000; self.ui.trigger_shake(15, 500)
        self.assets.stop_music(); self.assets.sounds['game_over'].play()
        prev_best = self.game_data['high_scores'].get(self.game_mode, 0)
        if self.current_score > prev_best:
            self.game_data['high_scores'][self.game_mode] = self.current_score
            self.new_high_score = True
        self.data_manager.save_data(self.game_data)

    def draw(self):
        dt = self.clock.get_time()
        shake = self.ui.get_shake_offset()
        self.screen.fill(config.BLACK)
        skip_menu_bg = self.state in ("PLAYING", "PAUSED", "SWIPE_TUTORIAL")
        if not skip_menu_bg:
            bg = self.assets.images['background'].copy()
            if self.game_data.get('bg_effect', True):
                bg.fill((20, 20, 40), special_flags=pygame.BLEND_RGB_MULT)
            self.screen.blit(bg, (0, 0))
        
        mouse = pygame.mouse.get_pos()
        if self.state == "NAME_INPUT":
            self.ui.draw_overlay(self.screen, 200)
            mid_x = config.WIDTH // 2
            self.ui.draw_text(self.screen, "SHEPU'S SNAKE", self.ui.font_large, config.BLUE, mid_x, 100)
            self.ui.draw_text(self.screen, "Welcome! Please enter your name:", self.ui.font_small, config.GOLD, mid_x, 220)
            # Input box
            box_w, box_h = 340, 52
            box_rect = pygame.Rect(mid_x - box_w // 2, 255, box_w, box_h)
            pygame.draw.rect(self.screen, (20, 20, 35), box_rect, border_radius=10)
            pygame.draw.rect(self.screen, config.CYAN, box_rect, 2, border_radius=10)
            # Blinking cursor
            cursor = "|" if int(time.time() * 2) % 2 == 0 else ""
            display_text = self.name_input_text + cursor
            self.ui.draw_text(self.screen, display_text, self.ui.font_small, config.WHITE, mid_x, 282)
            self.ui.draw_text(self.screen, "Press ENTER to confirm  (max 20 characters)", self.ui.font_tiny, config.LIGHT_GRAY, mid_x, 340)

        elif self.state == "SUPPORT":
            self.ui.draw_overlay(self.screen, 210)
            mid_x = config.WIDTH // 2
            self.ui.draw_text(self.screen, "SUPPORT THE PROJECT", self.ui.font_mid, config.CYAN, mid_x, 55)
            pygame.draw.line(self.screen, config.CYAN, (mid_x - 200, 85), (mid_x + 200, 85), 1)
            # Info cards — use font_num_tiny (Verdana) so all chars render correctly
            info_y = 115
            card_texts_normal = [
                (">> INVEST / JOIN OUR TEAM", config.GOLD, self.ui.font_tiny),
                ("We're building the next big thing!", config.LIGHT_GRAY, self.ui.font_tiny),
                ("", None, None),
                ("[Mail]   shepu9462@gmail.com", config.CYAN, self.ui.font_num_tiny),
                ("[Web]    shepu1.github.io/s", config.CYAN, self.ui.font_num_tiny),
            ]
            for txt, col, fnt in card_texts_normal:
                if col and fnt:
                    self.ui.draw_text(self.screen, txt, fnt, col, mid_x, info_y)
                info_y += 28
            # Facebook QR image (right side)
            qr_size = 130
            qr_x = mid_x + 130
            qr_y = 300
            try:
                if not hasattr(self, '_fb_qr_img'):
                    from utils import resource_path
                    raw = pygame.image.load(resource_path("assets/images/Facebook.png")).convert_alpha()
                    self._fb_qr_img = pygame.transform.smoothscale(raw, (qr_size, qr_size))
                screen_surf = pygame.Surface((qr_size + 10, qr_size + 10), pygame.SRCALPHA)
                pygame.draw.rect(screen_surf, (255, 255, 255, 220), (0, 0, qr_size + 10, qr_size + 10), border_radius=8)
                self.screen.blit(screen_surf, (qr_x - 5, qr_y - 5))
                self.screen.blit(self._fb_qr_img, (qr_x, qr_y))
                self.ui.draw_text(self.screen, "Facebook QR", self.ui.font_tiny, config.LIGHT_GRAY, qr_x + qr_size // 2, qr_y + qr_size + 12)
            except Exception:
                pygame.draw.rect(self.screen, (30, 30, 50), (qr_x, qr_y, qr_size, qr_size), border_radius=8)
                pygame.draw.rect(self.screen, config.LIGHT_GRAY, (qr_x, qr_y, qr_size, qr_size), 1, border_radius=8)
                self.ui.draw_text(self.screen, "Facebook", self.ui.font_tiny, config.LIGHT_GRAY, qr_x + qr_size // 2, qr_y + qr_size // 2 - 10)
                self.ui.draw_text(self.screen, "QR Code", self.ui.font_tiny, config.LIGHT_GRAY, qr_x + qr_size // 2, qr_y + qr_size // 2 + 12)
            # Donate text
            self.ui.draw_text(self.screen, ">> DONATE & HELP US GROW", self.ui.font_tiny, config.GOLD, mid_x - 60, 310)
            self.ui.draw_text(self.screen, "Your support keeps this project alive!", self.ui.font_tiny, config.LIGHT_GRAY, mid_x - 60, 340)
            self.ui.draw_text(self.screen, "Contact us for investment & partnership.", self.ui.font_tiny, config.LIGHT_GRAY, mid_x - 60, 368)
            self.ui.draw_text(self.screen, "shepu9462@gmail.com", self.ui.font_num_tiny, config.CYAN, mid_x - 60, 398)
            for btn in self.support_buttons.values(): btn.draw(self.screen, mouse)

        elif self.state == "SPLASH":
            self.splash.draw(self.screen)
        elif self.state == "MENU":
            self.ui.draw_text(self.screen, "SHEPU'S SNAKE", self.ui.font_large, config.BLUE, config.WIDTH // 2 + shake[0], 100 + shake[1])
            self.ui.draw_text(self.screen, "CREATED BY SHEPU - PROFESSIONAL EDITION", self.ui.font_tiny, config.GOLD, config.WIDTH // 2 + shake[0], 160 + shake[1])
            for btn in self.menu_buttons.values(): btn.draw(self.screen, mouse)
            self.ui.draw_level_info(self.screen, self.game_data['level'], self.game_data['lifetime_score'], config.LEVEL_UP_SCORES.get(self.game_data['level']+1, 'MAX'))
        
        elif self.state == "GAME_OVER":
            self.ui.draw_overlay(self.screen, 220)
            self.ui.draw_text(self.screen, "GAME OVER", self.ui.font_large, config.RED,
                              config.WIDTH // 2 + shake[0], config.HEIGHT // 2 - 90 + shake[1])
            self.ui.draw_text(self.screen, f"SCORE: {self.current_score}", self.ui.font_num_mid, config.WHITE,
                              config.WIDTH // 2, config.HEIGHT // 2 - 10)
            best = self.game_data['high_scores'].get(self.game_mode, 0)
            self.ui.draw_text(self.screen, f"BEST:  {best}", self.ui.font_num_small, config.GOLD,
                              config.WIDTH // 2, config.HEIGHT // 2 + 50)
            if self.new_high_score:
                self.ui.draw_text(self.screen, "*** NEW HIGH SCORE! ***", self.ui.font_small, config.CYAN,
                                  config.WIDTH // 2, config.HEIGHT // 2 + 100)
            self.ui.draw_text(self.screen, "THANKS FOR PLAYING SHEPU'S CREATION!",
                              self.ui.font_tiny, config.LIGHT_GRAY, config.WIDTH // 2, config.HEIGHT // 2 + 145)

        elif self.state == "MODE":
            self.ui.draw_text(self.screen, "SELECT MODE", self.ui.font_mid, config.BLUE, config.WIDTH // 2, 120)
            for mode, btn in self.mode_buttons.items():
                btn.draw(self.screen, mouse)
                if mode == self.game_mode: pygame.draw.rect(self.screen, config.CYAN, btn.rect, 2, border_radius=12)

        elif self.state == "SKINS":
            self.ui.draw_text(self.screen, "SNAKE SKINS", self.ui.font_mid, config.BLUE, config.WIDTH // 2, 120)
            for s, btn in self.skin_buttons.items():
                if s != "back":
                    req = config.SKIN_UNLOCKS.get(s, 0)
                    unlocked = self.game_data["lifetime_score"] >= req
                    btn.color = config.BLUE if unlocked else config.DARK_GRAY
                    if unlocked:
                        btn.text = s.upper()
                        btn.font = self.ui.font_small
                    else:
                        btn.text = f"LOCK {req} XP"
                        btn.font = self.ui.font_num_tiny
                btn.draw(self.screen, mouse)
                if s == self.game_data["current_skin"]: pygame.draw.rect(self.screen, config.CYAN, btn.rect, 2, border_radius=12)

        elif self.state == "CONTROL_SELECT":
            self.ui.draw_overlay(self.screen, 210)
            mid_x = config.WIDTH // 2
            self.ui.draw_text(self.screen, "SELECT CONTROL", self.ui.font_mid, config.CYAN, mid_x, 90)
            self.ui.draw_text(self.screen, "আপনার পছন্দের নিয়ন্ত্রণ পদ্ধতি বেছে নিন", self.ui.font_tiny, config.LIGHT_GRAY, mid_x, 140)
            for key, btn in self.control_select_buttons.items():
                btn.draw(self.screen, mouse)
                if key in (CONTROL_SWIPE, CONTROL_CORNER, CONTROL_SPLIT) and self.game_data.get("control_mode") == key:
                    pygame.draw.rect(self.screen, config.GOLD, btn.rect, 2, border_radius=12)

        elif self.state == "SETTINGS":
            self.ui.draw_text(self.screen, "SETTINGS", self.ui.font_mid, config.BLUE, config.WIDTH // 2, 50)
            lx, rx = config.WIDTH // 2 - 150, config.WIDTH // 2 + 150
            self.ui.draw_text(self.screen, f"SPEED: {config.FPS}", self.ui.font_num_tiny, config.WHITE, lx, 110)
            self.ui.draw_text(self.screen, f"SIZE: {config.STEP}", self.ui.font_num_tiny, config.WHITE, lx, 190)
            self.ui.draw_text(self.screen, "VISUAL STYLE", self.ui.font_tiny, config.WHITE, lx, 270)
            self.draw_volume_bar(self.screen, 110, rx, "MUSIC VOLUME", self.assets.music_volume)
            self.draw_volume_bar(self.screen, 190, rx, "SOUND VOLUME", self.assets.sound_volume)
            self.ui.draw_text(self.screen, "SELECT MUSIC TRACK", self.ui.font_tiny, config.WHITE, rx, 270)
            self.ui.draw_text(self.screen, "MOVEMENT STYLE", self.ui.font_tiny, config.WHITE, rx, 360)
            self.ui.draw_text(self.screen, "TOUCH CONTROLS", self.ui.font_tiny, config.WHITE, lx, 420)
            for btn in self.settings_buttons.values(): btn.draw(self.screen, mouse)

        elif self.state == "HIGH_SCORE":
            mid_x = config.WIDTH // 2
            self.ui.draw_text(self.screen, "HALL OF FAME", self.ui.font_mid, config.BLUE, mid_x, 120)
            # Player name at top - use font_num_small so * renders correctly
            player = self.game_data.get('player_name', 'PLAYER')
            self.ui.draw_text(self.screen, f"*  {player.upper()}  *", self.ui.font_num_small, config.GOLD, mid_x, 185)
            pygame.draw.line(self.screen, config.GOLD, (mid_x - 140, 210), (mid_x + 140, 210), 1)
            y = 240
            for m, sc in self.game_data['high_scores'].items():
                self.ui.draw_text(self.screen, f"{m.upper()}: {sc}", self.ui.font_num_small, config.WHITE, mid_x, y); y += 55
            self.ui.draw_text(self.screen, "Press any key to return", self.ui.font_tiny, config.LIGHT_GRAY, mid_x, 490)

        elif self.state in ["PLAYING", "PAUSED", "SWIPE_TUTORIAL"]:
            pa = self.control_manager.play_area
            play_rect = pa.game_rect()
            bg = self.assets.images['background'].copy()
            if self.game_data.get('bg_effect', True):
                bg.fill((20, 20, 40), special_flags=pygame.BLEND_RGB_MULT)
            if pa.control_mode == CONTROL_SPLIT:
                play_bg = pygame.transform.smoothscale(bg, (pa.play_w, pa.play_h))
                self.screen.blit(play_bg, (pa.offset_x, pa.offset_y))
            else:
                self.screen.blit(bg, (0, 0))

            prev_clip = self.screen.get_clip()
            self.screen.set_clip(play_rect)
            speed_mult = 0.5 if self.active_power_up == "slowmo" else 1.0
            move_delay = (1000 // config.FPS) / speed_mult
            interp = min(1.0, self.move_timer / move_delay)
            
            for o in self.obstacles: o.draw(self.screen, self.assets, offset=shake)
            self.snake.draw(self.screen, self.assets, self.game_data["current_skin"], offset=shake, interp=interp, style=self.game_data.get('movement_style', 'Robotic'))
            self.screen.blit(self.assets.images['food'], (self.food.pos[0] + shake[0], self.food.pos[1] + shake[1]))
            if self.special_food.active: self.screen.blit(self.assets.images['special_food'], (self.special_food.pos[0] + shake[0], self.special_food.pos[1] + shake[1]))
            if self.shepu_food.active: self.shepu_food.draw(self.screen, self.assets, offset=shake)
            if self.matrix_food.active: self.matrix_food.draw(self.screen, self.assets, offset=shake)
            if self.cut_food.active: self.screen.blit(self.assets.images['cut_food'], (self.cut_food.pos[0] + shake[0], self.cut_food.pos[1] + shake[1]))
            
            if self.matrix_active:
                overlay = pygame.Surface((config.WIDTH, config.HEIGHT))
                overlay.set_alpha(160)
                overlay.fill((0, 0, 0))
                self.screen.blit(overlay, (0,0))
                for c in self.matrix_chars:
                    c['y'] = (c['y'] + c['speed']) % config.HEIGHT
                    self.ui.draw_text(self.screen, c['char'], self.ui.font_num_tiny, (0, 255, 70), c['x'], c['y'], shadow=False)
                if int(time.time() * 4) % 2 == 0:
                    self.ui.draw_text(self.screen, "SYSTEM HACKED - MATRIX MODE", self.ui.font_small, (0, 255, 0), config.WIDTH // 2, 110)
            if self.power_up.active_on_field: self.power_up.draw(self.screen, self.assets, offset=shake)
            if self.boss.active: self.boss.draw(self.screen, self.assets, offset=shake)

            if self.night_alpha > 0:
                self.darkness.fill((0, 0, 0, self.night_alpha))
                hc = (self.snake.pos[0] + config.STEP // 2 + shake[0], self.snake.pos[1] + config.STEP // 2 + shake[1])
                vr = config.VISION_RADIUS
                for r in range(vr, 0, -15):
                    alpha = self.night_alpha - int((r / vr) * self.night_alpha)
                    pygame.draw.circle(self.darkness, (0, 0, 0, alpha), hc, r)
                self.screen.blit(self.darkness, (0, 0))

            self.ui.draw_text(self.screen, f'SCORE: {self.current_score}', self.ui.font_num_small, config.WHITE, config.WIDTH - 20, 40 + shake[1], center=False, align="right")
            self.ui.draw_level_info(self.screen, self.game_data['level'], self.game_data['lifetime_score'], config.LEVEL_UP_SCORES.get(self.game_data['level']+1, 'MAX'))
            
            if self.game_mode == "Time Attack":
                tl = max(0, config.TIME_ATTACK_DURATION - (time.time() - (self.start_time if self.state == "PLAYING" else self.pause_start_time)))
                self.ui.draw_text(self.screen, f'TIME: {int(tl)}s', self.ui.font_num_mid, config.RED, config.WIDTH // 2, 40)
            
            if time.time() - self.level_up_message_time < 3: self.ui.draw_text(self.screen, self.level_up_message, self.ui.font_small, config.GOLD, config.WIDTH // 2, 160)
            if self.boss_battle_active: self.ui.draw_text(self.screen, f"BOSS HP: {self.boss.health}", self.ui.font_num_mid, config.RED, config.WIDTH // 2, config.HEIGHT - 50)
            if self.moving_event_active: self.ui.draw_text(self.screen, f"STORM: {int(self.moving_event_timer/1000)}s", self.ui.font_num_tiny, config.RED, config.WIDTH // 2, 60)
            if self.active_power_up:
                c = config.CYAN if self.active_power_up == "slowmo" else (config.PURPLE if self.active_power_up == "ghost" else config.YELLOW)
                label = f"{self.active_power_up.upper()}: {int(self.power_up_timer/1000)}s"
                self.ui.draw_text(self.screen, label, self.ui.font_num_tiny, c, config.WIDTH // 2, 75)
                bar_w = 120
                bar_x = config.WIDTH // 2 - bar_w // 2
                bar_y = 44
                frac = max(0, self.power_up_timer / max(1, getattr(self, 'power_up_max_timer', config.POWER_UP_DURATION * 1000)))
                pygame.draw.rect(self.screen, (30, 30, 50), (bar_x, bar_y, bar_w, 6), border_radius=3)
                pygame.draw.rect(self.screen, c, (bar_x, bar_y, int(bar_w * frac), 6), border_radius=3)

            if self.state == "PAUSED":
                self.ui.draw_overlay(self.screen, 200)
                self.ui.draw_text(self.screen, "GAME PAUSED", self.ui.font_mid, config.WHITE, config.WIDTH // 2, 140)
                self.ui.draw_text(self.screen, f"SCORE: {self.current_score}", self.ui.font_num_small, config.GOLD,
                                  config.WIDTH // 2, 195)
                for btn in self.pause_buttons.values(): btn.draw(self.screen, mouse)

            self.screen.set_clip(prev_clip)
            tutorial_alpha = 255
            if self.state == "SWIPE_TUTORIAL":
                tutorial_alpha = max(80, int(255 * (self.swipe_tutorial_timer / 2000)))
            self.control_manager.draw(self.screen, self.state, swipe_tutorial_alpha=tutorial_alpha)

        self.ui.draw_particles(self.screen, offset=shake)
        if self.state not in ("PLAYING", "SWIPE_TUTORIAL") and not is_android():
            self.draw_custom_cursor(mouse, dt)
        pygame.display.update()

    def draw_volume_bar(self, surf, y, x, title, vol):
        self.ui.draw_text(surf, title, self.ui.font_tiny, config.WHITE, x, y - 25)
        pygame.draw.rect(surf, (30, 30, 50), (x - 100, y, 200, 10), border_radius=5)
        pygame.draw.rect(surf, config.CYAN, (x - 100, y, 200 * vol, 10), border_radius=5)

    def pre_render_cursor(self):
        surf = pygame.Surface((32, 32), pygame.SRCALPHA)
        pts = [(0, 0), (0, 17), (5, 13), (8, 20), (11, 18), (8, 12), (13, 12)]
        pygame.draw.polygon(surf, (0, 0, 0, 150), [(p[0]+1, p[1]+1) for p in pts])
        pygame.draw.polygon(surf, (57, 255, 20), pts)
        pygame.draw.polygon(surf, (0, 80, 0), pts, 1)
        return surf

    def draw_custom_cursor(self, mouse_pos, dt):
        try:
            mx, my = mouse_pos
            self.screen.blit(self.cursor_surf, (mx, my))
        except Exception:
            pass
