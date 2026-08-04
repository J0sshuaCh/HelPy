"""
Renderizado de hotkeys para tooltips y mensajes.

La notación de pynput ("<alt_gr>+g") se traduce a texto legible ("AltGr + G").
Es la única fuente para mostrar hotkeys en la interfaz, para que las pistas
nunca contradigan la configuración actual tras remapear.
"""
from app.ui.shared.settings import ui_settings

_MODIFIER_LABELS = {
    "alt_gr": "AltGr",
    "altgr": "AltGr",
    "ctrl": "Ctrl",
    "control": "Ctrl",
    "alt": "Alt",
    "shift": "Shift",
    "cmd": "Win",
    "super": "Win",
    "win": "Win",
    "space": "Espacio",
}


def format_hotkey(hotkey):
    """Convierte notación pynput ('<alt_gr>+g') a texto legible ('AltGr + G')."""
    if not hotkey:
        return ""
    tokens = [token.strip() for token in hotkey.split("+") if token.strip()]
    parts = []
    for token in tokens:
        core = token.strip().strip("<>").lower()
        label = _MODIFIER_LABELS.get(core)
        if label:
            parts.append(label)
            continue
        key = token[1:-1] if token.startswith("<") and token.endswith(">") else token
        if key.lower() == "space":
            parts.append("Espacio")
        elif len(key) == 1:
            parts.append(key.upper())
        else:
            parts.append(key.replace("_", " ").title())
    return " + ".join(parts) if parts else hotkey


def get_hotkey_display(action):
    """Hotkey actual legible para una acción (la configurada o la por defecto)."""
    from app.ui.overlay_window.hotkeys import DEFAULT_HOTKEYS

    current = ui_settings.get("hotkeys", {}).get(action) or DEFAULT_HOTKEYS.get(action, "")
    return format_hotkey(current)
