import json
import os
from typing import Dict, Any

from app.utils.path_utils import writable_config_path

class SettingsBase:
    def __init__(self, filename: str = "ui_settings.json"):
        self.filename = filename
        self.settings: Dict[str, Any] = self._load_settings()

    def _config_path(self) -> str:
        return writable_config_path(self.filename)

    def _load_settings(self) -> Dict[str, Any]:
        path = self._config_path()
        if not os.path.exists(path):
            return {}
        try:
            with open(path, "r", encoding="utf-8") as handle:
                return json.load(handle)
        except (OSError, json.JSONDecodeError):
            return {}

    def _save_settings(self):
        path = self._config_path()
        folder = os.path.dirname(path)
        os.makedirs(folder, exist_ok=True)
        try:
            with open(path, "w", encoding="utf-8") as handle:
                json.dump(self.settings, handle, indent=2)
        except OSError:
            pass

    def get(self, key: str, default: Any = None) -> Any:
        return self.settings.get(key, default)

    def set(self, key: str, value: Any):
        self.settings[key] = value
        self._save_settings()

# Default singleton for UI settings
ui_settings = SettingsBase()
