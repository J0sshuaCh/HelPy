from pynput import keyboard
from app.ui.shared import ui_settings


# Valores por defecto de hotkeys
DEFAULT_HOTKEYS = {
    "send_llm": "<alt_gr>+\\",
    "toggle_record": "<alt_gr>+g",
    "toggle_collapse": "<alt_gr>+h",
}

# Descripción legible de las hotkeys
HOTKEY_DESCRIPTIONS = {
    "send_llm": "Enviar a LLM",
    "toggle_record": "Iniciar/Detener grabación",
    "toggle_collapse": "Colapsar/Expandir ventana",
}


class HotkeyManager:
    def __init__(self, window):
        self.window = window
        self.hotkeys = None
        self._custom_hotkeys = ui_settings.get("hotkeys", {})
        self.init_hotkeys()

    def _get_hotkey(self, action: str) -> str:
        """Obtiene la hotkey configurada para una acción."""
        return self._custom_hotkeys.get(action, DEFAULT_HOTKEYS.get(action, ""))

    def init_hotkeys(self):
        def on_activate():
            self.window.assistant.send_buffer_to_llm()

        def on_toggle_record():
            self.window.toggle_recording()

        def on_toggle_collapse():
            self.window.toggle_collapsed()

        hotkey_map = {
            self._get_hotkey("send_llm"): on_activate,
            self._get_hotkey("toggle_record"): on_toggle_record,
            self._get_hotkey("toggle_collapse"): on_toggle_collapse,
        }

        try:
            self.hotkeys = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkeys.start()
        except Exception as e:
            print(f"Error al registrar hotkeys: {e}")
            # Fallback a hotkeys por defecto
            self.hotkeys = keyboard.GlobalHotKeys({
                DEFAULT_HOTKEYS["send_llm"]: on_activate,
                DEFAULT_HOTKEYS["toggle_record"]: on_toggle_record,
                DEFAULT_HOTKEYS["toggle_collapse"]: on_toggle_collapse,
            })
            self.hotkeys.start()

    def update_hotkey(self, action: str, new_hotkey: str):
        """Actualiza una hotkey y reinicia el listener."""
        if action not in DEFAULT_HOTKEYS:
            return False
        
        self._custom_hotkeys[action] = new_hotkey
        ui_settings.set("hotkeys", self._custom_hotkeys)
        
        # Reiniciar hotkeys
        self.stop()
        self.init_hotkeys()
        return True

    def reset_hotkeys(self):
        """Restaura hotkeys por defecto."""
        self._custom_hotkeys = {}
        ui_settings.set("hotkeys", {})
        self.stop()
        self.init_hotkeys()

    def get_current_hotkeys(self) -> dict:
        """Retorna las hotkeys actuales."""
        result = {}
        for action in DEFAULT_HOTKEYS:
            result[action] = self._get_hotkey(action)
        return result

    def stop(self):
        if self.hotkeys:
            self.hotkeys.stop()
