from pynput import keyboard
from PyQt5.QtCore import QTimer
from app.ui.shared import ui_settings
from app.ui.shared.hotkeys_display import format_hotkey
from app.utils.logger import get_logger

logger = get_logger(__name__)


# Valores por defecto de hotkeys
DEFAULT_HOTKEYS = {
    "send_llm": "<alt_gr>+\\",
    "toggle_record": "<alt_gr>+g",
    "toggle_collapse": "<alt_gr>+h",
}

# Descripción legible de las hotkeys
HOTKEY_DESCRIPTIONS = {
    "send_llm": "Enviar a IA",
    "toggle_record": "Iniciar/Detener grabación",
    "toggle_collapse": "Colapsar/Expandir ventana",
}


class HotkeyManager:
    def __init__(self, window):
        self.window = window
        self.hotkeys = None
        self._custom_hotkeys = ui_settings.get("hotkeys", {})
        self._on_change_callbacks = []
        self.init_hotkeys(clear_custom=True)

    def _get_hotkey(self, action: str) -> str:
        """Obtiene la hotkey configurada para una acción."""
        return self._custom_hotkeys.get(action, DEFAULT_HOTKEYS.get(action, ""))

    def get_hotkey_display(self, action: str) -> str:
        """Hotkey actual legible para una acción."""
        return format_hotkey(self._get_hotkey(action))

    def register_on_change(self, callback):
        """Registra un callback que se invoca cuando cambian las hotkeys."""
        if callback not in self._on_change_callbacks:
            self._on_change_callbacks.append(callback)

    def _notify_changed(self):
        for callback in self._on_change_callbacks:
            try:
                callback()
            except Exception:
                logger.exception("Error al refrescar hotkeys en la interfaz")

    def init_hotkeys(self, clear_custom=False):
        def on_activate():
            QTimer.singleShot(0, self.window.assistant.send_buffer_to_llm)

        def on_toggle_record():
            QTimer.singleShot(0, self.window.toggle_recording)

        def on_toggle_collapse():
            QTimer.singleShot(0, self.window.toggle_collapsed)

        hotkey_map = {
            self._get_hotkey("send_llm"): on_activate,
            self._get_hotkey("toggle_record"): on_toggle_record,
            self._get_hotkey("toggle_collapse"): on_toggle_collapse,
        }

        try:
            self.hotkeys = keyboard.GlobalHotKeys(hotkey_map)
            self.hotkeys.start()
            return True
        except Exception:
            logger.exception("Error al registrar los atajos configurados; se usan los por defecto")
            # Fallback a hotkeys por defecto
            try:
                self.hotkeys = keyboard.GlobalHotKeys({
                    DEFAULT_HOTKEYS["send_llm"]: on_activate,
                    DEFAULT_HOTKEYS["toggle_record"]: on_toggle_record,
                    DEFAULT_HOTKEYS["toggle_collapse"]: on_toggle_collapse,
                })
                self.hotkeys.start()
            except Exception:
                logger.exception("Error al registrar incluso los atajos por defecto")
                self.hotkeys = None
            if clear_custom and self._custom_hotkeys:
                # Los atajos configurados no se pudieron registrar: se descartan.
                self._custom_hotkeys = {}
                ui_settings.set("hotkeys", {})
                try:
                    if hasattr(self.window, "_set_warning"):
                        self.window._set_warning(
                            "No se pudieron cargar los atajos de teclado configurados. "
                            "Se usan los atajos por defecto."
                        )
                except Exception:
                    logger.exception("Error al mostrar el aviso de atajos por defecto")
            self._notify_changed()
            return False

    def update_hotkey(self, action: str, new_hotkey: str):
        """Actualiza una hotkey y reinicia el listener. Revierte si el registro falla."""
        if action not in DEFAULT_HOTKEYS:
            return False
        
        previous = dict(self._custom_hotkeys)
        self._custom_hotkeys[action] = new_hotkey
        ui_settings.set("hotkeys", self._custom_hotkeys)
        
        # Reiniciar hotkeys
        self.stop()
        success = self.init_hotkeys()
        if not success:
            # El atajo inválido no debe quedar guardado ni mostrarse en la interfaz.
            self._custom_hotkeys = previous
            ui_settings.set("hotkeys", previous)
            self.stop()
            self.init_hotkeys()
            self._notify_changed()
            return False
        self._notify_changed()
        return True

    def reset_hotkeys(self):
        """Restaura hotkeys por defecto."""
        self._custom_hotkeys = {}
        ui_settings.set("hotkeys", {})
        self.stop()
        self.init_hotkeys()
        self._notify_changed()

    def get_current_hotkeys(self) -> dict:
        """Retorna las hotkeys actuales."""
        result = {}
        for action in DEFAULT_HOTKEYS:
            result[action] = self._get_hotkey(action)
        return result

    def stop(self):
        if self.hotkeys:
            self.hotkeys.stop()
