import os
import pygame
import sys
from config import WIDTH, HEIGHT
from engine import GameEngine
from utils import is_android, get_android_display_size


def main():
    if is_android():
        os.environ["SDL_ANDROID_TRAP_BACK_BUTTON"] = "1"

    pygame.init()
    pygame.mixer.init()

    if is_android():
        import config
        w, h = get_android_display_size()
        config.WIDTH, config.HEIGHT = w, h
        screen = pygame.display.set_mode((w, h), pygame.FULLSCREEN)
        pygame.mouse.set_visible(False)
    else:
        screen = pygame.display.set_mode((WIDTH, HEIGHT), pygame.RESIZABLE)

    pygame.display.set_caption("Shepu's Snake Game - Professional Edition")

    if not is_android():
        try:
            from utils import resource_path
            icon = pygame.image.load(resource_path("snake.png"))
            icon = pygame.transform.smoothscale(icon, (32, 32))
            pygame.display.set_icon(icon)
        except Exception:
            try:
                from utils import resource_path
                icon = pygame.image.load(resource_path("snake.ico"))
                pygame.display.set_icon(icon)
            except Exception:
                pass

    engine = GameEngine(screen)

    while engine.running:
        engine.handle_events()
        engine.update()
        engine.draw()

    pygame.quit()
    sys.exit()


if __name__ == "__main__":
    main()
