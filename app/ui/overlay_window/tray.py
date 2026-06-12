from PyQt5.QtWidgets import QSystemTrayIcon, QMenu, QAction, QActionGroup
from PyQt5.QtGui import QIcon, QPixmap, QColor
from PyQt5.QtCore import QObject
from app.ui.shared import get_icon

class TrayManager(QObject):
    def __init__(self, parent_window, assistant, device_manager):
        super().__init__(parent_window)
        self.window = parent_window
        self.assistant = assistant
        self.device_manager = device_manager
        self.tray_icon = None
        self.init_tray_icon()

    def reload_icons(self):
        self.capture_mode_mic_action.setIcon(get_icon("mic"))
        self.capture_mode_sys_action.setIcon(get_icon("monitor"))
        self.capture_mode_both_action.setIcon(get_icon("mic_monitor"))

    def init_tray_icon(self):
        pixmap = QPixmap(16, 16)
        pixmap.fill(QColor(0, 120, 215))
        icon = QIcon(pixmap)

        self.tray_icon = QSystemTrayIcon(icon, self.window)

        menu = QMenu()
        self.record_action = menu.addAction("Iniciar grabacion")
        self.record_action.triggered.connect(self.window.toggle_recording)
        menu.addSeparator()

        devices_action = menu.addAction("Dispositivos")
        devices_menu = QMenu()
        devices_action.setMenu(devices_menu)
        
        self.mic_menu = QMenu("Microfono")
        self.sys_menu = QMenu("Sistema")
        devices_menu.addMenu(self.mic_menu)
        devices_menu.addMenu(self.sys_menu)
        
        # Link menus to device manager
        self.device_manager.set_menus(self.mic_menu, self.sys_menu)

        self.loopback_action = menu.addAction("Loopback soportado: ?")
        self.loopback_action.setEnabled(False)

        capture_mode_action = menu.addAction("Modo captura")
        capture_mode_menu = QMenu()
        capture_mode_action.setMenu(capture_mode_menu)

        self.capture_mode_group_tray = QActionGroup(self.window)
        self.capture_mode_group_tray.setExclusive(True)

        self.capture_mode_mic_action = QAction("Microfono", self.window)
        self.capture_mode_mic_action.setCheckable(True)
        self.capture_mode_mic_action.setIcon(get_icon("mic"))
        self.capture_mode_mic_action.triggered.connect(lambda: self.window.set_capture_mode("mic"))

        self.capture_mode_sys_action = QAction("Equipo", self.window)
        self.capture_mode_sys_action.setCheckable(True)
        self.capture_mode_sys_action.setIcon(get_icon("monitor"))
        self.capture_mode_sys_action.triggered.connect(lambda: self.window.set_capture_mode("system"))

        self.capture_mode_both_action = QAction("Ambos", self.window)
        self.capture_mode_both_action.setCheckable(True)
        self.capture_mode_both_action.setIcon(get_icon("mic_monitor"))
        self.capture_mode_both_action.triggered.connect(lambda: self.window.set_capture_mode("both"))

        self.capture_mode_group_tray.addAction(self.capture_mode_mic_action)
        self.capture_mode_group_tray.addAction(self.capture_mode_sys_action)
        self.capture_mode_group_tray.addAction(self.capture_mode_both_action)

        capture_mode_menu.addAction(self.capture_mode_mic_action)
        capture_mode_menu.addAction(self.capture_mode_sys_action)
        capture_mode_menu.addAction(self.capture_mode_both_action)

        mic_mode_action = menu.addAction("Modo microfono: Auto")
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
        estado = "SI" if soporta else "NO"
        if hasattr(self, "loopback_action"):
            self.loopback_action.setText(f"Loopback soportado: {estado}")

    def update_recording_state(self, is_recording: bool):
        if hasattr(self, "record_action"):
            if is_recording:
                self.record_action.setText("Detener grabacion")
                self.record_action.setIcon(QIcon())
            else:
                self.record_action.setText("Iniciar grabacion")

    def update_mic_mode(self, mode: str):
        if hasattr(self, "mic_mode_action"):
            if mode == "manual":
                self.mic_mode_action.setText("Modo microfono: Manual")
            else:
                self.mic_mode_action.setText("Modo microfono: Auto")

    def hide(self):
        if self.tray_icon:
            self.tray_icon.hide()
