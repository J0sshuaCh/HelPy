import sounddevice as sd
import soundcard as sc
from PyQt5.QtWidgets import QAction
from PyQt5.QtCore import QObject

class DeviceManager(QObject):
    def __init__(self, assistant, device_panel, settings, window):
        super().__init__(window)
        self.assistant = assistant
        self.device_panel = device_panel
        self.settings = settings
        self.window = window
        
        self.mic_menu = None
        self.sys_menu = None
        self.mic_devices = []
        self.sys_devices = []
        
        # Connect combos
        self.device_panel.mic_combo.currentIndexChanged.connect(self._on_mic_combo_changed)
        self.device_panel.sys_combo.currentIndexChanged.connect(self._on_sys_combo_changed)

    def set_menus(self, mic_menu, sys_menu):
        self.mic_menu = mic_menu
        self.sys_menu = sys_menu

    def refresh(self):
        if self.mic_menu:
            self.mic_menu.clear()
        if self.sys_menu:
            self.sys_menu.clear()
            
        self.device_panel.mic_combo.blockSignals(True)
        self.device_panel.sys_combo.blockSignals(True)
        
        self.device_panel.mic_combo.clear()
        self.device_panel.sys_combo.clear()
        self.mic_devices = []
        self.sys_devices = []

        try:
            devices = sd.query_devices()
            hostapis = sd.query_hostapis()
            
            for i, info in enumerate(devices):
                name = info.get("name", "Desconocido")
                api = hostapis[info.get("hostapi", 0)].get("name", "?")
                label = f"{i}: {name} ({api})"
                if info.get("max_input_channels", 0) > 0:
                    if self.mic_menu:
                        action = QAction(label, self.window)
                        action.triggered.connect(lambda checked, idx=i: self.set_mic_device(idx))
                        self.mic_menu.addAction(action)
                    self.device_panel.mic_combo.addItem(f"Microfono: {name} ({api})")
                    self.mic_devices.append(i)

            speakers = sc.all_speakers()
            for i, s in enumerate(speakers):
                label = f"Salida: {s.name}"
                if self.sys_menu:
                    action = QAction(label, self.window)
                    action.triggered.connect(lambda checked, idx=i: self.set_sys_device(idx))
                    self.sys_menu.addAction(action)
                self.device_panel.sys_combo.addItem(label)
                self.sys_devices.append(i)
        except Exception as e:
            print(f"Error enumerating devices: {e}")

        self.device_panel.mic_combo.blockSignals(False)
        self.device_panel.sys_combo.blockSignals(False)
        self._update_device_tooltips()
        self.sync_device_selection()
        self.window._update_capture_mode_warning()

    def set_mic_device(self, device_index: int):
        self.assistant.set_devices(device_index, self.assistant.transcriber.system_device_index)
        self.window._set_status_safe(f"Microfono: {device_index}")
        self.settings.set("mic_device_index", device_index)
        self.sync_device_selection()
        self.window._update_capture_mode_warning()

    def set_sys_device(self, device_index: int):
        self.assistant.set_devices(self.assistant.transcriber.mic_device_index, device_index)
        self.window._set_status_safe(f"Sistema: {device_index}")
        self.settings.set("system_device_index", device_index)
        self.sync_device_selection()
        self.window._update_capture_mode_warning()

    def sync_device_selection(self):
        mic_index = self.assistant.transcriber.mic_device_index
        sys_index = self.assistant.transcriber.system_device_index
        if mic_index in self.mic_devices:
            self.device_panel.mic_combo.blockSignals(True)
            self.device_panel.mic_combo.setCurrentIndex(self.mic_devices.index(mic_index))
            self.device_panel.mic_combo.blockSignals(False)
        if sys_index in self.sys_devices:
            self.device_panel.sys_combo.blockSignals(True)
            self.device_panel.sys_combo.setCurrentIndex(self.sys_devices.index(sys_index))
            self.device_panel.sys_combo.blockSignals(False)

    def _update_device_tooltips(self):
        self.device_panel.mic_combo.setToolTip(self.device_panel.mic_combo.currentText())
        self.device_panel.sys_combo.setToolTip(self.device_panel.sys_combo.currentText())

    def _on_mic_combo_changed(self, index):
        if index < 0 or index >= len(self.mic_devices):
            return
        self._update_device_tooltips()
        self.set_mic_device(self.mic_devices[index])

    def _on_sys_combo_changed(self, index):
        if index < 0 or index >= len(self.sys_devices):
            return
        self._update_device_tooltips()
        self.set_sys_device(self.sys_devices[index])

    def system_audio_available(self) -> bool:
        try:
            return len(sc.all_speakers()) > 0
        except Exception:
            return False

    def mic_available(self) -> bool:
        try:
            devices = sd.query_devices()
            for info in devices:
                if info.get("max_input_channels", 0) > 0:
                    return True
        except Exception:
            pass
        return False
