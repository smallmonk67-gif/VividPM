import os
import json

class ConfigManager:
    _instance = None
    _config_path = os.path.expanduser("~/.config/vividpm/vivid_config.json")
    
    DEFAULT_CONFIG = {
        "theme": "System",
        "accent_color": "blue",
        "startup_scan": True,
        "show_warnings": True
    }

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super(ConfigManager, cls).__new__(cls)
            cls._instance.config = cls.DEFAULT_CONFIG.copy()
            cls._instance.load()
        return cls._instance

    def load(self):
        if os.path.exists(self._config_path):
            try:
                with open(self._config_path, "r") as f:
                    data = json.load(f)
                    self.config.update(data)
            except Exception as e:
                print(f"Error loading config: {e}")
        else:
            self.save() # Create default config file

    def save(self):
        os.makedirs(os.path.dirname(self._config_path), exist_ok=True)
        try:
            with open(self._config_path, "w") as f:
                json.dump(self.config, f, indent=4)
        except Exception as e:
            print(f"Error saving config: {e}")

    def get(self, key, default=None):
        return self.config.get(key, default)

    def set(self, key, value):
        self.config[key] = value
        self.save()

# Global singleton accessor
config_manager = ConfigManager()
