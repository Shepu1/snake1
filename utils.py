import os
import sys
import config


def is_android():
    if "android" in sys.platform.lower():
        return True
    if os.environ.get("ANDROID_ARGUMENT"):
        return True
    try:
        from jnius import autoclass  # noqa: F401 — python-for-android
        return True
    except Exception:
        return False


def get_android_display_size():
    try:
        from jnius import autoclass
        PythonActivity = autoclass("org.kivy.android.PythonActivity")
        metrics = PythonActivity.mActivity.getResources().getDisplayMetrics()
        return int(metrics.widthPixels), int(metrics.heightPixels)
    except Exception:
        return config.WIDTH, config.HEIGHT


def resource_path(relative_path):
    if hasattr(sys, "_MEIPASS"):
        return os.path.join(sys._MEIPASS, relative_path)
    base_path = os.path.dirname(os.path.abspath(__file__))
    if not os.path.exists(os.path.join(base_path, relative_path)):
        base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)


def get_data_path(filename):
    if getattr(sys, "frozen", False):
        base_path = os.path.dirname(sys.executable)
    elif is_android():
        try:
            from android.storage import app_storage_path
            base_path = app_storage_path()
        except Exception:
            base_path = os.path.dirname(os.path.abspath(__file__))
    else:
        base_path = os.path.dirname(os.path.abspath(__file__))
    return os.path.join(base_path, filename)


class DataManager:
    def __init__(self, filename="game_data.txt"):
        self.filename = get_data_path(filename)

    def load_data(self):
        data = {
            "level": 1,
            "lifetime_score": 0,
            "high_scores": {"Classic": 0, "Time Attack": 0, "No Wall": 0},
            "current_skin": "classic",
            "game_mode": "Classic",
            "movement_style": "Robotic",
            "fps": 10,
            "step": 30,
            "music_volume": 0.5,
            "sound_volume": 0.5,
            "music_index": 0,
            "bg_effect": True,
            "player_name": "",
            "control_mode": config.DEFAULT_CONTROL_MODE,
            "control_setup_done": False,
            "joystick_side": config.DEFAULT_JOYSTICK_SIDE,
        }
        if os.path.exists(self.filename):
            try:
                with open(self.filename, "r") as f:
                    lines = f.readlines()
                    for line in lines:
                        parts = line.strip().split(":")
                        if len(parts) == 2:
                            key, value = parts
                            if key in ["level", "lifetime_score", "fps", "step", "music_index"]:
                                data[key] = int(value)
                            elif key in ["music_volume", "sound_volume"]:
                                data[key] = float(value)
                            elif key == "bg_effect":
                                data[key] = value == "True"
                            elif key == "control_setup_done":
                                data[key] = value == "True"
                            elif key in ["current_skin", "game_mode", "movement_style", "player_name", "control_mode", "joystick_side"]:
                                data[key] = value
                            elif key in data["high_scores"]:
                                data["high_scores"][key] = int(value)
            except Exception:
                pass
        return data

    def save_data(self, data):
        try:
            with open(self.filename, "w") as f:
                f.write(f"level:{data['level']}\n")
                f.write(f"lifetime_score:{data['lifetime_score']}\n")
                f.write(f"current_skin:{data['current_skin']}\n")
                f.write(f"game_mode:{data['game_mode']}\n")
                f.write(f"movement_style:{data.get('movement_style', 'Robotic')}\n")
                f.write(f"fps:{data['fps']}\n")
                f.write(f"step:{data['step']}\n")
                f.write(f"music_volume:{data['music_volume']}\n")
                f.write(f"sound_volume:{data['sound_volume']}\n")
                f.write(f"music_index:{data['music_index']}\n")
                f.write(f"bg_effect:{data['bg_effect']}\n")
                f.write(f"player_name:{data.get('player_name', '')}\n")
                f.write(f"control_mode:{data.get('control_mode', config.DEFAULT_CONTROL_MODE)}\n")
                f.write(f"control_setup_done:{data.get('control_setup_done', False)}\n")
                f.write(f"joystick_side:{data.get('joystick_side', config.DEFAULT_JOYSTICK_SIDE)}\n")
                for mode, score in data["high_scores"].items():
                    f.write(f"{mode}:{score}\n")
        except Exception:
            pass
