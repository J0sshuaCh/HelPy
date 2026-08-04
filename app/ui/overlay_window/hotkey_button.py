from PyQt5.QtWidgets import QPushButton, QWidget, QHBoxLayout, QSizePolicy
from PyQt5.QtCore import Qt, pyqtSignal
from app.ui.shared.hotkeys_display import format_hotkey

_MODIFIER_KEYS = {
    Qt.Key_Control, Qt.Key_Shift, Qt.Key_Alt, Qt.Key_Meta,
    Qt.Key_AltGr, Qt.Key_Super_L, Qt.Key_Super_R,
}

_NAMED_KEYS = {
    Qt.Key_Space: "space",
    Qt.Key_Return: "enter",
    Qt.Key_Enter: "enter",
    Qt.Key_Tab: "tab",
    Qt.Key_Backspace: "backspace",
    Qt.Key_Delete: "delete",
    Qt.Key_Escape: "esc",
    Qt.Key_Home: "home",
    Qt.Key_End: "end",
    Qt.Key_PageUp: "page_up",
    Qt.Key_PageDown: "page_down",
    Qt.Key_Insert: "insert",
    Qt.Key_Up: "up",
    Qt.Key_Down: "down",
    Qt.Key_Left: "left",
    Qt.Key_Right: "right",
    Qt.Key_F1: "f1", Qt.Key_F2: "f2", Qt.Key_F3: "f3",
    Qt.Key_F4: "f4", Qt.Key_F5: "f5", Qt.Key_F6: "f6",
    Qt.Key_F7: "f7", Qt.Key_F8: "f8", Qt.Key_F9: "f9",
    Qt.Key_F10: "f10", Qt.Key_F11: "f11", Qt.Key_F12: "f12",
}


def _qt_key_to_pynput(key: int, modifiers: int, text: str) -> str | None:
    mod_parts = []
    if modifiers & Qt.ControlModifier:
        mod_parts.append("<ctrl>")
    if modifiers & Qt.ShiftModifier:
        mod_parts.append("<shift>")
    if modifiers & Qt.AltModifier:
        mod_parts.append("<alt_gr>")
    if modifiers & Qt.MetaModifier:
        mod_parts.append("<cmd>")

    if not mod_parts:
        return None

    if key in _NAMED_KEYS:
        key_str = "<" + _NAMED_KEYS[key] + ">"
    elif Qt.Key_A <= key <= Qt.Key_Z:
        key_str = chr(key).lower()
    elif Qt.Key_0 <= key <= Qt.Key_9:
        key_str = chr(key)
    else:
        char = text
        if char and len(char) == 1 and 0x20 <= ord(char) <= 0x7e:
            key_str = char
        else:
            return None

    mod_parts.append(key_str)
    return "+".join(mod_parts)


class HotkeyCaptureButton(QPushButton):
    hotkey_changed = pyqtSignal(str, str)

    def __init__(self, action: str, parent: QWidget | None = None):
        super().__init__(parent)
        self.action = action
        self._pynput_value = ""
        self._recording = False
        self._previous_value = ""
        self.setCheckable(False)
        self.setFocusPolicy(Qt.StrongFocus)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.setMinimumHeight(32)
        self.setCursor(Qt.PointingHandCursor)
        self._update_display()

    def _update_display(self):
        if self._recording:
            self.setText("Presiona la combinación...")
            self.setToolTip("Presiona Escape para cancelar")
        elif self._pynput_value:
            self.setText(format_hotkey(self._pynput_value))
            self.setToolTip(self._pynput_value)
        else:
            self.setText("Haz clic para establecer atajo")
            self.setToolTip("Haz clic y presiona la combinación de teclas deseada")

    def set_pynput_hotkey(self, value: str):
        self._pynput_value = value
        self._update_display()
        self._clear_invalid()

    def get_pynput_hotkey(self) -> str:
        return self._pynput_value

    def clear_hotkey(self):
        self._pynput_value = ""
        self._update_display()
        self._clear_invalid()
        self.hotkey_changed.emit(self.action, "")

    def set_invalid(self, message: str):
        self.setProperty("invalid", True)
        self.setToolTip(message)
        self.style().unpolish(self)
        self.style().polish(self)

    def _clear_invalid(self):
        if self.property("invalid"):
            self.setProperty("invalid", False)
            self.style().unpolish(self)
            self.style().polish(self)

    def mousePressEvent(self, event):
        if not self._recording:
            self._start_recording()
        else:
            self._cancel_recording()

    def _start_recording(self):
        self._previous_value = self._pynput_value
        self._recording = True
        self._clear_invalid()
        self._update_display()
        self.grabKeyboard()
        self.setFocus()

    def _cancel_recording(self):
        self._pynput_value = self._previous_value
        self._stop_recording()

    def _stop_recording(self):
        self._recording = False
        self.releaseKeyboard()
        self._update_display()

    def keyPressEvent(self, event):
        if not self._recording:
            super().keyPressEvent(event)
            return

        key = event.key()
        modifiers = event.modifiers()

        if key == Qt.Key_Escape:
            self._cancel_recording()
            return

        if key in _MODIFIER_KEYS:
            return

        text = event.text()
        pynput_str = _qt_key_to_pynput(key, modifiers, text)
        if pynput_str:
            self._pynput_value = pynput_str
            self._stop_recording()
            self.hotkey_changed.emit(self.action, pynput_str)
        else:
            self._cancel_recording()

    def focusOutEvent(self, event):
        if self._recording:
            self._cancel_recording()
        super().focusOutEvent(event)


class HotkeyRow(QWidget):
    hotkey_changed = pyqtSignal(str, str)

    def __init__(self, action: str, description: str, parent: QWidget | None = None):
        super().__init__(parent)
        self._action = action
        layout = QHBoxLayout(self)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(4)

        self.capture_btn = HotkeyCaptureButton(action, self)
        self.capture_btn.hotkey_changed.connect(self._on_hotkey_changed)

        self.clear_btn = QPushButton("✕", self)
        self.clear_btn.setObjectName("clearHotkeyBtn")
        self.clear_btn.setFixedSize(24, 24)
        self.clear_btn.setToolTip("Quitar atajo")
        self.clear_btn.setCursor(Qt.PointingHandCursor)
        self.clear_btn.clicked.connect(self._on_clear)

        layout.addWidget(self.capture_btn, 1)
        layout.addWidget(self.clear_btn, 0)

    def _on_hotkey_changed(self, action: str, pynput_str: str):
        self.hotkey_changed.emit(action, pynput_str)

    def _on_clear(self):
        self.capture_btn.clear_hotkey()

    def set_pynput_hotkey(self, value: str):
        self.capture_btn.set_pynput_hotkey(value)

    def get_pynput_hotkey(self) -> str:
        return self.capture_btn.get_pynput_hotkey()

    def set_invalid(self, message: str):
        self.capture_btn.set_invalid(message)

    def _clear_invalid(self):
        self.capture_btn._clear_invalid()
