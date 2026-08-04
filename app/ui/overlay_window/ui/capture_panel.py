from PyQt5.QtWidgets import QWidget, QFrame, QVBoxLayout, QHBoxLayout, QPushButton, QComboBox, QButtonGroup
from PyQt5.QtCore import QSize
from app.ui.shared import get_icon

class CapturePanel(QWidget):
    """Modo de captura (Mic/Sistema/Ambos) y selección de dispositivos, colapsable."""
    def __init__(self, settings, parent=None):
        super().__init__(parent)
        self._collapsed = bool(settings.get("capture_collapsed", False))
        self.settings = settings

        outer = QVBoxLayout(self)
        outer.setContentsMargins(0, 0, 0, 0)
        outer.setSpacing(0)

        self.toggle_button = QPushButton("Fuente", self)
        self.toggle_button.setObjectName("sectionToggle")
        self.toggle_button.setToolTip("Modo de captura de audio: micrófono, sistema o ambos")
        self.toggle_button.clicked.connect(self._toggle)
        outer.addWidget(self.toggle_button)

        self.body = QFrame(self)
        self.body.setObjectName("captureBody")
        layout = QVBoxLayout(self.body)
        layout.setContentsMargins(0, 4, 0, 0)
        layout.setSpacing(6)

        mode_row = QHBoxLayout()
        mode_row.setContentsMargins(0, 0, 0, 0)
        mode_row.setSpacing(6)

        self.capture_mode_group = QButtonGroup(self)
        self.capture_mode_group.setExclusive(True)

        self.capture_mic_btn = QPushButton("Micrófono", self)
        self.capture_mic_btn.setObjectName("modeButton")
        self.capture_mic_btn.setCheckable(True)
        self.capture_mic_btn.setIcon(get_icon("mic"))
        self.capture_mic_btn.setIconSize(QSize(16, 16))
        self.capture_mic_btn.setToolTip("Solo micrófono")

        self.capture_sys_btn = QPushButton("Sistema", self)
        self.capture_sys_btn.setObjectName("modeButton")
        self.capture_sys_btn.setCheckable(True)
        self.capture_sys_btn.setIcon(get_icon("monitor"))
        self.capture_sys_btn.setIconSize(QSize(16, 16))
        self.capture_sys_btn.setToolTip("Solo audio del sistema")

        self.capture_both_btn = QPushButton("Ambos", self)
        self.capture_both_btn.setObjectName("modeButton")
        self.capture_both_btn.setCheckable(True)
        self.capture_both_btn.setIcon(get_icon("mic_monitor"))
        self.capture_both_btn.setIconSize(QSize(16, 16))
        self.capture_both_btn.setToolTip("Micrófono y sistema")

        for btn in (self.capture_mic_btn, self.capture_sys_btn, self.capture_both_btn):
            self.capture_mode_group.addButton(btn)
            mode_row.addWidget(btn, 1)

        device_row = QHBoxLayout()
        device_row.setContentsMargins(0, 0, 0, 0)
        device_row.setSpacing(6)

        self.mic_combo = QComboBox(self)
        self.mic_combo.setObjectName("deviceCombo")
        self.mic_combo.setToolTip("Seleccionar dispositivo de micrófono de entrada")

        self.sys_combo = QComboBox(self)
        self.sys_combo.setObjectName("deviceCombo")
        self.sys_combo.setToolTip("Seleccionar salida de audio del sistema (loopback)")

        self.refresh_button = QPushButton("", self)
        self.refresh_button.setObjectName("edgeButton")
        self.refresh_button.setIcon(get_icon("refresh"))
        self.refresh_button.setIconSize(QSize(14, 14))
        self.refresh_button.setToolTip("Actualizar dispositivos")

        device_row.addWidget(self.mic_combo, 1)
        device_row.addWidget(self.sys_combo, 1)
        device_row.addWidget(self.refresh_button, 0)

        layout.addLayout(mode_row)
        layout.addLayout(device_row)
        outer.addWidget(self.body)

        self._apply_visibility()

    def _toggle(self):
        self._collapsed = not self._collapsed
        self.settings.set("capture_collapsed", self._collapsed)
        self._apply_visibility()

    def _apply_visibility(self):
        self.body.setVisible(not self._collapsed)
        self._update_toggle_icon()
        window = self.window()
        if window and hasattr(window, "adjustSize"):
            window.adjustSize()

    def _update_toggle_icon(self):
        self.toggle_button.setIcon(get_icon("expand" if self._collapsed else "collapse"))

    def apply_mode(self, mode: str):
        self.mic_combo.setVisible(mode in ("mic", "both"))
        self.sys_combo.setVisible(mode in ("system", "both"))

    def reload_icons(self):
        self.capture_mic_btn.setIcon(get_icon("mic"))
        self.capture_sys_btn.setIcon(get_icon("monitor"))
        self.capture_both_btn.setIcon(get_icon("mic_monitor"))
        self.refresh_button.setIcon(get_icon("refresh"))
        self._update_toggle_icon()
