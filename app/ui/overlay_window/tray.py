from PyQt5.QtWidgets import QSystemTrayIcon, QMenu
from PyQt5.QtGui import QIcon
from PyQt5.QtCore import QObject
from app.ui.shared import ui_settings
from app.ui.shared.icons import get_logo_pixmap

class TrayManager(QObject):
    def __init__(self, parent_window, assistant, device_manager):
        super().__init__(parent_window)
        self.window = parent_window
        self.assistant = assistant
        self.device_manager = device_manager
        self.tray_icon = None
        self.init_tray_icon()

    def init_tray_icon(self):
        icon = QIcon(get_logo_pixmap(32, 32))
        self.tray_icon = QSystemTrayIcon(icon, self.window)

        menu = QMenu()
        self.record_action = menu.addAction("Iniciar grabación")
        self.record_action.triggered.connect(self.window.toggle_recording)
        config_action = menu.addAction("Configuración")
        config_action.triggered.connect(self.window.open_preferences)
        guide_action = menu.addAction("Guía de inicio")
        guide_action.triggered.connect(self._reopen_guide)
        menu.addSeparator()

        devices_action = menu.addAction("Dispositivos")
        devices_menu = QMenu()
        devices_action.setMenu(devices_menu)
        
        self.mic_menu = QMenu("Micrófono")
        self.sys_menu = QMenu("Audio del sistema")
        devices_menu.addMenu(self.mic_menu)
        devices_menu.addMenu(self.sys_menu)
        
        # Link menus to device manager
        self.device_manager.set_menus(self.mic_menu, self.sys_menu)

        self.loopback_action = menu.addAction("Captura de audio del sistema: ?")
        self.loopback_action.setEnabled(False)

        mic_mode_action = menu.addAction("Sensibilidad del micrófono: Automática")
        mic_mode_action.triggered.connect(self.window.toggle_mic_mode)
        self.mic_mode_action = mic_mode_action
        
        menu.addSeparator()
        quit_action = menu.addAction("Salir")
        quit_action.triggered.connect(self.window.quit_app)

        self.tray_icon.setContextMenu(menu)
        self.tray_icon.show()
        self.update_loopback_status()

    def update_loopback_status(self):
        soporta = self.assistant.supports_system_loopback()
        estado = "Sí" if soporta else "No"
        if hasattr(self, "loopback_action"):
            self.loopback_action.setText(f"Captura de audio del sistema: {estado}")

    def update_recording_state(self, is_recording: bool):
        if hasattr(self, "record_action"):
            if is_recording:
                self.record_action.setText("Detener grabación")
                self.record_action.setIcon(QIcon())
            else:
                self.record_action.setText("Iniciar grabación")

    def update_mic_mode(self, mode: str):
        if hasattr(self, "mic_mode_action"):
            if mode == "manual":
                self.mic_mode_action.setText("Sensibilidad del micrófono: Fija")
            else:
                self.mic_mode_action.setText("Sensibilidad del micrófono: Automática")

    def hide(self):
        if self.tray_icon:
            self.tray_icon.hide()

    def _reopen_guide(self):
        """Reabre la guía de inicio desde el menú de bandeja."""
        ui_settings.set("onboarding_completed", False)
        if hasattr(self.window, "_show_onboarding"):
            self.window._show_onboarding()
