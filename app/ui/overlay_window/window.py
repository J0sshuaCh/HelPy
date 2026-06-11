import sys
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QFrame, QApplication, QLabel
from PyQt5.QtCore import Qt, pyqtSignal, QSize

from app.core.assistant_controller import AssistantController
from app.ui.shared import ui_settings, DragMixin, apply_capture_affinity, update_window_position, apply_window_size, get_icon

from .ui import HeaderArea, PositionBar, DevicePanel, CapturePanel, RecordingPanel, TextDisplayPanel
from .device_manager import DeviceManager
from .theme_manager import ThemeManager
from .ai_config import AIConfigPanel
from .tray import TrayManager
from .hotkeys import HotkeyManager

class OverlayWindow(DragMixin, QWidget):
    text_received = pyqtSignal(str)
    status_changed = pyqtSignal(str)
    llm_received = pyqtSignal(str)

    def __init__(self, parent=None):
        super().__init__(parent)
        
        # State
        self.recording = False
        self.is_collapsed = ui_settings.get("collapsed", False)
        self.position_mode = ui_settings.get("position_mode", "right")
        self.capture_visible = ui_settings.get("capture_visible", False)
        self.opacity = ui_settings.get("overlay_opacity", 100)
        self.capture_mode = ui_settings.get("capture_mode", "both")
        
        # Core Assistant
        self.assistant = AssistantController(
            mic_device_index=ui_settings.get("mic_device_index"),
            system_device_index=ui_settings.get("system_device_index"),
            capture_mode=self.capture_mode,
        )
        self.assistant.on_result(self._on_transcription_result)
        self.assistant.on_status(self._on_status_change)
        self.assistant.on_llm_result(self._on_llm_result)

        # Signals
        self.text_received.connect(self._set_transcription_safe)
        self.status_changed.connect(self._set_status_safe)
        self.llm_received.connect(self._set_llm_safe)

        self._init_ui()
        
        # Managers
        self.theme_manager = ThemeManager(ui_settings, self)
        self.device_manager = DeviceManager(self.assistant, self.device_panel, ui_settings, self)
        
        # Insert AI Panel
        self.ai_config_panel = AIConfigPanel(ui_settings, self.theme_manager, self.container)
        self.container_layout.insertWidget(4, self.ai_config_panel)

        # Tray and Hotkeys
        self.tray_manager = TrayManager(self, self.assistant, self.device_manager)
        self.hotkey_manager = HotkeyManager(self)
        
        self._apply_settings()
        
        # Initial refresh
        self.device_manager.refresh()
        apply_window_size(self)
        
        self.show()
        self.adjustSize()
        self.update_position()
        self._apply_capture_affinity()

    def _init_ui(self):
        self.setWindowFlags(Qt.FramelessWindowHint | Qt.WindowStaysOnTopHint | Qt.Tool)
        self.setAttribute(Qt.WA_TranslucentBackground)

        self.main_layout = QVBoxLayout(self)
        self.main_layout.setContentsMargins(0, 0, 0, 0)
        self.main_layout.setSpacing(0)

        # UI Components
        self.header_area = HeaderArea(initial_opacity=self.opacity, parent=self)
        self.header_area.opacity_slider.valueChanged.connect(self._apply_global_opacity)
        self.header_area.capture_button.clicked.connect(self.toggle_capture_visibility)
        self.header_area.edge_button.clicked.connect(self.toggle_collapsed)
        self.main_layout.addWidget(self.header_area)

        self.container = QFrame(self)
        self.container.setObjectName("overlayContainer")
        self.container_layout = QVBoxLayout(self.container)
        self.container_layout.setContentsMargins(16, 5, 16, 16)
        self.container_layout.setSpacing(10)
        
        self.position_bar = PositionBar(initial_opacity=self.opacity, parent=self)
        self.position_bar.pos_left_btn.clicked.connect(lambda: self.set_position_mode("left"))
        self.position_bar.pos_center_btn.clicked.connect(lambda: self.set_position_mode("center"))
        self.position_bar.pos_right_btn.clicked.connect(lambda: self.set_position_mode("right"))
        self.position_bar.opacity_slider.valueChanged.connect(self._apply_global_opacity)
        self.container_layout.addWidget(self.position_bar)
        
        self.device_panel = DevicePanel(self)
        self.container_layout.addWidget(self.device_panel)
        
        self.capture_panel = CapturePanel(self)
        self.capture_panel.capture_mic_btn.clicked.connect(lambda: self.set_capture_mode("mic"))
        self.capture_panel.capture_sys_btn.clicked.connect(lambda: self.set_capture_mode("system"))
        self.capture_panel.capture_both_btn.clicked.connect(lambda: self.set_capture_mode("both"))
        self.container_layout.addWidget(self.capture_panel)
        
        self.recording_panel = RecordingPanel(self)
        self.recording_panel.record_button.clicked.connect(self.toggle_recording)
        self.recording_panel.send_button.clicked.connect(self.assistant.send_buffer_to_llm)
        self.recording_panel.refresh_button.clicked.connect(lambda: self.device_manager.refresh())
        self.container_layout.addWidget(self.recording_panel)
        
        self.status_label = QLabel("Estado: listo", self)
        self.status_label.setObjectName("statusLabel")
        self.container_layout.addWidget(self.status_label)

        self.warning_label = QLabel("", self)
        self.warning_label.setObjectName("warningLabel")
        self.warning_label.setVisible(False)
        self.container_layout.addWidget(self.warning_label)
        
        # Text display added at the end
        self.text_display = TextDisplayPanel(self)
        self.container_layout.addWidget(self.text_display)
        self.text_display.llm_text.document().contentsChanged.connect(self._update_llm_height)
        
        self.main_layout.addWidget(self.container)

    def _apply_settings(self):
        mic_mode = ui_settings.get("mic_mode")
        if mic_mode == "manual":
            self.assistant.set_mic_settings(mic_mode="manual", mic_energy_threshold=120, mic_dynamic=False, mic_adjust_duration=0.0)
            self.tray_manager.update_mic_mode("manual")
        elif mic_mode == "auto":
            self.assistant.set_mic_settings(mic_mode="auto", mic_energy_threshold=150, mic_dynamic=True, mic_adjust_duration=0.8)
            self.tray_manager.update_mic_mode("auto")

        if self.is_collapsed:
            self.container.setVisible(False)
            self.header_area.edge_button.setIcon(get_icon("expand"))
            self.header_area.edge_button.setToolTip("Expandir")
            
        self._update_capture_button()
        self._apply_capture_affinity()
        
        self.assistant.set_capture_mode(self.capture_mode)
        self._set_capture_mode_ui(self.capture_mode)
        self._update_capture_mode_warning()
        self.setWindowOpacity(self.opacity / 100.0)

    # --- Actions ---
    def toggle_recording(self):
        if self.recording:
            self.recording = False
            self.tray_manager.update_recording_state(False)
            self.recording_panel.record_button.setText("Grabar")
            self.assistant.stop_recording_and_transcribe()
        else:
            self.recording = True
            self.tray_manager.update_recording_state(True)
            self.recording_panel.record_button.setText("Parar")
            self.assistant.start_recording()

    def set_capture_mode(self, mode: str):
        if mode not in ("mic", "system", "both"): return
        self.capture_mode = mode
        ui_settings.set("capture_mode", mode)
        self.assistant.set_capture_mode(mode)
        self._set_capture_mode_ui(mode)
        self._update_capture_mode_warning()

    def set_position_mode(self, mode):
        self.position_mode = mode
        ui_settings.set("position_mode", mode)
        self.update_position()

    def update_position(self):
        update_window_position(self, self.position_mode)

    def toggle_collapsed(self):
        self.is_collapsed = not self.is_collapsed
        self.container.setVisible(not self.is_collapsed)
        icon_name = "expand" if self.is_collapsed else "collapse"
        self.header_area.edge_button.setIcon(get_icon(icon_name))
        self.header_area.edge_button.setToolTip("Expandir" if self.is_collapsed else "Retractar")
        ui_settings.set("collapsed", self.is_collapsed)
        self.adjustSize()

    def toggle_capture_visibility(self):
        self.capture_visible = not self.capture_visible
        ui_settings.set("capture_visible", self.capture_visible)
        self._apply_capture_affinity()
        self._update_capture_button()

    def toggle_mic_mode(self):
        if self.assistant.transcriber.mic_mode == "auto":
            self.assistant.set_mic_settings(mic_mode="manual", mic_energy_threshold=120, mic_dynamic=False, mic_adjust_duration=0.0)
            self.tray_manager.update_mic_mode("manual")
            self._set_status_safe("Modo microfono manual")
            ui_settings.set("mic_mode", "manual")
        else:
            self.assistant.set_mic_settings(mic_mode="auto", mic_energy_threshold=150, mic_dynamic=True, mic_adjust_duration=0.8)
            self.tray_manager.update_mic_mode("auto")
            self._set_status_safe("Modo microfono auto")
            ui_settings.set("mic_mode", "auto")

    def quit_app(self):
        self.assistant.cleanup()
        self.tray_manager.hide()
        QApplication.quit()

    # --- UI Helpers ---
    def _apply_global_opacity(self, value):
        self.opacity = value
        ui_settings.set("overlay_opacity", value)
        self.setWindowOpacity(value / 100.0)
        # Sync both sliders
        self.header_area.opacity_slider.blockSignals(True)
        self.position_bar.opacity_slider.blockSignals(True)
        self.header_area.opacity_slider.setValue(value)
        self.position_bar.opacity_slider.setValue(value)
        self.header_area.opacity_slider.blockSignals(False)
        self.position_bar.opacity_slider.blockSignals(False)

    def _apply_capture_affinity(self):
        apply_capture_affinity(int(self.winId()), self.capture_visible)

    def _update_capture_button(self):
        icon_name = "eye" if self.capture_visible else "eye_off"
        self.header_area.capture_button.setIcon(get_icon(icon_name))
        self.header_area.capture_button.setToolTip("Visible en captura" if self.capture_visible else "Oculto en captura")

    def _set_capture_mode_ui(self, mode: str):
        self.capture_panel.capture_mic_btn.setChecked(mode == "mic")
        self.capture_panel.capture_sys_btn.setChecked(mode == "system")
        self.capture_panel.capture_both_btn.setChecked(mode == "both")
        if hasattr(self.tray_manager, "capture_mode_mic_action"):
            self.tray_manager.capture_mode_mic_action.setChecked(mode == "mic")
            self.tray_manager.capture_mode_sys_action.setChecked(mode == "system")
            self.tray_manager.capture_mode_both_action.setChecked(mode == "both")

    def _update_capture_mode_warning(self):
        mic_ok = self.device_manager.mic_available()
        sys_ok = self.device_manager.system_audio_available()
        
        if self.capture_mode == "mic" and not mic_ok:
            self._set_warning("Microfono no disponible")
        elif self.capture_mode == "system" and not sys_ok:
            self._set_warning("Audio del equipo no disponible")
        elif self.capture_mode == "both":
            if not mic_ok and not sys_ok:
                self._set_warning("Microfono y audio del equipo no disponibles")
            elif not mic_ok:
                self._set_warning("Microfono no disponible")
            elif not sys_ok:
                self._set_warning("Audio del equipo no disponible")
            else:
                self._set_warning("")
        else:
            self._set_warning("")

    def _set_warning(self, message: str):
        if not message:
            self.warning_label.setVisible(False)
            self.warning_label.setText("")
            return
        texto = message if message.startswith("Advertencia") else f"Advertencia: {message}"
        self.warning_label.setText(texto)
        self.warning_label.setVisible(True)

    def _update_llm_height(self):
        doc_height = int(self.text_display.llm_text.document().size().height())
        padding = self.text_display.llm_text.frameWidth() * 2 + 12
        desired = doc_height + padding
        desired = max(self.text_display.llm_min_height, min(desired, self.text_display.llm_max_height))
        self.text_display.llm_text.setFixedHeight(desired)
        self.adjustSize()
        self.update_position()

    # --- Callbacks ---
    def _on_transcription_result(self, text: str):
        self.text_received.emit(text)

    def _on_llm_result(self, text: str):
        self.llm_received.emit(text)

    def _on_status_change(self, msg: str):
        self.status_changed.emit(msg)

    def _set_transcription_safe(self, text: str):
        self.text_display.transcription_text.setPlainText(text)
        scrollbar = self.text_display.transcription_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())

    def _set_status_safe(self, msg: str):
        self.status_label.setText(f"Estado: {msg}")
        if msg.startswith("No se pudo") or msg.startswith("Error"):
            self._set_warning(msg)

    def _set_llm_safe(self, text: str):
        self.text_display.llm_text.setPlainText(text)
        scrollbar = self.text_display.llm_text.verticalScrollBar()
        scrollbar.setValue(scrollbar.maximum())
        self._update_llm_height()

    # --- Events ---
    def keyPressEvent(self, event):
        if event.key() == Qt.Key_Escape:
            self.close()
        if event.key() == Qt.Key_Space and event.modifiers() & Qt.ControlModifier:
            self.toggle_recording()
        super().keyPressEvent(event)

    def closeEvent(self, event):
        self.assistant.cleanup()
        self.tray_manager.hide()
        self.hotkey_manager.stop()
        QApplication.quit()
