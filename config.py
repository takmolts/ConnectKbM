import os
import yaml

CONFIG_FILE = "config.yaml"

class Config:
    def __init__(self):
        self.settings = {
            "connection_mode": "usb",  # options: "usb" (OTG), "wifi" (ADB TCP/IP)
            "trigger_edge": "right",  # options: "left", "right", "top", "bottom", "none"
            "shortcut_toggle": "alt+f1",
            "shortcut_home": "ctrl+shift+h",
            "shortcut_back": "ctrl+shift+b",
            "shortcut_recent": "ctrl+shift+r",
            "shortcut_lock": "ctrl+shift+l",
            "shortcut_vol_up": "ctrl+up",
            "shortcut_vol_down": "ctrl+down",
            "mouse_sensitivity": 1.0,
            "device_serial": None # Auto-detect if None
        }
        self.load()

    def load(self):
        if os.path.exists(CONFIG_FILE):
            try:
                with open(CONFIG_FILE, 'r', encoding='utf-8') as f:
                    user_settings = yaml.safe_load(f)
                    if user_settings:
                        self.settings.update(user_settings)
            except Exception as e:
                print(f"Error loading config: {e}")

    def save(self):
        try:
            with open(CONFIG_FILE, 'w', encoding='utf-8') as f:
                yaml.dump(self.settings, f, default_flow_style=False)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.settings.get(key, default)

config = Config()
